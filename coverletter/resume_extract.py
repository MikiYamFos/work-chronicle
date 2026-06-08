"""Resume extraction — parse resume into source='resume' claims in the DB.

Auto-triggers on hash change when the resume is loaded by any command.
Manual force: clio resume extract
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from coverletter.config import Config

_EXTRACT_SYSTEM = """\
You are extracting career claims from a resume. A claim is a specific, concrete \
assertion about what this person owned, built, decided, or achieved — grounded in \
a particular role or project.

Rules:
- One claim per bullet point or distinct fact. Do not merge bullets.
- Keep the person's exact phrasing where possible — do not paraphrase or elevate.
- Preserve specifics: numbers, technology names, scope signals, ownership language.
- Do not invent anything not stated. Do not add interpretive framing.
- Skip generic filler ("responsible for", "worked on team") unless paired with a specific fact.
- Include company and role context for each claim.

Output JSON only:
{
  "claims": [
    {
      "text": "At BritBox, owned the VideoViewEvents pipeline end-to-end, processing 1B+ events/day",
      "company": "BritBox",
      "role": "Senior Data Engineer",
      "argument_categories": ["ownership", "scale"]
    }
  ]
}

argument_categories should be 1-3 of: ownership, scale, technical-depth, business-impact,
system-design, data-engineering, leadership, collaboration, process, tooling
"""


def _resume_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _last_extraction(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute(
        "SELECT * FROM resume_extractions ORDER BY version DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def needs_extraction(conn: sqlite3.Connection, current_hash: str) -> bool:
    last = _last_extraction(conn)
    return last is None or last["file_hash"] != current_hash


def extract_resume_claims(resume_text: str, api_key: str, model: str) -> list[dict]:
    """Call LLM to extract claims from raw resume text. Returns list of claim dicts."""
    import anthropic
    from coverletter.costs import record, supports_temperature

    client = anthropic.Anthropic(api_key=api_key)
    kwargs: dict = dict(
        model=model,
        max_tokens=4096,
        system=_EXTRACT_SYSTEM,
        messages=[{"role": "user", "content": f"Extract claims from this resume:\n\n{resume_text}"}],
    )
    if supports_temperature(model):
        kwargs["temperature"] = 0
    response = client.messages.create(**kwargs)
    record(
        model,
        response.usage.input_tokens,
        response.usage.output_tokens,
        label="resume_extract",
    )
    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(raw).get("claims", [])
    except Exception:
        return []


def _insert_resume_claims(
    conn: sqlite3.Connection,
    claims: list[dict],
    voyage_api_key: str = "",
) -> int:
    """Insert claims with source='resume' into the claims table. Returns count inserted."""
    from coverletter.extract import _embed_texts

    texts = [c["text"] for c in claims if c.get("text")]
    embeddings = _embed_texts(texts, voyage_api_key) if voyage_api_key else [None] * len(texts)

    inserted = 0
    for claim, emb in zip(claims, embeddings):
        text = claim.get("text", "").strip()
        if not text:
            continue
        arg_cats = claim.get("argument_categories", [])
        arg_cats_str = json.dumps(arg_cats) if arg_cats else None
        emb_blob = bytes(json.dumps(emb).encode()) if emb else None

        cur = conn.execute(
            "INSERT INTO claims (text, source_para_hash, embedding, argument_categories, source) "
            "VALUES (?, ?, ?, ?, ?)",
            (text, None, emb_blob, arg_cats_str, "resume"),
        )
        claim_id = cur.lastrowid
        inserted += 1

        company = claim.get("company", "").strip()
        if company:
            conn.execute(
                "INSERT INTO claim_contexts (claim_id, context_type, context_name) VALUES (?, ?, ?)",
                (claim_id, "employer", company),
            )
    conn.commit()
    return inserted


def _record_extraction(
    conn: sqlite3.Connection,
    file_hash: str,
    claim_count: int,
    notes: str = "",
) -> int:
    last = _last_extraction(conn)
    version = (last["version"] + 1) if last else 1
    conn.execute(
        "INSERT INTO resume_extractions (file_hash, version, claim_count, notes) VALUES (?, ?, ?, ?)",
        (file_hash, version, claim_count, notes or None),
    )
    conn.commit()
    return version


def _delete_old_resume_claims(conn: sqlite3.Connection) -> None:
    """Remove all existing source='resume' claims before re-extraction."""
    conn.execute("DELETE FROM claims WHERE source = 'resume'")
    conn.commit()


def run_resume_extraction(
    conn: sqlite3.Connection,
    resume_path: Path,
    api_key: str,
    model: str,
    voyage_api_key: str = "",
    force: bool = False,
    silent: bool = False,
) -> int:
    """Check hash, extract if needed, insert claims. Returns count of claims inserted (0 = skipped)."""
    from coverletter.resume import load_resume

    if not resume_path.exists():
        return 0

    current_hash = _resume_hash(resume_path)
    if not force and not needs_extraction(conn, current_hash):
        return 0

    if not silent:
        print("  Indexing resume...", end="", flush=True)

    resume_text = load_resume(resume_path)
    if not resume_text.strip():
        return 0

    claims = extract_resume_claims(resume_text, api_key, model)
    if not claims:
        return 0

    _delete_old_resume_claims(conn)
    count = _insert_resume_claims(conn, claims, voyage_api_key)
    version = _record_extraction(conn, current_hash, count)

    if not silent:
        print(f" {count} claims indexed (v{version})")

    return count


def maybe_extract_resume(cfg: "Config", conn: sqlite3.Connection) -> None:
    """Auto-trigger: call from any command that uses the resume. Silent if up to date."""
    if not cfg.resume_file or not cfg.resume_file.exists():
        return
    current_hash = _resume_hash(cfg.resume_file)
    if needs_extraction(conn, current_hash):
        run_resume_extraction(
            conn, cfg.resume_file, cfg.api_key, cfg.model,
            voyage_api_key=getattr(cfg, "voyage_api_key", ""),
            silent=False,
        )
