"""SQLite-backed paragraph index and claim-evidence store.

Markdown files are the source of truth for paragraphs. This module provides:
  - sync_from_markdown()         — parse .md files → upsert paragraphs
  - compute_embeddings()         — batch Voyage embeddings for paragraphs
  - extract_and_store_sentences() — split paragraphs into indexed sentences
  - compute_sentence_embeddings() — batch Voyage embeddings for sentences
  - assign_angles_canonical()    — classify paragraphs against 18 canonical angles
  - save_raw_response()          — preserve raw Q&A answers before they are drafted
  - build_angle_evidence()       — retrieve angle-organized evidence for a JD

Claim-evidence tables (claims, claim_contexts, support_items, conclusions):
  - Claims are atomic portable assertions sourced from paragraphs but not owned by them.
  - The same claim can appear in different paragraph assemblies for different letters.
  - Populated by `coverletter extract` (not run on every generate).
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from coverletter.parser import Paragraph

# ---------------------------------------------------------------------------
# Canonical angle taxonomy
# Descriptions written to match paragraph prose style for accurate embedding
# similarity. Adding or renaming angles here is the only change needed — the
# classifier picks up the new definitions on the next sync.
# ---------------------------------------------------------------------------

CANONICAL_ANGLES: dict[str, str] = {
    "through-line": (
        "The connecting thread across different roles, employers, or domains that makes a career "
        "legible as a single identity rather than a list of jobs. What this person reliably brings "
        "regardless of context, and the intellectual or professional commitments that hold across it."
    ),
    "autonomy": (
        "The condition of determining the path without being told how. Not just executing "
        "independently on a defined task, but being the person who figures out what needs to be "
        "done when no one else is going to — responsible for the function, not just for completing "
        "work within it."
    ),
    "ownership": (
        "End-to-end accountability for a specific system, pipeline, product, or function. The "
        "person who designed it, built it, and remained answerable for whether it worked correctly "
        "in production — not a contributor to something someone else held."
    ),
    "business-impact": (
        "Work whose outputs mattered outside of engineering — decisions made, strategy changed, "
        "performance measured, costs reduced, revenue affected. The work was not neutral to the "
        "organization's interests; it moved something."
    ),
    "system-design": (
        "The architectural calls that determined how a system works — structure, data flow, grain, "
        "component relationships, validation approach. Decisions about what got built and why, not "
        "decisions about how to implement what was already specified."
    ),
    "requirements-translation": (
        "The work of determining what was actually needed before anything was built. Gathering "
        "requirements from non-technical stakeholders, identifying the gap between what people said "
        "and what the system should do, and producing something buildable from ambiguous "
        "domain-specific asks."
    ),
    "compliance": (
        "Work with regulated, legally sensitive, or access-controlled data where technical failure "
        "has consequences that extend beyond the system — governance requirements, retention rules, "
        "PII handling, access control, legal or organizational stakes that make correctness "
        "mandatory rather than desirable."
    ),
    "technical-depth": (
        "Deep mastery of a specific tool, technology, or problem domain — not just facility with "
        "it, but knowledge of how it behaves under pressure, where it breaks, what its tradeoffs "
        "are, and how to get reliable production-grade output from it."
    ),
    "precision": (
        "Work where correctness is a hard constraint rather than a best-effort target. Output that "
        "feeds decisions with real stakes, records that must be exactly right. The accountability "
        "for accuracy is personal and specific, not diffused across a team or softened by "
        "approximation."
    ),
    "communication": (
        "Making complex or technical things legible to people who need to understand or act on "
        "them — documentation others depend on, constraints surfaced proactively, requirements "
        "gathered through the right questions, training that actually transferred knowledge."
    ),
    "leadership": (
        "Directing work beyond individual contribution — setting priorities, owning an initiative, "
        "making calls others depend on, keeping a team or project oriented to what matters. "
        "Organizing how work gets done, not just doing the work."
    ),
    "strategic-vision": (
        "A considered rationale for why something was built the way it was — a clear point of view "
        "about the problem, the approach, and what made this design the right one. The thinking "
        "behind the artifact, not just the artifact."
    ),
    "resilience": (
        "Staying with hard problems through setbacks, pressure, or failure without walking away or "
        "becoming unreliable. The capacity to absorb difficulty and remain dependable when the "
        "stakes make it harder to be."
    ),
    "problem-solving": (
        "Approaching broken, undefined, or ambiguous situations by diagnosing what is actually "
        "happening before attempting a fix — working backward from symptoms to root cause, finding "
        "a path when the path is not given."
    ),
    "problem-definition": (
        "Identifying what the real problem is before anyone else has framed it correctly. "
        "Recognizing that a stated requirement is a symptom of something upstream, and doing the "
        "work to reframe what needs to be solved so that what gets built is the right thing — not "
        "just a correct answer to the wrong question."
    ),
    "trust": (
        "The professional property of being someone whose output others depend on without needing "
        "to check it — earned through consistent accuracy, transparency about uncertainty, and a "
        "track record of catching problems before they become crises."
    ),
    "recovery": (
        "Taking ownership of a situation that arrived broken. Diagnosing what went wrong, "
        "executing a fix under pressure, and understanding the root cause well enough to prevent "
        "recurrence — not inheriting a clean system but making a broken one right."
    ),
    "scope-expansion": (
        "Carrying work that formally belonged above one's level — owning decisions, systems, or "
        "functions that exceeded the defined role, filling gaps no one else was filling, and "
        "delivering at a scope a more senior person would typically hold."
    ),
}

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS paragraphs (
    id          INTEGER PRIMARY KEY,
    role        TEXT NOT NULL,
    section     TEXT NOT NULL,
    text        TEXT NOT NULL,
    text_hash   TEXT NOT NULL,
    type        TEXT,
    frame       TEXT,
    angle       TEXT,               -- primary angle (for quick queries / backward compat)
    angle_auto  INTEGER DEFAULT 0,  -- 1 = classifier-assigned, not from markdown meta
    strength    TEXT,
    via         TEXT,
    tone        TEXT,
    tech        TEXT,
    layer       INTEGER DEFAULT 1,
    active      INTEGER DEFAULT 1,
    source_file TEXT,
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS paragraph_angles (
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    angle        TEXT NOT NULL,
    is_primary   INTEGER DEFAULT 0,
    confidence   REAL,
    angle_auto   INTEGER DEFAULT 0,
    PRIMARY KEY (paragraph_id, angle)
);

CREATE TABLE IF NOT EXISTS embeddings (
    paragraph_id INTEGER PRIMARY KEY REFERENCES paragraphs(id) ON DELETE CASCADE,
    model        TEXT NOT NULL,
    vector       TEXT NOT NULL,
    indexed_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sentences (
    id            INTEGER PRIMARY KEY,
    paragraph_id  INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    position      INTEGER NOT NULL,
    text          TEXT NOT NULL,
    text_hash     TEXT NOT NULL,
    UNIQUE(paragraph_id, position)
);

CREATE TABLE IF NOT EXISTS sentence_embeddings (
    sentence_id  INTEGER PRIMARY KEY REFERENCES sentences(id) ON DELETE CASCADE,
    model        TEXT NOT NULL,
    vector       TEXT NOT NULL,
    indexed_at   TEXT DEFAULT (datetime('now'))
);

-- Raw Q&A responses captured during build/gap sessions.
-- Linked to the paragraph they produced via para_text_hash.
-- Source of truth for claim extraction — preserves detail that may have been
-- compressed in the refined paragraph text.
CREATE TABLE IF NOT EXISTS raw_responses (
    id              INTEGER PRIMARY KEY,
    para_text_hash  TEXT,                           -- paragraph produced from this session (may be NULL if not yet saved)
    session_topic   TEXT,                           -- gap description or build topic
    responses_md    TEXT NOT NULL,                  -- full Q&A as markdown: Q then A alternating
    captured_at     TEXT DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- Claim-evidence-outline tables
-- Claims are atomic portable assertions sourced from paragraphs but not owned
-- by them. The same claim can appear in different paragraph assemblies for
-- different letters. Scope (general/employer/multi-employer/project) is DERIVED
-- at query time from claim_contexts rows — never stored as a fixed column.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS claims (
    id               INTEGER PRIMARY KEY,
    text             TEXT NOT NULL,
    source_para_hash TEXT,            -- attribution back to origin paragraph
    embedding        BLOB,
    extracted_at     TEXT DEFAULT (datetime('now'))
);

-- What grounds a claim. 0 rows = general. 1 employer = employer-specific.
-- 2+ employers = spans employers. Any project row = personal project.
CREATE TABLE IF NOT EXISTS claim_contexts (
    id           INTEGER PRIMARY KEY,
    claim_id     INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    context_type TEXT NOT NULL,       -- 'employer' | 'project'
    context_name TEXT NOT NULL        -- 'BritBox' | 'Universe' | 'CBA Clock' etc.
);

-- Evidence for a claim. Self-referential: parent_id NULL = top-level evidence,
-- parent_id set = sub-detail subordinate to parent (e.g. "nested event_params"
-- is a sub-detail under "worked with GA4 BigQuery export").
CREATE TABLE IF NOT EXISTS support_items (
    id               INTEGER PRIMARY KEY,
    claim_id         INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    parent_id        INTEGER REFERENCES support_items(id),
    text             TEXT NOT NULL,
    employer         TEXT,
    position         INTEGER DEFAULT 0,
    source_para_hash TEXT,
    embedding        BLOB
);

-- Synthesized "so what" conclusions that close a GROUP of claims.
-- Not all claims have conclusions. Linked many-to-many via conclusion_claims.
CREATE TABLE IF NOT EXISTS conclusions (
    id               INTEGER PRIMARY KEY,
    text             TEXT NOT NULL,
    source_para_hash TEXT,
    embedding        BLOB
);

CREATE TABLE IF NOT EXISTS conclusion_claims (
    conclusion_id    INTEGER NOT NULL REFERENCES conclusions(id) ON DELETE CASCADE,
    claim_id         INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    PRIMARY KEY (conclusion_id, claim_id)
);

-- ---------------------------------------------------------------------------
-- Application analytics tables
-- Capture what happened at each application: JD, claim matching, gaps.
-- Traceability links library development back to market signals.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS applications (
    id          INTEGER PRIMARY KEY,
    company     TEXT NOT NULL,
    role        TEXT,
    jd_text     TEXT NOT NULL,
    jd_hash     TEXT NOT NULL,
    jd_embedding BLOB,                  -- stored so JDs can be compared without re-embedding
    applied_at  TEXT DEFAULT (datetime('now')),
    outcome     TEXT,                   -- NULL until known: 'applied'|'response'|'interview'|'offer'|'rejected'|'withdrew'
    notes       TEXT
);

-- Which argument categories were relevant for this JD and how strongly
CREATE TABLE IF NOT EXISTS application_category_scores (
    id              INTEGER PRIMARY KEY,
    application_id  INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    argument_category TEXT NOT NULL,
    relevance_score REAL NOT NULL
);

-- Which claims were scored for this JD — whether they made the outline and letter
CREATE TABLE IF NOT EXISTS application_claim_scores (
    id              INTEGER PRIMARY KEY,
    application_id  INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    claim_id        INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    argument_category TEXT,
    similarity_score REAL NOT NULL,
    in_outline      INTEGER DEFAULT 0,  -- 1 = appeared in generated outline
    in_letter       INTEGER DEFAULT 0   -- 1 = appeared in sent letter
);

-- JD requirements with no claim coverage at time of application
CREATE TABLE IF NOT EXISTS application_gaps (
    id                  INTEGER PRIMARY KEY,
    application_id      INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    requirement_text    TEXT NOT NULL,
    inferred_category   TEXT,           -- which argument category this maps to
    had_db_coverage     INTEGER DEFAULT 0,  -- 1 = DB had claims but none scored well enough
    addressed_in_letter INTEGER DEFAULT 0,  -- 1 = letter addressed this despite no strong claim
    notes               TEXT            -- your interpretation: adjacent experience, genuine gap, etc.
);

-- Traceability: library actions taken in response to observed gaps
-- Populated by inference: topic match between build session and recent gap, not by prompting
CREATE TABLE IF NOT EXISTS gap_library_actions (
    id              INTEGER PRIMARY KEY,
    gap_id          INTEGER NOT NULL REFERENCES application_gaps(id) ON DELETE CASCADE,
    action_type     TEXT NOT NULL,      -- 'build'|'reflect'|'seed'
    paragraph_id    INTEGER REFERENCES paragraphs(id),
    session_topic   TEXT,
    actioned_at     TEXT DEFAULT (datetime('now'))
);

-- Provenance: how each paragraph came to exist
-- source_type inferred after the fact by matching session topic against recent gaps
CREATE TABLE IF NOT EXISTS paragraph_provenance (
    paragraph_id    INTEGER PRIMARY KEY REFERENCES paragraphs(id) ON DELETE CASCADE,
    source_type     TEXT NOT NULL,      -- 'organic'|'gap_driven'|'gap_adjacent'
    application_id  INTEGER REFERENCES applications(id),  -- application that prompted it
    gap_id          INTEGER REFERENCES application_gaps(id),
    inferred_at     TEXT DEFAULT (datetime('now'))
);

-- Gap-driven provenance: written at save time when a paragraph comes from the gap loop.
-- jd_score = cosine similarity of paragraph against the originating JD at write time.
-- This is the authoritative signal for retrieval — beats inferred angle assignment.
CREATE TABLE IF NOT EXISTS paragraph_gap_provenance (
    id              INTEGER PRIMARY KEY,
    para_hash       TEXT NOT NULL,      -- paragraph_hash(text) — survives layer moves
    jd_company      TEXT NOT NULL,
    jd_hash         TEXT NOT NULL,
    jd_score        REAL NOT NULL,      -- cosine sim of paragraph vs JD at write time
    gap_question    TEXT,               -- the alignment gap that triggered writing
    driving_angle   TEXT,               -- canonical angle the gap was filed under
    recorded_at     TEXT DEFAULT (datetime('now'))
);

-- Precomputed category description embeddings — stable, recomputed only when categories change
CREATE TABLE IF NOT EXISTS category_embeddings (
    category_name   TEXT PRIMARY KEY,
    embedding       BLOB NOT NULL,
    computed_at     TEXT DEFAULT (datetime('now'))
);

-- JD embedding cache — keyed by content hash so the same JD is never re-embedded
-- across generate, outline, blurb, build --jd regardless of which flow runs first.
-- company_values: extracted values/mission from the JD (NULL if none found or not yet extracted)
CREATE TABLE IF NOT EXISTS resume_extractions (
    id           INTEGER PRIMARY KEY,
    file_hash    TEXT NOT NULL,
    extracted_at TEXT DEFAULT (datetime('now')),
    version      INTEGER NOT NULL DEFAULT 1,
    claim_count  INTEGER DEFAULT 0,
    notes        TEXT
);

CREATE TABLE IF NOT EXISTS jd_versions (
    id             INTEGER PRIMARY KEY,
    jd_name        TEXT NOT NULL,
    file_hash      TEXT NOT NULL,
    saved_at       TEXT DEFAULT (datetime('now')),
    change_summary TEXT
);

CREATE TABLE IF NOT EXISTS jd_embedding_cache (
    jd_hash         TEXT PRIMARY KEY,
    embedding       BLOB NOT NULL,
    company_values  TEXT,
    cached_at       TEXT DEFAULT (datetime('now'))
);

-- Graph join tables: sentences → claims → canonical angles
-- These power the traversal: gap → angles → claims → sentences → assemble.
-- sentence_claims: which sentences prove which claims (many-to-many).
-- claim_angles: which canonical angles a claim supports (derived from argument_categories).
CREATE TABLE IF NOT EXISTS sentence_claims (
    sentence_id INTEGER NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    claim_id    INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    score       REAL,   -- cosine similarity between sentence and claim embeddings
    PRIMARY KEY (sentence_id, claim_id)
);

CREATE TABLE IF NOT EXISTS claim_angles (
    claim_id INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    angle    TEXT NOT NULL,
    PRIMARY KEY (claim_id, angle)
);

CREATE INDEX IF NOT EXISTS idx_para_hash          ON paragraphs(text_hash);
CREATE INDEX IF NOT EXISTS idx_para_source        ON paragraphs(source_file, active);
CREATE INDEX IF NOT EXISTS idx_para_type          ON paragraphs(type, active);
CREATE INDEX IF NOT EXISTS idx_para_angle         ON paragraphs(angle, active);
CREATE INDEX IF NOT EXISTS idx_para_angles_ang    ON paragraph_angles(angle);
CREATE INDEX IF NOT EXISTS idx_sent_para          ON sentences(paragraph_id);
CREATE INDEX IF NOT EXISTS idx_raw_para_hash      ON raw_responses(para_text_hash);
CREATE INDEX IF NOT EXISTS idx_app_company        ON applications(company);
CREATE INDEX IF NOT EXISTS idx_app_jd_hash        ON applications(jd_hash);
CREATE INDEX IF NOT EXISTS idx_app_cat_scores     ON application_category_scores(application_id, argument_category);
CREATE INDEX IF NOT EXISTS idx_app_claim_scores   ON application_claim_scores(application_id, claim_id);
CREATE INDEX IF NOT EXISTS idx_app_gaps           ON application_gaps(application_id);
CREATE INDEX IF NOT EXISTS idx_gap_actions        ON gap_library_actions(gap_id);
CREATE INDEX IF NOT EXISTS idx_para_provenance    ON paragraph_provenance(source_type);
CREATE INDEX IF NOT EXISTS idx_sent_claims_claim  ON sentence_claims(claim_id);
CREATE INDEX IF NOT EXISTS idx_sent_claims_sent   ON sentence_claims(sentence_id);
CREATE INDEX IF NOT EXISTS idx_claim_angles_angle ON claim_angles(angle);
"""


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:20]


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in parts if s.strip() and len(s.split()) >= 5]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def embed_query(
    text: str,
    voyage_api_key: str,
    provider: "object | None" = None,
) -> "list[float] | None":
    """Embed a query string. Tries provider-native embeddings first, then Voyage, then None."""
    if provider is not None:
        from coverletter.provider import Provider as ProviderBase
        if isinstance(provider, ProviderBase) and provider.supports_embed():
            result = provider.embed([text], input_type="query")
            if result:
                return result[0]

    if voyage_api_key:
        try:
            import voyageai  # type: ignore
            client = voyageai.Client(api_key=voyage_api_key)
            result = client.embed([text], model="voyage-3-lite", input_type="query")
            return result.embeddings[0]
        except Exception:
            pass

    return None


