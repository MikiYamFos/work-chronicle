"""Claim-evidence extraction pipeline.

Two user-facing modes:

  coverletter extract           — extract, judge, insert
  coverletter extract --dry-run — extract, judge, write review files for Streamlit review

After dry-run, open the Streamlit app to label claims. The app inserts approved claims
directly into the DB — no separate CLI command.

Internal quality gates (automatic, not user-initiated):
  - Judge runs on every claim before insertion. Not optional.
  - Judge is validated against gold standard at the start of every extraction run.
    If alignment drops below threshold, warns so you know to fix the judge prompt.
    Does not block extraction (gold standard may not exist yet).

Design constraints:
  - Claims are at the OWNERSHIP/DECISION level — matchable to JD requirements
  - Support items are the evidence that makes claims believable
  - Sub-details preserve technical specifics near-verbatim
  - Conclusions are insights, not summaries
  - Nested structure — claims own their evidence directly (no index references)
  - Raw Q&A feeds sub-details only, not new claims
"""
from __future__ import annotations

import json
import re
import sqlite3
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from coverletter.costs import record, supports_temperature
from coverletter.db import load_argument_categories

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

_EXTRACT_MODEL = "claude-haiku-4-5-20251001"
_JUDGE_MODEL   = "claude-haiku-4-5-20251001"

# Per-provider fast model for extraction and judging.
# When a non-Anthropic model is passed to extraction, this maps to the
# cheapest capable model for that provider.
_FAST_MODELS: dict[str, str] = {
    "anthropic": "claude-haiku-4-5-20251001",
    "mistral": "mistral/mistral-small-latest",
    "openai": "openai/gpt-4o-mini",
}


def _fast_model_for(model: str) -> str:
    """Return the cheap/fast model for the same provider as `model`."""
    from coverletter.provider import parse_model
    provider, _ = parse_model(model)
    return _FAST_MODELS.get(provider, _JUDGE_MODEL)

# Judge accuracy threshold. Below this, warn that the judge prompt needs work.
_JUDGE_ACCURACY_THRESHOLD = 0.80

# Minimum gold standard size for reliable judge validation.
_GS_MIN_APPROVED = 5
_GS_MIN_REJECTED = 5

# ---------------------------------------------------------------------------
# Extraction prompt
# ---------------------------------------------------------------------------

