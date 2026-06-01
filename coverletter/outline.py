"""Outline assembly from the claim-evidence database.

Given a JD (and optionally an existing thesis from generate_argument()), pulls
relevant claims from the DB, groups them into argument-driven paragraph blocks,
attaches support hierarchy with anchor phrases flagged, and writes an editable
markdown outline.

The outline is the human's review point before letter construction. Anchor phrases
are marked explicitly — they are the load-bearing language from the writer's own
words that must reach generation intact.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from coverletter.costs import record, supports_temperature
from coverletter.db import load_argument_categories

# ---------------------------------------------------------------------------
# Argument category grouping prompt — built dynamically from categories file
# ---------------------------------------------------------------------------

# Categories that stand alone as their own paragraph block rather than grouping
# with evidence claims. These are the argument about WHO the person is.
_STANDALONE_CATEGORIES = {
    "approach_method", "disposition", "motivation", "communication", "leadership"
}

# Categories that group with other claims around a JD requirement
_EVIDENCE_CATEGORIES = {
    "accountability", "stakeholder_fluency", "technical_ownership",
    "autonomy", "technical_depth"
}


def _build_group_system() -> str:
    """Build the grouping system prompt from the categories file.

    Reads argument_categories.json at call time — adding a category there
    automatically updates this prompt.
    """
    categories = load_argument_categories()

    if categories:
        evidence_cats = [c for c in categories if c["name"] in _EVIDENCE_CATEGORIES]
        standalone_cats = [c for c in categories if c["name"] in _STANDALONE_CATEGORIES]

        evidence_lines = "\n".join(
            f"  - {c['name']}: {c['description']}"
            for c in evidence_cats
        )
        standalone_lines = "\n".join(
            f"  - {c['name']}: {c['description']}"
            for c in standalone_cats
        )
    else:
        evidence_lines = "  (no categories loaded)"
        standalone_lines = "  (no categories loaded)"

    return f"""\
You are assembling a cover letter outline from extracted claims.

You will receive:
1. A job description
2. A thesis (the core argument the letter should make)
3. A list of claims — each labeled with its argument categories and employer contexts

━━━ TWO KINDS OF CLAIMS ━━━

EVIDENCE CLAIMS — group these around JD requirements:
{evidence_lines}

  Rules:
  - Group claims that address the same JD requirement area into one paragraph block
  - A paragraph usually contains 2–4 claims from the same requirement area
  - Claims from different employers CAN share a paragraph if they address the same argument point
  - Name the block with a SHORT label: what argument it makes
    e.g. "production ownership of event pipelines", "accountability under high stakes"

STANDALONE CLAIMS — each forms its own paragraph block:
{standalone_lines}

  Rules:
  - Do NOT group these with evidence claims
  - One standalone claim per block is fine — these are the argument about WHO this person is
  - Label them by what they argue: "working method", "professional character", "orientation"
  - Place them where they serve the argument:
    * disposition/motivation/communication: usually open or close the letter
    * approach_method/leadership: can bridge between evidence blocks
  - Do NOT put these in "unused" — they are required argument types

━━━ CLAIM ORDERING ━━━

Arrange paragraph blocks to build the argument logically:
1. Open with the thesis — the core claim about who this person is (disposition or motivation)
2. Evidence blocks in order of JD priority — most critical requirement first
3. Method or approach block to bridge if it connects evidence areas
4. Close on motivation or communication if present

━━━ OUTPUT ━━━

Return ONLY valid JSON:
{{
  "paragraphs": [
    {{
      "label": "short argument point label",
      "argument_categories": ["accountability", "stakeholder_fluency"],
      "jd_requirement": "which JD requirement this addresses, or the argument type for standalone blocks",
      "claim_ids": [0, 3, 5]
    }}
  ],
  "unused": [1, 2, 4]
}}

