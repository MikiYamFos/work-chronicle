# Cover Letter Generator — End-to-End Workflow

This document walks through the full system as it currently exists. It covers what works,
what is partial, and what is not yet built. It does not describe aspirations as if they
are implemented.

---

## Overview

The system has two distinct tracks that were built at different times and connect
imperfectly. Understanding both is necessary to understand where things stand.

**Track 1 — Paragraph assembly (original flow)**
The library is a set of markdown paragraphs. The tool selects the most relevant ones for
a given JD and sends them to Claude with a system prompt. Claude writes a letter grounded
in that material. This is fully working end to end.

**Track 2 — Claim-evidence extraction (newer flow)**
Library paragraphs are parsed into atomic claims with hierarchical evidence. Claims are
stored in a SQLite database. An outline tool groups them into paragraph blocks against a
JD. Track 2 ends at the outline — there is no `coverletter generate --from-outline`
command. Track 1 is still what actually generates letters.

---

## Library files — what lives where

Files fall into two groups: **main flow** (what generation uses and what you write into
going forward) and **triage** (cleanup work for existing damaged material, not the ongoing path).

### Main flow files — these are what matters

| File | Role |
|------|------|
| `library.md` | Your raw paragraphs. Write here first. Source of truth. Never rewritten by the tool. |
| `library_rebuilt.md` | Paragraphs built through the correct workflow: raw → coaching → your edits → approved. This is where new good material lands. |
| `library_salvaged.md` | Paragraphs recovered from damaged material via the diff tool. Same status as `library_rebuilt.md` once approved. |
| `library.db` | SQLite database. Populated by `coverletter sync`. Holds claims, evidence, embeddings. Generation uses this. |
| `candidate_profile.toml` | Your goals, working style, values, seniority signals. Drives thesis and alignment. |

**The write path going forward:**
Raw text → `library.md` → diff tool (draft + coaching + your edits) → `library_rebuilt.md` → `coverletter sync` → extraction → DB

### Triage files — cleanup work, not the ongoing path

| File | What it is |
|------|------------|
| `library_refined.md` | Historically Claude-damaged refinements. Being corrected via the diff tool. Not written to anymore — it is input to the diff tool, not output. Once fully processed, it retires. |
| `story_notes.md` | Raw conversation material that hasn't been turned into paragraphs yet. Not used in generation. The diff tool surfaces relevant sections when you're working through related paragraphs. |

### Other files

| File | What it is |
|------|------------|
| `experiences.md` | Supplementary fact sheet per experience — raw notes, angle inventory, Q&A targets. Used by `build` to ask better questions. Not prose, not used directly in generation. |
| `corrections.md` | Band-aid file — sentence-level fixes applied before generation to catch known problems. A corrections entry means a paragraph should probably be fixed at source. |
| `resume_bullets.md` | Alternative bullets for the resume command. Separate from the letter flow. |

---

## Phase 1 — Cold start: getting material into the system

### 1a. `coverletter init`

Creates the initial config file (`.coverletter.yaml`) and the markdown library files.
Asks for name, target role, and API keys. Nothing is generated yet; this is scaffolding only.

### 1b. `coverletter seed`

If you have existing material — a resume, a LinkedIn export, old cover letters — `seed`
reads it and extracts initial paragraphs into the library via light Q&A.

**What's incomplete**: paragraphs from `seed` tend to be thinner than paragraphs built
through the full `build` loop. They need further Q&A development afterward.

### 1c. `coverletter profile`

Captures the candidate's goals, values, working style, and seniority signals into
`.coverletter_profile.yaml`. Used in alignment reporting, thesis generation, and blurb
generation. Not required to generate a letter but substantially improves quality.

Profile sections:
- `goals` — what the person is looking for in their next role
- `values` — what they believe as an engineer and teammate
- `working_style` — how they work (used heavily in `blurb`)
- `avoid` — roles or contexts that are wrong for them (values inference)
- `seniority_signals` — what dimensions to flag when evaluating fit for senior roles

Profiles are versioned. When you re-run `profile`, the previous one is archived with a
timestamp. If your goals have changed since the last profile, the tool detects the diff
and offers a perspective Q&A session to capture the shift before saving.

---

## Phase 2 — Building and refining the library

### 2a. `coverletter sync`

Reads all configured `.md` files and upserts paragraphs into the SQLite DB (`library.db`).
Run this any time you edit the markdown files directly or add new paragraphs.

Sync also:
- Computes Voyage AI embeddings for paragraphs (`--embed` flag, requires Voyage key)
- Assigns angle classifications (`--angles` flag)