def _build_extract_system() -> str:
    """Build the extraction system prompt, loading argument categories from file.

    Called once per extraction run. Categories are read from
    coverletter/evals/argument_categories.json — adding a category there
    automatically updates this prompt with no code change.
    """
    categories = load_argument_categories()
    if categories:
        cat_lines = "\n".join(
            f"  - {c['name']}: {c['description']}"
            for c in categories
        )
        cat_names = ", ".join(f'"{c["name"]}"' for c in categories)
        cat_block = f"""━━━ ARGUMENT CATEGORIES ━━━

Every claim must be tagged with one or more argument categories. A claim can serve
multiple categories — tag all that apply.

Available categories:
{cat_lines}

Add argument_categories to each claim as a JSON array of category name strings.
Example: "argument_categories": ["accountability", "stakeholder_fluency"]

━━━ ANCHOR PHRASES ━━━

Some support items contain load-bearing language — the specific phrases from the
writer's own words that carry both the argument and their voice. These phrases must
reach letter generation intact, not summarized. Flag them with is_anchor: true.

A support item is an anchor if:
  - It contains phrasing from the source text that is specific, vivid, and irreplaceable
  - Summarizing it would lose the voice or the precision
  - It is the kind of sentence a hiring manager would remember

Example: "figuring out whole workflows and procedures, writing documentation and
training people on systems I worked out" → is_anchor: true
Example: "processed play/pause/seek/heartbeat events" → is_anchor: false (describes
what happened, not load-bearing language)

"""
        format_extra = f"""  "argument_categories": [{cat_names.split(",")[0]}, ...],  // one or more from the category list
      "support": [
        {{
          "text": "top-level evidence point proving the claim",
          "is_anchor": false,  // true if this phrase must reach generation verbatim
          "details": [
            "sub-detail: technical specifics near-verbatim"
          ]
        }}
      ]"""
    else:
        cat_block = ""
        format_extra = """  "support": [
        {
          "text": "top-level evidence point proving the claim",
          "is_anchor": false,
          "details": [
            "sub-detail: technical specifics near-verbatim"
          ]
        }
      ]"""

    return f"""\
You are extracting structured argument components from career writing.

Your output feeds a cover letter construction system. Claims will be matched against
job description requirements. Support items will be used as required evidence in
paragraphs. The quality of what you extract determines whether arguments can be built.

━━━ WHAT MAKES A GOOD CLAIM ━━━

A claim is what you would say to a hiring manager in one sentence to make them
understand what this person DID, HOW THEY WORK, WHO THEY ARE, or WHY THIS WORK
MATTERS TO THEM — and where specific evidence could back it up.

A cover letter makes five kinds of arguments. Extract claims in all five categories:

1. OWNERSHIP / DECISION — what the person built, owned, or decided at a specific employer
   GOOD: "At Acme Corp, I owned the subscriber data pipeline end-to-end"
   GOOD: "At Acme Corp, I determined what 'watch duration' meant before any engineering began"

2. APPROACH / METHOD — how the person thinks about and does the work, consistently
   GOOD: "I work backwards from what someone needs to understand into the data model that produces it"

3. DISPOSITION / CHARACTER — who the person IS as an engineer, their professional standing
   GOOD: "I had accountability for data integrity at a level that is rare for data engineers"

4. MOTIVATION / ORIENTATION — what kind of work the person finds meaningful and why
   GOOD: "I am most excited by work where careful engineering makes organizations more accountable"

5. PERSONAL PROJECT — context type must be "project", not "employer".

━━━ THE QUALITY BAR ━━━

The core test: CAN THIS BE BACKED UP WITH SPECIFIC EVIDENCE?

  INVALID: "I have experience with event-based data" — not provable, just said
  VALID: "I work backwards from output requirements into data models" — provable across employers
  INVALID: "I care about data quality" — just words
  VALID: "I had data integrity accountability at a level rare for a DE" — specific standing, provable

Granularity: a claim is at the RIGHT level if it could anchor a paragraph argument.
  TOO SPECIFIC: "I implemented 30-minute gap logic" — that's a support item
  TOO GENERIC: "I am a data engineer" — says nothing specific
  RIGHT: "At BritBox, I owned the watch-duration pipeline and defined the metric before writing code"

Use the person's actual words and register. Do not polish into resume-speak.

{cat_block}━━━ SUPPORT ITEMS AND SUB-DETAILS ━━━

Support items are what make claims believable — the specific facts, decisions,
and technical realities that prove the claim is true.

Two levels:
  - Top-level: the main evidence point
  - Sub-detail (nested in "details"): nuance, technical specifics, the how and why

CRITICAL — preserve technical detail exactly. Do not compress. Do not summarize.

━━━ CONCLUSIONS ━━━

A conclusion is an insight that emerges from all the claims together — what the
evidence MEANS about this person. Only include if the paragraph explicitly states one.
If no conclusion is present, conclusion is null.

━━━ SOURCING RULES ━━━

Extract ONLY what is explicitly stated. Do not infer, generalize, or add anything
not directly present in the text.

When raw Q&A is provided: use it to find technical detail compressed in the paragraph.
Do NOT extract claims from Q&A that aren't supported by the paragraph text itself.

━━━ OUTPUT FORMAT ━━━

Return ONLY valid JSON. No preamble.

{{
  "claims": [
    {{
      "text": "claim in person's actual words",
      "contexts": [
        {{"type": "employer", "name": "Acme Corp"}}
      ],
      {format_extra}
    }}
  ],
  "conclusion": "insight string or null"
}}

context type: "employer" for companies, "project" for personal projects.
General claims not grounded in one place: contexts is [].
details is [] if no sub-details. is_anchor defaults to false.
"""


# Build once at module load time. Re-import to pick up category changes.
_EXTRACT_SYSTEM = _build_extract_system()

# ---------------------------------------------------------------------------
# Judge prompt — aligned against gold standard failure patterns
#
# Alignment process (from evals/gold_standard_claims.json):
#   - 9 rejected examples with labeled failure categories
#   - Judge must be STRICT: high recall (catch all bad claims) is more
#     important than precision (false rejects can be fixed in review)
#   - Rules derived directly from observed failure patterns
# ---------------------------------------------------------------------------

