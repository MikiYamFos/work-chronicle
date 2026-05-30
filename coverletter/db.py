"""SQLite-backed paragraph index.

Markdown files are the source of truth. This module provides:
  - sync_from_markdown()       — parse .md files → upsert paragraphs
  - compute_embeddings()       — batch Voyage embeddings for paragraphs
  - extract_and_store_sentences() — split paragraphs into indexed sentences
  - compute_sentence_embeddings() — batch Voyage embeddings for sentences
  - assign_angles_canonical()  — classify every paragraph against 14 canonical
                                  angle definitions using embedding similarity;
                                  stores multiple angles per paragraph in the
                                  junction table, no user input required

The sentence layer enables patchwork letter assembly: instead of dumping whole
paragraphs into the prompt, retrieval pulls the most relevant sentences across
the library so the model synthesizes from fine-grained evidence.
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

CREATE INDEX IF NOT EXISTS idx_para_hash       ON paragraphs(text_hash);
CREATE INDEX IF NOT EXISTS idx_para_source     ON paragraphs(source_file, active);
CREATE INDEX IF NOT EXISTS idx_para_type       ON paragraphs(type, active);
CREATE INDEX IF NOT EXISTS idx_para_angle      ON paragraphs(angle, active);
CREATE INDEX IF NOT EXISTS idx_para_angles_ang ON paragraph_angles(angle);
CREATE INDEX IF NOT EXISTS idx_sent_para       ON sentences(paragraph_id);
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


# ---------------------------------------------------------------------------
# DB lifecycle
# ---------------------------------------------------------------------------

def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


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