Paragraphs are tagged with metadata in their markdown front matter: `role`, `section`,
`angle`, `tone`, `layer`, `via`, etc. The angle taxonomy has 18 categories. Tags drive
paragraph selection during generation.

### 2b. `coverletter build`

The core library-building tool. Takes a gap or topic and runs a focused Q&A session that
draws out specific details about that experience. Drafts a paragraph at the end.

The build agent searches the library before asking anything, so it does not re-ask about
things already documented. One question per turn. Type `e` to open `$EDITOR` for a long
answer.

**The draft prompt is strictly constrained**: the draft must lift the writer's actual
sentences, must not invent openers or closers not present in the source, and must not
paraphrase or substitute polished language for the writer's register.

### 2c. `coverletter reflect`

Captures perspective material — through-lines, pivots, reframes, and synthesis paragraphs.
These are not evidence paragraphs — they are the candidate's voice connecting their arc.

Q&A is angle-specific: a through-line session asks about what's been consistent across
the whole arc. A pivot session asks about the specific moment of change and the reason.

Perspective paragraphs are tagged `via=reflect` and pinned during prefilter (never filtered
out by relevance scoring). They are labeled `[NARRATIVE FRAME]` in the library block so
the generation model knows their role.

### 2d. `coverletter intake`

Two modes: `--mission` (capture why a company's purpose resonates) and `--evidence`
(capture what was built or owned at a specific role). Both run focused Q&A sessions and
draft paragraphs.

---

## Phase 3 — Library diff tool (Streamlit)

```
uv run streamlit run coverletter/library_diff.py
```

The diff tool is for correcting the existing `library_refined.md` paragraphs that were
damaged by Claude rewriting. It shows three sources side by side and lets you decide what
goes into `library_salvaged.md`.

**Three columns:**
- **Raw** (`library.md`) — your words, read-only, source of truth
- **Damaged** (`library_refined.md`) — Claude-corrupted version, read-only reference
- **Story notes** (`story_notes.md`) — relevant sections surfaced automatically by
  keyword match, in case there's additional material that didn't make it into either file

**Edit area** below the three columns — your working version. Starts from raw text.
Edit here. This is what gets saved to `library_salvaged.md`.

**Two coaching buttons** above the action buttons — both are manual triggers, both cost
API calls, both disabled if no API key is set:

- **"Check what the draft got wrong"** — Level 1 coach. Compares the damaged column
  against your raw text. Finds where Claude swapped your words for worse ones, added
  sentences you never wrote, or dropped things you said. Run this before editing to
  understand what got corrupted.

- **"Check my edited version"** — Level 2 coach. Checks your edited text for specific
  problems before saving: a weak opener that doesn't do any work, AI writing constructs
  that lose precision (false contrast, em-dash, banned words), or a main claim sentence
  in passive voice. Run this after editing, before saving.

**Action buttons:**
- **Use raw & next** — your raw text is already correct, approve it as-is
- **Use damaged & next** — the damaged version is actually fine, use it
- **Save edit & next** — save your edited version
- **Skip** — come back later
- **Exclude** — mark reviewed without saving; paragraph won't appear in output

Progress saves automatically to `library_salvaged.reviewed.txt`. Output writes to
`library_salvaged.md` only when you click **Save to output file** in the sidebar. Raw and
damaged files are never modified.

---

## Phase 4 — Claim-evidence extraction (Track 2)

This track is built but does not yet connect to letter generation.

### 4a. `coverletter extract --dry-run`

Extracts claims from all pending paragraphs in the DB. For each paragraph, pulls:
- **Claims** — atomic assertions in five types: ownership/decision, approach/method,
  disposition/character, motivation/orientation, personal project
- **Support items** — evidence that makes claims believable
- **Sub-details** — technical specifics nested under support items, preserved near-verbatim
- **Conclusions** — insights that emerge from the claims (only if explicit in the paragraph)

The judge runs on every claim concurrently. Paragraphs run concurrently against each other.

In `--dry-run` mode, nothing writes to the DB. Results go to `extractions_review.json`.

### 4b. `coverletter extract` (without dry-run)

Same extraction and judging, but passing claims insert directly into the DB. Requires a
gold standard with at least 5 approved and 5 rejected examples.

### 4c. Claim review app (Streamlit)

```
uv run streamlit run coverletter/label_evals.py
```

Review extracted claims after a dry-run. For each claim: source paragraph (editable),
claim text, judge pass/fail with reason, contexts, and support hierarchy.

**Session resumption**: cursor position saves to the review JSON on every action. Reopen
the app and it picks up where you left off. Jump to any paragraph via the sidebar selector.

**Paragraph editing**: the source paragraph is an editable text area. Save edits to the
review JSON — nothing re-extracts yet.

**End-of-session re-extract**: when all claims are labeled, a "Re-extract N edited
paragraphs" button appears. One click, one API pass. New claims go into a judge queue
stored in the JSON — visible and actionable but not blocking. Come back to the queue in
a later session.

**Gold standard candidates**: also surfaces at end of session. Both approved claims and
rejected claims with failure categories appear as candidates, grouped and explained. Only
add unambiguous cases. The mid-flow gold standard checkbox (in the label area) is for
clear cases you want to capture as you go.

### 4d. `coverletter outline`

Given a JD, generates a thesis, loads claims from the DB, scores by relevance, and groups
claims into paragraph blocks. Handles all five claim types — ownership claims group into
argument blocks; disposition, motivation, and approach claims get their own standalone
blocks and are not forced into evidence groups or marked unused.

**Track 2 ends here.** No `coverletter generate --from-outline` exists. The handoff from
structured claims to generation is unresolved — see the design questions section below.

---

## Phase 5 — Generating a letter (Track 1)

### 5a. `coverletter generate`

Takes a JD (file, clipboard, or typed), selects paragraphs from the library, streams a letter.

**Paragraph selection**: Voyage embeddings if available, BM25 keyword fallback. Perspective
paragraphs are always included. Layer-0 paragraphs supersede layer-1 for the same section.

**After the letter streams**:
1. Verification — LLM pass for invented facts and banned constructs; deterministic verbatim check
2. Alignment report — JD requirements covered, gaps, seniority signal gaps, goal alignment,
   BM25 library coverage detection
3. Thesis — one sentence stating what the letter argues

**Revision loop**: enter a gap number to Q&A and add a paragraph; `r` + feedback to revise
inline; `g` for the full gap loop; `s` to save; `q` to quit.

After saving, if a `.typ` resume file is configured, the tool offers to generate a tailored
resume for the same application.

**What's incomplete**: thesis is generated after the letter, not used to focus it. Alignment
report gaps are addressed manually.

### 5b. `coverletter pdf`

Converts a saved letter markdown to PDF using Typst. Requires Typst to be installed.

### 5c. `coverletter resume`

Generates a tailored resume by selecting bullet options per company. Also offered
automatically after `coverletter generate` saves a letter.

---

## Phase 6 — Short-form applications

### `coverletter blurb`

For application prompts that are not full cover letters — biographical summaries, "why
this role" questions, behavioral prompts, approach questions.

Two-input flow: JD first (paragraph selection), then the specific application prompt.
The model uses `working_style` + `values` as the argument spine, library paragraphs as
evidence.

If `working_style` + `values` + `avoid` entries total fewer than 2, the tool warns before
generation and offers to bail. The model will surface `BIOGRAPHICAL_GAPS` if material is
thin — the tool catches this and offers to add profile entries on the spot.

When the application prompt contains a character or word limit, the model compresses the
argument rather than the voice — evidence sentences get cut before biographical language.

Revision loop retains rejected drafts in conversation history.

**What's incomplete**: behavioral and approach prompt types are less tested than
biographical.

---

## What is not built and needs design before building

**Letter generation from the claim-evidence DB** (Track 2 completion). The generation
prompt structure when the input is structured claims rather than prose paragraphs is
unresolved. Key questions: do claims replace paragraphs in the library block or supplement
them? What is the prompt structure for claim types 3-5 (disposition, motivation,
orientation) that don't map to argument paragraphs?

**Coaching pass — Level 3 narrative awareness**. The current letter-level coaching pass
(`coach.py:analyze_letter`) evaluates sentences in isolation. It does not know what kind
of paragraph it is reading or what the letter as a whole is arguing. A first pass that
identifies what each paragraph is doing before evaluating sentences against that
understanding is needed.

**Thesis as input to generation, not output**. Currently the thesis is generated from the
finished letter. Using the argument target to shape paragraph selection and assembly
ordering has not been done.

**Multi-provider support**. The tool is Anthropic-only. See ROADMAP.md for the full design.

**Gold standard → judge feedback loop**. Adding examples to the gold standard has no
automatic effect on the judge prompt (`_JUDGE_SYSTEM` in `extract.py`). The loop between
"gold standard grows" → "judge improves" requires a human to read `align_judge.py` output
and manually update the prompt.