def _build_judge_system() -> str:
    """Build the judge system prompt, loading argument categories from file.

    Called once per extraction run. Categories are read from
    coverletter/evals/argument_categories.json — adding a category there
    automatically updates this prompt with no code change.
    """
    categories = load_argument_categories()
    if categories:
        cat_lines = "\n".join(
            f"  - {c['name']}: {c['description']}"
            for c in categories
        )
        anchor_block = f"""━━━ ARGUMENT CATEGORIES AND ANCHOR CHECK ━━━

The claim has been tagged with one or more argument categories. Evaluate whether
the claim is specific enough to constitute a real argument for each category it claims.

Categories and what makes a claim work for each:
{cat_lines}

For each tagged category, ask: does this claim assert something specific enough
that evidence could prove it for that category? A claim tagged "accountability"
with no specific ownership or outcome language is incomplete. A claim tagged
"stakeholder_fluency" with no specific translation or training language is incomplete.

If the claim is tagged with categories but the text doesn't support any of them
specifically — fail it.

"""
    else:
        anchor_block = ""

    return f"""\
You are evaluating whether a claim extracted from a career paragraph is well-formed
for use in a cover letter argument construction system.

━━━ THE CORE TEST ━━━

Ask one question: CAN THIS CLAIM BE BACKED UP WITH SPECIFIC EVIDENCE?

A claim is valid if it makes an assertion about this person — what they DID, how they WORK,
who they ARE as an engineer, or what KIND of work they find meaningful — AND there is any
plausible way to substantiate it with specific experiences, episodes, or patterns.

A claim is invalid if it is pure assertion with nothing behind it — no evidence could
prove or disprove it because it is just words.

━━━ USE THE SOURCE PARAGRAPH ━━━

You are given the source paragraph alongside the claim. Use it.

If a claim reads as broad or thin in isolation, check the source paragraph. If the source
paragraph contains specific facts, episodes, or named work that could back the claim up,
the claim is valid even if the claim text itself is general. The claim is a heading; the
paragraph is the evidence beneath it.

PASS claims where the source paragraph makes substantiation plausible, even if the claim
alone would look thin.

━━━ VALID CLAIM TYPES ━━━

1. EMPLOYER-SPECIFIC OWNERSHIP: Named employer, named deliverable, ownership verb.
   PASS: "At Acme Corp, I owned the data pipeline end-to-end"
   FAIL: "I have experience with event-based data" — just said, not provable

2. CROSS-EMPLOYER THESIS: Spans the whole career, specific enough to be provable.
   PASS: "I had data integrity accountability at a level rare for data engineers"

3. APPROACH / METHOD: Describes HOW this person consistently works.
   PASS: "I work backwards from what someone needs to understand into the data model"
   PASS: "I built production Python while staying deeply thoughtful about non-technical users"
        — broad, no employer named, but provable from the work history in the source paragraph
   FAIL: "I have strong skills in Python" — names a tool, not a way of working

4. DISPOSITION / CHARACTER: Who the person IS — backed by real work history.
   PASS: "I spent years caring for data where precision was non-negotiable — that's rare for a DE"
   PASS: "I am the kind of engineer who treats the question before the query as real work"
        — broad, but the source paragraph likely contains specific episodes that prove it
   FAIL: "I care about data quality" — says nothing a hiring manager could verify

5. MOTIVATION / ORIENTATION: Specific about WHAT kind of work and WHY.
   PASS: "I am most excited by work where careful engineering makes organizations more accountable"
   FAIL: "I am passionate about data" — says nothing specific

6. PERSONAL PROJECT: Context type must be "project", not "employer".

{anchor_block}━━━ DEFINITELY INVALID ━━━

INVALID — PURE CAPABILITY STATEMENT:
   Names a tool or skill but makes no claim about how the person works or what they built.
   FAIL: "I have experience with event-based data"
   FAIL: "I work comfortably in both Airflow and dbt"
   Note: "I used Airflow to build X at Y" is valid — it names what was done, not just the tool.

INVALID — SHOULD BE A SUPPORT ITEM:
   Describes what a SYSTEM did, not what the PERSON owned or decided.
   FAIL: "The pipeline processed play, pause, seek, heartbeat signals"

INVALID — WRONG CONTEXT TYPE:
   Personal projects listed as employers.

INVALID — PURE SUMMARY / RESUME-SPEAK:
   "demonstrates", "showcases", "this shows my", "strong background in", "ability to"

INVALID — NEGATIVE FRAMING:
   "I have never needed X" — claims prove what was done/true, not what was avoided.

━━━ ON ARGUMENT CATEGORIES ━━━

The claim has been tagged with argument categories. Treat these as hints about what type
of claim it is — not as a pass/fail test. Category tagging is imperfect. A valid claim
tagged with the wrong category is still a valid claim. Do not fail a claim because its
text doesn't perfectly match its tagged category. Judge the claim on its own merits using
the core test above.

━━━ WHEN IN DOUBT: PASS ━━━

If a claim is broad but provable given the source paragraph, pass it. The human reviewer
can reject it in the app. Only reject claims that are clearly unsubstantiatable — where
no specific evidence could possibly back them up — or clearly wrong in type/structure.

Reason through your assessment, then return ONLY the JSON:
{{"pass": true}} or {{"pass": false, "reason": "one sentence naming the specific failure"}}
"""


_JUDGE_SYSTEM = _build_judge_system()

# ---------------------------------------------------------------------------
# Grounding validation (deterministic, no LLM)
# ---------------------------------------------------------------------------

_STOP = {
    "i", "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "did", "not", "my", "we", "it", "this", "that",
    "as", "so", "its", "all", "can", "also", "into", "which", "when", "where",
    "what", "how", "who", "their", "they", "you", "would", "could", "just",
}

_SUMMARY_SIGNALS = {
    "demonstrates", "showcases", "shows", "illustrates", "highlights",
    "reflects", "underscores", "proves my", "experience with", "ability to",
    "skills in", "strong background", "this shows", "this demonstrates",
}


