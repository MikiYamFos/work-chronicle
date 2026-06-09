# clio — Workflow Reference

This document describes what the system does, how to use it, and how to test it end
to end. It covers what works, what is partial, and what is not built. It does not
describe aspirations as if they are implemented.

Run `clio help` for a quick command reference organized by workflow.

---

## Library files — what lives where

| File | Role |
|------|------|
| `library.md` | Your raw paragraphs. Write here first. Never rewritten by the tool. |
| `library_rebuilt.md` | Output of the paragraph editor — paragraphs you've reviewed and approved in your own voice. Highest priority in generation. |
| `library_refined.md` | Coach drafts from `clio build` Q&A sessions. Higher priority than `library.md`, lower than `library_rebuilt.md`. |
| `library_salvaged.md` | Paragraphs recovered via the diff tool. Same status as `library_rebuilt.md` once approved. |
| `library.db` | SQLite database. Populated by `clio sync`. Holds paragraphs, claims, embeddings. |
| `candidate_profile.toml` | Your goals, working style, values, seniority signals. |
| `experiences.md` | Per-experience fact sheet and Q&A agenda. Populated automatically during `seed` and `build`. |
| `custom_angles.toml` | Personal overrides for the 18 paragraph angles. Gitignored. Created by `clio init`. |
| `custom_categories.toml` | Personal overrides for the 10 claim categories. Gitignored. Created by `clio init`. |

**File priority in generation (highest to lowest):**
`library_rebuilt.md` → `library_refined.md` → `library.md`

When multiple files contain a paragraph for the same section, the highest-priority
version wins. You never need to delete from lower files.

---

## Phase 1 — Setup (run once per working directory)

### `clio init`

Run from the directory where your personal files will live (the repo root for this
project). Creates:
- `.env` — add your API keys and `AUTHOR_NAME` here
- `library.md` — empty, ready to write into
- `experiences.md` — empty, populated automatically by build and seed
- `custom_angles.toml` — commented template for overriding paragraph angles
- `custom_categories.toml` — commented template for overriding claim categories

Fill in `.env` before running anything else:
```
ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...         # optional — enables semantic search; BM25 fallback if absent
AUTHOR_NAME=Your Name
RESUME_FILE=/path/to/resume.pdf
```

### `clio onboard`

Check setup readiness. Reports missing keys, missing files, and what's ready.
Run this after filling in `.env` to confirm everything is wired correctly.

---

## Phase 2 — Getting material into the system

Do this before `sync`. The DB needs content to be useful.

### `clio seed <file>`

For bootstrapping from existing material — a resume, LinkedIn export, old cover
letters, or a PDF. Extracts initial paragraphs via light Q&A. Paragraphs are appended
to `library.md`. Q&A agenda items are written to `experiences.md`.

```bash
uv run clio seed ~/resume.pdf
uv run clio seed old_cover_letter.txt
```

Paragraphs from `seed` tend to be thinner than paragraphs built through `build`. They
establish the library baseline; `build` develops them further.

### `clio build`

The core library-building tool. Runs a focused Q&A session on a specific topic —
a project, a decision, an experience. Drafts a paragraph and appends it to
`library_refined.md`.

```bash
uv run clio build                           # prompts for topic
uv run clio build --jd jds/acme.txt        # gap-driven — analyzes library first
uv run clio build --resume ~/resume.pdf    # coach aware of resume content
```

The build agent searches the library before asking anything — it will not re-ask about
things already documented. One question per turn.

**During a session**: press Enter twice to submit a multi-line answer. Type `draft` to
force a draft at any point. Type `done` to exit without saving.

**Gap-driven mode** (`--jd`): shows which argument categories are covered vs missing for
a specific JD, then starts a Q&A session targeting gaps. Requires `clio sync` and
`clio extract` to have been run first.

Repeat `build` for each major project or experience. Plan 4–6 paragraphs minimum before
the library is useful for generation.

### `clio reflect`

Captures through-lines, pivots, reframes, and synthesis paragraphs — your voice
connecting your arc. These are not evidence paragraphs.

