# clio — Workflow Reference

This document describes what the system does and how to use it. It covers what works,
what is partial, and what is not built. It does not describe aspirations as if implemented.

Run `clio help` for a quick command reference organized by workflow.

---

## Library files — what lives where

| File | Role |
|------|------|
| `library.md` | Your raw paragraphs. Write here first. Never rewritten by the tool. |
| `library_rebuilt.md` | Paragraphs built through the correct workflow: raw → coaching → your edits → approved. |
| `library_salvaged.md` | Paragraphs recovered from damaged material via the diff tool. Same status as `library_rebuilt.md` once approved. |
| `library.db` | SQLite database. Populated by `clio sync`. Holds paragraphs, claims, evidence, embeddings. |
| `candidate_profile.toml` | Your goals, working style, values, seniority signals. |

**The write path going forward:**
Raw text → `library.md` → diff tool (draft + coaching + your edits) → `library_rebuilt.md` → `clio sync` → `clio extract` → DB

### Triage files — cleanup work only, not the ongoing path

| File | What it is |
|------|------------|
| `library_refined.md` | Historically Claude-damaged refinements. Being corrected via the diff tool. Input to the diff tool, not output. Retires once fully processed. |
| `story_notes.md` | Raw conversation material not yet turned into paragraphs. The diff tool surfaces relevant sections when working through related paragraphs. |

---

## Building your library

This is ongoing work, not a one-time setup. Every time you have new material — a project
that just shipped, a decision you made, something you want to be able to say — you come
back here.

### `clio init`

First-time setup only. Creates `.env` and empty library files. Run once.

### `clio profile`

Captures your goals, values, working style, and seniority signals into
`candidate_profile.toml`. Used in alignment reporting, thesis generation, and blurb
generation. Profiles are versioned — re-running archives the previous one.

Profile sections: `goals`, `values`, `working_style`, `avoid`, `seniority_signals`.

### `clio jd`

Manage saved job descriptions. JDs are saved automatically when you paste one during
`generate` or `blurb`. They are saved after cleaning — boilerplate is stripped before
storage so the file matches what gets embedded. JD embeddings and company values are
cached in the DB so the same JD is never re-embedded across multiple runs.

```bash
clio jd list                  # show saved JDs with date, size, preview
clio jd rename <old> <new>    # rename a saved JD
clio jd replace <name>        # paste new JD from clipboard; clears DB cache
```

`jd replace` logs the change to the `jd_versions` table with a hash and change summary,
so you can track how a JD evolved and whether your coverage improved across versions.

### `clio build`

The core library-building tool. Runs a focused Q&A session that draws out specific details
and drafts a paragraph. Two modes:

**Manual mode** (default): prompts for a topic — a project, experience, or angle you want
to capture.

**Gap-driven mode** (`--jd`): takes a job description and uses the claims DB to identify
which argument categories are covered and which are not. Shows covered categories with the
best-matching claim, shows gaps with a concrete starting question for each, then lets you
pick which gaps to address.

```bash
clio build                          # manual — prompts for topic
clio build --jd /path/to/jd.txt    # gap-driven — analyzes library first
```

`--jd` gap analysis requires `clio sync` and `clio extract` to have been run first.

Pass `--resume` to make the coach aware of your resume. Resume bullets are injected as
established fact — the coach does not re-ask what the resume states; it asks about
constraints, consequences, and decisions not captured there.

```bash
clio build --resume ~/resume.pdf --jd jd.txt
```

**How the Q&A session works:**

The session opens with a static prompt — no model call, no cost. After your response,
two free checks run before spending any tokens:

1. **Metadata check** — if you described a specific project but employment context is
   unclear (personal vs employer, which company), a boilerplate question fires at zero cost.

2. **Model follow-up** — one question per turn. The question type matches the gap:
   competence gaps ask what was built; production gaps ask about constraints and ownership;
   impact gaps ask what became possible.

The Q&A agent uses `search_library` to check what's already documented before asking —
it will not re-ask about things already written.

**Entering long answers**: press Enter for new lines, Enter twice to submit.

**At any point**: type `draft` to force a draft. Type `done` to exit without saving.

### `clio reflect`

Captures perspective material — through-lines, pivots, reframes, and synthesis paragraphs.
These are not evidence paragraphs — they are your voice connecting your arc.

Perspective paragraphs are pinned during prefilter (never filtered out by relevance
scoring) and labeled `[NARRATIVE FRAME]` in the generation context.

### `clio seed`

For bootstrapping from existing material — a resume, LinkedIn export, old cover letters.
Reads the file and extracts initial paragraphs via light Q&A.

### `clio sync`

Reads all configured `.md` files and upserts paragraphs into the SQLite DB. Run this any
time you edit the markdown files directly or add new paragraphs.

