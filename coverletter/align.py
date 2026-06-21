from __future__ import annotations

import re
from dataclasses import dataclass, field

from coverletter.costs import record, supports_temperature
from coverletter.parser import Paragraph
from coverletter.profile import CandidateProfile

ARGUMENT_SYSTEM = """\
You are a cover letter strategist. Be direct and specific. No filler.
"""

ARGUMENT_PROMPT = """\
=== JOB DESCRIPTION ===
{jd}
{candidate_section}{evidence_section}
What is the single strongest argument for this candidate at this role?

Complete this sentence:
"This letter should argue that [candidate clause] is exactly what this role needs because \
[employer clause]."

Rules for the CANDIDATE CLAUSE:
- Read the CANDIDATE PROFILE — including working style, values, and what draws them to
  certain kinds of work. The candidate clause should reflect who this person actually is
  and what motivates them, not just a list of technical outputs.
  If this employer has a mission, find the overlap between the candidate's drives and that
  mission — that is the argument. "Someone who has spent their career building systems that
  change what decision-makers can see" connects to a healthcare data mission. A pure technical
  credential list does not.
- Name specific things they built, owned, or decided — not paraphrases of the JD
- Ground it in the evidence sentences above. The strongest arguments name what was at stake:
  what would have broken, who would have been harmed, what the output was used for.
  "shipping data that ran live in production applications where wrong data meant a broken product"
  is an argument. "owning every layer from ingestion to serving" is a list.
- Lead with what the candidate owned and delivered. Never frame around what was absent:
  WRONG: "with no team beneath them", "without a senior engineer to catch errors"
  RIGHT: "as the sole practitioner responsible for..." / "owning the full platform end-to-end..."
- No adjectives as arguments: "high-stakes", "consequential", "critical" are empty.
  Name the actual stake. What broke when it was wrong?

Rules for the EMPLOYER CLAUSE:
- Read the full JD — including any "About" or mission sections at the top. If the employer
  states a mission (what problem they exist to solve, who they serve, why it matters),
  the employer clause should reflect that — not just the technical requirements list.
  A mission-driven employer clause names what this organization is trying to do in the world
  and why this candidate's background makes them the right person to build for it.
- State what the JD is specifically seeking that this candidate uniquely provides
- No false comparisons: never "not inherit them", "not just X", "rather than Y"
  State what the role IS, not what it isn't.

- One sentence. Output only the sentence. No preamble. No em-dash.
"""

THESIS_SYSTEM = """\
You are a cover letter strategist.
{candidate_profile}
When evaluating a thesis, square THREE things simultaneously:
1. What the candidate wants from this role — goals, values, and what kind of work they find meaningful
2. What this JD is explicitly asking for
3. What angle the letter actually leads with

Mission alignment and values alignment count toward fit alongside technical goal overlap.
Express fit positively — what the role IS and what it offers the candidate.
Never frame fit as contrast, avoidance, or escape. Say what is true, not what it opposes.
Only name tensions that genuinely affect fit. Do not manufacture caveats.
Be direct and specific. No filler.
"""

THESIS_SYSTEM_EMPTY = """\
You are a cover letter strategist. Be direct and specific. No filler.
"""

THESIS_PROMPT = """\
=== JOB DESCRIPTION ===
{jd}

=== COVER LETTER ===
{letter}
{candidate_goals_section}{correction_section}
Write ONE sentence — the thesis of this cover letter. Complete this template:
"This letter argues that [candidate description] is the right fit for this role because \
[specific claim grounded in the letter's actual content]."

Rules:
- The claim must be specific to THIS letter and THIS JD. Name the actual experience or angle
  the letter leads with — not a generic description.
- Ground it in what the letter SAYS — specific experiences, decisions, or evidence named
  in the body paragraphs. Do not summarize goals or values not evidenced in the letter.
- One clause only. Do not add a second clause about why the role fits the candidate.
  That question belongs in the alignment report, not the thesis.
- Crisp enough that someone reading it could predict what evidence the body paragraphs contain.
{correction_rule}
Output only the one sentence. No preamble, no explanation.
"""

