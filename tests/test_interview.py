"""Tests for the interview prep agent tools."""
from __future__ import annotations

import sqlite3

import pytest

from coverletter.db import open_db, _SCHEMA, _run_migrations


@pytest.fixture
def mem_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    _run_migrations(conn)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def db_with_claims(mem_db, tmp_path):
    """DB with one library claim and one resume claim."""
    mem_db.execute(
        "INSERT INTO claims (text, source, argument_categories) VALUES (?, ?, ?)",
        ("At Acme, owned the VideoViewEvents pipeline end-to-end", "library", '["ownership"]'),
    )
    mem_db.execute(
        "INSERT INTO claims (text, source, argument_categories) VALUES (?, ?, ?)",
        ("Reduced pipeline latency by 40% through schema redesign at BritBox", "resume", '["technical-depth"]'),
    )
    mem_db.commit()

    db_file = tmp_path / "test.db"
    import shutil
    # write to file so _tool_get_claims can open it
    file_conn = sqlite3.connect(str(db_file))
    file_conn.row_factory = sqlite3.Row
    file_conn.executescript(_SCHEMA)
    _run_migrations(file_conn)
    file_conn.execute(
        "INSERT INTO claims (text, source, argument_categories) VALUES (?, ?, ?)",
        ("At Acme, owned the VideoViewEvents pipeline end-to-end", "library", '["ownership"]'),
    )
    file_conn.execute(
        "INSERT INTO claims (text, source, argument_categories) VALUES (?, ?, ?)",
        ("Reduced pipeline latency by 40% through schema redesign at BritBox", "resume", '["technical-depth"]'),
    )
    file_conn.commit()
    file_conn.close()
    return db_file


def test_get_claims_finds_library_claim(db_with_claims):
    from coverletter.interview import _tool_get_claims
    result = _tool_get_claims("pipeline ownership", db_with_claims)
    assert "[LIBRARY]" in result
    assert "VideoViewEvents" in result


def test_get_claims_finds_resume_claim(db_with_claims):
    from coverletter.interview import _tool_get_claims
    result = _tool_get_claims("schema latency", db_with_claims)
    assert "[RESUME]" in result
    assert "BritBox" in result


def test_get_claims_no_db():
    from coverletter.interview import _tool_get_claims
    result = _tool_get_claims("anything", None)
    assert "not available" in result.lower()


def test_get_claims_missing_db(tmp_path):
    from coverletter.interview import _tool_get_claims
    result = _tool_get_claims("anything", tmp_path / "nonexistent.db")
    assert "not available" in result.lower()


def test_get_claims_short_topic(db_with_claims):
    from coverletter.interview import _tool_get_claims
    result = _tool_get_claims("a", db_with_claims)
    assert "too short" in result.lower()


def test_get_experience_facts_no_experiences():
    from coverletter.interview import _tool_get_experience_facts
    result = _tool_get_experience_facts("Acme", [], [])
    assert "no experience register" in result.lower()


def test_get_experience_facts_no_match():
    from coverletter.experiences import Experience
    from coverletter.interview import _tool_get_experience_facts
    exp = Experience(name="BritBox / Streaming Analytics", company="BritBox")
    result = _tool_get_experience_facts("CompanyThatDoesNotExist", [exp], [])
    assert "No experience matching" in result
    assert "BritBox" in result


def test_get_experience_facts_match():
    from coverletter.experiences import Experience
    from coverletter.interview import _tool_get_experience_facts
    exp = Experience(
        name="BritBox / Streaming Analytics",
        company="BritBox",
        years="2023-present",
        angles=["ownership", "technical-depth"],
        raw_notes="Built VideoViewEvents pipeline. 1B+ events/day.",
        qa_targets=["What downstream decisions depended on this data?"],
    )
    result = _tool_get_experience_facts("BritBox streaming", [exp], [])
    assert "BritBox" in result
    assert "ownership" in result


def test_tool_source_labels_distinct(db_with_claims):
    """Library and resume claims are tagged differently."""
    from coverletter.interview import _tool_get_claims
    result = _tool_get_claims("pipeline", db_with_claims)
    assert "[LIBRARY]" in result or "[RESUME]" in result
