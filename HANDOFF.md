---
name: handoff-2026-05-31
description: "Session handoff — provider abstraction, Cohere/BGE-M3, resume in build, gap-driven build mode, audit fixes"
metadata: 
  node_type: memory
  type: project
  updated: 2026-05-31
  branch: outline_interoperable
  originSessionId: 79977e5e-02ab-46f8-b3e4-acc16662800c
---

# Session Handoff — 2026-05-31

All work uncommitted. User does their own commits.

---

## What was built this session

### 1. Provider-native embeddings in Track 1 embed_prefilter (prompt.py)

`embed_prefilter` now accepts `provider=None`. Priority: hybrid_scores() (BGE-M3) → provider embed + cosine (Mistral/OpenAI/Cohere) → Voyage → BM25.

The pinning/scoring logic (perspective boost, strength boost, experience bucketing) is unchanged — it runs on top of whatever base scores come back.

All three cli.py call sites updated. Each creates `_embed_provider = get_embed_provider(cfg.embed_model) or _provider` and passes it through.

### 2. CohereProvider (provider.py)

- `embed()` → embed-v4.0 (maps `input_type` to `search_query`/`search_document`)
- `rerank()` → rerank-v3.5, returns scores in original document order
- `supports_embed() = True`, `supports_rerank() = True`
- config.py reads `COHERE_API_KEY`
- costs.py: command-r, command-r-plus, command-a, embed-v4.0, rerank-v3.5

### 3. BGEM3Provider (provider.py)

- Lazy-loads `BAAI/bge-m3` via FlagEmbedding (local, ~2GB, no API key)
- `embed()` → dense vectors (compatible with DB storage)
- `hybrid_scores(query, docs, alpha=0.5)` → encodes query+docs together, returns `alpha * dense_cosine + (1-alpha) * sparse_dot`
- `supports_embed() = True`, `supports_hybrid() = True`
- Activated via `EMBED_MODEL=bge-m3` in .env — independent of generation provider

### 4. Base Provider additions (provider.py)

- `rerank(query, documents) → list[float] | None` — default None
- `supports_rerank() → False`
- `hybrid_scores(query, documents, alpha) → list[float] | None` — default None
- `supports_hybrid() → False`
- `get_embed_provider(embed_model: str) → Provider | None` factory

### 5. Claim retrieval now three-stage (outline.py _category_aware_retrieval)

- Stage 1: category embedding scoring (unchanged)
- Stage 2: claim cosine scoring, OR hybrid_scores() if embed_provider.supports_hybrid()
- Stage 3 (new, optional): Cohere rerank-v3.5 over selected_evidence set
- `build_outline()` accepts `embed_model` param, creates embed_provider, passes reranker

### 6. embed_query moved to db.py (db.py)

`embed_query(text, voyage_api_key, provider)` is now a public function in `db.py`.
`outline._embed_query` is a thin wrapper that delegates to it.
`align.py` imports `embed_query` and `_cosine` from `db` directly — no more private outline imports.

### 7. Resume in build/QA flow (build.py, cli.py)

- `_build_initial_context` gains `resume_context` param — injected as "RESUME BLOCK — treat as established fact"
- `BUILD_SYSTEM` has matching instruction: resume tells you WHAT, ask about HOW/WHY/WHAT CHANGED
- `_qa_session` gains `resume_text` param, threads through to `_build_initial_context`
- `_gap_loop` gains `resume_text` param, threads through to `_qa_session`
- `coverletter build` gains `--resume` / `-R` flag, loads and passes resume_text
- Gap-fill sessions in generate flow pass `resume_text` through `_gap_loop`

### 8. Gap-driven build mode (cli.py, align.py)