ALIGN_SYSTEM = """\
You are a job description analyst.

When seniority signals are provided, evaluate the letter against them. Flag a signal as
missing only if the letter genuinely doesn't address it — not if it is implicit. A letter
that describes owning a system through production incidents covers "production ownership"
without using that phrase.

Be direct, specific, and actionable. Do not be encouraging or add filler.
"""

SENIORITY_SIGNALS_BLOCK = """\
SENIORITY SIGNALS FOR THIS ROLE TYPE
{signals}
These are the dimensions that distinguish senior candidates from mid-level ones for this
role. Flag missing ones only if genuinely absent — not if they are implicit or understated.
"""

ALIGN_PROMPT = """\
=== PARAGRAPH LIBRARY (available but may not all be in the letter) ===
{library}

=== JOB DESCRIPTION ===
{jd}

=== CURRENT LETTER ===
{letter}
{seniority_signals_section}{candidate_goals_section}
Analyze how well the letter addresses the JD. Output exactly {num_sections} sections with no extra text.

SCORE: [N covered] of [M total] JD requirements

COVERED
One line per requirement the LETTER itself addresses — not the library.
A requirement is covered only if the letter contains sentences that address it.
A paragraph sitting in the library but absent from the letter does NOT count as covered.
Format: ✓ [requirement] — [how the letter covers it]

GAPS
One line per gap. A gap is anything the JD explicitly requires or prefers that the letter
does not address. If a library paragraph covers the gap but the letter omits it, it is
still a gap — note that the paragraph exists so the writer knows to include it.
Format: ✗ [requirement] — [why it matters; note "paragraph [N] covers this" if applicable]
{seniority_gaps_section}{goal_alignment_section}
Do not add encouragement, filler, or any sections beyond these {num_sections}.
"""

SENIORITY_GAPS_SECTION = """\

SENIORITY SIGNAL GAPS
One line per missing signal (see seniority signals above). Write "(none)" if all are covered.
These are not JD requirements — they are what separates senior candidates from mid-level ones.
Format: ✗ [signal] — [what's missing and why it matters]
"""

GOAL_ALIGNMENT_BLOCK = """\
GOAL ALIGNMENT
One line. Does this role serve the candidate's stated goals? Be direct — yes, partially, or no,
with one specific reason grounded in the JD and the candidate's goals.
"""




@dataclass
class AlignmentResult:
    raw_text: str
    covered: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    seniority_gaps: list[str] = field(default_factory=list)
    goal_alignment: str = ""
    score_pct: int = 0
    perspective_note: str = ""  # set when no narrative frame paragraphs are in the library

    def score_line(self) -> str:
        n = len(self.covered)
        m = n + len(self.gaps)
        base = f"{self.score_pct}% aligned ({n} covered, {len(self.gaps)} gap(s))"
        if self.seniority_gaps:
            base += f", {len(self.seniority_gaps)} seniority signal gap(s)"
        return base


def _parse_alignment(text: str) -> AlignmentResult:
    covered: list[str] = []
    gaps: list[str] = []
    seniority_gaps: list[str] = []
    goal_alignment = ""
    score_pct = 0

    score_match = re.search(r"SCORE:\s*(\d+)\s*covered.*?(\d+)\s*total", text, re.IGNORECASE)
    if score_match:
        n_covered = int(score_match.group(1))
        n_total = int(score_match.group(2))
        score_pct = round(100 * n_covered / n_total) if n_total else 0

    section = None
    for line in text.splitlines():
        stripped = line.strip()
        upper = stripped.upper()
        if "SENIORITY SIGNAL" in upper:
            section = "seniority"
            continue
        elif "GOAL ALIGNMENT" in upper:
            section = "goal"
            continue
        elif upper.startswith("COVERED"):
            section = "covered"
            continue
        elif upper.startswith("GAPS") and "GOAL" not in upper:
            section = "gaps"
            continue

        if stripped.startswith("✓"):
            covered.append(stripped[1:].strip())
        elif stripped.startswith("✗"):
            if section == "seniority":
                seniority_gaps.append(stripped[1:].strip())
            else:
                gaps.append(stripped[1:].strip())
        elif section == "goal" and stripped and not stripped.startswith("SCORE"):
            if goal_alignment:
                goal_alignment += " " + stripped
            else:
                goal_alignment = stripped

    if not score_pct and (covered or gaps):
        total = len(covered) + len(gaps)
        score_pct = round(100 * len(covered) / total) if total else 0

    return AlignmentResult(
        raw_text=text,
        covered=covered,
        gaps=gaps,
        seniority_gaps=seniority_gaps,
        goal_alignment=goal_alignment,
        score_pct=score_pct,
    )


