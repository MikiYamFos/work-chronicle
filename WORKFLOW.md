# Cover Letter Generator — Workflow Reference

This document describes what the system does and how to use it. It covers what works,
what is partial, and what is not built. It does not describe aspirations as if implemented.

---

## Library files — what lives where

| File | Role |
|------|------|
| `library.md` | Your raw paragraphs. Write here first. Never rewritten by the tool. |
| `library_rebuilt.md` | Paragraphs built through the correct workflow: raw → coaching → your edits → approved. |
| `library_salvaged.md` | Paragraphs recovered from damaged material via the diff tool. Same status as `library_rebuilt.md` once approved. |
| `library.db` | SQLite database. Populated by `coverletter sync`. Holds paragraphs, claims, evidence, embeddings. |
| `candidate_profile.toml` | Your goals, working style, values, seniority signals. |

**The write path going forward:**
Raw text → `library.md` → diff tool (draft + coaching + your edits) → `library_rebuilt.md` → `coverletter sync` → `coverletter extract` → DB

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

### `coverletter init`

First-time setup only. Creates `.coverletter.yaml` and empty library files. Run once.

### `coverletter profile`

Captures your goals, values, working style, and seniority signals into
`.coverletter_profile.yaml`. Used in alignment reporting, thesis generation, and blurb
generation. Profiles are versioned — re-running archives the previous one. If your goals
have shifted, the tool detects the diff and runs a brief Q&A before saving.

Profile sections: `goals`, `values`, `working_style`, `avoid`, `seniority_signals`.

### `coverletter build`

The core library-building tool. Runs a focused Q&A session that draws out specific details
and drafts a paragraph. Two modes:

**Manual mode** (default): prompts for a topic — a project, experience, or angle you want
to capture.

**Gap-driven mode** (`--jd`): takes a job description and uses the claims DB to identify
which argument categories are covered and which are not. Shows covered categories with the
best-matching claim, shows gaps with a concrete starting question for each, then lets you
pick which gaps to address. Each gap session feeds the Q&A coach the gap requirement and
starting angle so it begins from a specific, grounded place rather than cold.

```bash
coverletter build                          # manual — prompts for topic
coverletter build --jd /path/to/jd.txt    # gap-driven — analyzes library first
coverletter build --jd "JD text..."       # gap-driven — inline text
```

`--jd` gap analysis uses DB embeddings, not an LLM scan of the library. It requires
`coverletter sync` and `coverletter extract` to have been run first.

Pass `--resume` to make the coach aware of your resume. Resume bullets are injected as
established fact — the coach does not re-ask what the resume states; it asks about
constraints, consequences, and decisions not captured there.

```bash
coverletter build --resume ~/resume.pdf --jd jd.txt
```

The build agent searches the library before asking anything, so it does not re-ask about
things already documented. One question per turn. Type `e` to open `$EDITOR` for a long
answer.

**The draft is strictly constrained**: it must lift your actual sentences, must not invent
openers or closers not present in the source, and must not paraphrase or substitute
polished language for your register.

After each accepted paragraph in `--jd` mode, the DB syncs automatically so subsequent
gap sessions in the same run see updated coverage.

### `coverletter reflect`

Captures perspective material — through-lines, pivots, reframes, and synthesis paragraphs.
These are not evidence paragraphs — they are your voice connecting your arc.

Q&A is angle-specific: a through-line session asks about what has been consistent across
your whole arc. A pivot session asks about the specific moment of change and the reason.

Perspective paragraphs are pinned during prefilter (never filtered out by relevance
scoring) and labeled `[NARRATIVE FRAME]` in the generation context.

### `coverletter intake`