`coverletter build --jd <file-or-text>`:
1. Opens DB, embeds JD
2. Scores JD against category_embeddings (pure cosine, no LLM)
3. Finds best-scoring claim per category (DB query + cosine, no LLM)
4. Covered = strong category score OR high claim score; gap = both weak
5. One small LLM call to generate build_prompt per gap category
6. Shows covered (green) with best claim snippet, gaps (red) with build prompt
7. User picks which gaps to address (1,3 or all)
8. Each gap runs _qa_session with gap_description + build_prompt seeded as topic
9. After each accepted paragraph: syncs to DB so subsequent gaps see updated coverage

**Requires**: `coverletter sync` + `coverletter extract` to have been run. Prints actionable message if DB missing or no category embeddings.

### 9. align.py LibraryGapResult

```python
@dataclass
class LibraryGapResult:
    covered: list[dict]   # [{"requirement": str, "best_score": float, "best_claim": str}]
    gaps: list[dict]      # [{"requirement": str, "build_prompt": str}]
    no_db: bool = False   # True when DB/embeddings unavailable
```

---

## Bugs found and fixed this session

**Critical** (would have crashed at runtime):
- `db_path(cfg.paragraphs_files[0])` — `db_path` takes `list[Path]`, single `Path` raises `TypeError`. Found in 3 places (two in `build --jd` flow, one in DB sync after gap accept). All fixed to `db_path(cfg.paragraphs_files)`.
- `library_gap_analysis` scoring block was dead code — indentation collapsed after removing redundant `if category_embeddings:`, leaving the entire scoring loop unreachable. Rewrote at correct indent.
- `coverletter claims` command — `db_path(ctx.obj["paragraphs"])` passed a string, not a list. Pre-existing. Fixed to load config properly.

**Correctness**:
- `_embed_query` and `_cosine` imported from private `outline.py` — moved `embed_query` to `db.py` as public function. `outline._embed_query` delegates to it. `align.py` imports from `db` directly.
- `library_gap_analysis` fallback returned empty silently — now sets `no_db=True`, cli.py prints "run sync + extract" before user wastes time.
- `category_embeddings` empty (no sync run) now returns `no_db=True` immediately.
- Cohere `stream()` field `event.delta.message.content.text` — wrapped with try/except for SDK field name variance.
- `OpenAIProvider.embed()` hardcoded `text-embedding-3-small` — now reads `OPENAI_EMBED_MODEL` env var (defaults to same, lets compat hosts specify their model).
- `CohereProvider.complete()` had no cost tracking — added `record()` call with `getattr` guards.
- `uv run` stripped from init next-steps output — restored. All `pip install` occurrences → `uv add` across all files (provider.py, cli.py, WORKFLOW.md, ROADMAP.md, README.md).

## Test suite (187 passing, 0.27s)

New test files added this session:

| File | What it guards |
|---|---|
| `tests/test_provider.py` | `parse_model`, `get_provider`, `get_embed_provider`, all capability flags, BGEM3 raises on complete/stream |
| `tests/test_db_path.py` | `db_path` requires `list[Path]` — bare Path or string raises; catches the recurring bug |
| `tests/test_build_context.py` | `_build_initial_context` injection order, resume block presence/absence, JD truncation, tool flag |
| `tests/test_embed_prefilter.py` | Pinning, hybrid path called correctly, dense path embed calls, BM25 fallback |
| `tests/test_library_gap.py` | `LibraryGapResult` fields/properties, `no_db` flag, in-memory DB scoring |
| `tests/test_claim_retrieval.py` | `_category_aware_retrieval` all three stages: category filter, cosine/hybrid Stage 2, reranker Stage 3, standalone always included, per-category cap, reranker crash safety |
| `tests/test_config_env.py` | `embed_model` env wiring, Cohere key routing, all new model aliases, `db_path` from real config |
| `tests/test_init_output.py` | `uv run` in output (fails if reverted), no pip anywhere, all provider keys in .env scaffold, `build --jd` mentioned, idempotency |

---

## Provider matrix (current)