def generate_thesis(
    jd: str,
    letter: str,
    api_key: str,
    model: str,
    profile: CandidateProfile | None = None,
    correction: str | None = None,
) -> str:

    if profile and not profile.is_empty:
        system = THESIS_SYSTEM.format(candidate_profile=profile.as_full_text())
        fit_context = profile.as_fit_context()
        candidate_goals_section = f"\n=== CANDIDATE FIT CONTEXT (background only — do not include in thesis) ===\n{fit_context}\n"
    else:
        system = THESIS_SYSTEM_EMPTY
        candidate_goals_section = ""

    correction_section = (
        f"\n=== CANDIDATE CORRECTION — PRIMARY INSTRUCTION ===\n{correction}\n"
        "The candidate has told you what is wrong or missing. Your revised thesis MUST use "
        "their specific language and include every point they raised. Do not rewrite from "
        "scratch. Do not ignore any part of the correction. Their words take priority over "
        "the rules below.\n"
        if correction else ""
    )

    correction_rule = (
        "- THE CANDIDATE CORRECTION above overrides everything else. Include every point "
        "they named, using their language where possible."
        if correction else
        "- If there is genuine tension between the letter's angle and the JD, name it briefly."
    )

    prompt = THESIS_PROMPT.format(
        jd=jd.strip(),
        letter=letter.strip(),
        candidate_goals_section=candidate_goals_section,
        correction_section=correction_section,
        correction_rule=correction_rule,
    )

    from coverletter.provider import get_provider
    return get_provider(model, api_key).complete(system, prompt, max_tokens=300)


def generate_argument(
    jd: str,
    api_key: str,
    model: str,
    profile: CandidateProfile | None = None,
    company_values: str | None = None,
    evidence_sentences: list[str] | None = None,
) -> str:
    """Generate a provisional argument target.

    When evidence_sentences are provided (post-retrieval), the argument is grounded in what
    the candidate actually wrote, not just what the JD asks for.
    When called without evidence (pre-retrieval fallback), the argument is JD-derived only.
    """

    if profile and not profile.is_empty:
        parts = [profile.as_goals_text(), profile.as_working_style_text(), profile.as_values_text(), profile.as_differentiators_text()]
        candidate_section = "\n=== CANDIDATE PROFILE ===\n" + "\n\n".join(p for p in parts if p) + "\n"
    else:
        candidate_section = ""

    values_section = (
        f"\n=== COMPANY VALUES / MISSION ===\n{company_values.strip()}\n"
        if company_values else ""
    )

    if evidence_sentences:
        # Cap to avoid ballooning the prompt — top sentences are highest-scored
        sample = evidence_sentences[:20]
        evidence_section = "\n=== CANDIDATE'S STRONGEST EVIDENCE (from their paragraph library) ===\n"
        evidence_section += "\n".join(f"- {s}" for s in sample) + "\n"
    else:
        evidence_section = ""

    prompt = ARGUMENT_PROMPT.format(
        jd=jd.strip() + values_section,
        candidate_section=candidate_section,
        evidence_section=evidence_section,
    )
    from coverletter.provider import get_provider
    return get_provider(model, api_key).complete(ARGUMENT_SYSTEM, prompt, max_tokens=200)