### Library diff tool (Streamlit)

```
uv run streamlit run coverletter/library_diff.py
```

For correcting `library_refined.md` paragraphs that were damaged by Claude rewriting.
Shows three sources side by side — raw, damaged, and story notes.

---

## Resume extraction

Your resume is automatically indexed into the claims DB the first time any command that
uses it runs. This happens silently — one line prints when indexing occurs:

```
  Indexing resume... 24 claims indexed (v1)
```

Resume claims are stored with `source='resume'` alongside library claims
(`source='library'`). This distinction matters in two places:

- **Interview prep** — `[RESUME]` means it's already on paper; `[LIBRARY]` means it
  needs to come out verbally; `[GAP]` means you have no strong material.
- **Gap analysis** — the tool can distinguish what the interviewer has already read vs.
  what you need to surface in conversation.

### `clio resume-extract`

Force a fresh extraction — use after a major resume overhaul or to revert to a
re-extracted state.

```bash
clio resume-extract          # shows last extraction info, prompts to confirm
clio resume-extract --force  # re-extracts without prompting
```

Version history is preserved in `resume_extractions` table. Each extraction gets a version
number and timestamp.

---

## Extracting claims

Claims are extracted from your library paragraphs and stored in the DB. This powers the
argument-driven generation flow and interview prep. You do not need this before generating
with the classic flow, but you need it before `clio outline` and `clio interview`.

### `clio extract --dry-run`

Extracts claims from all pending paragraphs. For each paragraph, pulls:
- **Claims** — atomic assertions: ownership/decision, approach/method, disposition/character, motivation, personal project
- **Support items** — evidence that makes claims believable
- **Sub-details** — technical specifics, preserved near-verbatim
- **Conclusions** — insights that emerge from the claims

In `--dry-run` mode, nothing writes to the DB. Results go to `extractions_review.json`.

### `clio extract` (without `--dry-run`)

Same extraction and judging; passing claims insert directly into the DB. Requires a gold
standard with at least 5 approved and 5 rejected examples before it will run.

### Claim review app (Streamlit)

```
uv run streamlit run coverletter/label_evals.py
```

Review extracted claims after a dry-run. Approve inserts to DB immediately. Reject with a
failure category. Gold standard checkbox marks a claim as a reference example for the judge.

Session position saves on every action — reopen and it picks up where you left off.

### `clio claims`

Zero-cost view of claim coverage across the library. Shows claim count, anchor count, and
argument categories per paragraph.

### Judge calibration

```
uv run python coverletter/evals/align_judge.py
```

Checks judge accuracy against your gold standard. Reports accuracy, precision, and recall.
If alignment is below target, offers to draft a targeted patch to `_JUDGE_SYSTEM`.

**Alignment targets**: recall ≥ 89%, accuracy ≥ 80%.

```
uv run python coverletter/evals/run_evals.py
```

Measures overall pipeline quality as the percentage of claims the judge approves. Use this
to compare the effect of prompt changes across runs.

---

## Job description processing

Every JD is cleaned before use — `clean_jd()` strips EEO, disability disclosure, and
legal boilerplate. Company values and mission content are explicitly not stripped.

JD embeddings are cached by content hash. Once embedded, subsequent runs on the same JD
return the cached vector immediately.

When a JD is replaced via `clio jd replace`, the change is logged to `jd_versions` with
the old and new hash and a change summary. This lets you track coverage improvement over
time as a JD evolves.

---

## Generating letters

Two paths. Use the argument-driven path when you have a populated claim library.
Use the classic path for speed, or when the claim library is thin.

### Argument-driven path

#### Step 1 — `clio outline`

```
clio outline jd.txt --company "Acme Corp"
```

Generates a thesis, retrieves claims via up to three-stage retrieval:
1. Score argument categories against the JD embedding
2. Rank claims within relevant categories by embedding similarity
3. Optional Cohere reranker pass for precision

Groups claims into argument-driven paragraph blocks and writes an editable markdown outline.
Prints any JD requirements no claim covers (gaps recorded in analytics DB).

**Edit the outline before generating.** Reorder blocks, drop weak claims, adjust framing.

#### Step 2 — `clio generate --from-outline`

```
clio generate --from-outline acme_corp_outline.md jd.txt
```

Reads the edited outline and generates a letter grounded in that structure. Anchor phrases
from the outline appear in the letter verbatim.

### Classic path

#### `clio generate`

Takes a JD, selects paragraphs from the library using semantic embeddings (BM25 fallback),
and streams a letter.

After the letter:
1. Verification — LLM pass for invented facts and banned constructs
2. Alignment report — JD requirements covered, gaps, seniority signal gaps, goal alignment
3. Thesis — one sentence stating what the letter argues

