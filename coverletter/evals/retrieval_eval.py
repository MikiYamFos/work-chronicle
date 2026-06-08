"""Retrieval evaluation — compares BM25 vs semantic search on paragraph retrieval.

Measures how well each method surfaces relevant paragraphs for a set of JD queries.
Uses MRR (Mean Reciprocal Rank) and Hit@k as metrics.

Usage:
    uv run python coverletter/evals/retrieval_eval.py

Requires:
    - library.md (or LIBRARY_FILE env var) with at least 5 paragraphs
    - VOYAGE_API_KEY for semantic results (BM25 runs without it)

Output:
    Prints a comparison table and writes results to coverletter/evals/retrieval_eval_results.json
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Sequence

# ---------------------------------------------------------------------------
# Test queries — each has a query string and a list of keyword signals that
# indicate a relevant paragraph. These are intentionally phrased differently
# from the paragraph content to stress-test semantic vs keyword matching.
# ---------------------------------------------------------------------------

TEST_QUERIES = [
    {
        "id": "pipeline_ownership",
        "query": "owns production data pipelines end-to-end, responsible for reliability",
        "signals": ["pipeline", "production", "owned", "built", "stable", "engineer"],
    },
    {
        "id": "stakeholder_communication",
        "query": "communicates complex technical findings to non-technical leadership",
        "signals": ["cfo", "cto", "ceo", "leadership", "finance", "reported", "communicated"],
    },
    {
        "id": "cloud_infrastructure",
        "query": "AWS infrastructure experience, IAM, Glue, cloud data platform",
        "signals": ["aws", "glue", "iam", "cloudformation", "terraform", "infrastructure"],
    },
    {
        "id": "data_quality",
        "query": "data quality validation, correctness checks, reconciliation",
        "signals": ["reconcil", "validat", "quality", "incorrect", "bug", "double"],
    },
    {
        "id": "solo_ownership",
        "query": "sole data engineer, operated independently without team support",
        "signals": ["sole", "only", "alone", "independently", "no dedicated", "without"],
    },
    {
        "id": "mission_driven",
        "query": "motivated by social impact, values-driven work, mission alignment",
        "signals": ["amnesty", "aclu", "unite here", "union", "rights", "mission", "workers"],
    },
    {
        "id": "spark_scale",
        "query": "Spark or PySpark at scale, large event data processing",
        "signals": ["spark", "pyspark", "billion", "scale", "events", "playback"],
    },
    {
        "id": "compliance_privacy",
        "query": "privacy compliance, GDPR, consent management, regulatory constraints",
        "signals": ["bbc", "compliance", "privacy", "consent", "regulatory", "gdpr"],
    },
]


# ---------------------------------------------------------------------------
# Retrieval helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    import re
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()


def bm25_retrieve(query: str, paragraphs: list, top_k: int = 5) -> list[tuple[float, object]]:
    """BM25 retrieval with angle tag boost."""
    from rank_bm25 import BM25Okapi

    corpus = [_tokenize(p.section + " " + p.role + " " + p.text) for p in paragraphs]
    bm25 = BM25Okapi(corpus)
    scores = list(bm25.get_scores(_tokenize(query)))

    query_words = set(_tokenize(query))
    boosted = []
    for i, p in enumerate(paragraphs):
        angle_words = set(_tokenize(p.meta.get("angle", "").replace("-", " ")))
        overlap = len(query_words & angle_words)
        boost = 1.0 + overlap * 1.5
        boosted.append((scores[i] * boost, p))

    boosted.sort(key=lambda x: -x[0])
    return boosted[:top_k]


def semantic_retrieve(
    query: str,
    paragraphs: list,
    voyage_api_key: str,
    top_k: int = 5,
) -> list[tuple[float, object]]:
    """Voyage semantic retrieval."""
    import voyageai
    from coverletter.prompt import _cosine

    texts = [p.text for p in paragraphs]
    client = voyageai.Client(api_key=voyage_api_key)
    doc_result = client.embed(texts, model="voyage-3-lite", input_type="document")
    query_result = client.embed([query], model="voyage-3-lite", input_type="query")
    doc_vecs = doc_result.embeddings
    query_vec = query_result.embeddings[0]

    scored = [(float(_cosine(doc_vecs[i], query_vec)), p) for i, p in enumerate(paragraphs)]
    scored.sort(key=lambda x: -x[0])
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Relevance judge — uses keyword signals as a lightweight proxy for relevance.
# For each query, a paragraph is "relevant" if it contains at least 2 signals.
# ---------------------------------------------------------------------------

def is_relevant(paragraph, signals: list[str]) -> bool:
    text = (paragraph.text + " " + paragraph.section + " " + paragraph.role).lower()
    hits = sum(1 for s in signals if s.lower() in text)
    return hits >= 2


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def reciprocal_rank(results: list[tuple[float, object]], signals: list[str]) -> float:
    for rank, (_, p) in enumerate(results, 1):
        if is_relevant(p, signals):
            return 1.0 / rank
    return 0.0


def hit_at_k(results: list[tuple[float, object]], signals: list[str], k: int = 3) -> bool:
    return any(is_relevant(p, signals) for _, p in results[:k])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_eval(library_path: Path, voyage_api_key: str, top_k: int = 5) -> dict:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from coverletter.parser import parse_paragraphs

    text = library_path.read_text(encoding="utf-8")
    paragraphs = parse_paragraphs(text)

    if not paragraphs:
        print(f"No paragraphs found in {library_path}")
        sys.exit(1)

    print(f"\nLoaded {len(paragraphs)} paragraphs from {library_path.name}")
    print(f"Running {len(TEST_QUERIES)} queries at top-{top_k}\n")

    bm25_rr: list[float] = []
    bm25_h3: list[bool] = []
    sem_rr: list[float] = []
    sem_h3: list[bool] = []
    rows: list[dict] = []

    for q in TEST_QUERIES:
        query_id = q["id"]
        query = q["query"]
        signals = q["signals"]

        # BM25
        bm25_results = bm25_retrieve(query, paragraphs, top_k)
        rr_bm25 = reciprocal_rank(bm25_results, signals)
        h3_bm25 = hit_at_k(bm25_results, signals, k=3)
        bm25_rr.append(rr_bm25)
        bm25_h3.append(h3_bm25)

        # Semantic
        rr_sem, h3_sem = 0.0, False
        if voyage_api_key:
            time.sleep(0.2)  # rate limit
            sem_results = semantic_retrieve(query, paragraphs, voyage_api_key, top_k)
            rr_sem = reciprocal_rank(sem_results, signals)
            h3_sem = hit_at_k(sem_results, signals, k=3)
        sem_rr.append(rr_sem)
        sem_h3.append(h3_sem)

        bm25_top = bm25_results[0][1] if bm25_results else None
        sem_top = sem_results[0][1] if (voyage_api_key and sem_results) else None

        rows.append({
            "query_id": query_id,
            "bm25_rr": round(rr_bm25, 3),
            "bm25_hit3": h3_bm25,
            "bm25_top": f"{bm25_top.role} / {bm25_top.section}" if bm25_top else "—",
            "sem_rr": round(rr_sem, 3),
            "sem_hit3": h3_sem,
            "sem_top": f"{sem_top.role} / {sem_top.section}" if sem_top else "—",
        })

    mrr_bm25 = sum(bm25_rr) / len(bm25_rr)
    mrr_sem = sum(sem_rr) / len(sem_rr)
    hit3_bm25 = sum(bm25_h3) / len(bm25_h3)
    hit3_sem = sum(sem_h3) / len(sem_h3)

    # Print table
    header = f"{'Query':<30} {'BM25 RR':>8} {'BM25 H@3':>9} {'Sem RR':>8} {'Sem H@3':>9}"
    print(header)
    print("-" * len(header))
    for r in rows:
        sem_rr_str = f"{r['sem_rr']:.3f}" if voyage_api_key else "  n/a"
        sem_h3_str = ("✓" if r["sem_hit3"] else "✗") if voyage_api_key else " n/a"
        print(
            f"{r['query_id']:<30} {r['bm25_rr']:>8.3f} {'✓' if r['bm25_hit3'] else '✗':>9} "
            f"{sem_rr_str:>8} {sem_h3_str:>9}"
        )
    print("-" * len(header))
    sem_mrr_str = f"{mrr_sem:.3f}" if voyage_api_key else "  n/a"
    sem_h3_str = f"{hit3_sem:.1%}" if voyage_api_key else "  n/a"
    print(f"{'MRR / Hit@3':<30} {mrr_bm25:>8.3f} {hit3_bm25:>8.1%} {sem_mrr_str:>8} {sem_h3_str:>9}")

    if voyage_api_key:
        winner = "Semantic" if mrr_sem > mrr_bm25 else "BM25"
        delta = abs(mrr_sem - mrr_bm25)
        print(f"\nWinner: {winner} (+{delta:.3f} MRR)")
    else:
        print("\nSet VOYAGE_API_KEY to run semantic comparison.")

    results = {
        "library": str(library_path),
        "paragraph_count": len(paragraphs),
        "top_k": top_k,
        "bm25": {"mrr": round(mrr_bm25, 4), "hit_at_3": round(hit3_bm25, 4)},
        "semantic": {"mrr": round(mrr_sem, 4), "hit_at_3": round(hit3_sem, 4)} if voyage_api_key else None,
        "rows": rows,
    }

    out = Path(__file__).parent / "retrieval_eval_results.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults written to {out.relative_to(Path.cwd())}")
    return results


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(override=True)

    library_file = Path(os.environ.get("LIBRARY_FILE", "library.md"))
    if not library_file.exists():
        # try rebuilt/refined as fallback
        for candidate in ["library_rebuilt.md", "library_refined.md"]:
            if Path(candidate).exists():
                library_file = Path(candidate)
                break

    if not library_file.exists():
        print(f"No library file found. Set LIBRARY_FILE or run from your working directory.")
        sys.exit(1)

    voyage_key = os.environ.get("VOYAGE_API_KEY", "")
    run_eval(library_file, voyage_key)
