"""
Tests for _category_aware_retrieval — the three-stage claim pipeline.
Uses in-memory fixtures. No API calls, no file I/O.

Stages under test:
  Stage 1 — category embedding scoring + relevant_categories filter
  Stage 2 — cosine scoring OR hybrid_scores() via embed_provider
  Stage 3 — reranker rescoring (Cohere or compatible)

Also tests edge cases: None jd_embedding, standalone categories always included,
relevance threshold filtering, per-category capping.
"""
import json
import sqlite3

import pytest

from coverletter.outline import _category_aware_retrieval, _STANDALONE_CATEGORIES
from coverletter.provider import Provider


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_conn(claims: list[dict]) -> sqlite3.Connection:
    """In-memory DB with claims table populated from dicts."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE claims (
            id INTEGER PRIMARY KEY,
            text TEXT,
            source_para_hash TEXT,
            argument_categories TEXT,
            embedding BLOB
        )
    """)
    conn.execute("""
        CREATE TABLE claim_contexts (
            id INTEGER PRIMARY KEY,
            claim_id INTEGER,
            context_type TEXT,
            context_name TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE support_items (
            id INTEGER PRIMARY KEY,
            claim_id INTEGER,
            text TEXT,
            is_anchor INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE conclusions (id INTEGER PRIMARY KEY, text TEXT)
    """)
    conn.execute("""
        CREATE TABLE conclusion_claims (conclusion_id INTEGER, claim_id INTEGER)
    """)
    for c in claims:
        cats = json.dumps(c.get("argument_categories", []))
        emb = json.dumps(c["embedding"]).encode() if c.get("embedding") else None
        conn.execute(
            "INSERT INTO claims (id, text, argument_categories, embedding) VALUES (?,?,?,?)",
            (c["id"], c["text"], cats, emb),
        )
    conn.commit()
    return conn


def _claim(id, text, categories, embedding=None):
    return {"id": id, "text": text, "argument_categories": categories,
            "embedding": embedding, "_similarity_score": 0.0}


# Dense unit vectors in 2D
VEC_A = [1.0, 0.0]   # aligns with technical_ownership
VEC_B = [0.0, 1.0]   # aligns with motivation (standalone)
VEC_JD = [1.0, 0.0]  # JD close to technical_ownership


CLAIMS = [
    _claim(1, "Built Kafka pipeline at scale.", ["technical_ownership"], VEC_A),
    _claim(2, "Driven by curiosity about data systems.", ["motivation"], VEC_B),
    _claim(3, "Owned dbt models across three environments.", ["technical_ownership"], VEC_A),
    _claim(4, "Designed schema for slowly-changing dimensions.", ["technical_depth"], VEC_A),
]

CAT_EMBEDDINGS = {
    "technical_ownership": VEC_A,
    "motivation": VEC_B,
    "technical_depth": VEC_A,
}


# ── None jd_embedding returns all claims ─────────────────────────────────────

def test_none_jd_embedding_returns_all_claims():
    conn = _make_conn(CLAIMS)
    result, cat_scores = _category_aware_retrieval(CLAIMS, conn, None, CAT_EMBEDDINGS)
    assert result == CLAIMS
    assert cat_scores == []


# ── Stage 1 — standalone categories always included ──────────────────────────

def test_standalone_categories_always_included():
    """motivation is standalone — included even if category score is low."""
    conn = _make_conn(CLAIMS)
    # JD aligns only with technical_ownership; motivation score will be 0
    result, _ = _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS, relevance_threshold=0.0
    )
    texts = [c["text"] for c in result]
    assert any("curiosity" in t for t in texts), "standalone motivation claim must be in result"


def test_standalone_claim_gets_score_1():
    conn = _make_conn(CLAIMS)
    result, _ = _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS, relevance_threshold=0.0
    )
    standalone = next(c for c in result if "curiosity" in c["text"])
    assert standalone["_similarity_score"] == 1.0


# ── Stage 1 — irrelevant categories filtered ─────────────────────────────────

def test_low_scoring_non_standalone_category_excluded():
    """technical_depth aligns with JD (score=1.0) — should be included.
    A category with near-zero alignment should be excluded."""
    # Add a claim in a far-away category
    claims_with_far = CLAIMS + [
        _claim(99, "This claim is in an irrelevant area.", ["stakeholder_fluency"], VEC_B),
    ]
    cat_with_far = dict(CAT_EMBEDDINGS, stakeholder_fluency=VEC_B)  # perpendicular to JD
    conn = _make_conn(claims_with_far)
    result, _ = _category_aware_retrieval(
        claims_with_far, conn, VEC_JD, cat_with_far,
        category_score_threshold=0.30, relevance_threshold=0.0,
    )
    # stakeholder_fluency score = cosine([1,0],[0,1]) = 0 < 0.30 → excluded
    texts = [c["text"] for c in result]
    assert not any("irrelevant area" in t for t in texts)


# ── Stage 2 — cosine scoring ─────────────────────────────────────────────────

def test_cosine_scoring_returns_relevant_claims():
    conn = _make_conn(CLAIMS)
    result, _ = _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS, relevance_threshold=0.5
    )
    # VEC_A claims align with JD; VEC_B claims (non-standalone) should not pass threshold
    evidence = [c for c in result if c["text"] != "Driven by curiosity about data systems."]
    assert all("_similarity_score" in c for c in evidence)