def _meaningful(text: str) -> set[str]:
    words = set(re.findall(r"[a-z][a-z0-9]*", text.lower()))
    return {w for w in words if len(w) > 3 and w not in _STOP}


def _is_grounded(text: str, source_text: str, raw: str | None) -> bool:
    combined = (source_text + " " + (raw or "")).lower()
    m = _meaningful(text)
    if not m:
        return True
    return sum(1 for w in m if w in combined) / len(m) >= 0.45


def _is_summary_conclusion(text: str) -> bool:
    lower = text.lower()
    return any(sig in lower for sig in _SUMMARY_SIGNALS)


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

def _call_haiku(system: str, content: str, api_key: str, model: str, max_tokens: int = 256) -> str:
    from coverletter.provider import get_provider
    return get_provider(model, api_key).complete(system, content, max_tokens=max_tokens)


def _extract_json_object(text: str) -> dict:
    """Extract the first complete JSON object from text, ignoring surrounding prose."""
    # Strip code fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    # Find first { and parse from there, ignoring trailing content
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")
    obj, _ = json.JSONDecoder().raw_decode(text, start)
    return obj


def _extract_from_paragraph(para_text: str, raw: str | None, api_key: str, model: str) -> dict:
    if raw:
        content = (
            "=== PARAGRAPH (refined — primary source; extract claims from here) ===\n"
            f"{para_text.strip()}\n\n"
            "=== RAW Q&A SESSION (use only to find technical detail compressed in paragraph) ===\n"
            f"{raw.strip()}"
        )
    else:
        content = para_text.strip()
    raw_resp = _call_haiku(_EXTRACT_SYSTEM, content, api_key, model, max_tokens=2048)
    return _extract_json_object(raw_resp)


def _judge_claim(claim_text: str, para_text: str, api_key: str, model: str = _JUDGE_MODEL) -> tuple[bool, str]:
    """Run the judge on a single claim. Returns (passed, reason)."""
    judge_model = _fast_model_for(model)
    prompt = f"Source paragraph:\n{para_text.strip()}\n\nClaim to judge:\n{claim_text}"
    try:
        raw = _call_haiku(_JUDGE_SYSTEM, prompt, api_key, judge_model, max_tokens=512)
        data = _extract_json_object(raw)
        if data.get("pass"):
            return True, ""
        return False, data.get("reason", "failed quality check")
    except Exception:
        return True, ""  # parse failure — don't block


# ---------------------------------------------------------------------------
# Embedding helper
# ---------------------------------------------------------------------------

def _embed_texts(texts: list[str], voyage_api_key: str) -> list[bytes | None]:
    if not voyage_api_key or not texts:
        return [None] * len(texts)
    try:
        import voyageai  # type: ignore
        client = voyageai.Client(api_key=voyage_api_key)
        result = client.embed(texts, model="voyage-3-lite", input_type="document")
        return [json.dumps(v).encode() if v else None for v in result.embeddings]
    except Exception:
        return [None] * len(texts)


# ---------------------------------------------------------------------------
# DB insertion helpers
# ---------------------------------------------------------------------------

def _extract_employer(claim: dict) -> str | None:
    for ctx in claim.get("contexts", []):
        if ctx.get("type") == "employer":
            return ctx.get("name")
    return None


def _insert_one_claim(
    conn: sqlite3.Connection,
    claim: dict,
    para_hash: str,
    voyage_api_key: str,
) -> int | None:
    """Insert a single claim with its contexts, support items, and sub-details.
    Returns claim ID or None if skipped (empty text).
    """
    text = claim.get("text", "").strip()
    if not text:
        return None

    emb_list = _embed_texts([text], voyage_api_key)
    emb = emb_list[0] if emb_list else None

    arg_cats = claim.get("argument_categories", [])
    arg_cats_str = json.dumps(arg_cats) if arg_cats else None

    cur = conn.execute(
        "INSERT INTO claims (text, source_para_hash, embedding, argument_categories) VALUES (?, ?, ?, ?)",
        (text, para_hash, emb, arg_cats_str),
    )
    claim_id = cur.lastrowid

    for ctx in claim.get("contexts", []):
        ctx_type = ctx.get("type", "employer")
        ctx_name = ctx.get("name", "").strip()
        if ctx_name:
            conn.execute(
                "INSERT INTO claim_contexts (claim_id, context_type, context_name) VALUES (?, ?, ?)",
                (claim_id, ctx_type, ctx_name),
            )

    employer = _extract_employer(claim)
    for pos, support in enumerate(claim.get("support", [])):
        support_text = support.get("text", "").strip()
        if not support_text:
            continue
        emb_list = _embed_texts([support_text], voyage_api_key)
        s_emb = emb_list[0] if emb_list else None
        is_anchor = 1 if support.get("is_anchor") else 0
        cur2 = conn.execute(
            "INSERT INTO support_items "
            "(claim_id, parent_id, text, employer, position, source_para_hash, embedding, is_anchor) "
            "VALUES (?, NULL, ?, ?, ?, ?, ?, ?)",
            (claim_id, support_text, employer, pos, para_hash, s_emb, is_anchor),
        )
        support_id = cur2.lastrowid

        for d_pos, detail in enumerate(support.get("details", [])):
            detail = detail.strip()
            if not detail:
                continue
            conn.execute(
                "INSERT INTO support_items "
                "(claim_id, parent_id, text, employer, position, source_para_hash, embedding) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (claim_id, support_id, detail, employer, d_pos, para_hash),
            )

    return claim_id