def get_or_embed_jd(
    conn: "sqlite3.Connection",
    jd_text: str,
    voyage_api_key: str,
    provider: "object | None" = None,
) -> "list[float] | None":
    """Return a JD embedding, using the cache when available.

    Checks jd_embedding_cache by content hash first. On a cache miss, embeds
    and stores the result so subsequent calls (generate → outline → blurb on
    the same JD) skip re-embedding entirely.
    """
    jd_hash = _hash(jd_text)
    row = conn.execute(
        "SELECT embedding FROM jd_embedding_cache WHERE jd_hash = ?", (jd_hash,)
    ).fetchone()
    if row and row["embedding"]:
        try:
            return json.loads(row["embedding"])
        except Exception:
            pass

    vec = embed_query(jd_text, voyage_api_key, provider)
    if vec is not None:
        conn.execute(
            "INSERT OR REPLACE INTO jd_embedding_cache (jd_hash, embedding) VALUES (?, ?)",
            (jd_hash, json.dumps(vec).encode()),
        )
        conn.commit()
    return vec


def gap_library_coverage(
    conn: "sqlite3.Connection",
    gaps: "list[str]",
    voyage_api_key: str,
    embed_provider: "object | None" = None,
    threshold: float = 0.45,
) -> "set[int]":
    """Return indices (0-based) of gaps that have matching claims in the DB.

    Embeds all gaps in one batch call. Loads all claim embeddings once.
    Returns the set of gap indices where at least one claim scores above threshold.
    Falls back to empty set if no embeddings are available.
    """
    if not gaps:
        return set()

    # Load claim embeddings once
    rows = conn.execute(
        "SELECT embedding FROM claims WHERE embedding IS NOT NULL"
    ).fetchall()
    if not rows:
        return set()

    claim_vecs: list[list[float]] = []
    for row in rows:
        try:
            claim_vecs.append(json.loads(row["embedding"]))
        except Exception:
            pass
    if not claim_vecs:
        return set()

    # Embed all gaps in one call
    if embed_provider is not None:
        from coverletter.provider import Provider as _P
        if isinstance(embed_provider, _P) and embed_provider.supports_embed():
            gap_vecs = embed_provider.embed(gaps, input_type="query")
        else:
            gap_vecs = None
    else:
        gap_vecs = None

    if gap_vecs is None and voyage_api_key:
        try:
            import voyageai  # type: ignore
            client = voyageai.Client(api_key=voyage_api_key)
            gap_vecs = client.embed(gaps, model="voyage-3-lite", input_type="query").embeddings
        except Exception:
            gap_vecs = None

    if not gap_vecs:
        return set()

    covered: set[int] = set()
    for i, gap_vec in enumerate(gap_vecs):
        for claim_vec in claim_vecs:
            if _cosine(gap_vec, claim_vec) >= threshold:
                covered.add(i)
                break
    return covered