def test_per_category_cap_enforced():
    """claims_per_category=1 means only the top claim per category survives."""
    many_claims = [
        _claim(i, f"Claim {i} about technical_ownership.", ["technical_ownership"], VEC_A)
        for i in range(1, 6)
    ]
    conn = _make_conn(many_claims)
    result, _ = _category_aware_retrieval(
        many_claims, conn, VEC_JD, {"technical_ownership": VEC_A},
        relevance_threshold=0.0, claims_per_category=1,
    )
    evidence = [c for c in result if "technical_ownership" in c.get("argument_categories", [])]
    assert len(evidence) == 1


def test_flat_fallback_when_no_category_embeddings():
    """No category embeddings → treat all categories as relevant, score everything."""
    conn = _make_conn(CLAIMS)
    result, cat_scores = _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, {},  # empty category_embeddings
        relevance_threshold=0.0,
    )
    assert cat_scores == []
    # All claims should be returned (no category filtering)
    assert len(result) == len(CLAIMS)


# ── Stage 2 — hybrid path ────────────────────────────────────────────────────

class _HybridProvider(Provider):
    def __init__(self, scores):
        super().__init__("test", "")
        self._scores = scores
        self.calls = []
    def supports_hybrid(self): return True
    def supports_embed(self): return False
    def complete(self, *a, **kw): raise NotImplementedError
    def stream(self, *a, **kw): raise NotImplementedError
    def hybrid_scores(self, query, documents, alpha=0.5):
        self.calls.append((query, documents))
        return self._scores[:len(documents)]


def test_hybrid_path_invoked_when_provider_supports_it():
    conn = _make_conn(CLAIMS)
    provider = _HybridProvider([0.9, 0.8, 0.7, 0.6, 0.5])
    _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS,
        relevance_threshold=0.0, embed_provider=provider, jd_query="Kafka data pipeline",
    )
    assert len(provider.calls) == 1
    query, docs = provider.calls[0]
    assert "Kafka" in query


def test_hybrid_path_requires_jd_query():
    """If jd_query is empty, hybrid should NOT be called even if provider supports it."""
    conn = _make_conn(CLAIMS)
    provider = _HybridProvider([0.9, 0.8])
    _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS,
        relevance_threshold=0.0, embed_provider=provider, jd_query="",
    )
    assert provider.calls == []


def test_hybrid_path_scores_replace_cosine():
    """Hybrid scores determine which claims survive the relevance threshold."""
    # Claim 1 gets high hybrid score, claim 3 gets zero — threshold should filter claim 3
    conn = _make_conn(CLAIMS)
    scores_by_position = [0.9, 0.0, 0.9, 0.0]  # alternating high/low
    provider = _HybridProvider(scores_by_position)
    result, _ = _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS,
        relevance_threshold=0.5, embed_provider=provider, jd_query="Kafka pipeline",
    )
    # Only claims with hybrid score >= 0.5 should be in evidence (plus standalone)
    evidence = [c for c in result if c["_similarity_score"] != 1.0]
    assert all(c["_similarity_score"] >= 0.5 for c in evidence)


# ── Stage 3 — reranker ───────────────────────────────────────────────────────

class _MockReranker(Provider):
    def __init__(self, scores):
        super().__init__("test", "")
        self._scores = scores
        self.calls = []
    def supports_rerank(self): return True
    def complete(self, *a, **kw): raise NotImplementedError
    def stream(self, *a, **kw): raise NotImplementedError
    def rerank(self, query, documents):
        self.calls.append((query, documents))
        return self._scores[:len(documents)]


def test_reranker_invoked_with_jd_query():
    conn = _make_conn(CLAIMS)
    reranker = _MockReranker([0.9, 0.8, 0.7])
    _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS,
        relevance_threshold=0.0, reranker=reranker, jd_query="Kafka pipeline",
    )
    assert len(reranker.calls) == 1
    query, _ = reranker.calls[0]
    assert "Kafka" in query


def test_reranker_not_invoked_without_jd_query():
    conn = _make_conn(CLAIMS)
    reranker = _MockReranker([0.9, 0.8])
    _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS,
        relevance_threshold=0.0, reranker=reranker, jd_query="",
    )
    assert reranker.calls == []


def test_reranker_rescores_evidence_not_standalone():
    """Reranker should only touch evidence claims, not standalone ones."""
    conn = _make_conn(CLAIMS)
    # Give reranker low scores — if it touched standalone, that claim would drop
    reranker = _MockReranker([0.1, 0.1, 0.1])
    result, _ = _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS,
        relevance_threshold=0.0, reranker=reranker, jd_query="pipeline",
    )
    # Standalone (motivation) claim must still be present with score 1.0
    standalone = [c for c in result if "curiosity" in c["text"]]
    assert len(standalone) == 1
    assert standalone[0]["_similarity_score"] == 1.0


def test_reranker_failure_does_not_crash():
    """If reranker raises, result should still be returned (Stage 3 is try/except)."""
    class _BadReranker(Provider):
        def __init__(self): super().__init__("t", "")
        def supports_rerank(self): return True
        def complete(self, *a, **kw): raise NotImplementedError
        def stream(self, *a, **kw): raise NotImplementedError
        def rerank(self, q, docs): raise RuntimeError("reranker down")

    conn = _make_conn(CLAIMS)
    result, _ = _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS,
        relevance_threshold=0.0, reranker=_BadReranker(), jd_query="pipeline",
    )
    assert isinstance(result, list)
    assert len(result) > 0


def test_category_scores_returned():
    conn = _make_conn(CLAIMS)
    _, cat_scores = _category_aware_retrieval(
        CLAIMS, conn, VEC_JD, CAT_EMBEDDINGS, relevance_threshold=0.0
    )
    assert isinstance(cat_scores, list)
    assert all(isinstance(name, str) and isinstance(score, float) for name, score in cat_scores)