def _insert_conclusion(
    conn: sqlite3.Connection,
    text: str,
    claim_ids: list[int],
    para_hash: str,
    voyage_api_key: str,
) -> None:
    if not text or _is_summary_conclusion(text):
        return
    emb_list = _embed_texts([text], voyage_api_key)
    cur = conn.execute(
        "INSERT INTO conclusions (text, source_para_hash, embedding) VALUES (?, ?, ?)",
        (text, para_hash, emb_list[0] if emb_list else None),
    )
    cid = cur.lastrowid
    for claim_id in claim_ids:
        conn.execute(
            "INSERT OR IGNORE INTO conclusion_claims (conclusion_id, claim_id) VALUES (?, ?)",
            (cid, claim_id),
        )


# ---------------------------------------------------------------------------
# Internal judge alignment check
#
# Runs automatically at the start of every extraction.
# If the judge is misaligned (accuracy below threshold), warns to stdout.
# Does NOT block extraction — gold standard may not exist yet.
# ---------------------------------------------------------------------------

def _check_gold_standard_readiness() -> tuple[bool, str]:
    """Return (ready, message). Ready means gold standard has enough examples to validate the judge."""
    gs_path = Path(__file__).parent / "evals" / "gold_standard_claims.json"
    if not gs_path.exists():
        return False, (
            "No gold standard found. Run `coverletter extract --dry-run` first,\n"
            "then open the Streamlit review app and label claims — checking\n"
            "'Save as gold standard example' on clear approved and rejected cases.\n"
            "Need at least 5 approved + 5 rejected before running full extraction.\n"
            "  uv run streamlit run coverletter/label_evals.py"
        )
    gs = json.loads(gs_path.read_text(encoding="utf-8"))
    examples = gs.get("examples", [])
    approved = sum(1 for e in examples if e["label"] == "approved")
    rejected = sum(1 for e in examples if e["label"] == "rejected")
    if approved < _GS_MIN_APPROVED or rejected < _GS_MIN_REJECTED:
        parts = []
        if approved < _GS_MIN_APPROVED:
            parts.append(f"{_GS_MIN_APPROVED - approved} more approved examples")
        if rejected < _GS_MIN_REJECTED:
            parts.append(f"{_GS_MIN_REJECTED - rejected} more rejected examples")
        return False, (
            f"Gold standard too small to validate judge ({approved} approved, {rejected} rejected).\n"
            f"Need {' and '.join(parts)}.\n"
            "Open the review app and label more claims, checking 'Save as gold standard example':\n"
            "  uv run streamlit run coverletter/label_evals.py"
        )
    return True, ""


def _check_judge_alignment(api_key: str) -> dict | None:
    """Validate judge against gold standard. Called internally before extraction.

    Returns alignment report dict, or None if gold standard not available.
    Emits a warning if accuracy is below threshold — does not raise.
    """
    gs_path = Path(__file__).parent / "evals" / "gold_standard_claims.json"
    if not gs_path.exists():
        return None

    gs = json.loads(gs_path.read_text(encoding="utf-8"))
    examples = gs.get("examples", [])
    if not examples:
        return None

    results = []
    for ex in examples:
        claim_text = ex["claim_text"]
        human_label = ex["label"]
        judge_pass, judge_reason = _judge_claim(claim_text, claim_text, api_key)
        judge_label = "approved" if judge_pass else "rejected"
        results.append({
            "id": ex["id"],
            "claim_text": claim_text,
            "human_label": human_label,
            "judge_label": judge_label,
            "judge_reason": judge_reason,
            "correct": judge_label == human_label,
            "failure_categories": ex.get("failure_categories", []),
        })

    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    accuracy = correct / total if total else 0

    approved_total = sum(1 for r in results if r["human_label"] == "approved")
    false_negatives = [r for r in results if r["human_label"] == "approved" and r["judge_label"] == "rejected"]
    false_positives = [r for r in results if r["human_label"] == "rejected" and r["judge_label"] == "approved"]
    true_positives = approved_total - len(false_negatives)
    precision = true_positives / (true_positives + len(false_positives)) if (true_positives + len(false_positives)) else 0
    recall = true_positives / approved_total if approved_total else 0

    report = {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }

    if accuracy < _JUDGE_ACCURACY_THRESHOLD:
        warnings.warn(
            f"Judge accuracy {accuracy:.0%} is below threshold {_JUDGE_ACCURACY_THRESHOLD:.0%}. "
            f"FP: {len(false_positives)}, FN: {len(false_negatives)}. "
            f"Run coverletter/evals/align_judge.py to see disagreements and fix the judge prompt.",
            stacklevel=3,
        )

    return report