Paragraph order matters. Do not put required standalone claims in unused.
"""


_GROUP_SYSTEM = _build_group_system()


# ---------------------------------------------------------------------------
# Claim retrieval from DB
# ---------------------------------------------------------------------------

def _load_claims(conn: sqlite3.Connection) -> list[dict]:
    """Load all claims with argument categories, anchor phrases, and full support hierarchy."""
    claims = conn.execute(
        "SELECT id, text, source_para_hash, argument_categories FROM claims ORDER BY id"
    ).fetchall()

    result = []
    for claim in claims:
        cid = claim["id"]

        contexts = conn.execute(
            "SELECT context_type, context_name FROM claim_contexts WHERE claim_id = ?",
            (cid,),
        ).fetchall()

        # Load top-level support items, flagging anchors
        top_support = conn.execute(
            "SELECT id, text, is_anchor FROM support_items "
            "WHERE claim_id = ? AND parent_id IS NULL ORDER BY position",
            (cid,),
        ).fetchall()

        support_out = []
        for s in top_support:
            details = conn.execute(
                "SELECT text FROM support_items WHERE parent_id = ? ORDER BY position",
                (s["id"],),
            ).fetchall()
            support_out.append({
                "text": s["text"],
                "is_anchor": bool(s["is_anchor"]),
                "details": [d["text"] for d in details],
            })

        # Parse argument_categories from JSON string
        raw_cats = claim["argument_categories"]
        try:
            arg_cats = json.loads(raw_cats) if raw_cats else []
        except Exception:
            arg_cats = []

        result.append({
            "id": cid,
            "text": claim["text"],
            "contexts": [{"type": c["context_type"], "name": c["context_name"]} for c in contexts],
            "argument_categories": arg_cats,
            "support": support_out,
        })

    return result


def _load_conclusion_for_claims(conn: sqlite3.Connection, claim_ids: list[int]) -> str | None:
    """Return conclusion text that spans the most claims in claim_ids, if any."""
    if not claim_ids:
        return None
    placeholders = ",".join("?" * len(claim_ids))
    row = conn.execute(
        f"""SELECT c.text, COUNT(cc.claim_id) AS n
            FROM conclusions c
            JOIN conclusion_claims cc ON c.id = cc.conclusion_id
            WHERE cc.claim_id IN ({placeholders})
            GROUP BY c.id
            ORDER BY n DESC
            LIMIT 1""",
        claim_ids,
    ).fetchone()
    return row["text"] if row and row["n"] >= 2 else None


# ---------------------------------------------------------------------------
# Embedding + similarity
# ---------------------------------------------------------------------------

def _embed_query(
    text: str,
    voyage_api_key: str,
    provider: "object | None" = None,
) -> list[float] | None:
    """Embed a query string. Delegates to db.embed_query."""
    from coverletter.db import embed_query
    return embed_query(text, voyage_api_key, provider)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _category_aware_retrieval(
    claims: list[dict],
    conn: sqlite3.Connection,
    jd_embedding: list[float] | None,
    category_embeddings: dict[str, list[float]],
    relevance_threshold: float = 0.35,
    claims_per_category: int = 4,
    category_score_threshold: float = 0.30,
    reranker=None,
    jd_query: str = "",
    embed_provider=None,
) -> tuple[list[dict], list[tuple[str, float]]]:
    """Retrieve claims using category-aware two-stage (optionally three-stage) filtering.

    Stage 1: Score argument categories against the JD embedding.
             Only query claims from categories that are relevant to this JD.
             Standalone categories (disposition, motivation, etc.) always included.

    Stage 2: Within each relevant category, rank claims by embedding similarity
             to the JD. Take top claims_per_category per category.
             With BGE-M3 (embed_provider.supports_hybrid()), uses hybrid dense+sparse
             scores against claim text rather than pre-stored dense embeddings.

    Stage 3 (optional, Cohere reranker): Cross-encode each selected claim text
             against the full JD. Replace embedding score with reranker relevance
             score and re-sort within each category. Provides precision gain for
             terminology-sensitive matching (e.g. "Kafka" vs "event streaming").

    Returns (selected_claims, category_scores) where category_scores is
    [(category_name, score)] for analytics capture.

    Falls back to flat scoring if no category embeddings are stored.
    """
    if jd_embedding is None:
        return claims, []

    # Stage 1 — score categories against JD
    category_scores: list[tuple[str, float]] = []
    if category_embeddings:
        from coverletter.db import score_jd_against_categories
        category_scores = score_jd_against_categories(jd_embedding, category_embeddings)
        relevant_categories = {
            cat for cat, score in category_scores
            if score >= category_score_threshold or cat in _STANDALONE_CATEGORIES
        }
    else:
        # No category embeddings stored — treat all categories as relevant
        relevant_categories = None

    # Build lookup: claim_id -> embedding vector (read from DB once)
    claim_ids = [c["id"] for c in claims]
    if not claim_ids:
        return claims, category_scores

    placeholders = ",".join("?" * len(claim_ids))
    emb_rows = conn.execute(
        f"SELECT id, embedding FROM claims WHERE id IN ({placeholders})",
        claim_ids,
    ).fetchall()
    emb_map: dict[int, list[float]] = {}
    for row in emb_rows:
        if row["embedding"]:
            try:
                emb_map[row["id"]] = json.loads(row["embedding"])
            except Exception:
                pass

    # Stage 2 — score claims within relevant categories
    # Standalone claims always included at score 1.0
    standalone_claims = []
    evidence_candidates: list[dict] = []

    for claim in claims:
        cats = set(claim.get("argument_categories", []))
        if cats & _STANDALONE_CATEGORIES:
            standalone_claims.append(dict(claim, _similarity_score=1.0))
            continue
        if relevant_categories is not None and not (cats & relevant_categories):
            continue
        evidence_candidates.append(claim)

    # Score evidence candidates — hybrid (BGE-M3) or dense cosine
    use_hybrid = (
        embed_provider is not None
        and embed_provider.supports_hybrid()
        and jd_query
        and evidence_candidates
    )
    if use_hybrid:
        candidate_texts = [c.get("text", "") for c in evidence_candidates]
        hybrid_score_list = embed_provider.hybrid_scores(jd_query, candidate_texts) or []
        hybrid_score_map = {
            c["id"]: s for c, s in zip(evidence_candidates, hybrid_score_list)
        }

    evidence_by_category: dict[str, list[tuple[float, dict]]] = {}
    for claim in evidence_candidates:
        if use_hybrid:
            score = hybrid_score_map.get(claim["id"], 0.0)
        else:
            emb = emb_map.get(claim["id"])
            score = _cosine(jd_embedding, emb) if emb else 0.0

        if score < relevance_threshold and relevant_categories is not None:
            continue

        primary_cat = next(
            (c for c in claim.get("argument_categories", []) if c in _EVIDENCE_CATEGORIES),
            "uncategorized"
        )
        evidence_by_category.setdefault(primary_cat, []).append((score, dict(claim, _similarity_score=score)))

    # Take top claims_per_category per evidence category
    selected_evidence: list[dict] = []
    for cat, scored in evidence_by_category.items():
        scored.sort(key=lambda x: -x[0])
        selected_evidence.extend(c for _, c in scored[:claims_per_category])

    # Stage 3 — cross-encoder reranking (Cohere rerank-v3.5 or compatible)
    # Runs over selected_evidence only (small set), replaces cosine score with
    # reranker relevance score, then re-sorts. Standalone claims are not reranked.
    if reranker is not None and jd_query and selected_evidence:
        try:
            texts = [c.get("claim_text", "") or c.get("text", "") for c in selected_evidence]
            rerank_scores = reranker.rerank(jd_query, texts)
            if rerank_scores is not None:
                selected_evidence = [
                    dict(c, _similarity_score=s)
                    for c, s in zip(selected_evidence, rerank_scores)
                ]
                selected_evidence.sort(key=lambda c: -c["_similarity_score"])
        except Exception:
            pass

    result = standalone_claims + selected_evidence
    if not result:
        result = [dict(c, _similarity_score=0.0) for c in claims]

    return result, category_scores


# ---------------------------------------------------------------------------
# LLM grouping
# ---------------------------------------------------------------------------

def _group_claims(
    claims: list[dict],
    jd: str,
    thesis: str,
    api_key: str,
    model: str,
) -> dict:
    """Ask the LLM to group claims into paragraph blocks."""

    def _label(c: dict) -> str:
        cats = c.get("argument_categories", [])
        if cats:
            return ", ".join(cats)
        # Fallback heuristic for claims extracted before argument_categories existed
        text = c.get("text", "").lower()
        ctxs = c.get("contexts", [])
        if any(ctx.get("type") == "project" for ctx in ctxs):
            return "personal_project"
        if any(w in text for w in ("most excited", "draws me", "what i find")):
            return "motivation"
        if any(w in text for w in ("rare for", "spent years", "intensive")):
            return "disposition"
        if ctxs and any(ctx.get("type") == "employer" for ctx in ctxs):
            return "technical_ownership"
        if any(w in text for w in ("i work ", "i build ", "i approach")):
            return "approach_method"
        return "technical_ownership"

    claims_text = "\n".join(
        f"[{i}] [{_label(c)}] (id={c['id']}) {c['text']}"
        + (f"  [{', '.join(ctx['name'] for ctx in c['contexts'])}]" if c['contexts'] else "")
        for i, c in enumerate(claims)
    )

    content = (
        f"=== JOB DESCRIPTION ===\n{jd.strip()}\n\n"
        f"=== THESIS ===\n{thesis.strip()}\n\n"
        f"=== CLAIMS (index: [argument_categories] text [employer]) ===\n{claims_text}"
    )

    from coverletter.provider import get_provider
    raw = get_provider(model, api_key).complete(_GROUP_SYSTEM, content, max_tokens=1024)
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Gap detection
# ---------------------------------------------------------------------------

_GAP_SYSTEM = """\
You are a requirements analyst. Given a job description and a list of JD requirements that
the candidate's outline already addresses, identify requirements that are NOT covered.