def get_or_company_values(
    conn: "sqlite3.Connection",
    jd_text: str,
    api_key: str,
    model: str,
) -> "str | None":
    """Return company values/mission extracted from the JD, using cache when available.

    Values are extracted once per unique JD and stored alongside the embedding.
    Returns None if the JD contains no values/mission content.
    """
    jd_hash = _hash(jd_text)

    row = conn.execute(
        "SELECT company_values FROM jd_embedding_cache WHERE jd_hash = ?", (jd_hash,)
    ).fetchone()

    if row is not None:
        # Row exists — return cached value (may be NULL meaning "no values found")
        return row["company_values"]

    # No cache entry yet — extract and store
    from coverletter.jd import extract_company_values
    values = extract_company_values(jd_text, api_key, model)
    # Store even if None — records that extraction ran so we don't repeat it
    conn.execute(
        """INSERT INTO jd_embedding_cache (jd_hash, embedding, company_values)
           VALUES (?, ?, ?)
           ON CONFLICT(jd_hash) DO UPDATE SET company_values = excluded.company_values""",
        (jd_hash, b"", values),
    )
    conn.commit()
    return values


# ---------------------------------------------------------------------------
# DB lifecycle
# ---------------------------------------------------------------------------

_CATEGORIES_PATH = Path(__file__).parent / "evals" / "argument_categories.json"


def load_canonical_angles(custom_file: "Path | None" = None) -> dict[str, str]:
    """Return CANONICAL_ANGLES merged with user overrides from custom_angles.toml.

    New keys in the user file add angles; matching keys override baseline descriptions.
    Auto-detects custom_angles.toml in CWD when no path is given.
    """
    import copy
    angles = copy.copy(CANONICAL_ANGLES)

    if custom_file is None:
        custom_file = Path.cwd() / "custom_angles.toml"

    if not custom_file.exists():
        return angles

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            return angles

    try:
        data = tomllib.loads(custom_file.read_text(encoding="utf-8"))
        for name, body in data.get("angles", {}).items():
            if isinstance(body, dict) and "description" in body:
                angles[name] = body["description"]
    except Exception:
        pass

    return angles


def load_argument_categories(custom_file: "Path | None" = None) -> list[dict]:
    """Load argument categories merged with user overrides from custom_categories.toml.

    Baseline comes from argument_categories.json. User file adds new categories or
    overrides existing ones by name. Auto-detects custom_categories.toml in CWD.
    """
    baseline: list[dict] = []
    if _CATEGORIES_PATH.exists():
        try:
            baseline = json.loads(_CATEGORIES_PATH.read_text(encoding="utf-8")).get("categories", [])
        except Exception:
            pass

    if custom_file is None:
        custom_file = Path.cwd() / "custom_categories.toml"

    if not custom_file.exists():
        return baseline

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            return baseline

    try:
        data = tomllib.loads(custom_file.read_text(encoding="utf-8"))
        custom_cats = data.get("categories", [])
    except Exception:
        return baseline

    merged = {c["name"]: c for c in baseline}
    for cat in custom_cats:
        if "name" in cat:
            merged[cat["name"]] = cat

    return list(merged.values())


_MIGRATIONS = [
    # Add argument_categories to claims — comma-separated list of category names.
    # NULL on existing rows; populated on next extraction run.
    "ALTER TABLE claims ADD COLUMN argument_categories TEXT",
    # Add is_anchor to support_items — 1 = load-bearing language that must reach generation.
    # 0 on existing rows.
    "ALTER TABLE support_items ADD COLUMN is_anchor INTEGER DEFAULT 0",
    # Add source to claims — where the claim originated.
    # 'library' = extracted from a library paragraph (existing rows backfilled).
    # 'resume'  = extracted from resume PDF.
    # Future sources add a new string value; no schema change needed.
    "ALTER TABLE claims ADD COLUMN source TEXT NOT NULL DEFAULT 'library'",
    # Add description_hash to category_embeddings so stale entries are detected
    # automatically when CANONICAL_ANGLES definitions change.
    "ALTER TABLE category_embeddings ADD COLUMN description_hash TEXT",
]


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Apply schema migrations that can't be expressed in CREATE TABLE IF NOT EXISTS."""
    for sql in _MIGRATIONS:
        try:
            conn.execute(sql)
        except Exception:
            pass  # column already exists — normal on subsequent opens
    conn.commit()


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    _run_migrations(conn)
    conn.commit()
    return conn