# ---------------------------------------------------------------------------
# Review file generation (for dry-run mode)
# ---------------------------------------------------------------------------

def _build_review_entry(
    para_hash: str,
    para_text: str,
    role: str,
    section: str,
    raw: str | None,
    data: dict,
    judge_results: dict[int, tuple[bool, str]],
) -> dict:
    claims_out = []
    for i, claim in enumerate(data.get("claims", [])):
        passed, reason = judge_results.get(i, (True, ""))
        entry: dict = {
            "text": claim.get("text", ""),
            "contexts": claim.get("contexts", []),
            "support": claim.get("support", []),
            "judge": {"pass": passed, "reason": reason or None},
            # Judge rejection pre-marks as rejected; human can override in app
            "status": "pending" if passed else "rejected",
        }
        claims_out.append(entry)

    return {
        "para_hash": para_hash,
        "role": role,
        "section": section,
        "para_text": para_text,
        "raw_response_available": raw is not None,
        "claims": claims_out,
        "conclusion": data.get("conclusion"),
        "warning": data.get("_zero_claim_warning"),
    }


def _write_review_markdown(review_data: dict, path: Path) -> None:
    lines = [
        f"# Extraction Review — {review_data['generated_at'][:10]}",
        f"Model: {review_data['model_used']}",
        f"Judge alignment: {review_data.get('judge_accuracy', 'not checked')}",
        f"{len(review_data['paragraphs'])} paragraph(s)\n",
        "Open the Streamlit app to review and insert:",
        "  uv run streamlit run coverletter/label_evals.py\n",
        "---\n",
    ]

    for para in review_data["paragraphs"]:
        lines.append(f"## {para['role']} / {para['section']}")
        lines.append(f"*hash: {para['para_hash'][:12]}...*  "
                     f"{'[raw Q&A available]' if para['raw_response_available'] else ''}\n")
        lines.append("**Paragraph:**")
        for line in para["para_text"].splitlines():
            lines.append(f"> {line}")
        lines.append("")

        if para.get("warning"):
            lines.append(f"> ⚠️ **{para['warning']}**\n")
        if not para["claims"]:
            lines.append("*No claims extracted.*\n")
        else:
            for i, claim in enumerate(para["claims"]):
                judge = claim.get("judge", {})
                judge_tag = " ✅" if judge.get("pass") else f" ❌ ({judge.get('reason', '')})"
                status = claim.get("status", "pending").upper()
                lines.append(f"### Claim {i + 1}  [{status}]{judge_tag}")
                lines.append(f"> {claim['text']}\n")
                ctxs = ", ".join(f"{c['type']}: {c['name']}" for c in claim.get("contexts", []))
                if ctxs:
                    lines.append(f"*Contexts: {ctxs}*\n")
                for s in claim.get("support", []):
                    lines.append(f"- {s['text']}")
                    for d in s.get("details", []):
                        lines.append(f"  - {d}")
                lines.append("")

        if para.get("conclusion"):
            lines.append(f"**Conclusion:** {para['conclusion']}\n")

        lines.append("---\n")

    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Concurrent processing helpers
# ---------------------------------------------------------------------------

def _judge_claims_concurrent(
    claims: list[dict],
    para_text: str,
    api_key: str,
    max_workers: int,
    model: str = _JUDGE_MODEL,
) -> dict[int, tuple[bool, str]]:
    """Judge all claims in one paragraph concurrently. Returns {index: (passed, reason)}."""
    results: dict[int, tuple[bool, str]] = {}
    eligible = [(i, claim.get("text", "")) for i, claim in enumerate(claims) if claim.get("text", "")]
    if not eligible:
        return results

    def _one(i: int, text: str) -> tuple[int, bool, str]:
        passed, reason = _judge_claim(text, para_text, api_key, model)
        return i, passed, reason

    with ThreadPoolExecutor(max_workers=min(max_workers, len(eligible))) as pool:
        futures = {pool.submit(_one, i, text): i for i, text in eligible}
        for future in as_completed(futures):
            i, passed, reason = future.result()
            results[i] = (passed, reason)

    return results