Perspective paragraphs are pinned during prefilter (never filtered out by relevance
scoring) and labeled `[NARRATIVE FRAME]` in the generation context.

### `clio profile`

Guided Q&A that writes `candidate_profile.toml`. Covers goals, working style, values,
and seniority signals. Used in alignment reporting, thesis generation, and blurb generation.

Run once early. Re-run if your goals have changed — the previous profile is archived.

```bash
uv run clio profile
uv run clio profile --model opus    # use a more capable model for this
```

---

## Phase 3 — Loading the library into the DB

### `clio sync`

Reads all configured `.md` files and upserts paragraphs into `library.db`. Run this:
- After `seed` or `build` adds new paragraphs
- After you edit any markdown file directly
- Any time the DB appears empty

```bash
uv run clio sync
```

Sync reads `library_rebuilt.md`, `library_refined.md`, and `library.md` in priority
order. Paragraphs with the same section name are deduplicated by priority.

---

## Phase 4 — Extracting claims

Claims power the argument-driven generation path, gap analysis, and interview prep.
Skip this for a first letter — do it once you have 4+ solid paragraphs.

### `clio extract --dry-run`

Extracts claims from all paragraphs in the DB that haven't been extracted yet. For each
paragraph, pulls:
- **Claims** — atomic assertions: ownership/decision, approach/method,
  disposition/character, motivation, personal project
- **Support items** — evidence that makes claims believable
- **Sub-details** — technical specifics, preserved near-verbatim
- **Conclusions** — insights that emerge from the claims

In `--dry-run` mode, nothing writes to the DB. Results go to `extractions_review.json`.

### Label claims (Streamlit)

```bash
uv run streamlit run coverletter/label_evals.py
```

Review extracted claims after a dry-run. Approve good claims (they insert to DB
immediately). Reject bad ones with a failure category. Mark gold standard examples —
you need 5 approved + 5 rejected before live extraction will run.

Session position saves on every action — reopen and it picks up where you left off.

### `clio extract`

Same extraction and judging as dry-run; passing claims insert directly into the DB.
Requires the gold standard threshold.

### Judge calibration

```bash
uv run python coverletter/evals/align_judge.py
```

Checks judge accuracy against your gold standard. Reports accuracy, precision, recall.
Alignment targets: recall ≥ 89%, accuracy ≥ 80%.

---

## Phase 5 — Resume extraction

Your resume is automatically indexed into the claims DB the first time any command that
uses it runs. This happens silently — one line prints when indexing occurs:

```
  Indexing resume... 24 claims indexed (v1)
```

Resume claims are stored with `source='resume'` alongside library claims
(`source='library'`). This distinction shows up in interview prep as coverage tags.

### `clio resume-extract`

Force a fresh extraction — use after a major resume overhaul.

```bash
uv run clio resume-extract          # shows last extraction info, prompts to confirm
uv run clio resume-extract --force  # re-extracts without prompting
```

---

## Phase 6 — Job descriptions

JDs are saved automatically when you paste one during `generate` or `blurb`. They are
cleaned before storage — boilerplate is stripped, company values are kept. Embeddings
are cached by content hash so the same JD is never re-embedded across runs.

```bash
uv run clio jd list                   # show saved JDs with date, size, preview
uv run clio jd rename <old> <new>     # rename a saved JD
uv run clio jd replace <name>         # paste new JD; clears DB cache, logs version change
```

`jd replace` logs the change to `jd_versions` with old/new hash. Planned: coverage
delta reporting (did your library coverage of this JD improve after adding paragraphs?).

---

## Phase 7 — Generating letters

### Classic path (works with thin library, no claims required)

```bash
uv run clio
```

Paste a JD when prompted. Streams a letter. After generation:
1. Verification — LLM pass for invented facts and banned constructs
2. Alignment report — JD requirements covered, gaps, seniority signal gaps, goal alignment
3. Thesis — one sentence stating what the letter argues

Revision loop: enter a gap number to Q&A and add a paragraph; `r` + feedback to revise
inline; `s` to save; `q` to quit.

### Argument-driven path (requires claims in DB)