| Provider | Generation | Caching | Embed (Track 1+2) | Hybrid | Rerank |
|---|---|---|---|---|---|
| Anthropic | ✓ | 90% cache_control | via Voyage | — | — |
| Mistral | ✓ | 90% cache_key | mistral-embed ✓ | — | — |
| OpenAI | ✓ | 50% auto | text-embedding-3-small ✓ | — | — |
| Cohere | ✓ | unknown | embed-v4.0 ✓ | — | rerank-v3.5 ✓ |
| BGE-M3 | embed-only | local | dense ✓ | hybrid ✓ | — |

---

## Key file map (grep before reading)

- `coverletter/provider.py` — all providers + factories. `get_provider(model, api_key)`, `get_embed_provider(embed_model)`.
- `coverletter/config.py` — reads ANTHROPIC/MISTRAL/OPENAI/COHERE_API_KEY, VOYAGE_API_KEY, EMBED_MODEL. Config.embed_model field.
- `coverletter/prompt.py:553` — `embed_prefilter`. Three-path: hybrid → dense → Voyage. Boosting logic unchanged.
- `coverletter/outline.py:225` — `_category_aware_retrieval`. Three-stage: category filter → claim scoring (hybrid or cosine) → Cohere rerank.
- `coverletter/outline.py:802` — `build_outline`. Accepts `embed_model` param.
- `coverletter/align.py:498` — `library_gap_analysis`. DB-first gap analysis.
- `coverletter/build.py:795` — `_build_initial_context`. Accepts `resume_context`.
- `coverletter/cli.py` — always grep first. ~3700 lines.
  - `_gap_loop` line ~226 — gap fill loop, takes `resume_text`
  - `_qa_session` line ~1065 — central Q&A hub, takes `resume_text`
  - `build_library` line ~1229 — `coverletter build` command
  - Three embed_prefilter call sites: lines ~678, ~856, ~2031

---

## What's next (priority order)

### Immediate — content work (unblocked now)

1. **Run `align_judge.py`** — judge prompt changed this session (source paragraph now used, category tags advisory, broad disposition claims shown as valid). Calibration unknown. Must verify before extraction run.
   ```
   uv run python coverletter/evals/align_judge.py
   ```

2. **Fix refined paragraphs** — content work in Streamlit diff tool. Blocks extraction.
   ```
   uv run streamlit run coverletter/library_diff.py
   ```

3. **Full extraction run** — once paragraphs clean.
   ```
   coverletter extract --dry-run   # review in label_evals.py
   coverletter extract             # write to DB
   ```

### After extraction — end-to-end validation (unit tests can't cover these)

4. **Test `coverletter build --jd`** — needs populated claims DB. Verify: covered/gap classification makes sense, build_prompts are specific not generic, DB sync after accept works, `no_db` message fires correctly when DB is empty.

5. **Test resume threading** — `uv run coverletter build --resume resume.pdf`. Verify coach references resume bullets without re-asking them.

6. **Test Cohere provider** — needs a real `COHERE_API_KEY`. Verify `complete()`, `stream()` (field names may need adjustment), and `embed()` against a real endpoint.

7. **Test BGE-M3** — `uv add FlagEmbedding` then `EMBED_MODEL=bge-m3 uv run coverletter generate`. First run downloads model (~2GB). Verify hybrid scoring returns sensible paragraph rankings.

### Remaining known gaps (not bugs, just not built)

- **Cohere `stream()` field names unverified** — wrapped defensively but untested against real SDK. ClientV2 streaming event structure may differ from what's implemented.
- **BGE-M3 hybrid_scores() untested end-to-end** — logic correct by inspection; FlagEmbedding not installed in this environment.
- **Ollama** — not yet implemented.

---

## Untracked files that need committing
- `coverletter/evals/` (gold standard, eval results)
- `extractions_review.json` / `.md`
- `library_rebuilt.md` / `library_salvaged.md` (empty scaffolds, low priority)