def alignment_report(
    jd: str,
    letter: str,
    filtered_paragraphs: list[Paragraph],
    api_key: str,
    model: str,
    profile: CandidateProfile | None = None,
) -> AlignmentResult:

    library_lines = []
    for p in filtered_paragraphs:
        library_lines.append(f"[{p.index}] {p.role} / {p.section}")
        library_lines.append(p.text)
        library_lines.append("")
    library_text = "\n".join(library_lines)

    has_profile = profile and not profile.is_empty
    has_signals = profile and bool(profile.seniority_signals)

    if has_profile:
        candidate_goals_section = f"\n=== CANDIDATE GOALS ===\n{profile.as_goals_text()}\n"
        goal_alignment_section = GOAL_ALIGNMENT_BLOCK
    else:
        candidate_goals_section = ""
        goal_alignment_section = ""

    if has_signals:
        signal_lines = "\n".join(f"- {s}" for s in profile.seniority_signals)
        seniority_signals_section = (
            f"\n=== SENIORITY SIGNALS ===\n{signal_lines}\n"
        )
        seniority_gaps_section = SENIORITY_GAPS_SECTION
    else:
        seniority_signals_section = ""
        seniority_gaps_section = ""

    num_sections_count = 2  # COVERED + GAPS always present
    if has_signals:
        num_sections_count += 1
    if has_profile:
        num_sections_count += 1
    num_sections = {2: "two", 3: "three", 4: "four"}.get(num_sections_count, str(num_sections_count))

    # Library is the stable part — cache it. JD + letter change per call.
    library_block = f"=== PARAGRAPH LIBRARY (available but may not all be in the letter) ===\n{library_text}"
    jd_block = ALIGN_PROMPT.format(
        jd=jd.strip(),
        letter=letter.strip(),
        seniority_signals_section=seniority_signals_section,
        candidate_goals_section=candidate_goals_section,
        library="",  # library is in its own cached block above
        seniority_gaps_section=seniority_gaps_section,
        goal_alignment_section=goal_alignment_section,
        num_sections=num_sections,
    ).replace("=== PARAGRAPH LIBRARY (available but may not all be in the letter) ===\n\n", "")

    user_content = [
        {"type": "text", "text": library_block, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": jd_block},
    ]

    from coverletter.provider import get_provider
    result = _parse_alignment(
        get_provider(model, api_key).complete(ALIGN_SYSTEM, user_content, max_tokens=1200)
    )

    # Perspective frame check — Python level, no LLM call needed.
    # If the library has no through-line, pivot, reframe, or synthesis paragraphs,
    # the letter has evidence but no narrative frame.
    from coverletter.prompt import PERSPECTIVE_ANGLES
    has_perspective = any(
        p.meta.get("angle", "").lower() in PERSPECTIVE_ANGLES
        for p in filtered_paragraphs
    )
    if not has_perspective:
        result.perspective_note = (
            "No through-line, pivot, reframe, or synthesis paragraph in library. "
            "The letter has evidence but no narrative frame. "
            "Run: coverletter reflect"
        )

    return result


# ---------------------------------------------------------------------------
# Library-only gap analysis (no letter required — for cold build mode)
# ---------------------------------------------------------------------------

# Coverage threshold: category cosine score below this → treat as a gap candidate.
_CATEGORY_GAP_THRESHOLD = 0.30
# Claim coverage threshold: highest claim score below this → no claim covers the category.
_CLAIM_COVERAGE_THRESHOLD = 0.35

_BUILD_PROMPT_SYSTEM = """\
You are a cover letter coach. For each argument category listed below that is a gap, write one
concrete, specific question or prompt the candidate can answer to build a paragraph for it.

Return ONLY valid JSON — a dict mapping category_name to build_prompt string:
{"category_name": "build_prompt", ...}

Rules:
- The prompt must be specific to the category and JD context — not generic ("tell me about your experience").
- Anchor to what the JD is actually asking for: "What pipeline did you build that handles real-time event data?"
- One sentence max per prompt.
"""


@dataclass
class LibraryGapResult:
    covered: list[dict]   # [{"requirement": str, "best_score": float, "best_claim": str}]
    gaps: list[dict]      # [{"requirement": str, "build_prompt": str}]
    no_db: bool = False   # True when DB/embeddings unavailable — caller should tell user

    @property
    def gap_requirements(self) -> list[str]:
        return [g["requirement"] for g in self.gaps]

    @property
    def gap_prompts(self) -> dict[str, str]:
        return {g["requirement"]: g.get("build_prompt", "") for g in self.gaps}


def library_gap_analysis(
    jd: str,
    api_key: str,
    model: str,
    conn: "sqlite3.Connection | None" = None,
    voyage_api_key: str = "",
    embed_provider: "object | None" = None,
) -> "LibraryGapResult":
    """Analyze JD coverage using the claims DB — no LLM scan of the full library.

    Steps:
    1. Embed the JD using provider-native or Voyage embeddings.
    2. Score against category_embeddings (already in DB) — zero cost beyond one embed call.
    3. For weak categories, check best matching claim score from claims table.
    4. Covered = strong category score OR a claim that scores above threshold.
       Gap = category is weak AND no claim covers it.
    5. One targeted LLM call to generate a concrete build_prompt per gap category.

    Falls back to BM25 paragraph matching if no DB or no embeddings.
    """
    import json, re as _re, sqlite3
    from coverletter.provider import get_provider
    from coverletter.db import embed_query, get_or_embed_jd, _cosine

    provider = get_provider(model, api_key)
    effective_embed = embed_provider or provider

    # --- Embed the JD (cached if conn available) ---
    if conn is not None:
        jd_embedding = get_or_embed_jd(conn, jd, voyage_api_key, effective_embed)
    else:
        jd_embedding = embed_query(jd, voyage_api_key, effective_embed)

    covered: list[dict] = []
    gaps: list[dict] = []

    if conn is not None and jd_embedding is not None:
        # --- DB path: category + claim scoring ---
        from coverletter.db import get_category_embeddings, score_jd_against_categories

        category_embeddings = get_category_embeddings(conn)
        if not category_embeddings:
            return LibraryGapResult(covered=[], gaps=[], no_db=True)

        cat_scores = score_jd_against_categories(jd_embedding, category_embeddings)

        # Load all claim embeddings once
        rows = conn.execute(
            "SELECT id, text, argument_categories, embedding FROM claims WHERE embedding IS NOT NULL"
        ).fetchall()
        claim_rows = []
        for row in rows:
            try:
                emb = json.loads(row["embedding"])
                claim_rows.append({
                    "id": row["id"],
                    "text": row["text"],
                    "cats": json.loads(row["argument_categories"]) if row["argument_categories"] else [],
                    "emb": emb,
                })
            except Exception:
                pass

        gap_categories: list[str] = []
        for cat_name, cat_score in cat_scores:
            cat_claims = [c for c in claim_rows if cat_name in c["cats"]]
            best_claim_score = max(
                (_cosine(jd_embedding, c["emb"]) for c in cat_claims),
                default=0.0,
            )
            best_claim_text = ""
            if cat_claims:
                best_claim_text = max(cat_claims, key=lambda c: _cosine(jd_embedding, c["emb"]))["text"]

            if cat_score >= _CATEGORY_GAP_THRESHOLD or best_claim_score >= _CLAIM_COVERAGE_THRESHOLD:
                covered.append({
                    "requirement": cat_name,
                    "best_score": round(best_claim_score, 3),
                    "best_claim": best_claim_text[:120] if best_claim_text else "",
                })
            else:
                gap_categories.append(cat_name)

        # Generate build prompts for gap categories in one small LLM call
        if gap_categories:
            gap_list = "\n".join(f"- {c}" for c in gap_categories)
            content = (
                f"=== JOB DESCRIPTION ===\n{jd.strip()[:800]}\n\n"
                f"=== GAP CATEGORIES (not covered by the candidate's library) ===\n{gap_list}"
            )
            raw = provider.complete(_BUILD_PROMPT_SYSTEM, content, max_tokens=512)
            raw = _re.sub(r"^```(?:json)?\s*", "", raw.strip())
            raw = _re.sub(r"\s*```$", "", raw)
            try:
                prompts: dict[str, str] = json.loads(raw)
            except Exception:
                prompts = {}
            for cat_name in gap_categories:
                gaps.append({
                    "requirement": cat_name,
                    "build_prompt": prompts.get(cat_name, ""),
                })

        return LibraryGapResult(covered=covered, gaps=gaps)

    # No DB or no embeddings — caller should prompt user to run sync + extract.
    return LibraryGapResult(covered=[], gaps=[], no_db=True)


def has_library_coverage(gap: str) -> bool:
    """Stub — semantic gap coverage check against claims DB not yet wired into gap loop.
    Returns False so all gaps show as actionable until DB connection is threaded through."""
    return False