def _process_paragraph_for_review(
    para_hash: str,
    para_text: str,
    role: str,
    section: str,
    raw: str | None,
    api_key: str,
    model: str,
    max_workers: int,
) -> dict:
    """Extract + judge one paragraph. Pure compute — no DB access. Thread-safe."""
    try:
        data = _extract_from_paragraph(para_text, raw, api_key, model)
    except Exception as e:
        data = {"claims": [], "conclusion": None, "_error": str(e)}

    if not data.get("claims") and raw is not None:
        data["_zero_claim_warning"] = (
            "This paragraph came from a Q&A session but contains no extractable claims. "
            "A paragraph should yield at least one claim — about what was built or owned, "
            "how the person works, who they are as an engineer, or what draws them to this kind of work. "
            "Review the paragraph and consider rebuilding it with `coverletter build`."
        )

    judge_results = _judge_claims_concurrent(data.get("claims", []), para_text, api_key, max_workers, model)
    return _build_review_entry(para_hash, para_text, role, section, raw, data, judge_results)


def _process_paragraph_for_insert(
    para_hash: str,
    para_text: str,
    section: str,
    raw: str | None,
    api_key: str,
    model: str,
    max_workers: int,
) -> tuple[str, list[dict], str | None]:
    """Extract + judge + filter one paragraph. Pure compute — no DB access. Thread-safe.

    Returns (para_hash, approved_claims, conclusion_text).
    Approved means: non-empty, grounded, judge-passed.
    """
    try:
        data = _extract_from_paragraph(para_text, raw, api_key, model)
    except Exception:
        return para_hash, [], None

    if not data.get("claims") and raw is not None:
        warnings.warn(
            f"Q&A paragraph produced 0 claims — no extractable assertions about what was built, "
            f"how the person works, their professional character, or their orientation toward the work. "
            f"Consider rebuilding with `coverletter build`.\nSection: {section}",
            stacklevel=4,
        )

    claims = data.get("claims", [])
    eligible = [
        (i, claim) for i, claim in enumerate(claims)
        if claim.get("text", "").strip() and _is_grounded(claim.get("text", ""), para_text, raw)
    ]

    if not eligible:
        return para_hash, [], data.get("conclusion")

    judge_results = _judge_claims_concurrent(
        [c for _, c in eligible], para_text, api_key, max_workers, model
    )
    # judge_results keys are 0..len(eligible)-1 (re-indexed inside _judge_claims_concurrent)
    approved = [claim for j, (_, claim) in enumerate(eligible) if judge_results.get(j, (True, ""))[0]]

    return para_hash, approved, data.get("conclusion")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_to_review(
    conn: sqlite3.Connection,
    api_key: str,
    model: str = _EXTRACT_MODEL,
    force: bool = False,
    max_workers: int = 4,
) -> dict:
    """Extract from all pending paragraphs and return review data. Inserts nothing.

    Paragraphs are processed concurrently (extract + judge per paragraph run in
    parallel); claims within each paragraph are also judged concurrently.
    DB is read serially before dispatch and results are collected in order after.

    Judge alignment is checked if gold standard exists; skipped if not (first run is ok).
    """
    gs_ready, gs_msg = _check_gold_standard_readiness()
    if not gs_ready:
        warnings.warn(
            f"Gold standard not yet ready — judge results unvalidated.\n{gs_msg}",
            stacklevel=2,
        )
        alignment = None
    else:
        alignment = _check_judge_alignment(api_key)

    if force:
        rows = conn.execute(
            "SELECT text_hash, text, role, section FROM paragraphs WHERE active = 1"
        ).fetchall()
    else:
        already = {
            r[0] for r in conn.execute(
                "SELECT DISTINCT source_para_hash FROM claims WHERE source_para_hash IS NOT NULL"
            ).fetchall()
        }
        rows = [
            r for r in conn.execute(
                "SELECT text_hash, text, role, section FROM paragraphs WHERE active = 1"
            ).fetchall()
            if r["text_hash"] not in already
        ]

    # Fetch raw Q&A for each paragraph while still on the DB connection (serial, cheap).
    para_inputs: list[tuple] = []
    for row in rows:
        raw_row = conn.execute(
            "SELECT responses_md FROM raw_responses WHERE para_text_hash = ? "
            "ORDER BY captured_at DESC LIMIT 1",
            (row["text_hash"],),
        ).fetchone()
        para_inputs.append((
            row["text_hash"], row["text"], row["role"], row["section"],
            raw_row["responses_md"] if raw_row else None,
        ))

    if not para_inputs:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_used": model,
            "paragraph_count": 0,
            "judge_accuracy": "gold standard not found",
            "paragraphs": [],
        }

    # Dispatch extract+judge work concurrently across paragraphs.
    # Each future is keyed by its original position so we can restore order.
    ordered: list[dict | None] = [None] * len(para_inputs)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                _process_paragraph_for_review,
                para_hash, para_text, role, section, raw,
                api_key, model, max_workers,
            ): idx
            for idx, (para_hash, para_text, role, section, raw) in enumerate(para_inputs)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                ordered[idx] = future.result()
            except Exception as e:
                para_hash, para_text, role, section, raw = para_inputs[idx]
                ordered[idx] = _build_review_entry(
                    para_hash, para_text, role, section, raw,
                    {"claims": [], "conclusion": None, "_error": str(e)}, {},
                )

    paragraphs_out = [e for e in ordered if e is not None]
    judge_accuracy = f"{alignment['accuracy']:.0%}" if alignment else "gold standard not found"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_used": model,
        "paragraph_count": len(paragraphs_out),
        "judge_accuracy": judge_accuracy,
        "paragraphs": paragraphs_out,
    }