Two modes: `--mission` (capture why a company's purpose resonates) and `--evidence`
(capture what was built or owned at a specific role). Both run focused Q&A and draft
paragraphs.

### `coverletter seed`

For bootstrapping from existing material — a resume, LinkedIn export, old cover letters.
Reads the file and extracts initial paragraphs via light Q&A. Paragraphs from `seed` tend
to be thinner than paragraphs built through the full `build` loop and need further
development.

### `coverletter sync`

Reads all configured `.md` files and upserts paragraphs into the SQLite DB. Run this any
time you edit the markdown files directly or add new paragraphs.

Sync also computes Voyage AI embeddings (`--embed` flag) and angle classifications
(`--angles` flag).

### Library diff tool (Streamlit)

```
uv run streamlit run coverletter/library_diff.py
```

For correcting `library_refined.md` paragraphs that were damaged by Claude rewriting.
Shows three sources side by side — raw, damaged, and story notes — and lets you decide
what goes into `library_salvaged.md`.

**Two coaching buttons**: "Check what the draft got wrong" (Level 1 — finds where Claude
corrupted your words) and "Check my edited version" (Level 2 — checks for weak openers,
AI constructs, passive claims before you save).

**Action buttons**: Use raw & next / Use damaged & next / Save edit & next / Skip / Exclude.

---

## Extracting claims

Claims are extracted from your library paragraphs and stored in the DB. This is what
powers the argument-driven generation flow. You do not need to do this before generating
with the classic flow, but you do need it before `coverletter outline`.

### `coverletter extract --dry-run`

Extracts claims from all pending paragraphs. For each paragraph, pulls:
- **Claims** — atomic assertions in five types: ownership/decision, approach/method,
  disposition/character, motivation/orientation, personal project
- **Support items** — evidence that makes claims believable
- **Sub-details** — technical specifics nested under support items, preserved near-verbatim
- **Conclusions** — insights that emerge from the claims (only if explicit in the paragraph)

The judge runs on every claim concurrently. Paragraphs run concurrently against each other.

In `--dry-run` mode, nothing writes to the DB. Results go to `extractions_review.json`.

### `coverletter extract` (without `--dry-run`)

Same extraction and judging; passing claims insert directly into the DB. Requires a gold
standard with at least 5 approved and 5 rejected examples before it will run.

### Claim review app (Streamlit)

```
uv run streamlit run coverletter/label_evals.py
```

Review extracted claims after a dry-run. For each claim: source paragraph (editable),
claim text, judge pass/fail with reason, contexts, and support hierarchy.

**Approve** inserts the claim to the DB immediately. **Reject** with a failure category.
**Gold standard checkbox** marks a claim as a reference example for the judge.

**Session resumption**: cursor position saves on every action. Reopen and it picks up where
you left off.

**End-of-session re-extract**: when all claims are labeled, a button appears to re-extract
paragraphs you edited. New claims go into a judge queue in the JSON.

**Gold standard candidates**: surfaces at end of session. Both approved and rejected claims
with clear failure categories appear as candidates. Mark unambiguous cases only.

### `coverletter claims`

Zero-cost view of claim coverage across the library. Shows claim count, anchor count, and
argument categories per paragraph. Run this to see which paragraphs still need extraction.

```
coverletter claims
```

### Judge calibration

```
uv run python coverletter/evals/align_judge.py
```

Checks judge accuracy against your gold standard. Reports accuracy, precision, and recall.
Shows all disagreements with the judge's reasoning.

If alignment is below target, the script offers to draft a targeted patch to `_JUDGE_SYSTEM`
in `extract.py` via a Haiku call. Review the draft before applying it — the script does
not edit the file automatically.

**Alignment targets**: recall ≥ 89% (catching bad claims), accuracy ≥ 80%.

```
uv run python coverletter/evals/run_evals.py
```

Measures overall pipeline quality as the percentage of claims the judge approves across
the full library. Use this to compare the effect of prompt changes.

---

## Writing a letter

Two paths. Both are fully working. Use the argument-driven path when you have a populated
claim library. Use the classic path for speed, or when the claim library is thin.

### Argument-driven path

#### Step 1 — `coverletter outline`

```
coverletter outline jd.txt --company "Acme Corp"
```

Generates a thesis from the JD, then pauses and lets you edit the thesis before grouping
runs — this is where you steer the argument. Then retrieves claims from the DB using
up to three-stage retrieval:

1. Score argument categories against the JD embedding — filter to relevant categories.
2. Rank claims within relevant categories by embedding similarity (or BGE-M3 hybrid
   dense+sparse if `EMBED_MODEL=bge-m3`).
3. Optional Cohere reranker pass over the selected claim set — cross-encoder sees the full
   (JD, claim) pair jointly for precision on terminology-sensitive requirements.

Groups claims into argument-driven paragraph blocks and writes an editable markdown outline.

After writing, prints any JD requirements that no claim covers (gaps). These are also
recorded in the analytics DB for cross-application tracking.

**Edit the outline before generating.** The outline is the steering point — reorder blocks,
drop weak claims, adjust the thesis framing, add notes to claims.

#### Step 2 — Edit the outline

Open the generated `acme_corp_outline.md`. The format:

```markdown
## paragraph label
*Addresses: JD requirement*

- **Claim:** At Acme, I owned the VideoViewEvents pipeline [Acme]
  - support item text
    - sub-detail text

*Conclusion: insight text*
```

You can reorder paragraph blocks, remove claims, add notes below a claim, and change the
`Addresses:` line to be more specific. Do not change the `**Claim:**` prefix or anchor
phrase formatting — those are parsed.

#### Step 3 — `coverletter generate --from-outline`

```
coverletter generate --from-outline acme_corp_outline.md jd.txt
```

Reads the edited outline, reconstructs claim/support/conclusion structure, and generates
a letter grounded in that structure. Anchor phrases from the outline appear in the letter
verbatim. Construction rules (first-sentence anchoring, banned words, em-dashes) are
applied here.

After generation:
1. Verification — LLM pass for invented facts and banned constructs
2. Alignment report — which outline blocks made it into the letter (by anchor phrase match)
   vs. were dropped
3. Revision loop — free text feedback to revise; accept or reject each revision

After saving, marks which claims reached the letter in the analytics DB and updates the
application outcome to "applied".

### Classic path

#### `coverletter generate`

Takes a JD (file, clipboard, or typed), selects paragraphs from the library using semantic
embeddings (BM25 keyword fallback), and streams a letter. Perspective paragraphs are always
included. Layer-0 paragraphs supersede layer-1 for the same section.

**Embedding provider priority**: provider-native embeddings (Mistral, OpenAI, Cohere) if
available, then Voyage, then BM25. Set `EMBED_MODEL=bge-m3` to use local BGE-M3 hybrid
dense+sparse scoring regardless of generation provider.

After the letter streams:
1. Verification — LLM pass for invented facts and banned constructs; deterministic verbatim check
2. Alignment report — JD requirements covered, gaps, seniority signal gaps, goal alignment,
   library coverage detection
3. Thesis — one sentence stating what the letter argues

**Revision loop**: enter a gap number to Q&A and add a paragraph; `r` + feedback to revise
inline; `g` for the full gap loop; `s` to save; `q` to quit.

After saving, if a `.typ` resume file is configured, the tool offers to generate a tailored
resume.

### After generating

#### `coverletter pdf`

Converts a saved letter markdown to PDF using Typst. Requires Typst to be installed.

#### `coverletter resume`

Generates a tailored resume by selecting bullet options per company. Also offered
automatically after `coverletter generate` saves a letter.

---

## Short-form applications

### `coverletter blurb`

For application prompts that are not full cover letters — biographical summaries, "why
this role" questions, behavioral prompts, approach questions.

Two-input flow: JD first (paragraph selection), then the specific application prompt.
The model uses `working_style` + `values` as the argument spine, library paragraphs as
evidence.

When the application prompt contains a character or word limit, the model compresses the
argument rather than the voice — evidence sentences get cut before biographical language.

Revision loop retains rejected drafts in conversation history.

---

## Analytics and tracking

These commands are useful after you have run several applications.

### `coverletter outcome <company> <result>`

Record the result of an application. Fuzzy-matches against recorded applications by
company name.

```
coverletter outcome "Acme Corp" interview
coverletter outcome "Acme Corp" rejected
```

Results: `interview`, `rejected`, `offer`, `ghosted`, or any string.

### `coverletter analytics`

Cross-application analysis: category coverage rates, recurring JD gaps (grouped by
requirement text across companies), highest-use claims, never-used claims (after 3+
applications), JD similarity between past applications.

Run this after several applications to see what your letter is consistently missing and
which claims are doing the most work.

---

## Provider support

| Provider | Generation | Caching | Embeddings | Hybrid | Rerank |
|---|---|---|---|---|---|
| Anthropic | ✓ | 90% cache_control | via Voyage | — | — |
| Mistral | ✓ | 90% cache_key | mistral-embed ✓ | — | — |
| OpenAI | ✓ | 50% auto | text-embedding-3-small ✓ | — | — |
| Cohere | ✓ | unknown | embed-v4.0 ✓ | — | rerank-v3.5 ✓ |
| BGE-M3 | embed-only | local | dense ✓ | hybrid dense+sparse ✓ | — |

Set via `COVERLETTER_MODEL` (or `--model`). Set `EMBED_MODEL=bge-m3` to use BGE-M3 for
embeddings independent of the generation provider. BGE-M3 requires `uv add FlagEmbedding`
and downloads BAAI/bge-m3 (~2GB) on first use.

For OpenAI-compatible hosts (Regolo, local inference servers), set `OPENAI_EMBED_MODEL`
to the embedding model the server expects. Defaults to `text-embedding-3-small` for
OpenAI proper.

Cohere's reranker runs as a Stage 3 pass over the already-filtered claim set in the
outline pipeline. It sees (query, document) pairs jointly — more precise than embedding
cosine similarity for terminology-sensitive matching.

---

## What is not built

**Coaching pass — Level 3 narrative awareness**. The current letter-level coaching pass
(`coach.py:analyze_letter`) evaluates sentences in isolation. It does not know what kind
of paragraph it is reading or what the letter as a whole is arguing.

**`build --jd` gap analysis requires populated claims DB**. The gap analysis scores the JD
against argument categories and claims already in the DB. If the DB is empty or no
`coverletter extract` has been run, it returns no results. The tool prints an actionable
message. Classic `coverletter build` (manual mode) works without the DB.

**BGE-M3 hybrid scoring for Track 1 requires FlagEmbedding**. Dense-only BGE-M3 works
via any OpenAI-compatible local server (set `OPENAI_BASE_URL`). Hybrid dense+sparse
requires `FlagEmbedding` and a local model download.