Return ONLY valid JSON:
{
  "gaps": [
    {
      "requirement_text": "short paraphrase of the uncovered requirement",
      "inferred_category": "the closest argument category: technical_ownership | approach_method | disposition | motivation | stakeholder_fluency | data_infrastructure | systems_thinking | communication | other",
      "had_db_coverage": false
    }
  ]
}

Rules:
- Only include genuine gaps — requirements explicitly stated in the JD that nothing in the
  covered list addresses.
- Do not invent requirements. Do not include nice-to-haves not stated in the JD.
- Keep requirement_text short (one clause).
- Return an empty gaps list if everything is covered.
"""


def _detect_gaps(
    jd: str,
    covered_requirements: list[str],
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
) -> list[dict]:
    """Compare JD requirements against what the outline covers. Return uncovered gaps."""
    from coverletter.provider import get_provider

    covered_block = "\n".join(f"- {r}" for r in covered_requirements if r.strip())
    content = (
        f"=== JOB DESCRIPTION ===\n{jd.strip()}\n\n"
        f"=== REQUIREMENTS COVERED BY THE OUTLINE ===\n{covered_block or '(none)'}"
    )

    raw = get_provider(model, api_key).complete(_GAP_SYSTEM, content, max_tokens=512)
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw).get("gaps", [])
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Markdown outline writer
# ---------------------------------------------------------------------------

def _write_outline_markdown(
    outline: dict,
    claims: list[dict],
    conn: sqlite3.Connection,
    jd: str,
    thesis: str,
    company: str,
) -> str:
    """Render the grouped outline to editable markdown.

    Anchor phrases are marked with ⚓ and a generation note — they are the
    load-bearing language from the writer's words that must reach the letter intact.
    Regular support items are listed normally beneath them.
    """
    claim_by_idx = {i: c for i, c in enumerate(claims)}

    lines = [
        f"# Cover Letter Outline — {company}",
        "",
        f"**Thesis:** {thesis}",
        "",
        "---",
        "",
        "> Edit this outline: reorder paragraphs, drop claims, add notes.",
        "> Anchor phrases (⚓) are load-bearing language from your source material —",
        "> they must appear in the letter. Do not paraphrase them.",
        "",
        "---",
        "",
    ]

    for para_block in outline.get("paragraphs", []):
        label = para_block.get("label", "paragraph")
        jd_req = para_block.get("jd_requirement", "")
        arg_cats = para_block.get("argument_categories", [])
        indices = para_block.get("claim_ids", [])

        # Header with argument categories
        cat_str = f"  `[{', '.join(arg_cats)}]`" if arg_cats else ""
        lines.append(f"## {label}{cat_str}")
        if jd_req:
            lines.append(f"*Addresses: {jd_req}*")
        lines.append("")

        block_claim_ids = []
        for idx in indices:
            claim = claim_by_idx.get(idx)
            if not claim:
                continue
            block_claim_ids.append(claim["id"])

            ctxs = ", ".join(c["name"] for c in claim.get("contexts", []))
            ctx_str = f"  [{ctxs}]" if ctxs else ""
            lines.append(f"- **Claim:** {claim['text']}{ctx_str}")

            anchors = [s for s in claim.get("support", []) if s.get("is_anchor")]
            regular = [s for s in claim.get("support", []) if not s.get("is_anchor")]

            # Anchor phrases first — marked visibly as generation constraints
            for s in anchors:
                lines.append(f"  - ⚓ **{s['text']}**  *(anchor — use this language)*")
                for d in s.get("details", []):
                    lines.append(f"    - {d}")

            # Regular support items
            for s in regular:
                lines.append(f"  - {s['text']}")
                for d in s.get("details", []):
                    lines.append(f"    - {d}")

            lines.append("")

        conclusion = _load_conclusion_for_claims(conn, block_claim_ids)
        if conclusion:
            lines.append(f"*Conclusion: {conclusion}*")
            lines.append("")

        lines.append("---")
        lines.append("")

    unused_indices = outline.get("unused", [])
    if unused_indices:
        lines.append("## Unused claims")
        lines.append("*These claims weren't placed — review if any should be included.*")
        lines.append("")
        for idx in unused_indices:
            claim = claim_by_idx.get(idx)
            if claim:
                cats = claim.get("argument_categories", [])
                cat_str = f" `[{', '.join(cats)}]`" if cats else ""
                lines.append(f"- {claim['text']}{cat_str}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Outline parser — reads edited markdown back into structured data
# ---------------------------------------------------------------------------

def parse_outline(path: Path) -> dict:
    """Parse an edited outline markdown file back into structured data.

    Returns:
    {
      "company": str,
      "thesis": str,
      "paragraphs": [
        {
          "label": str,
          "argument_categories": [str],
          "jd_requirement": str,
          "claims": [
            {
              "text": str,
              "employer": str | None,
              "anchors": [str],
              "support": [str],
            }
          ],
          "notes": [str],   # user-added lines
        }
      ]
    }
    """
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    company = ""
    thesis = ""
    paragraphs: list[dict] = []
    current_para: dict | None = None
    current_claim: dict | None = None
    in_unused = False

    title_re = re.compile(r"^# Cover Letter Outline — (.+)$")
    thesis_re = re.compile(r"^\*\*Thesis:\*\* (.+)$")
    para_re = re.compile(r"^## (.+?)(?:\s+`\[(.+?)\]`)?$")
    addresses_re = re.compile(r"^\*Addresses: (.+)\*$")
    claim_re = re.compile(r"^- \*\*Claim:\*\* (.+?)(?:\s+\[(.+?)\])?$")
    anchor_re = re.compile(r"^  - ⚓ \*\*(.+?)\*\*")
    support_re = re.compile(r"^  - (.+)$")

    def _flush_claim():
        if current_claim and current_para is not None:
            current_para["claims"].append(current_claim)

    def _flush_para():
        _flush_claim()
        if current_para is not None:
            paragraphs.append(current_para)

    for line in lines:
        # Skip metadata / navigation lines
        if line.startswith(">") or line.startswith("---") or not line.strip():
            continue

        # Title
        m = title_re.match(line)
        if m:
            company = m.group(1).strip()
            continue

        # Thesis
        m = thesis_re.match(line)
        if m:
            thesis = m.group(1).strip()
            continue

        # Stop at unused section
        if line.startswith("## Unused claims"):
            in_unused = True
            _flush_para()
            current_para = None
            current_claim = None
            continue
        if in_unused:
            continue

        # Paragraph block header
        m = para_re.match(line)
        if m:
            _flush_para()
            cats_str = m.group(2) or ""
            cats = [c.strip() for c in cats_str.split(",")] if cats_str else []
            current_para = {
                "label": m.group(1).strip(),
                "argument_categories": cats,
                "jd_requirement": "",
                "claims": [],
                "notes": [],
            }
            current_claim = None
            continue

        if current_para is None:
            continue

        # Addresses line
        m = addresses_re.match(line)
        if m:
            current_para["jd_requirement"] = m.group(1).strip()
            continue

        # Claim line
        m = claim_re.match(line)
        if m:
            _flush_claim()
            current_claim = {
                "text": m.group(1).strip(),
                "employer": m.group(2).strip() if m.group(2) else None,
                "anchors": [],
                "support": [],
            }
            continue

        if current_claim is not None:
            # Anchor phrase
            m = anchor_re.match(line)
            if m:
                current_claim["anchors"].append(m.group(1).strip())
                continue

            # Regular support item
            m = support_re.match(line)
            if m:
                text = m.group(1).strip()
                # Strip any residual anchor marker that survived editing
                text = re.sub(r"⚓\s*\*\*(.+?)\*\*.*", r"\1", text).strip()
                if text:
                    current_claim["support"].append(text)
                continue

        # User-added note line
        if line.strip() and current_para is not None:
            current_para["notes"].append(line.strip())

    _flush_para()

    return {"company": company, "thesis": thesis, "paragraphs": paragraphs}


def _lookup_source_paragraph(conn: sqlite3.Connection, claim_text: str) -> str | None:
    """Find the source paragraph text for a claim by text match."""
    row = conn.execute(
        """SELECT p.text FROM paragraphs p
           JOIN claims c ON c.source_para_hash = p.text_hash
           WHERE c.text = ?
           LIMIT 1""",
        (claim_text,),
    ).fetchone()
    return row["text"] if row else None


def build_outline_user_message(
    outline: dict,
    conn: sqlite3.Connection,
    jd: str,
    company: str,
    profile_text: str = "",
) -> str:
    """Build the user message for generate-from-outline.

    Structures each paragraph block with claim, anchor phrases, support items,
    and source paragraph as voice reference.
    """
    parts: list[str] = []

    if company:
        parts.append(f"=== COMPANY ===\n{company}\n")

    parts.append(f"=== JOB DESCRIPTION ===\n{jd.strip()}\n")
    parts.append(f"=== THESIS ===\n{outline['thesis'].strip()}\n")

    if profile_text:
        parts.append(f"=== CANDIDATE PROFILE ===\n{profile_text.strip()}\n")

    parts.append("=== OUTLINE PARAGRAPH BLOCKS ===\n")
    parts.append(
        "Write one body paragraph per block below. "
        "Anchor phrases (⚓) must appear verbatim. "
        "Source paragraph is your voice reference.\n"
    )

    for i, para in enumerate(outline["paragraphs"], 1):
        cats = ", ".join(para["argument_categories"]) if para["argument_categories"] else "evidence"
        block: list[str] = [
            f"━━━ PARAGRAPH {i}: {para['label']} ━━━",
            f"Argument type: {cats}",
        ]
        if para["jd_requirement"]:
            block.append(f"JD connection: {para['jd_requirement']}")

        for claim in para["claims"]:
            employer_str = f" [{claim['employer']}]" if claim["employer"] else ""
            block.append(f"\nCLAIM: {claim['text']}{employer_str}")

            if claim["anchors"]:
                block.append("\nANCHOR PHRASES — must appear verbatim:")
                for anchor in claim["anchors"]:
                    block.append(f"  ⚓ {anchor}")

            if claim["support"]:
                block.append("\nSUPPORTING EVIDENCE:")
                for s in claim["support"]:
                    block.append(f"  • {s}")

            # Look up source paragraph for voice reference (only if DB is available)
            if conn is not None:
                source = _lookup_source_paragraph(conn, claim["text"])
                if source:
                    block.append(f"\nSOURCE PARAGRAPH (voice reference — stay close to this register):\n{source.strip()}")

        if para["notes"]:
            block.append("\nNOTES (user-added guidance):")
            for note in para["notes"]:
                block.append(f"  {note}")

        block.append(f"\n━━━ END PARAGRAPH {i} ━━━\n")
        parts.append("\n".join(block))

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_outline(
    conn: sqlite3.Connection,
    jd: str,
    thesis: str,
    api_key: str,
    model: str,
    company: str = "Company",
    voyage_api_key: str = "",
    relevance_threshold: float = 0.35,
    embed_model: str = "",
) -> tuple[str, list[dict], list[tuple[str, float]], list[dict]]:
    """Build an editable markdown outline from the claim-evidence DB.

    Returns (outline_markdown, relevant_claims, category_scores, gaps).
    """
    all_claims = _load_claims(conn)
    if not all_claims:
        return "# No claims found\n\nRun `coverletter extract` first.\n", [], [], []

    from coverletter.provider import get_embed_provider, get_provider
    provider = get_provider(model, api_key)
    embed_provider = get_embed_provider(embed_model) or provider

    jd_embedding = _embed_query(jd + "\n" + thesis, voyage_api_key, embed_provider)

    from coverletter.db import ensure_category_embeddings
    category_embeddings = ensure_category_embeddings(conn, voyage_api_key, embed_provider)
    reranker = provider if provider.supports_rerank() else None
    relevant_claims, category_scores = _category_aware_retrieval(
        all_claims, conn, jd_embedding, category_embeddings, relevance_threshold,
        reranker=reranker, jd_query=jd + "\n" + thesis, embed_provider=embed_provider,
    )

    grouping = _group_claims(relevant_claims, jd, thesis, api_key, model)

    covered = [p.get("jd_requirement", "") for p in grouping.get("paragraphs", [])]
    gaps = _detect_gaps(jd, covered, api_key, model)

    outline_md = _write_outline_markdown(grouping, relevant_claims, conn, jd, thesis, company)
    return outline_md, relevant_claims, category_scores, gaps
