"""Tests for resume extraction — hash detection, source tagging, DB insertion."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from coverletter.db import open_db


@pytest.fixture
def mem_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    from coverletter.db import _SCHEMA
    conn.executescript(_SCHEMA)
    from coverletter.db import _run_migrations
    _run_migrations(conn)
    conn.commit()
    yield conn
    conn.close()


def test_needs_extraction_empty_db(mem_db):
    """No extraction record → needs extraction."""
    from coverletter.resume_extract import needs_extraction
    assert needs_extraction(mem_db, "abc123") is True


def test_needs_extraction_matching_hash(mem_db):
    """Same hash as last extraction → no extraction needed."""
    from coverletter.resume_extract import needs_extraction
    mem_db.execute(
        "INSERT INTO resume_extractions (file_hash, version, claim_count) VALUES (?, ?, ?)",
        ("abc123", 1, 5),
    )
    mem_db.commit()
    assert needs_extraction(mem_db, "abc123") is False


def test_needs_extraction_different_hash(mem_db):
    """Different hash → needs re-extraction."""
    from coverletter.resume_extract import needs_extraction
    mem_db.execute(
        "INSERT INTO resume_extractions (file_hash, version, claim_count) VALUES (?, ?, ?)",
        ("abc123", 1, 5),
    )
    mem_db.commit()
    assert needs_extraction(mem_db, "def456") is True


def test_insert_resume_claims_source_tag(mem_db):
    """Inserted resume claims have source='resume'."""
    from coverletter.resume_extract import _insert_resume_claims

    claims = [
        {"text": "At Acme, owned the data pipeline end-to-end", "company": "Acme", "role": "Data Engineer"},
        {"text": "Reduced query latency by 40% through schema redesign", "company": "Acme", "role": "Data Engineer"},
    ]
    count = _insert_resume_claims(mem_db, claims, voyage_api_key="")
    assert count == 2

    rows = mem_db.execute("SELECT source FROM claims").fetchall()
    assert all(r["source"] == "resume" for r in rows)


def test_insert_resume_claims_no_source_para_hash(mem_db):
    """Resume claims have NULL source_para_hash — not linked to a library paragraph."""
    from coverletter.resume_extract import _insert_resume_claims

    claims = [{"text": "Built streaming pipeline at BritBox", "company": "BritBox", "role": "DE"}]
    _insert_resume_claims(mem_db, claims, voyage_api_key="")

    row = mem_db.execute("SELECT source_para_hash FROM claims LIMIT 1").fetchone()
    assert row["source_para_hash"] is None


def test_insert_resume_claims_context_inserted(mem_db):
    """Company context is inserted into claim_contexts for resume claims."""
    from coverletter.resume_extract import _insert_resume_claims

    claims = [{"text": "Owned the ingestion pipeline", "company": "Acme Corp", "role": "DE"}]
    _insert_resume_claims(mem_db, claims, voyage_api_key="")

    claim_id = mem_db.execute("SELECT id FROM claims LIMIT 1").fetchone()["id"]
    ctx = mem_db.execute(
        "SELECT context_type, context_name FROM claim_contexts WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()
    assert ctx["context_type"] == "employer"
    assert ctx["context_name"] == "Acme Corp"


def test_delete_old_resume_claims(mem_db):
    """_delete_old_resume_claims removes only source='resume' claims."""
    from coverletter.resume_extract import _delete_old_resume_claims

    mem_db.execute(
        "INSERT INTO claims (text, source) VALUES (?, ?)", ("library claim", "library")
    )
    mem_db.execute(
        "INSERT INTO claims (text, source) VALUES (?, ?)", ("resume claim", "resume")
    )
    mem_db.commit()

    _delete_old_resume_claims(mem_db)

    rows = mem_db.execute("SELECT source FROM claims").fetchall()
    assert len(rows) == 1
    assert rows[0]["source"] == "library"


def test_record_extraction_increments_version(mem_db):
    """Each call to _record_extraction increments the version number."""
    from coverletter.resume_extract import _record_extraction

    v1 = _record_extraction(mem_db, "hash1", 3)
    v2 = _record_extraction(mem_db, "hash2", 5)
    assert v1 == 1
    assert v2 == 2


def test_library_claims_unaffected_by_resume_insert(mem_db):
    """Inserting resume claims does not touch existing library claims."""
    from coverletter.resume_extract import _insert_resume_claims

    mem_db.execute(
        "INSERT INTO claims (text, source) VALUES (?, ?)",
        ("This is a library claim", "library"),
    )
    mem_db.commit()

    _insert_resume_claims(
        mem_db,
        [{"text": "Resume claim", "company": "Co", "role": "DE"}],
        voyage_api_key="",
    )

    library_rows = mem_db.execute(
        "SELECT text FROM claims WHERE source = 'library'"
    ).fetchall()
    assert len(library_rows) == 1
    assert library_rows[0]["text"] == "This is a library claim"
