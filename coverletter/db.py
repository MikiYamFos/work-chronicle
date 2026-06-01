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
        "A broad narrative about professional identity across domains — who I am as an engineer "
        "and what drives my work, connecting different industries and roles into a coherent story "
        "about what I consistently bring and what I find most meaningful."
    ),
    "autonomy": (
        "Working solo or far beyond my title in under-resourced environments with high expectations "
        "and minimal direction — being the only person responsible for a job function, operating "
        "through ambiguity without waiting for someone to define the path."
    ),
    "ownership": (
        "End-to-end ownership of a specific system, pipeline, or product — I designed it, built it, "
        "maintained it, and was accountable for its correctness and reliability in production."
    ),
    "business-impact": (
        "Concrete, measurable outcomes for the business — subscriber numbers the CEO reads, "
        "content decisions driven by viewership data, campaign results, revenue metrics. "
        "What the work produced that the organization actually needed and acted on."
    ),
    "system-design": (
        "Architectural decisions that shaped how a system works — grain choices, schema design, "
        "pipeline structure, partitioning strategy, validation frameworks, session-boundary logic. "
        "Making the technical calls that determined how data flowed and how the system held together."
    ),
    "requirements-translation": (
        "Working out what was actually needed before building anything — gathering requirements from "
        "non-technical stakeholders, translating fuzzy asks into data models, doing the specification "
        "work that the engineering depended on, interviewing people who had been doing their jobs "
        "for decades and understanding their processes well enough to translate them into data structures."
    ),
    "compliance": (
        "Handling legally sensitive or regulated data — union membership, health fund, dues records, "
        "PII, HIPAA, infosec vetting, data retention decisions, role-based access control, governance "
        "frameworks. Getting it wrong has legal or organizational consequences, not just technical ones."
    ),
    "technical-depth": (
        "Deep mastery of a specific tool or technology — Spark, Redshift, dbt, Airflow, BigQuery, "
        "Prefect, Elasticsearch, Snowflake, PySpark, Glue. Not just using the tool but understanding "
        "its tradeoffs, failure modes, and how to optimize it under real production conditions at scale."
    ),
    "precision": (
        "Exactness and accountability around numbers — data that has to be right, not approximately "
        "right. The CFO reads these numbers. The grievance depends on this record. The campaign "
        "outcome turns on this count. The engineering work serves that precision requirement directly."
    ),
    "communication": (
        "Communicating complex technical things clearly across varied audiences — non-technical "
        "stakeholders, organizing staff, leadership, users, collaborators. Training people. "
        "Writing documentation that reflects how work actually moves. Proactively surfacing "
        "constraints and failure modes before anyone asked."
    ),
    "leadership": (
        "Directing projects, teams, or technical work — product ownership, sprint planning, "
        "cutting tickets, setting priorities, running design reviews, making architectural calls "
        "with authority. Organizing how the work gets done and keeping people oriented to it."
    ),
    "strategic-vision": (
        "Personal projects built from a clear point of view about a problem worth solving — "
        "Personal tools and applications built from a clear point of view about a problem "
        "worth solving. The design rationale, the technical architecture, and the larger purpose."
    ),
    "resilience": (
        "Staying with hard problems under pressure — rebuilding logic overnight, working until "
        "midnight to hit a deadline, not putting something down until it works, absorbing "
        "failures and getting the system back online. Reliability when the stakes are high."
    ),
    "problem-solving": (
        "Approaching undefined or broken situations analytically — diagnosing root causes, "
        "working backwards from what someone needs to understand, figuring out what the problem "
        "actually is before trying to solve it. Thriving when the path is not obvious."
    ),
    "problem-definition": (
        "Identifying what the actual problem was before anyone else had framed it correctly — "
        "recognizing that the stated requirement was a symptom, not the root cause, and doing "
        "the upstream work to redefine the question itself. I figured out what we were solving "
        "before we built anything, and that reframing changed what got built."
    ),
    "trust": (
        "Being the person whose numbers had to be right — not approximately right, not "
        "directionally correct, but exact and defensible. The output fed executive decisions, "
        "campaign results, or public-facing products, and the accountability for its accuracy "
        "was mine personally, not shared or buffered. The number had to be right and I made "
        "sure it was."
    ),
    "recovery": (
        "Stepping into something already broken, wrong, or on fire and making it right — "
        "diagnosing a data failure in production, rebuilding a corrupted migration, correcting "
        "a reporting error before it became a crisis, staying with the problem until the system "
        "was back to a state I would stand behind. Includes understanding why it broke and "
        "building the safeguards that prevented recurrence."
    ),
    "scope-expansion": (
        "Doing significantly more than my title or role formally required — owning systems, "
        "functions, or decisions that belonged above my level, filling gaps nobody else was "
        "filling, covering scope that was not in my job description but needed to happen and "
        "I made it happen. I did the job of a more senior person without the title or support."
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

-- Precomputed category description embeddings — stable, recomputed only when categories change
CREATE TABLE IF NOT EXISTS category_embeddings (
    category_name   TEXT PRIMARY KEY,
    embedding       BLOB NOT NULL,
    computed_at     TEXT DEFAULT (datetime('now'))
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


# ---------------------------------------------------------------------------
# DB lifecycle
# ---------------------------------------------------------------------------

_CATEGORIES_PATH = Path(__file__).parent / "evals" / "argument_categories.json"


def load_argument_categories() -> list[dict]:
    """Load argument categories from the data file.

    Returns list of category dicts with keys: name, description, anchor_signals.
    Adding a new category to argument_categories.json is all that's needed —
    both the extraction and judge prompts read from this at runtime.
    """
    if not _CATEGORIES_PATH.exists():
        return []
    return json.loads(_CATEGORIES_PATH.read_text(encoding="utf-8")).get("categories", [])


_MIGRATIONS = [
    # Add argument_categories to claims — comma-separated list of category names.
    # NULL on existing rows; populated on next extraction run.
    "ALTER TABLE claims ADD COLUMN argument_categories TEXT",
    # Add is_anchor to support_items — 1 = load-bearing language that must reach generation.
    # 0 on existing rows.
    "ALTER TABLE support_items ADD COLUMN is_anchor INTEGER DEFAULT 0",
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
    primary_threshold: float = 0.45,
    secondary_threshold: float = 0.40,
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

    # Track which paragraphs have human-labeled primary angles (don't override)
    human_primaries: set[int] = {
        row[0]
        for row in conn.execute(
            "SELECT paragraph_id FROM paragraph_angles WHERE is_primary=1 AND angle_auto=0"
        )
    }

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

        # Assign primary angle if no human label exists
        if para_id not in human_primaries:
            conn.execute(
                """INSERT INTO paragraph_angles (paragraph_id, angle, is_primary, confidence, angle_auto)
                   VALUES (?, ?, 1, ?, 1)
                   ON CONFLICT(paragraph_id, angle) DO UPDATE SET
                       is_primary=1, confidence=excluded.confidence, angle_auto=1""",
                (para_id, best_angle, best_score),
            )
            # Update denormalized column on paragraphs for quick lookup
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
) -> list[dict]:
    """Return angle-organized evidence for letter synthesis.

    Scores canonical angles against the JD to find the top argument categories
    the role needs, then retrieves the most JD-relevant sentences from paragraphs
    tagged with each angle — with a sentence of context on each side for grounding.

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
        zip(angle_names, desc_result.embeddings),
        key=lambda x: _cosine(jd_vec, x[1]),
        reverse=True,
    )
    top_angle_names = [name for name, _ in angle_scores[:top_angles]]

    result = []
    for angle in top_angle_names:
        # Fetch all sentences from paragraphs tagged with this angle
        rows = conn.execute(
            """SELECT s.id, s.text, s.position, s.paragraph_id,
                      p.role, p.section, se.vector
               FROM sentences s
               JOIN sentence_embeddings se ON s.id = se.sentence_id
               JOIN paragraphs p ON s.paragraph_id = p.id
               JOIN paragraph_angles pa ON p.id = pa.paragraph_id
               WHERE pa.angle = ? AND p.active = 1""",
            (angle,),
        ).fetchall()

        if not rows:
            continue

        # Score each sentence against the JD and sort best first
        scored = sorted(
            rows,
            key=lambda r: _cosine(jd_vec, json.loads(r["vector"])),
            reverse=True,
        )

        # Take top sentences_per_angle sentences — at most one per source paragraph
        # to force diversity of evidence across different experiences
        sentences = []
        seen_paragraphs: set[int] = set()
        for row in scored:
            if len(sentences) >= sentences_per_angle:
                break
            if row["paragraph_id"] in seen_paragraphs:
                continue
            seen_paragraphs.add(row["paragraph_id"])

            # Get one sentence of context on each side (by stored position)
            ctx = {
                r["position"]: r["text"]
                for r in conn.execute(
                    """SELECT position, text FROM sentences
                       WHERE paragraph_id = ? AND position BETWEEN ? AND ?
                       ORDER BY position""",
                    (row["paragraph_id"], row["position"] - 1, row["position"] + 1),
                )
            }
            sentences.append({
                "text": row["text"],
                "context_before": ctx.get(row["position"] - 1, ""),
                "context_after": ctx.get(row["position"] + 1, ""),
                "role": row["role"],
                "section": row["section"],
            })

        if sentences:
            result.append({"angle": angle, "sentences": sentences})

    return result


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

    existing = {
        row["category_name"]: row["embedding"]
        for row in conn.execute("SELECT category_name, embedding FROM category_embeddings").fetchall()
    }

    to_compute = [c for c in categories if c["name"] not in existing]
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
            "INSERT OR REPLACE INTO category_embeddings (category_name, embedding, computed_at) "
            "VALUES (?, ?, datetime('now'))",
            (cat["name"], blob),
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