def insert_from_review(
    conn: sqlite3.Connection,
    review_data: dict,
    voyage_api_key: str = "",
) -> tuple[int, int]:
    """Insert approved claims from review data into the DB.

    Called directly by the Streamlit app — not a CLI command.
    Returns (claims_inserted, paragraphs_processed).
    """
    claims_inserted = 0
    paragraphs_processed = 0

    for para in review_data.get("paragraphs", []):
        para_hash = para.get("para_hash", "")
        conclusion_text = para.get("conclusion")
        inserted_claim_ids: list[int] = []

        for claim in para.get("claims", []):
            if claim.get("status") != "approved":
                continue
            claim_id = _insert_one_claim(conn, claim, para_hash, voyage_api_key)
            if claim_id is not None:
                inserted_claim_ids.append(claim_id)
                claims_inserted += 1

        if conclusion_text and inserted_claim_ids:
            _insert_conclusion(conn, conclusion_text, inserted_claim_ids, para_hash, voyage_api_key)

        if inserted_claim_ids:
            paragraphs_processed += 1

    conn.commit()
    return claims_inserted, paragraphs_processed


def extract_claims_and_evidence(
    conn: sqlite3.Connection,
    api_key: str,
    model: str = _EXTRACT_MODEL,
    voyage_api_key: str = "",
    force: bool = False,
    max_workers: int = 4,
) -> tuple[int, dict | None]:
    """Extract, judge, and insert claims from all pending paragraphs.

    Extract + judge work runs concurrently across paragraphs (and claims within
    each paragraph are judged concurrently). DB writes happen serially after all
    concurrent work is done — SQLite does not allow concurrent writes.

    Judge alignment is checked first. If no gold standard exists, raises so the
    CLI can redirect to onboarding.
    Returns (paragraphs_processed, alignment_report).
    """
    gs_ready, gs_msg = _check_gold_standard_readiness()
    if not gs_ready:
        raise RuntimeError(gs_msg)
    alignment = _check_judge_alignment(api_key)

    if force:
        rows = conn.execute(
            "SELECT text_hash, text, section FROM paragraphs WHERE active = 1"
        ).fetchall()
    else:
        already = {
            r[0] for r in conn.execute(
                "SELECT DISTINCT source_para_hash FROM claims WHERE source_para_hash IS NOT NULL"
            ).fetchall()
        }
        rows = [
            r for r in conn.execute(
                "SELECT text_hash, text, section FROM paragraphs WHERE active = 1"
            ).fetchall()
            if r["text_hash"] not in already
        ]

    if not rows:
        return 0, alignment

    # Fetch raw Q&A while still on the DB connection (serial, cheap).
    para_inputs: list[tuple] = []
    for row in rows:
        raw_row = conn.execute(
            "SELECT responses_md FROM raw_responses WHERE para_text_hash = ? "
            "ORDER BY captured_at DESC LIMIT 1",
            (row["text_hash"],),
        ).fetchone()
        para_inputs.append((
            row["text_hash"], row["text"], row["section"],
            raw_row["responses_md"] if raw_row else None,
        ))

    # Dispatch extract+judge concurrently. Results are (para_hash, approved_claims, conclusion).
    results: list[tuple[str, list[dict], str | None]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                _process_paragraph_for_insert,
                para_hash, para_text, section, raw,
                api_key, model, max_workers,
            ): (para_hash, para_text, section, raw)
            for para_hash, para_text, section, raw in para_inputs
        }
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception:
                para_hash = futures[future][0]
                results.append((para_hash, [], None))

    # Serial DB writes — SQLite requires this.
    processed = 0
    for para_hash, approved_claims, conclusion in results:
        if not approved_claims:
            continue
        inserted_ids: list[int] = []
        for claim in approved_claims:
            claim_id = _insert_one_claim(conn, claim, para_hash, voyage_api_key)
            if claim_id is not None:
                inserted_ids.append(claim_id)
        if conclusion and inserted_ids:
            _insert_conclusion(conn, conclusion, inserted_ids, para_hash, voyage_api_key)
        conn.commit()
        processed += 1

    return processed, alignment