```bash
uv run clio outline jds/acme.txt --company "Acme Corp"
# edit the outline file it produces
uv run clio generate --from-outline output/acme_outline.md jds/acme.txt
```

`outline` generates a thesis, scores claims against the JD, groups them into argument
blocks, and writes an editable markdown outline. Edit it — reorder blocks, drop weak
claims, adjust framing — before generating. Anchor phrases from the outline appear in
the letter verbatim.

### After generating

```bash
uv run clio pdf output/acme_letter.md    # convert to PDF via Typst
uv run clio resume                        # tailored resume for this application
```

---

## Phase 8 — Interview prep

Requires claims in the DB (Phase 4 complete).

```bash
uv run clio interview jds/acme.txt --company "Acme Corp"
uv run clio interview jds/acme.txt --company "Acme Corp" --summary
```

Prompts for an optional recruiter or HR note (paste and double-Enter, or Enter to skip).
Output saved to `output/YYYY-MM-DD_Company_interview.md`.

The agent uses three tools to gather material before writing:
- `search_library` — searches paragraph library
- `get_claims` — searches claims DB (`source='library'` and `source='resume'`)
- `get_experience_facts` — looks up experience register for a named employer or project

**Full briefing sections:**
1. Role snapshot — what the role is actually about
2. What they're probing for — themes ranked by signal strength
3. Your coverage — per theme: `[RESUME]` (on paper), `[LIBRARY]` (needs to come out verbally), `[GAP]` (thin or no material)
4. Likely questions — 4–6 questions with "Lead with:" notes

`--summary` produces a shorter version: role snapshot + key themes + one strongest match
per theme.

---

## Phase 9 — Short-form applications

### `clio blurb`

For application prompts that are not full cover letters — biographical summaries,
"why this role" questions, behavioral prompts, approach questions.

Two-input flow: JD first (paragraph selection), then the specific prompt.

---

## Phase 10 — Tracking and monitoring

```bash
uv run clio outcome "Acme Corp" interview     # record application result
uv run clio outcome "Acme Corp" rejected
```

Results: `response`, `interview`, `offer`, `rejected`, `withdrew`, or any string.

```bash
uv run clio analytics    # coverage patterns, recurring gaps, highest-use claims
```

```bash
uv run clio log              # last 20 calls + last 10 session summaries
uv run clio log --tail 50    # last 50 calls
uv run clio log --sessions 5 # last 5 sessions only
```

Every API call is logged with timestamp, caller label, model, token counts, cache
hit/miss, and estimated cost.

---

## Library diff tool (Streamlit)

For reviewing and correcting `library_refined.md` paragraphs — comparing the coach
draft against your original and rewriting in your own voice.

```bash
uv run streamlit run coverletter/library_diff.py
```

**Three columns:**
- **Raw** (`library.md`) — your words, read-only
- **Damaged / Coach draft** (`library_refined.md`) — read-only reference
- **Story notes** (`story_notes.md`) — relevant sections surfaced by keyword match

**Edit area** below — your working version. Starts from raw. Edit here. This is what
gets saved to `library_salvaged.md`.

**Two coaching buttons:**
- **Check what the draft got wrong** — Level 1. Compares damaged column against raw.
  Finds where Claude swapped your words, added sentences you didn't write, dropped
  things you said. Run before editing.
- **Check my edited version** — Level 2. Checks your edited text for weak openers,
  AI constructs, passive voice main claims. Run after editing, before saving.

**Action buttons:** Use raw & next / Use damaged & next / Save edit & next / Skip / Exclude

Progress saves to `library_salvaged.reviewed.txt`. Output writes to `library_salvaged.md`
only when you click **Save to output file** in the sidebar.

---

## Full end-to-end test checklist

Use this on a fresh clone to confirm everything works.

### Setup
- [ ] `uv sync` — installs without errors
- [ ] `uv run clio init` — creates `.env`, `library.md`, `experiences.md`, `custom_angles.toml`, `custom_categories.toml`
- [ ] Fill in `.env` with API keys and `AUTHOR_NAME` and `RESUME_FILE`
- [ ] `uv run clio onboard` — shows green for all configured items

