# Retrieval Evaluation

This document describes how paragraph retrieval works in clio, how the approaches
were evaluated, and why the current default was chosen.

---

## What retrieval does here

When generating a letter or running interview prep, the system needs to select the
most relevant paragraphs from your library for a given job description. With a small
library (under `COVERLETTER_TOP_N`, default 100) every paragraph is passed to the
model directly. With a larger library, retrieval narrows the candidate set before
generation.

The same retrieval logic runs in three other places:

- **`clio build --jd`** — find which argument categories are covered vs missing
- **`clio interview`** — surface the most relevant library material per interview theme
- **`search_library` tool** — the build agent checks the library before asking questions

Retrieval quality directly determines letter quality. A weak retrieval that misses
your best paragraph means that paragraph never appears in the letter.

---

## The three retrieval tiers

The system tries methods in priority order, falling back when a key or dependency
is unavailable:

### Tier 1 — Semantic (Voyage AI or provider-native)

Embeds both the job description and each paragraph into a shared vector space.
Ranks paragraphs by cosine similarity to the JD embedding. Applies a small angle-tag
boost so tagged paragraphs (`angle=production-ownership`, etc.) surface higher when
the query vocabulary overlaps with their angle label.

**Requires**: `VOYAGE_API_KEY` in `.env`, or a provider with native embedding support
(Mistral, OpenAI, Cohere). Falls back to Tier 2 if neither is available.

**Strength**: catches semantic matches that share no vocabulary with the query.
Example: a JD asking for "observability and reliability" retrieves a paragraph about
"DynamoDB logging and pipeline execution visibility" even though none of those words
appear in the JD.

### Tier 2 — BM25 with angle-tag boost

TF-IDF variant (BM25Okapi) over tokenized paragraph text. Angle tags are appended to
the document before tokenization so tagged paragraphs score higher on matching queries.
Query words that overlap with angle vocabulary receive a 1.5x score multiplier.

**Requires**: `rank-bm25` (included in dependencies). Always available.

**Strength**: fast, interpretable, reliable on exact vocabulary overlap. Catches
clear keyword matches reliably.

**Weakness**: misses semantic matches. A JD about "data reliability engineering" scores
zero against a paragraph about "pipeline stability and monitoring" if the exact words
don't appear.

### Tier 3 — Keyword fallback

Pure word overlap between the query and paragraph text/section/role. No weighting,
no BM25 scoring. Last resort when `rank-bm25` is not installed.

---

## Evaluation methodology

### Metrics

**MRR (Mean Reciprocal Rank)** — for each query, the reciprocal of the rank of the
first relevant result. MRR=1.0 means the top result is always relevant.
MRR=0.5 means the first relevant result is on average at rank 2.

**Hit@3** — the fraction of queries where at least one relevant paragraph appears
in the top 3 results.

### Relevance labeling

Relevance is determined by keyword signals per query — each query has a list of
content signals (e.g. `["spark", "pyspark", "billion", "scale"]`) and a paragraph
is considered relevant if it contains at least 2 of them. This is a lightweight
proxy for human relevance judgment; it intentionally does not overlap with the query
vocabulary itself to avoid rewarding keyword matching.

### Test queries

Eight queries covering the argument categories most commonly required by senior
data engineering JDs:

| Query ID | What it targets |
|---|---|
| `pipeline_ownership` | End-to-end pipeline ownership and reliability |
| `stakeholder_communication` | Technical findings communicated to leadership |
| `cloud_infrastructure` | AWS/cloud platform experience |
| `data_quality` | Validation, reconciliation, correctness |
| `solo_ownership` | Independent operation without team support |
| `mission_driven` | Values alignment and mission-driven motivation |
| `spark_scale` | Spark/PySpark at billion-event scale |
| `compliance_privacy` | Privacy, consent, regulatory compliance |

Queries are intentionally phrased differently from paragraph content. "Motivated by
social impact, values-driven work" should retrieve the Amnesty International paragraph
without the word "Amnesty" appearing in the query.

---

## Running the evaluation

```bash
uv run python coverletter/evals/retrieval_eval.py
```

Requires a populated `library.md` (or `LIBRARY_FILE` env var pointing at your library).
Run from your working directory (where `.env` lives).

- **Without `VOYAGE_API_KEY`**: runs BM25 only, prints BM25 metrics
- **With `VOYAGE_API_KEY`**: runs both methods and prints a comparison table

Results are written to `coverletter/evals/retrieval_eval_results.json`.

Example output (with semantic enabled):

```
Loaded 13 paragraphs from library_rebuilt.md
Running 8 queries at top-5

Query                          BM25 RR  BM25 H@3   Sem RR  Sem H@3
-----------------------------------------------------------------------
pipeline_ownership               0.500        ✓    1.000        ✓
stakeholder_communication        0.333        ✓    1.000        ✓
cloud_infrastructure             1.000        ✓    1.000        ✓
data_quality                     0.500        ✓    1.000        ✓
solo_ownership                   0.500        ✓    0.500        ✓
mission_driven                   0.000        ✗    1.000        ✓
spark_scale                      1.000        ✓    1.000        ✓
compliance_privacy               0.333        ✓    1.000        ✓
-----------------------------------------------------------------------
MRR / Hit@3                      0.521    87.5%    0.938   100.0%

Winner: Semantic (+0.417 MRR)
```

The `mission_driven` query is the key differentiator — BM25 scores zero because
the query ("motivated by social impact") shares no vocabulary with the paragraph
("Amnesty International", "ACLU", "UNITE HERE"). Semantic search retrieves it
correctly because the underlying meaning is aligned.

---

## Why semantic is the default

Semantic search outperforms BM25 specifically on queries where meaning and vocabulary
diverge — which is exactly the case in cover letter generation. A JD asks for
"mission alignment" and your best paragraph talks about labor organizing. A JD asks
for "observability" and your paragraph talks about "DynamoDB logging." BM25 misses
these; semantic search does not.

BM25 remains available as a zero-cost fallback for users without an embedding key.
For users who want good retrieval, adding `VOYAGE_API_KEY` to `.env` is the single
highest-leverage configuration change.

---

## Extending the evaluation

To add your own test queries, add entries to `TEST_QUERIES` in
`coverletter/evals/retrieval_eval.py`:

```python
{
    "id": "your_query_id",
    "query": "phrased like a JD requirement — different words from your paragraphs",
    "signals": ["word1", "word2", "word3"],  # at least 2 must appear in a relevant paragraph
},
```

To run a formal comparison on a specific library file:

```bash
LIBRARY_FILE=/path/to/library.md uv run python coverletter/evals/retrieval_eval.py
```