**Gap coverage**: gaps are checked against the claims DB. Gaps with a claim above threshold
are dimmed and labeled `[in library]`.

### After generating

#### `clio pdf`

Converts a saved letter markdown to PDF using Typst.

#### `clio resume`

Generates a tailored resume by selecting bullet options per company.

---

## Interview prep

### `clio interview`

```bash
clio interview jd.txt --company "Acme Corp"          # full briefing
clio interview jd.txt --company "Acme Corp" --summary # one-page version
```

Prompts for an optional recruiter or HR note (paste and double-Enter, or Enter to skip).
Saved to `output/YYYY-MM-DD_Company_interview.md`.

**The agent uses three tools** to gather your material per theme before writing:
- `search_library` — searches your paragraph library
- `get_claims` — searches the claims DB, both `source='library'` and `source='resume'`
- `get_experience_facts` — looks up your experience register for a named employer or project

**Full briefing sections:**
1. **Role snapshot** — what the role is actually about (not a restatement)
2. **What they're probing for** — themes ranked by signal strength; recruiter signals called out separately
3. **Your coverage** — per theme: `[RESUME]` (on paper), `[LIBRARY]` (needs to come out verbally), `[GAP]` (thin or no material)
4. **Likely questions** — 4-6 questions with "Lead with:" notes pointing to your best material

The `[LIBRARY]` tag is the grounding layer — material the interviewer cannot see that you
need to proactively surface in conversation.

**`--summary`** produces a shorter version: role snapshot + key themes + one strongest
match per theme. Fast to read before a call.

---

## Short-form applications

### `clio blurb`

For application prompts that are not full cover letters — biographical summaries, "why
this role" questions, behavioral prompts, approach questions.

Two-input flow: JD first (paragraph selection), then the specific application prompt.

---

## Analytics and tracking

### `clio outcome <company> <result>`

Record the result of an application.

```
clio outcome "Acme Corp" interview
clio outcome "Acme Corp" rejected
```

Results: `interview`, `rejected`, `offer`, `ghosted`, or any string.

### `clio analytics`

Cross-application analysis: category coverage rates, recurring JD gaps, highest-use claims,
never-used claims (after 3+ applications).

### `clio log`

Shows LLM call history from `~/.coverletter/runs.jsonl`. Every API call is logged with
timestamp, caller label, model, token counts, cache hit/miss, and estimated cost.

```bash
clio log                   # last 20 calls + last 10 session summaries
clio log --tail 50         # last 50 calls
clio log --sessions 5      # last 5 sessions only
```

Use this to understand what a run actually cost and which code paths are making calls.

---

## Provider support

| Provider | Generation | Caching | Embeddings | Hybrid | Rerank |
|---|---|---|---|---|---|
| Anthropic | ✓ | 90% cache_control | via Voyage | — | — |
| Mistral | ✓ | 90% cache_key | mistral-embed ✓ | — | — |
| OpenAI | ✓ | 50% auto | text-embedding-3-small ✓ | — | — |
| Cohere | ✓ | unknown | embed-v4.0 ✓ | — | rerank-v3.5 ✓ |
| BGE-M3 | embed-only | local | dense ✓ | hybrid dense+sparse ✓ | — |

Set via `COVERLETTER_MODEL` (or `--model`). Set `EMBED_MODEL=bge-m3` for local hybrid
embeddings. BGE-M3 requires `uv add FlagEmbedding` (~2GB download on first use).

---

## What is not built

**Coaching pass — Level 3 narrative awareness**. The current letter-level coaching pass
evaluates sentences in isolation. It does not know what kind of paragraph it is reading
or what the letter as a whole is arguing.

**`build --jd` gap analysis requires populated claims DB**. If no `clio extract` has been
run, gap analysis returns no results with a clear message. Classic `clio build` works
without the DB.

**BGE-M3 hybrid scoring requires FlagEmbedding**. Dense-only BGE-M3 works via any
OpenAI-compatible local server. Hybrid requires `uv add FlagEmbedding` and a local
model download.

**Cohere generation and streaming untested against real keys**. The provider is implemented
but has not been verified against a live Cohere API key.

**Ollama** — not yet implemented.

**Thesis correction memory**: each correction to the thesis replaces the previous one.
Accumulated correction history is not passed through regeneration turns.

**Positioning notes**: accepted thesis corrections are not saved for reuse across runs.
Planned: `positioning/` directory of role-type → argument framing notes.

**JD improvement metrics**: `jd_versions` logs changes but does not yet compute a coverage
delta (did your library coverage of this JD improve after adding paragraphs?). Planned as
part of `clio analytics`.