def record_gap_provenance(
    conn: sqlite3.Connection,
    para_text: str,
    jd_company: str,
    jd_text: str,
    gap_question: str | None,
    driving_angle: str | None,
    voyage_api_key: str,
    model: str = "voyage-3-lite",
) -> None:
    """Record provenance for a paragraph written in response to a JD gap.

    Computes and stores the cosine similarity of the paragraph against the JD
    at write time — this is the authoritative retrieval signal, more reliable
    than inferred canonical angle assignment.
    """
    para_hash = _hash(para_text.strip())
    jd_hash = _hash(jd_text.strip())

    # Check for duplicate (same paragraph + same JD)
    existing = conn.execute(
        "SELECT id FROM paragraph_gap_provenance WHERE para_hash = ? AND jd_hash = ?",
        (para_hash, jd_hash),
    ).fetchone()
    if existing:
        return

    jd_score = 0.0
    try:
        import voyageai  # type: ignore
        client = voyageai.Client(api_key=voyage_api_key)
        para_result = client.embed([para_text], model=model, input_type="document")
        jd_result = client.embed([jd_text], model=model, input_type="query")
        jd_score = _cosine(para_result.embeddings[0], jd_result.embeddings[0])
    except Exception:
        pass

    conn.execute(
        """INSERT INTO paragraph_gap_provenance
           (para_hash, jd_company, jd_hash, jd_score, gap_question, driving_angle)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (para_hash, jd_company, jd_hash, jd_score, gap_question, driving_angle),
    )
    conn.commit()


def save_raw_response(
    conn: "sqlite3.Connection",
    history: list[dict],
    topic: str,
    para_text_hash: str | None = None,
) -> None:
    """Save the user's raw Q&A answers from a build/gap session to the DB.

    Formats the conversation as alternating Q (assistant) / A (user) markdown,
    preserving every word the person said before it gets compressed into a draft.
    Only captures human-readable turns — skips system messages and tool calls.
    """
    lines: list[str] = []
    for msg in history:
        if not isinstance(msg.get("content"), str):
            continue  # skip tool results and structured content
        role = msg["role"]
        text = msg["content"].strip()
        if not text:
            continue
        # Skip the very first system-context message (topic/JD framing)
        if role == "user" and lines == [] and len(text) > 400:
            continue
        if role == "assistant":
            # Coach question — render as prompt
            lines.append(f"**Q:** {text}\n")
        elif role == "user":
            lines.append(f"**A:** {text}\n")

    if not lines:
        return

    responses_md = "\n".join(lines)
    conn.execute(
        "INSERT INTO raw_responses (para_text_hash, session_topic, responses_md) VALUES (?, ?, ?)",
        (para_text_hash, topic, responses_md),
    )
    conn.commit()


def db_path(paragraphs_files: list[Path]) -> Path:
    return paragraphs_files[0].parent / "library.db"


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def sync_from_markdown(
    conn: sqlite3.Connection,
    paragraphs: list[Paragraph],
    source_files: list[Path],
) -> dict[str, int]:
    """Upsert paragraphs from markdown into the DB.

    Match on text_hash within source_file. Text changes → new row.
    Paragraphs no longer in the file are retired (active=0).
    """
    counts = {"inserted": 0, "updated": 0, "retired": 0, "unchanged": 0}

    for layer, source_file in enumerate(source_files):
        source_str = str(source_file)
        file_paragraphs = [p for p in paragraphs if p.layer == layer]

        existing: dict[str, dict] = {
            row["text_hash"]: dict(row)
            for row in conn.execute(
                "SELECT * FROM paragraphs WHERE source_file = ? AND active = 1",
                (source_str,),
            )
        }

        current_hashes: set[str] = set()

        for p in file_paragraphs:
            h = _hash(p.text)
            current_hashes.add(h)
            meta = p.meta

            row_data = dict(
                role=p.role, section=p.section, text=p.text, text_hash=h,
                type=meta.get("type"), frame=meta.get("frame"),
                angle=meta.get("angle"), strength=meta.get("strength"),
                via=meta.get("via"), tone=meta.get("tone"), tech=meta.get("tech"),
                layer=p.layer, source_file=source_str,
            )

            if h in existing:
                ex = existing[h]
                meta_keys = ("role", "section", "type", "frame", "angle",
                             "strength", "via", "tone", "tech")
                if any(ex[k] != row_data[k] for k in meta_keys):
                    conn.execute(
                        """UPDATE paragraphs
                           SET role=:role, section=:section, type=:type, frame=:frame,
                               angle=:angle, angle_auto=0, strength=:strength, via=:via,
                               tone=:tone, tech=:tech, updated_at=datetime('now')
                           WHERE text_hash=:text_hash AND source_file=:source_file AND active=1""",
                        row_data,
                    )
                    counts["updated"] += 1
                else:
                    counts["unchanged"] += 1
            else:
                conn.execute(
                    """INSERT INTO paragraphs
                           (role, section, text, text_hash, type, frame, angle, strength,
                            via, tone, tech, layer, active, source_file)
                       VALUES
                           (:role, :section, :text, :text_hash, :type, :frame, :angle,
                            :strength, :via, :tone, :tech, :layer, 1, :source_file)""",
                    row_data,
                )
                # Seed paragraph_angles from markdown meta (human label, not auto)
                para_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                if meta.get("angle"):
                    conn.execute(
                        """INSERT OR IGNORE INTO paragraph_angles
                               (paragraph_id, angle, is_primary, confidence, angle_auto)
                           VALUES (?, ?, 1, NULL, 0)""",
                        (para_id, meta["angle"]),
                    )
                counts["inserted"] += 1

        for h, ex in existing.items():
            if h not in current_hashes:
                conn.execute(
                    "UPDATE paragraphs SET active=0, updated_at=datetime('now') WHERE id=?",
                    (ex["id"],),
                )
                counts["retired"] += 1

    conn.commit()
    return counts


# ---------------------------------------------------------------------------
# Paragraph embeddings
# ---------------------------------------------------------------------------

def compute_embeddings(
    conn: sqlite3.Connection,
    voyage_api_key: str,
    model: str = "voyage-3-lite",
    batch_size: int = 64,
) -> int:
    """Embed active paragraphs that have no stored embedding. Returns count."""
    rows = conn.execute(
        """SELECT p.id, p.text FROM paragraphs p
           LEFT JOIN embeddings e ON p.id = e.paragraph_id
           WHERE p.active = 1 AND e.paragraph_id IS NULL"""
    ).fetchall()

    if not rows:
        return 0

    try:
        import voyageai  # type: ignore
        client = voyageai.Client(api_key=voyage_api_key)
    except (ImportError, Exception):
        return 0

    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            result = client.embed(
                [r["text"] for r in batch], model=model, input_type="document"
            )
        except Exception:
            break
        for row, vec in zip(batch, result.embeddings):
            conn.execute(
                """INSERT OR REPLACE INTO embeddings (paragraph_id, model, vector, indexed_at)
                   VALUES (?, ?, ?, datetime('now'))""",
                (row["id"], model, json.dumps(vec)),
            )
        total += len(batch)

    conn.commit()
    return total


# ---------------------------------------------------------------------------
# Sentence extraction and embeddings
# ---------------------------------------------------------------------------

def extract_and_store_sentences(conn: sqlite3.Connection) -> int:
    """Split active paragraphs into sentences and store them.

    Only processes paragraphs with no existing sentence rows.
    Returns number of sentences stored.
    """
    para_ids_with_sentences = {
        row[0]
        for row in conn.execute("SELECT DISTINCT paragraph_id FROM sentences")
    }

    rows = conn.execute(
        "SELECT id, text FROM paragraphs WHERE active = 1"
    ).fetchall()

    total = 0
    for row in rows:
        if row["id"] in para_ids_with_sentences:
            continue
        for pos, sent in enumerate(_split_sentences(row["text"])):
            conn.execute(
                """INSERT OR IGNORE INTO sentences (paragraph_id, position, text, text_hash)
                   VALUES (?, ?, ?, ?)""",
                (row["id"], pos, sent, _hash(sent)),
            )
            total += 1

    conn.commit()
    return total


def compute_sentence_embeddings(
    conn: sqlite3.Connection,
    voyage_api_key: str,
    model: str = "voyage-3-lite",
    batch_size: int = 128,
) -> int:
    """Embed sentences that have no stored embedding. Returns count."""
    rows = conn.execute(
        """SELECT s.id, s.text FROM sentences s
           LEFT JOIN sentence_embeddings se ON s.id = se.sentence_id
           WHERE se.sentence_id IS NULL"""
    ).fetchall()

    if not rows:
        return 0

    try:
        import voyageai  # type: ignore
        client = voyageai.Client(api_key=voyage_api_key)
    except (ImportError, Exception):
        return 0

    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            result = client.embed(
                [r["text"] for r in batch], model=model, input_type="document"
            )
        except Exception:
            break
        for row, vec in zip(batch, result.embeddings):
            conn.execute(
                """INSERT OR REPLACE INTO sentence_embeddings
                       (sentence_id, model, vector, indexed_at)
                   VALUES (?, ?, ?, datetime('now'))""",
                (row["id"], model, json.dumps(vec)),
            )
        total += len(batch)

    conn.commit()
    return total


# ---------------------------------------------------------------------------
# Canonical angle classification
# ---------------------------------------------------------------------------

def assign_angles_canonical(
    conn: sqlite3.Connection,
    voyage_api_key: str,
    model: str = "voyage-3-lite",
    primary_threshold: float = 0.30,
    secondary_threshold: float = 0.25,
) -> dict[str, int]:
    """Classify every active paragraph against canonical angle descriptions.

    Embeds the 14 angle descriptions, then scores each paragraph embedding
    against all of them. Assigns:
      - Primary angle: highest scorer above primary_threshold
      - Secondary angles: all others above secondary_threshold

    Human-labeled angles from markdown (angle_auto=0 in paragraph_angles)
    keep their is_primary=1 status; the classifier adds secondaries around them.

    Returns {angle: count_assigned}.
    """
    try:
        import voyageai  # type: ignore
        client = voyageai.Client(api_key=voyage_api_key)
    except (ImportError, Exception):
        return {}

    # Embed all canonical angle descriptions
    angle_names = list(CANONICAL_ANGLES.keys())
    angle_descs = [CANONICAL_ANGLES[a] for a in angle_names]
    try:
        desc_result = client.embed(angle_descs, model=model, input_type="document")
    except Exception:
        return {}
    angle_vecs = {name: vec for name, vec in zip(angle_names, desc_result.embeddings)}

    # Get all active paragraphs with embeddings
    rows = conn.execute(
        """SELECT p.id, e.vector FROM paragraphs p
           JOIN embeddings e ON p.id = e.paragraph_id
           WHERE p.active = 1"""
    ).fetchall()

    assigned: dict[str, int] = {}

    for row in rows:
        para_id = row["id"]
        para_vec = json.loads(row["vector"])

        scores = {
            angle: _cosine(para_vec, angle_vecs[angle])
            for angle in angle_names
        }

        best_angle = max(scores, key=lambda a: scores[a])
        best_score = scores[best_angle]

        if best_score < primary_threshold:
            continue

        # Always assign the canonical primary angle — angle tags in markdown are written
        # by the seed/extract process, not the user, so there are no human labels to protect.
        # Clear any existing non-canonical primary flag first so retrieval isn't confused.
        conn.execute(
            "UPDATE paragraph_angles SET is_primary=0 WHERE paragraph_id=? AND angle NOT IN (%s)"
            % ",".join("?" * len(angle_names)),
            (para_id, *angle_names),
        )
        conn.execute(
            """INSERT INTO paragraph_angles (paragraph_id, angle, is_primary, confidence, angle_auto)
               VALUES (?, ?, 1, ?, 1)
               ON CONFLICT(paragraph_id, angle) DO UPDATE SET
                   is_primary=1, confidence=excluded.confidence, angle_auto=1""",
            (para_id, best_angle, best_score),
        )
        conn.execute(
            "UPDATE paragraphs SET angle=?, angle_auto=1 WHERE id=?",
            (best_angle, para_id),
        )
        assigned[best_angle] = assigned.get(best_angle, 0) + 1

        # Assign secondary angles for all others above secondary threshold
        for angle, score in scores.items():
            if angle == best_angle:
                continue
            if score >= secondary_threshold:
                conn.execute(
                    """INSERT INTO paragraph_angles
                           (paragraph_id, angle, is_primary, confidence, angle_auto)
                       VALUES (?, ?, 0, ?, 1)
                       ON CONFLICT(paragraph_id, angle) DO UPDATE SET
                           confidence=excluded.confidence, angle_auto=1""",
                    (para_id, angle, score),
                )

    conn.commit()
    return assigned


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def query_sentences(
    conn: sqlite3.Connection,
    query_text: str,
    voyage_api_key: str,
    top_n: int = 25,
    angle_filter: str | None = None,
    type_filter: str | None = None,
    model: str = "voyage-3-lite",
) -> list[dict]:
    """Return top_n sentences most relevant to query_text.

    Each result includes the sentence text, its parent paragraph's role/section,
    and all angles assigned to the paragraph — so the model knows what each
    sentence is evidence of.

    This is the foundation of patchwork letter assembly.
    """
    try:
        import voyageai  # type: ignore
        client = voyageai.Client(api_key=voyage_api_key)
        result = client.embed([query_text], model=model, input_type="query")
        query_vec = result.embeddings[0]
    except Exception:
        return []

    where_clauses = ["p.active = 1", "se.sentence_id IS NOT NULL"]
    params: list = []

    if type_filter:
        where_clauses.append("p.type = ?")
        params.append(type_filter)

    if angle_filter:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM paragraph_angles pa WHERE pa.paragraph_id = p.id AND pa.angle = ?)"
        )
        params.append(angle_filter)

    where = " AND ".join(where_clauses)

    rows = conn.execute(
        f"""SELECT s.id, s.text, s.paragraph_id, p.role, p.section, p.type,
                   se.vector
            FROM sentences s
            JOIN paragraphs p ON s.paragraph_id = p.id
            JOIN sentence_embeddings se ON s.id = se.sentence_id
            WHERE {where}""",
        params,
    ).fetchall()

    if not rows:
        return []

    # Score and sort
    scored = []
    for row in rows:
        score = _cosine(query_vec, json.loads(row["vector"]))
        scored.append((score, dict(row)))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_n]

    # Attach all angles to each result
    results = []
    for score, row in top:
        angles = [
            r["angle"]
            for r in conn.execute(
                "SELECT angle FROM paragraph_angles WHERE paragraph_id = ? ORDER BY is_primary DESC, confidence DESC",
                (row["paragraph_id"],),
            )
        ]
        results.append({
            "sentence": row["text"],
            "role": row["role"],
            "section": row["section"],
            "type": row["type"],
            "angles": angles,
            "score": score,
            "paragraph_id": row["paragraph_id"],
        })

    return results


def paragraph_hash(text: str) -> str:
    """Public wrapper — same hash used when syncing from markdown."""
    return _hash(text)


def rank_paragraphs_by_sentences(
    conn: sqlite3.Connection,
    query_text: str,
    voyage_api_key: str,
    model: str = "voyage-3-lite",
) -> dict[str, float]:
    """Return {text_hash: best_sentence_score} for all paragraphs with sentence embeddings.

    Score is the highest cosine similarity of any sentence in the paragraph against
    the query. Use this to re-rank a prefiltered paragraph list with sentence-level
    precision — more targeted than paragraph-level embeddings alone.
    """
    rows = conn.execute(
        """SELECT p.text_hash, se.vector
           FROM sentences s
           JOIN sentence_embeddings se ON s.id = se.sentence_id
           JOIN paragraphs p ON s.paragraph_id = p.id
           WHERE p.active = 1"""
    ).fetchall()

    if not rows:
        return {}

    try:
        import voyageai  # type: ignore
        client = voyageai.Client(api_key=voyage_api_key)
        result = client.embed([query_text], model=model, input_type="query")
        query_vec = result.embeddings[0]
    except Exception:
        return {}

    best: dict[str, float] = {}
    for row in rows:
        score = _cosine(query_vec, json.loads(row["vector"]))
        h = row["text_hash"]
        if score > best.get(h, -1.0):
            best[h] = score

    return best


def build_angle_evidence(
    conn: sqlite3.Connection,
    jd_text: str,
    voyage_api_key: str,
    top_angles: int = 4,
    sentences_per_angle: int = 3,
    model: str = "voyage-3-lite",
    thesis_text: str | None = None,
    required_gap_queries: list[str] | None = None,
) -> list[dict]:
    """Return angle-organized evidence for letter synthesis.

    Scores canonical angles against the JD to find the top argument categories
    the role needs, then retrieves the most JD-relevant sentences from paragraphs
    tagged with each angle — with a sentence of context on each side for grounding.

    required_gap_queries: gap descriptions that were filled during Q&A. For each,
    a direct sentence search is run against all paragraphs (bypassing angle selection)
    so gap-filling content always enters the evidence pool.

    One sentence per source paragraph (forces diversity across experiences).

    Returns:
        [
            {
                "angle": "ownership",
                "sentences": [
                    {
                        "text": "I owned the pipeline...",   # key sentence
                        "context_before": "...",             # sentence before (or "")
                        "context_after": "...",              # sentence after (or "")
                        "role": "Data Engineer",
                        "section": "Voter File",
                    },
                    ...
                ]
            },
            ...
        ]
    """
    try:
        import voyageai  # type: ignore
        client = voyageai.Client(api_key=voyage_api_key)
    except (ImportError, Exception):
        return []

    # Score each canonical angle description against the JD (+ thesis beacon when available)
    angle_names = list(CANONICAL_ANGLES.keys())
    angle_descriptions = list(CANONICAL_ANGLES.values())

    # Combining the provisional argument with the JD gives the query more semantic
    # specificity — angles are ranked against what the letter SHOULD argue, not just
    # what the JD mentions. This focuses sentence retrieval on the argument that matters.
    query_text = f"{thesis_text}\n\n{jd_text}" if thesis_text else jd_text

    try:
        jd_result = client.embed([query_text], model=model, input_type="query")
        jd_vec = jd_result.embeddings[0]
        desc_result = client.embed(angle_descriptions, model=model, input_type="document")
    except Exception:
        return []

    angle_scores = sorted(
        [(name, _cosine(jd_vec, vec)) for name, vec in zip(angle_names, desc_result.embeddings)],
        key=lambda x: x[1],
        reverse=True,
    )
    top_angle_names = [name for name, _ in angle_scores[:top_angles]]
    angle_score_map = {name: score for name, score in angle_scores}

    # Determine if graph traversal is available (sentence_claims + claim_angles populated)
    graph_ready = conn.execute("SELECT COUNT(*) FROM sentence_claims").fetchone()[0] > 0

    # Provenance-first pass: paragraphs written specifically for this JD, ordered by
    # stored jd_score. These are guaranteed into the evidence pool before angle scoring.
    jd_hash = _hash(jd_text.strip())
    provenance_para_ids: set[int] = set()
    provenance_texts: set[str] = set()
    try:
        prov_rows = conn.execute(
            """SELECT pgp.para_hash, pgp.jd_score, pgp.gap_question, pgp.driving_angle,
                      p.id as para_id, p.role, p.section, p.text as para_text
               FROM paragraph_gap_provenance pgp
               JOIN paragraphs p ON p.text_hash = pgp.para_hash
               WHERE pgp.jd_hash = ? AND p.active = 1
               ORDER BY pgp.jd_score DESC""",
            (jd_hash,),
        ).fetchall()
        if prov_rows:
            prov_sentences = []
            for row in prov_rows:
                # Best sentence from this paragraph
                sent_rows = conn.execute(
                    """SELECT s.text, s.position, se.vector
                       FROM sentences s
                       JOIN sentence_embeddings se ON s.id = se.sentence_id
                       WHERE s.paragraph_id = ?
                       ORDER BY s.position""",
                    (row["para_id"],),
                ).fetchall()
                best_sent = max(
                    sent_rows,
                    key=lambda r: _cosine(jd_vec, json.loads(r["vector"])),
                    default=None,
                ) if sent_rows else None
                sent_text = best_sent["text"] if best_sent else row["para_text"][:120]
                provenance_para_ids.add(row["para_id"])
                provenance_texts.add(sent_text)
                src = row["para_text"]
                prov_sentences.append({
                    "text": sent_text,
                    "source_paragraph": src[:250] + ("..." if len(src) > 250 else ""),
                    "role": row["role"],
                    "section": row["section"],
                    "claim": f"[written for this JD — score {row['jd_score']:.2f}] {row['gap_question'] or ''}",
                })
            if prov_sentences:
                result_provenance = [{
                    "angle": "provenance-match",
                    "sentences": prov_sentences,
                    "jd_score": 1.0,
                    "required": True,
                    "rank": 0,
                }]
            else:
                result_provenance = []
        else:
            result_provenance = []
    except Exception:
        result_provenance = []

    result = []
    for angle in top_angle_names:
        # Graph path: angle → claims → sentences → source paragraph
        # This is the full layered traversal the design intends.
        claim_rows = conn.execute(
            """SELECT DISTINCT c.id, c.text as claim_text, c.source_para_hash,
                      s.id as sent_id, s.text as sent_text, s.position,
                      s.paragraph_id, p.role, p.section, p.text as para_text,
                      se.vector
               FROM claim_angles ca
               JOIN claims c ON ca.claim_id = c.id
               JOIN sentence_claims sc ON sc.claim_id = c.id
               JOIN sentences s ON sc.sentence_id = s.id
               JOIN sentence_embeddings se ON s.id = se.sentence_id
               JOIN paragraphs p ON s.paragraph_id = p.id
               WHERE ca.angle = ? AND p.active = 1""",
            (angle,),
        ).fetchall()

        if not claim_rows:
            # Fallback: paragraph_angles path — at least get the paragraph
            claim_rows = conn.execute(
                """SELECT NULL as claim_text, NULL as source_para_hash,
                          s.id as sent_id, s.text as sent_text, s.position,
                          s.paragraph_id, p.role, p.section, p.text as para_text,
                          se.vector
                   FROM sentences s
                   JOIN sentence_embeddings se ON s.id = se.sentence_id
                   JOIN paragraphs p ON s.paragraph_id = p.id
                   JOIN paragraph_angles pa ON p.id = pa.paragraph_id
                   WHERE pa.angle = ? AND pa.is_primary = 1 AND p.active = 1""",
                (angle,),
            ).fetchall()

        if not claim_rows:
            continue

        # Score each sentence against the JD
        scored = sorted(
            claim_rows,
            key=lambda r: _cosine(jd_vec, json.loads(r["vector"])),
            reverse=True,
        )

        # Take top sentences_per_angle — one per source paragraph for diversity.
        # Skip paragraphs already in the provenance block to avoid duplication.
        entries = []
        seen_paragraphs: set[int] = set(provenance_para_ids)
        for row in scored:
            if len(entries) >= sentences_per_angle:
                break
            if row["paragraph_id"] in seen_paragraphs:
                continue
            seen_paragraphs.add(row["paragraph_id"])
            entries.append({
                "claim": row["claim_text"] or "",
                "text": row["sent_text"],
                "source_paragraph": row["para_text"],
                "role": row["role"],
                "section": row["section"],
            })

        if entries:
            rank = top_angle_names.index(angle) + 1  # 1-based rank by JD relevance
            score = angle_score_map.get(angle, 0.0)
            # Required = scores strongly against the JD, not an arbitrary top-N count.
            # Angles above 0.45 cosine similarity are explicit JD requirements.
            # Angles 0.35-0.45 are supporting — relevant but not the core ask.
            required = score >= 0.45
            result.append({
                "angle": angle,
                "sentences": entries,
                "jd_score": score,
                "required": required,
                "rank": rank,
            })

    # For each gap that was filled during Q&A, do a direct sentence search
    # against all active paragraphs — bypassing angle selection so gap-filling
    # evidence enters the pool even if its angle didn't rank in the top N.
    if required_gap_queries:
        existing_sentence_ids: set[int] = {
            s_row["id"]
            for block in result
            for s_row in block["sentences"]
            # sentences in result dicts don't carry id — track by text instead
        }
        existing_texts: set[str] = {
            s["text"] for block in result for s in block["sentences"]
        }
        all_sent_rows = conn.execute(
            """SELECT s.id, s.text, s.position, s.paragraph_id,
                      p.role, p.section, se.vector
               FROM sentences s
               JOIN sentence_embeddings se ON s.id = se.sentence_id
               JOIN paragraphs p ON s.paragraph_id = p.id
               WHERE p.active = 1"""
        ).fetchall()
        if all_sent_rows:
            for gap_query in required_gap_queries:
                try:
                    gap_result = client.embed([gap_query], model=model, input_type="query")
                    gap_vec = gap_result.embeddings[0]
                except Exception:
                    continue
                scored_gap = sorted(
                    all_sent_rows,
                    key=lambda r: _cosine(gap_vec, json.loads(r["vector"])),
                    reverse=True,
                )
                gap_sentences = []
                seen_paragraphs_gap: set[int] = set()
                for row in scored_gap:
                    if len(gap_sentences) >= sentences_per_angle:
                        break
                    if row["paragraph_id"] in seen_paragraphs_gap:
                        continue
                    if row["text"] in existing_texts:
                        continue
                    seen_paragraphs_gap.add(row["paragraph_id"])
                    existing_texts.add(row["text"])
                    ctx = {
                        r["position"]: r["text"]
                        for r in conn.execute(
                            """SELECT position, text FROM sentences
                               WHERE paragraph_id = ? AND position BETWEEN ? AND ?
                               ORDER BY position""",
                            (row["paragraph_id"], row["position"] - 1, row["position"] + 1),
                        )
                    }
                    gap_sentences.append({
                        "text": row["text"],
                        "context_before": ctx.get(row["position"] - 1, ""),
                        "context_after": ctx.get(row["position"] + 1, ""),
                        "role": row["role"],
                        "section": row["section"],
                    })
                if gap_sentences:
                    result.append({"angle": f"gap: {gap_query[:60]}", "sentences": gap_sentences})

    # Prepend provenance-matched paragraphs — they came first because they were written for this JD
    result = result_provenance + result

    # Direct JD similarity pass — catches paragraphs the user wrote for this JD that
    # got miscategorized or whose canonical angle didn't rank in the top N.
    # Embeds the JD query directly against all paragraph embeddings (not sentences),
    # takes the top 5 paragraphs by cosine similarity, and adds any whose best sentence
    # isn't already in the evidence pool.
    try:
        existing_texts: set[str] = {s["text"] for block in result for s in block["sentences"]}
        para_rows = conn.execute(
            """SELECT p.id, p.role, p.section, p.text, e.vector
               FROM paragraphs p
               JOIN embeddings e ON p.id = e.paragraph_id
               WHERE p.active = 1"""
        ).fetchall()
        if para_rows:
            scored_paras = sorted(
                para_rows,
                key=lambda r: _cosine(jd_vec, json.loads(r["vector"])),
                reverse=True,
            )
            direct_sentences = []
            seen_para_ids: set[int] = set()
            for row in scored_paras[:8]:  # top 8 paragraphs by direct JD similarity
                if row["id"] in seen_para_ids:
                    continue
                # pick the best sentence from this paragraph that isn't already in pool
                sent_rows = conn.execute(
                    """SELECT s.text, s.position, se.vector
                       FROM sentences s
                       JOIN sentence_embeddings se ON s.id = se.sentence_id
                       WHERE s.paragraph_id = ?
                       ORDER BY s.position""",
                    (row["id"],),
                ).fetchall()
                best_sent = None
                best_score = -1.0
                for sr in sent_rows:
                    if sr["text"] in existing_texts:
                        continue
                    sc = _cosine(jd_vec, json.loads(sr["vector"]))
                    if sc > best_score:
                        best_score = sc
                        best_sent = sr
                if best_sent is None:
                    continue
                seen_para_ids.add(row["id"])
                existing_texts.add(best_sent["text"])
                src = row["text"]
                direct_sentences.append({
                    "text": best_sent["text"],
                    "source_paragraph": src[:250] + ("..." if len(src) > 250 else ""),
                    "role": row["role"],
                    "section": row["section"],
                })
            if direct_sentences:
                result.append({
                    "angle": "direct-jd-match",
                    "sentences": direct_sentences,
                    "jd_score": 1.0,
                    "required": True,
                    "rank": 0,
                })
    except Exception:
        pass

    return result


def link_claims_to_graph(
    conn: sqlite3.Connection,
    voyage_api_key: str,
    model: str = "voyage-3-lite",
    force: bool = False,
) -> tuple[int, int]:
    """Wire existing claims into the sentence_claims and claim_angles graph tables.

    For each claim not yet linked:
    - Find sentences in the same source paragraph (via source_para_hash → paragraphs → sentences)
    - Score each sentence against the claim embedding; link any sentence scoring above threshold
    - Write claim_angles rows from the claim's argument_categories JSON

    Returns (sentence_links_created, angle_links_created).
    """
    try:
        import voyageai  # type: ignore
        client = voyageai.Client(api_key=voyage_api_key)
    except (ImportError, Exception):
        return 0, 0

    if force:
        claims = conn.execute(
            "SELECT id, text, embedding, argument_categories, source_para_hash FROM claims"
        ).fetchall()
    else:
        already_linked = {
            r[0] for r in conn.execute("SELECT DISTINCT claim_id FROM sentence_claims")
        }
        claims = [
            r for r in conn.execute(
                "SELECT id, text, embedding, argument_categories, source_para_hash FROM claims"
            ).fetchall()
            if r["id"] not in already_linked
        ]

    if not claims:
        return 0, 0

    sent_links = 0
    angle_links = 0
    SCORE_THRESHOLD = 0.5

    for claim in claims:
        claim_id = claim["id"]
        claim_text = claim["text"]
        para_hash = claim["source_para_hash"]

        # --- sentence_claims ---
        if para_hash:
            para_row = conn.execute(
                "SELECT id FROM paragraphs WHERE text_hash = ? LIMIT 1", (para_hash,)
            ).fetchone()
            if para_row:
                para_id = para_row["id"]
                sent_rows = conn.execute(
                    """SELECT s.id, s.text, se.vector
                       FROM sentences s
                       JOIN sentence_embeddings se ON s.id = se.sentence_id
                       WHERE s.paragraph_id = ?""",
                    (para_id,),
                ).fetchall()
                if sent_rows:
                    # Get or compute claim embedding
                    if claim["embedding"]:
                        claim_vec = json.loads(claim["embedding"])
                    else:
                        try:
                            res = client.embed([claim_text], model=model, input_type="document")
                            claim_vec = res.embeddings[0]
                            conn.execute(
                                "UPDATE claims SET embedding = ? WHERE id = ?",
                                (json.dumps(claim_vec).encode(), claim_id),
                            )
                        except Exception:
                            claim_vec = None

                    if claim_vec:
                        for sent in sent_rows:
                            score = _cosine(claim_vec, json.loads(sent["vector"]))
                            if score >= SCORE_THRESHOLD:
                                conn.execute(
                                    "INSERT OR IGNORE INTO sentence_claims (sentence_id, claim_id, score) VALUES (?, ?, ?)",
                                    (sent["id"], claim_id, score),
                                )
                                sent_links += 1

        # --- claim_angles via embedding similarity ---
        # Always classify claims against canonical angles using embeddings — this is more
        # reliable than parsing argument_categories (which only fires for 6 of 18 angles).
        # argument_categories is used as a secondary signal when available.
        claim_vec = None
        if claim["embedding"]:
            claim_vec = json.loads(claim["embedding"])
        elif claim_text:
            try:
                res = client.embed([claim_text], model=model, input_type="document")
                claim_vec = res.embeddings[0]
                conn.execute(
                    "UPDATE claims SET embedding = ? WHERE id = ?",
                    (json.dumps(claim_vec).encode(), claim_id),
                )
            except Exception:
                pass

        if claim_vec:
            # Get cached angle description embeddings (or embed them now)
            angle_names = list(CANONICAL_ANGLES.keys())
            angle_descs = list(CANONICAL_ANGLES.values())
            try:
                desc_result = client.embed(angle_descs, model=model, input_type="document")
                angle_scores = [
                    (name, _cosine(claim_vec, vec))
                    for name, vec in zip(angle_names, desc_result.embeddings)
                ]
                # Link top 2 angles scoring above 0.35 — ensures every claim is reachable
                angle_scores.sort(key=lambda x: x[1], reverse=True)
                for angle_name, score in angle_scores[:2]:
                    if score >= 0.35:
                        conn.execute(
                            "INSERT OR IGNORE INTO claim_angles (claim_id, angle) VALUES (?, ?)",
                            (claim_id, angle_name),
                        )
                        angle_links += 1
            except Exception:
                pass

    conn.commit()
    return sent_links, angle_links


def query_similar(
    conn: sqlite3.Connection,
    text: str,
    voyage_api_key: str,
    top_n: int = 3,
    type_filter: str | None = None,
    model: str = "voyage-3-lite",
) -> list[tuple[str, str, float]]:
    """Return top_n [(role, section, score)] from paragraph embeddings.
    Used by intake to suggest where a new paragraph belongs."""
    where = "p.active = 1"
    params: list = []
    if type_filter:
        where += " AND p.type = ?"
        params.append(type_filter)

    rows = conn.execute(
        f"""SELECT p.role, p.section, e.vector FROM paragraphs p
            JOIN embeddings e ON p.id = e.paragraph_id
            WHERE {where}""",
        params,
    ).fetchall()

    if not rows:
        return []

    try:
        import voyageai  # type: ignore
        client = voyageai.Client(api_key=voyage_api_key)
        result = client.embed([text], model=model, input_type="query")
        query_vec = result.embeddings[0]
    except Exception:
        return []

    best: dict[tuple[str, str], float] = {}
    for row in rows:
        score = _cosine(query_vec, json.loads(row["vector"]))
        key = (row["role"], row["section"])
        if score > best.get(key, -1.0):
            best[key] = score

    results = sorted(best.items(), key=lambda x: x[1], reverse=True)
    return [(role, section, score) for (role, section), score in results[:top_n]]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM paragraphs WHERE active=1").fetchone()[0]
    embedded = conn.execute(
        "SELECT COUNT(*) FROM paragraphs p JOIN embeddings e ON p.id=e.paragraph_id WHERE p.active=1"
    ).fetchone()[0]
    n_sentences = conn.execute("SELECT COUNT(*) FROM sentences").fetchone()[0]
    sent_embedded = conn.execute("SELECT COUNT(*) FROM sentence_embeddings").fetchone()[0]
    n_angle_assignments = conn.execute("SELECT COUNT(*) FROM paragraph_angles").fetchone()[0]
    paragraphs_with_angle = conn.execute(
        "SELECT COUNT(DISTINCT paragraph_id) FROM paragraph_angles"
    ).fetchone()[0]
    return {
        "total": total,
        "embedded": embedded,
        "sentences": n_sentences,
        "sentences_embedded": sent_embedded,
        "paragraphs_with_angle": paragraphs_with_angle,
        "angle_assignments": n_angle_assignments,
        "missing_angle": total - paragraphs_with_angle,
        "missing_embedding": total - embedded,
    }


# ---------------------------------------------------------------------------
# Category embeddings — precomputed, stored in DB, recomputed only on change
# ---------------------------------------------------------------------------

def ensure_category_embeddings(
    conn: sqlite3.Connection,
    voyage_api_key: str,
    provider: "object | None" = None,
) -> int:
    """Compute and store category description embeddings if missing or stale.

    Tries provider-native embeddings first, then Voyage, then skips.
    Returns number of categories (re)computed.
    """
    categories = load_argument_categories()
    if not categories:
        return 0

    import hashlib

    existing = {
        row["category_name"]: row["description_hash"]
        for row in conn.execute(
            "SELECT category_name, description_hash FROM category_embeddings"
        ).fetchall()
    }

    def _desc_hash(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    to_compute = [
        c for c in categories
        if c["name"] not in existing
        or existing[c["name"]] != _desc_hash(c["description"])
    ]
    if not to_compute:
        return 0

    descriptions = [c["description"] for c in to_compute]
    vectors: list[list[float]] | None = None

    # Try provider-native embeddings first
    if provider is not None:
        from coverletter.provider import Provider as ProviderBase
        if isinstance(provider, ProviderBase) and provider.supports_embed():
            vectors = provider.embed(descriptions, input_type="document")

    # Fall back to Voyage
    if vectors is None and voyage_api_key:
        try:
            import voyageai  # type: ignore
            client = voyageai.Client(api_key=voyage_api_key)
            result = client.embed(descriptions, model="voyage-3-lite", input_type="document")
            vectors = result.embeddings
        except Exception:
            pass

    if not vectors:
        return 0

    for cat, vec in zip(to_compute, vectors):
        blob = json.dumps(vec).encode()
        conn.execute(
            "INSERT OR REPLACE INTO category_embeddings "
            "(category_name, embedding, computed_at, description_hash) "
            "VALUES (?, ?, datetime('now'), ?)",
            (cat["name"], blob, _desc_hash(cat["description"])),
        )
    conn.commit()
    return len(to_compute)


def get_category_embeddings(conn: sqlite3.Connection) -> dict[str, list[float]]:
    """Return {category_name: embedding_vector} for all stored categories."""
    result = {}
    for row in conn.execute("SELECT category_name, embedding FROM category_embeddings").fetchall():
        try:
            result[row["category_name"]] = json.loads(row["embedding"])
        except Exception:
            pass
    return result


def score_jd_against_categories(
    jd_embedding: list[float],
    category_embeddings: dict[str, list[float]],
) -> list[tuple[str, float]]:
    """Rank argument categories by relevance to a JD embedding.

    Returns [(category_name, score)] sorted descending.
    """
    scores = []
    for name, vec in category_embeddings.items():
        score = _cosine(jd_embedding, vec)
        scores.append((name, score))
    scores.sort(key=lambda x: -x[1])
    return scores


# ---------------------------------------------------------------------------
# Application capture
# ---------------------------------------------------------------------------

def record_application(
    conn: sqlite3.Connection,
    company: str,
    role: str,
    jd_text: str,
    jd_embedding: list[float] | None = None,
) -> int:
    """Create an application record. Returns application id."""
    jd_hash = _hash(jd_text)
    jd_blob = json.dumps(jd_embedding).encode() if jd_embedding else None
    cur = conn.execute(
        "INSERT INTO applications (company, role, jd_text, jd_hash, jd_embedding) "
        "VALUES (?, ?, ?, ?, ?)",
        (company, role or "", jd_text, jd_hash, jd_blob),
    )
    conn.commit()
    return cur.lastrowid


def record_category_scores(
    conn: sqlite3.Connection,
    application_id: int,
    scores: list[tuple[str, float]],
) -> None:
    """Store category relevance scores for an application."""
    conn.executemany(
        "INSERT INTO application_category_scores (application_id, argument_category, relevance_score) "
        "VALUES (?, ?, ?)",
        [(application_id, cat, score) for cat, score in scores],
    )
    conn.commit()


def record_claim_scores(
    conn: sqlite3.Connection,
    application_id: int,
    scored_claims: list[dict],
) -> None:
    """Store claim similarity scores for an application.

    scored_claims: list of {claim_id, argument_category, similarity_score,
                             in_outline, in_letter}
    """
    conn.executemany(
        "INSERT INTO application_claim_scores "
        "(application_id, claim_id, argument_category, similarity_score, in_outline, in_letter) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                application_id,
                c["claim_id"],
                c.get("argument_category"),
                c["similarity_score"],
                1 if c.get("in_outline") else 0,
                1 if c.get("in_letter") else 0,
            )
            for c in scored_claims
        ],
    )
    conn.commit()


def record_gaps(
    conn: sqlite3.Connection,
    application_id: int,
    gaps: list[dict],
) -> list[int]:
    """Store JD requirement gaps for an application. Returns gap ids."""
    ids = []
    for gap in gaps:
        cur = conn.execute(
            "INSERT INTO application_gaps "
            "(application_id, requirement_text, inferred_category, had_db_coverage, addressed_in_letter) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                application_id,
                gap["requirement_text"],
                gap.get("inferred_category"),
                1 if gap.get("had_db_coverage") else 0,
                1 if gap.get("addressed_in_letter") else 0,
            ),
        )
        ids.append(cur.lastrowid)
    conn.commit()
    return ids


def update_application_outcome(
    conn: sqlite3.Connection,
    application_id: int,
    outcome: str,
    notes: str | None = None,
) -> None:
    """Update outcome after the fact: applied|response|interview|offer|rejected|withdrew"""
    conn.execute(
        "UPDATE applications SET outcome = ?, notes = COALESCE(?, notes) WHERE id = ?",
        (outcome, notes, application_id),
    )
    conn.commit()


def mark_claims_in_letter(
    conn: sqlite3.Connection,
    application_id: int,
    claim_ids: list[int],
) -> None:
    """Mark which claims actually appeared in the sent letter."""
    if not claim_ids:
        return
    placeholders = ",".join("?" * len(claim_ids))
    conn.execute(
        f"UPDATE application_claim_scores SET in_letter = 1 "
        f"WHERE application_id = ? AND claim_id IN ({placeholders})",
        [application_id] + claim_ids,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Provenance inference
# ---------------------------------------------------------------------------

def infer_paragraph_provenance(conn: sqlite3.Connection, days_window: int = 14) -> int:
    """Infer paragraph provenance by matching build sessions against recent gaps.

    For each paragraph without provenance:
    - Find the raw_response that produced it (via para_text_hash)
    - Check if any gap exists in applications within days_window before the paragraph
    - If session_topic semantically overlaps with a gap's requirement_text, mark gap_driven
    - Otherwise mark organic

    Uses simple keyword overlap — no embedding call needed here.
    Returns number of paragraphs tagged.
    """
    # Find paragraphs without provenance
    untagged = conn.execute(
        """SELECT p.id, p.text_hash, p.created_at
           FROM paragraphs p
           LEFT JOIN paragraph_provenance pp ON p.id = pp.paragraph_id
           WHERE pp.paragraph_id IS NULL AND p.active = 1"""
    ).fetchall()

    if not untagged:
        return 0

    tagged = 0
    for para in untagged:
        para_id = para["id"]
        created_at = para["created_at"]

        # Find the raw_response session that produced this paragraph
        raw = conn.execute(
            "SELECT session_topic FROM raw_responses WHERE para_text_hash = ? LIMIT 1",
            (para["text_hash"],),
        ).fetchone()
        session_topic = raw["session_topic"] if raw else None

        # Look for gaps in applications within the window before this paragraph was created
        nearby_gaps = conn.execute(
            """SELECT g.id, g.requirement_text, a.id as app_id
               FROM application_gaps g
               JOIN applications a ON g.application_id = a.id
               WHERE a.applied_at <= ? AND a.applied_at >= datetime(?, '-{} days')""".format(days_window),
            (created_at, created_at),
        ).fetchall()

        matched_gap = None
        if session_topic and nearby_gaps:
            topic_words = set(re.findall(r"[a-z]{4,}", session_topic.lower()))
            best_overlap = 0
            for gap in nearby_gaps:
                gap_words = set(re.findall(r"[a-z]{4,}", gap["requirement_text"].lower()))
                overlap = len(topic_words & gap_words)
                if overlap >= 2 and overlap > best_overlap:
                    best_overlap = overlap
                    matched_gap = gap

        if matched_gap:
            source_type = "gap_driven"
            app_id = matched_gap["app_id"]
            gap_id = matched_gap["id"]
        else:
            source_type = "organic"
            app_id = None
            gap_id = None

        conn.execute(
            "INSERT OR IGNORE INTO paragraph_provenance "
            "(paragraph_id, source_type, application_id, gap_id) VALUES (?, ?, ?, ?)",
            (para_id, source_type, app_id, gap_id),
        )
        tagged += 1

    conn.commit()
    return tagged


# ---------------------------------------------------------------------------
# Cross-application analytics
# ---------------------------------------------------------------------------

def recurring_gaps(conn: sqlite3.Connection, min_count: int = 2) -> list[dict]:
    """Return gap requirement patterns that appear across multiple applications.

    Groups by requirement text similarity (exact match for now — fuzzy grouping
    is a future enhancement). Returns gaps ordered by frequency.
    """
    rows = conn.execute(
        """SELECT g.requirement_text, g.inferred_category,
                  COUNT(DISTINCT g.application_id) as app_count,
                  SUM(g.addressed_in_letter) as addressed_count,
                  GROUP_CONCAT(a.company, ', ') as companies
           FROM application_gaps g
           JOIN applications a ON g.application_id = a.id
           GROUP BY g.requirement_text
           HAVING app_count >= ?
           ORDER BY app_count DESC""",
        (min_count,),
    ).fetchall()
    return [dict(r) for r in rows]


def claim_usage_stats(conn: sqlite3.Connection) -> list[dict]:
    """Return claims ranked by usage across applications.

    Shows which claims are doing work vs. sitting in the DB unused.
    """
    rows = conn.execute(
        """SELECT c.text, c.argument_categories,
                  COUNT(DISTINCT acs.application_id) as times_scored,
                  SUM(acs.in_outline) as times_in_outline,
                  SUM(acs.in_letter) as times_in_letter,
                  AVG(acs.similarity_score) as avg_score
           FROM claims c
           LEFT JOIN application_claim_scores acs ON c.id = acs.claim_id
           GROUP BY c.id
           ORDER BY times_in_letter DESC, times_in_outline DESC""",
    ).fetchall()
    return [dict(r) for r in rows]


def category_coverage_trend(conn: sqlite3.Connection) -> list[dict]:
    """Return argument category coverage rates across applications over time."""
    rows = conn.execute(
        """SELECT acs.argument_category,
                  COUNT(DISTINCT acs.application_id) as apps_scored,
                  SUM(acs.in_outline) as times_in_outline,
                  SUM(acs.in_letter) as times_in_letter,
                  AVG(acs.similarity_score) as avg_score
           FROM application_claim_scores acs
           WHERE acs.argument_category IS NOT NULL
           GROUP BY acs.argument_category
           ORDER BY avg_score DESC""",
    ).fetchall()
    return [dict(r) for r in rows]


def application_summary(conn: sqlite3.Connection) -> list[dict]:
    """Return per-application summary for cross-application comparison."""
    rows = conn.execute(
        """SELECT a.id, a.company, a.role, a.applied_at, a.outcome,
                  COUNT(DISTINCT acs.claim_id) as claims_scored,
                  SUM(acs.in_outline) as claims_in_outline,
                  SUM(acs.in_letter) as claims_in_letter,
                  COUNT(DISTINCT g.id) as gap_count,
                  SUM(g.addressed_in_letter) as gaps_addressed
           FROM applications a
           LEFT JOIN application_claim_scores acs ON a.id = acs.application_id
           LEFT JOIN application_gaps g ON a.id = g.application_id
           GROUP BY a.id
           ORDER BY a.applied_at DESC""",
    ).fetchall()
    return [dict(r) for r in rows]


def jd_similarity_matrix(conn: sqlite3.Connection) -> list[dict]:
    """Return pairwise JD similarity for all applications with stored embeddings.

    Useful for understanding whether you're applying to similar roles
    or genuinely different ones.
    """
    apps = conn.execute(
        "SELECT id, company, role, jd_embedding FROM applications WHERE jd_embedding IS NOT NULL"
    ).fetchall()

    if len(apps) < 2:
        return []

    pairs = []
    app_list = list(apps)
    for i in range(len(app_list)):
        for j in range(i + 1, len(app_list)):
            a, b = app_list[i], app_list[j]
            try:
                vec_a = json.loads(a["jd_embedding"])
                vec_b = json.loads(b["jd_embedding"])
                score = _cosine(vec_a, vec_b)
                pairs.append({
                    "company_a": a["company"],
                    "role_a": a["role"],
                    "company_b": b["company"],
                    "role_b": b["role"],
                    "similarity": round(score, 3),
                })
            except Exception:
                pass

    pairs.sort(key=lambda x: -x["similarity"])
    return pairs
