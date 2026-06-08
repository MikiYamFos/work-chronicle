"""
Tests for LibraryGapResult and library_gap_analysis.
The analysis function is tested with a mock DB connection and mock provider
so no API calls or real files are needed.
"""
import json
import sqlite3
import pytest
from coverletter.align import LibraryGapResult, library_gap_analysis
from coverletter.provider import Provider


# ── LibraryGapResult ──────────────────────────────────────────────────────────

def test_no_db_flag_defaults_false():
    r = LibraryGapResult(covered=[], gaps=[])
    assert not r.no_db


def test_no_db_flag_set():
    r = LibraryGapResult(covered=[], gaps=[], no_db=True)
    assert r.no_db


def test_gap_requirements_property():
    r = LibraryGapResult(
        covered=[],
        gaps=[{"requirement": "Kafka", "build_prompt": "What did you build?"},
              {"requirement": "dbt", "build_prompt": "What models?"}],
    )
    assert r.gap_requirements == ["Kafka", "dbt"]


def test_gap_prompts_property():
    r = LibraryGapResult(
        covered=[],
        gaps=[{"requirement": "Kafka", "build_prompt": "What pipeline?"}],
    )
    assert r.gap_prompts == {"Kafka": "What pipeline?"}


def test_empty_gaps_properties():
    r = LibraryGapResult(covered=[], gaps=[])
    assert r.gap_requirements == []
    assert r.gap_prompts == {}


# ── library_gap_analysis with no conn → no_db ─────────────────────────────────

def test_returns_no_db_when_conn_is_none():
    result = library_gap_analysis("some JD", "key", "claude-sonnet-4-6", conn=None)
    assert result.no_db
    assert result.covered == []
    assert result.gaps == []


def test_returns_no_db_when_db_has_no_category_embeddings_table():
    """DB exists but was never synced — category_embeddings table is empty → no_db."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE category_embeddings (category_name TEXT, embedding BLOB, computed_at TEXT)")
    conn.execute("CREATE TABLE claims (id INTEGER, text TEXT, argument_categories TEXT, embedding BLOB)")
    conn.execute("CREATE TABLE jd_embedding_cache (jd_hash TEXT PRIMARY KEY, embedding BLOB, cached_at TEXT)")
    conn.commit()
    provider = _FixedEmbedProvider([1.0, 0.0])
    result = library_gap_analysis("JD text", "key", "claude-sonnet-4-6",
                                  conn=conn, embed_provider=provider)
    assert result.no_db


# ── library_gap_analysis with in-memory DB ────────────────────────────────────

def _make_db_with_categories():
    """In-memory SQLite with category_embeddings populated."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE category_embeddings (
            category_name TEXT PRIMARY KEY,
            embedding BLOB,
            computed_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE claims (
            id INTEGER PRIMARY KEY,
            text TEXT,
            argument_categories TEXT,
            embedding BLOB
        )
    """)
    conn.execute("""
        CREATE TABLE jd_embedding_cache (
            jd_hash TEXT PRIMARY KEY,
            embedding BLOB,
            cached_at TEXT
        )
    """)
    # Two categories with real (unit) embeddings
    vec_a = json.dumps([1.0, 0.0]).encode()
    vec_b = json.dumps([0.0, 1.0]).encode()
    conn.execute("INSERT INTO category_embeddings VALUES (?, ?, ?)", ("technical_ownership", vec_a, "now"))
    conn.execute("INSERT INTO category_embeddings VALUES (?, ?, ?)", ("motivation", vec_b, "now"))
    conn.commit()
    return conn


class _FixedEmbedProvider(Provider):
    """Returns a fixed vector for any text."""
    def __init__(self, vec):
        super().__init__("test", "")
        self._vec = vec

    def supports_embed(self): return True
    def supports_hybrid(self): return False
    def complete(self, *a, **kw): raise NotImplementedError
    def stream(self, *a, **kw): raise NotImplementedError
    def embed(self, texts, input_type="document"):
        return [list(self._vec)] * len(texts)


def test_gap_category_when_jd_misaligns(monkeypatch):
    """JD embedding [1,0] scores 0.0 against motivation [0,1] → gap (below threshold)."""
    conn = _make_db_with_categories()
    ep = _NoLLMProvider([1.0, 0.0])
    import coverletter.provider as _prov_mod
    monkeypatch.setattr(_prov_mod, "get_provider", lambda m, k: ep)
    result = library_gap_analysis("JD text", "key", "claude-sonnet-4-6",
                                  conn=conn, embed_provider=ep)
    gap_names = [g["requirement"] for g in result.gaps]
    assert "motivation" in gap_names


class _NoLLMProvider(_FixedEmbedProvider):
    """Aligns with technical_ownership, returns empty JSON for build prompts."""
    def complete(self, system, content, **kw):
        return "{}"


class _StubLLMProvider(_FixedEmbedProvider):
    """Returns a build prompt for the motivation gap."""
    def complete(self, system, content, **kw):
        return '{"motivation": "What drives you to work on data problems?"}'


def test_covered_category_when_jd_aligns(monkeypatch):
    """JD embedding [1,0] aligns with technical_ownership [1,0] → covered."""
    conn = _make_db_with_categories()
    ep = _NoLLMProvider([1.0, 0.0])
    import coverletter.provider as _prov_mod
    monkeypatch.setattr(_prov_mod, "get_provider", lambda m, k: ep)
    result = library_gap_analysis("JD text", "key", "claude-sonnet-4-6",
                                  conn=conn, embed_provider=ep)
    covered_names = [c["requirement"] for c in result.covered]
    assert "technical_ownership" in covered_names


def test_build_prompt_populated_from_llm(monkeypatch):
    """Gap categories get build_prompt text from the LLM call."""
    conn = _make_db_with_categories()
    ep = _StubLLMProvider([1.0, 0.0])
    import coverletter.provider as _prov_mod
    monkeypatch.setattr(_prov_mod, "get_provider", lambda m, k: ep)
    result = library_gap_analysis("JD text", "key", "claude-sonnet-4-6",
                                  conn=conn, embed_provider=ep)
    motivation_gap = next((g for g in result.gaps if g["requirement"] == "motivation"), None)
    assert motivation_gap is not None
    assert "drives you" in motivation_gap["build_prompt"]


def test_covered_best_score_is_numeric(monkeypatch):
    """best_score in covered items is a float, not a string or None."""
    conn = _make_db_with_categories()
    ep = _NoLLMProvider([1.0, 0.0])
    import coverletter.provider as _prov_mod
    monkeypatch.setattr(_prov_mod, "get_provider", lambda m, k: ep)
    result = library_gap_analysis("JD text", "key", "claude-sonnet-4-6",
                                  conn=conn, embed_provider=ep)
    for item in result.covered:
        assert isinstance(item["best_score"], float)
        assert 0.0 <= item["best_score"] <= 1.0