### Getting material in
- [ ] `uv run clio seed <file>` — runs without error, appends paragraphs to `library.md`, writes Q&A agenda to `experiences.md`
- [ ] `uv run clio profile` — runs Q&A, writes `candidate_profile.toml`
- [ ] `uv run clio build` — Q&A session runs, follow-up question fires, `draft` command works mid-session, `done` exits cleanly, paragraph appended to `library_refined.md`

### DB and extraction
- [ ] `uv run clio sync` — runs without error, reports paragraph count
- [ ] `uv run clio extract --dry-run` — writes `extractions_review.json`, no DB writes
- [ ] `uv run streamlit run coverletter/label_evals.py` — loads claims, approve/reject works, gold standard checkbox works
- [ ] `uv run clio extract` — runs after gold standard threshold met, claims land in DB

### Resume extraction
- [ ] `uv run clio` (first run with RESUME_FILE set) — prints `Indexing resume... N claims indexed (v1)` before letter streams
- [ ] `uv run clio resume-extract --force` — re-extracts, version increments

### Generation
- [ ] `uv run clio` — letter streams, verification runs, alignment report prints, thesis prints
- [ ] Revision loop — enter gap number, add paragraph; `r` + feedback revises inline; `s` saves
- [ ] `uv run clio outline jds/<file>.txt --company "Name"` — outline file written
- [ ] Edit outline file, then `uv run clio generate --from-outline <outline> <jd>` — generates from outline

### Interview prep
- [ ] `uv run clio interview jds/<file>.txt --company "Name"` — recruiter note prompt fires, briefing written to `output/`
- [ ] Coverage tags `[RESUME]`, `[LIBRARY]`, `[GAP]` appear in output
- [ ] `--summary` flag produces shorter version

### JD management
- [ ] `uv run clio jd list` — shows saved JDs
- [ ] `uv run clio jd replace <name>` — logs version change to `jd_versions`

### Monitoring
- [ ] `uv run clio log` — shows every API call from this session with tokens and cost
- [ ] `uv run clio outcome "Company" interview` — records without error
- [ ] `uv run clio analytics` — runs without error (may be sparse on first use)

### Library diff tool
- [ ] `uv run streamlit run coverletter/library_diff.py` — loads without error
- [ ] Three columns render correctly when `library_refined.md` exists
- [ ] Level 1 and Level 2 coach buttons work
- [ ] Save writes to `library_salvaged.md`

---

## Provider support

| Provider | Generation | Caching | Embeddings | Rerank |
|---|---|---|---|---|
| Anthropic | ✓ | 90% cache_control | via Voyage | — |
| Mistral | ✓ | 90% cache_key | mistral-embed ✓ | — |
| OpenAI | ✓ | 50% auto | text-embedding-3-small ✓ | — |
| Cohere | ✓ | unknown | embed-v4.0 ✓ | rerank-v3.5 ✓ |
| BGE-M3 | embed-only | local | dense ✓ | — |

Set via `COVERLETTER_MODEL` env var or `--model` flag. Set `EMBED_MODEL=bge-m3` for
local hybrid embeddings (requires `uv add FlagEmbedding`, ~2GB download on first use).

---

## What is not built

**`clio edit`** — general-purpose paragraph editor (Streamlit). Planned: side-by-side
view of `library.md` vs `library_refined.md`, line editing, save to `library_rebuilt.md`.
Separate from `library_diff.py` which stays for the corruption-fix workflow.

**Coaching pass — Level 3 narrative awareness**. The current coaching pass evaluates
sentences in isolation. It does not know what kind of paragraph it is reading or what
the letter as a whole is arguing.

**JD coverage delta**. `jd_versions` logs changes but does not yet compute whether your
library coverage of a JD improved after adding paragraphs.

**Thesis as generation input**. Currently the thesis is generated after the letter.
Using it to shape paragraph selection has not been done.

**Positioning notes**. Accepted thesis corrections are not saved for reuse across runs.
Planned: `positioning/` directory of role-type → argument framing notes.

**Ollama**. Not yet implemented.

**Cohere generation untested against live keys**. The provider is implemented but has
not been verified against a real Cohere API key.
