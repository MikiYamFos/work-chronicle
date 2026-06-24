# Handoff — 2026-06-21 (session 2)

## What this session fixed (in order)

1. **Prompt structure** — removed conflicting patches (argument stated twice, defensive notes framing, redundant opener rules in BEFORE RETURNING)
2. **Argument-first evidence** — `build_argument_evidence()` in db.py replaces the angle-based second pass. Scores sentences 70% argument + 30% JD, greedy MMR diversity (max 1 sentence per source paragraph). Returns 8 flat sentences, not angle blocks.
3. **Evidence cache** — `jd_evidence_cache` table keyed by `(jd_hash, library_checksum)`. Memoizes argument + evidence across runs of the same JD. Invalidates when library changes.
4. **Full-library prompt structure** — bio is block 1 (cached, always hits), full `role_paragraphs` library is block 2 (cached, hits when library unchanged). JD-specific content uncached. Stage 1 Haiku paragraph selection removed entirely.
5. **[VOICE]/[DRAFT] library labeling** — `library_refined.md` (layer 1, LLM-generated Q&A drafts) marked `[DRAFT — FACTS ONLY]`. `library_approved.md` (layer 0) and `library.md` (layer 2, seed-written) marked `[VOICE]`. Model told explicitly: use DRAFT paragraphs for facts, not voice.
6. **Voice examples in Q&A draft** — `_voice_examples_block()` in build.py samples 2-3 excerpts from `[VOICE]` paragraphs at system prompt time AND at draft time. Model sees actual writing register before drafting, not just rules about it. Wired through `_qa_session` in cli.py.

## Root cause of 100% bad letters (confirmed this session)

- `library_refined.md` contains LLM-drafted paragraphs from Q&A sessions. User approved them at the end of Q&A but the model's refinement of their raw answers introduced wooden LLM voice.
- The generation prompt was using these as voice reference — the model imitated LLM prose and produced more LLM prose. Circular.
- `library.md` (seed-letter, user wrote entirely) and `library_approved.md` (user line-edited) are the clean voice.
- Fix: [VOICE]/[DRAFT] labeling + voice examples in draft step.

## Before the demo — what YOU need to do

1. **Run `clio edit-library`** — go through `library_refined.md` paragraphs one at a time. In your editor, rewrite each in your actual voice using the facts in it. Approve into `library_approved.md`. Each approved paragraph flips from `[DRAFT]` to `[VOICE]`.  You don't need all 36 — 8-10 covering distinct experiences is enough to demo.

2. **Write `voice.md`** — a positive description of how you write. Not rules about what not to do. Patterns: how you open paragraphs, sentence length, level of formality, how you name things, how you handle technical specifics. One to two pages. Load it into the Q&A system prompt as the positive voice spec alongside the negative rules. (This is the technique from https://github.com/alexeygrigorev/telegram-writing-assistant — see `process/style-curation.md` for format reference.)

3. **Run `clio sync`** after line-editing to rebuild embeddings with the new approved paragraphs.

4. **Test a generation** — `clio generate <jd>`. Check console for "Cache hit" or "Argument evidence: 8 sentences (argument-first)". Read the letter: do body paragraphs pull from different stories? Does the argument stay consistent? Does it sound like you?

## What's NOT done yet

- `voice.md` file not written — the single highest-leverage thing for demo quality
- `clio outline` → `clio generate --from-outline` path not tested end-to-end
- `build_user_message_stage2` still exists but is now the no-Voyage-key fallback only

---

## Branch: `flow_bugs`

## Critical principle — DO NOT VIOLATE

**Diagnose root cause before writing any code. Never patch a symptom.**
When the user reports a pattern failure (judge blocking, rewrites ignoring input, content truncated), find
the actual structural cause in the code and fix that. Do not increase a number, add a filter, or inject
a workaround without understanding exactly what the flow does and why the symptom appears. The user pays
for every model call and cannot afford broken runs caused by wrong fixes.

---

## ✅ DONE (2026-06-21): Two-stage paragraph-commit generation

### What was implemented

**`coverletter/select.py`** (new file)
- `select_paragraphs(paragraphs, argument, jd, api_key)` — Haiku call
- Sends prefiltered library (IDs, sections, first 150 chars) + argument + first 400 chars of JD
- Returns `list[tuple[Paragraph, str]]` — (paragraph, one-sentence reason)
- Falls back to full library if Haiku call fails or returns nothing

**`coverletter/prompt.py`**
- Added `ASSEMBLY MODE` section to `SYSTEM_PROMPT` under `═══ GENERATION MODE ═══`
  - Triggers on `=== SELECTED PARAGRAPHS ===` header in user message
  - Instructs model to assemble FROM source paragraphs, not synthesize across all experiences
  - Anchor phrases must appear verbatim or near-verbatim
- Added `build_user_message_stage2(job_description, selected_paragraphs, ...)` function
  - Uses `=== SELECTED PARAGRAPHS ===` header (triggers ASSEMBLY MODE)
  - No angle_evidence block — argument target included but not 37-sentence evidence
  - Same bio/notes/JD structure as `build_user_message`

**`coverletter/cli.py`**
- Added `select_paragraphs` import from `coverletter.select`
- Added `build_user_message_stage2` import from `coverletter.prompt`
- Both the initial generation path and the regen path (after gap loop) now:
  1. Run Stage 1 selection if `len(corrected) >= 6`
  2. Display selected paragraph IDs + rationale before generating
  3. If `angle_evidence` present → synthesis path with `build_user_message` (selected library subset)
  4. If no `angle_evidence` → assembly path with `build_user_message_stage2`

### Gap-pinning fix (same session, second pass)

Root cause: stage 1 selector scores paragraphs by JD vocabulary overlap. Gap-written
paragraphs are written to address a gap description ("stakeholder communication"), not
the JD's exact wording ("cross-functional collaboration") — so they score low and get cut.

Fix:
- `db.py`: added `get_gap_pinned_hashes(conn, jd_text)` — queries `paragraph_gap_provenance`
  by `jd_hash`, returns `set[str]` of text hashes of paragraphs written for this JD's gaps
- `cli.py`: before prefiltering, query gap-pinned hashes. Split `role_paragraphs` into
  pinned + rest. Prefilter only rest with reduced budget. `filtered = pinned + rest_filtered`.
  Gap paragraphs bypass scoring entirely.
- `select.py`: `select_paragraphs()` now accepts `pinned_ids: set[object]`. Marks pinned
  paragraphs with `[PINNED — written for this JD's gap]` in the selector prompt. After
  getting the selector's response, enforces: any pinned paragraph not returned gets appended.
- Both initial generation and regen paths pass `_gap_pinned_ids` to the selector.

### What to test
- Run with Voyage key (DB path): should see "Pinning N gap-written paragraph(s)" and
  "Stage 1: selected N of M paragraphs" before "Generating..."
- Write a gap paragraph for a job, come back to the same JD — that paragraph should be pinned
- Run without Voyage key: stage 1 still runs, no gap pinning (no DB)
- Run with `--fast`: same paths, just no alignment report
- Check that regen path also shows stage 1 output

### Known gaps / next
- No user override for stage 1 selection (ask user if they want to swap a paragraph)
- `top_n` config could be reduced to 8-10 now that stage 1 narrows further
- Could show full selected paragraph text (not just ID) for user review before generating

---

## Next major work (remaining): Two-stage paragraph-commit generation (original description below)

### The problem (root cause, not symptom)

The letter generation model currently receives:
- Full library (30+ paragraphs after prefilter)
- 37-sentence argument evidence block
- Bio, notes, JD

With 200K+ tokens of context, the model synthesizes prose from the evidence block rather than lifting
from the user's library paragraphs. The result: letters that violate rules, ignore the user's voice,
and don't use the material they wrote. This is structural — no amount of prompting fixes a model that
has too much latitude and too much context.

### The fix: two-stage approach

**Stage 1 — Paragraph selection** (cheap, small context)
A separate model call (Haiku) receives the prefiltered library (8-10 paragraphs max) plus the JD and
argument target. It returns a JSON list of 4-6 paragraph IDs it will use, with a one-sentence rationale
for each. This commits the model to specific source material before writing begins.

**Stage 2 — Assembly from selected paragraphs only** (smaller generation context)
The letter writer receives ONLY the selected paragraphs (not the full library), the notes, bio, and JD.
It writes the letter by assembling and lightly connecting those paragraphs — not synthesizing from
scratch. The argument evidence block is either removed or reduced to the angle priority list only.

### What this fixes
- **Voice**: Model writes FROM the user's paragraphs, not over them
- **Cost**: Generation context drops from ~200K to ~40K tokens
- **Violations**: Less wandering = fewer invented constructions
- **Library ignored**: Model commits to specific paragraphs before generation begins

### Key files to touch
- `coverletter/prompt.py`: New `build_user_message_stage2()` that takes `selected_paragraphs: list[int]`
  instead of full library; removes or minimizes argument evidence block; emphasizes assembly over synthesis
- `coverletter/align.py` or new `coverletter/select.py`: Stage 1 selection call — takes prefiltered
  paragraphs + argument + JD, returns list of paragraph IDs with rationale
- `coverletter/cli.py`: Wire stage 1 → stage 2 in the generation path; show user which paragraphs were
  selected (ID + section) before generating so they can override if needed
- `SYSTEM_PROMPT`: Add explicit "ASSEMBLY MODE" instruction — write FROM the source paragraphs; your
  job is to connect them, not rewrite them; anchor phrases from source paragraphs must appear verbatim

### Selection prompt design
The stage 1 selector should receive:
```
=== ARGUMENT TARGET ===
[argument]

=== JD REQUIREMENTS ===
[top 400 chars of JD]

=== AVAILABLE PARAGRAPHS ===
[ID] Role / Section [angle=X strength=Y]
[first 150 chars of text]
...

Select 4-6 paragraphs that together make this argument. Return JSON:
{"selected": [{"id": N, "reason": "one sentence"}]}
```

### What NOT to do
- Do not use GraphRAG or knowledge graphs — the library is already structured; the problem is
  generation latitude, not retrieval quality
- Do not add more rules to SYSTEM_PROMPT — the system prompt is already too long; more rules
  make the model worse, not better
- Do not increase prefilter `top_n` — it should be reduced (8-10), not increased

---

## Fixes this session (2026-06-21)

### QA question judge — conceptual questions for competence gaps (`question_judge.py`)
- `_JUDGE_SYSTEM` COMPETENCE/TOOL GAPS had "What does the Airflow DAG do?" as a GOOD example
- Model interpreted this as permission to ask "What does the gold layer enforce?" — textbook question
- Fix: replaced example with three employer-specific examples; added explicit BAD category for
  conceptual/definitional questions; added test: "does the question reference something specific
  the person said they built or owned?"

### Coach revision — prose vs instruction separation (`coach.py`)
- `REWRITE_SYSTEM` instruction "USE IT" caused model to treat user meta-commentary as letter prose
- "This is a great fit for me" (explaining what to argue) ended up in the letter
- Fix: added instruction to separate reactions/instructions from actual prose content the user wants
  in the letter; use only the prose parts

### APPLICATION NOTES repositioned (`prompt.py`)
- Notes were buried in `library_lines` (the first, large cached block) — the model read the
  argument target right before the JD and used that for the opener, ignoring the notes
- Fix: notes removed from `library_lines` and added as a separate block AFTER bio, BEFORE argument
  target — now in recency position when the opener is written

### Opener instruction rewritten with positive example (`prompt.py`)
- Opener rule was all negative constraints — model ignored them in favor of argument framing
- Fix: added explicit "THE OPENER DOES NOT START FROM THE ARGUMENT" carve-out; added positive
  examples of what a good opener looks like when notes say "I believe in the mission"; added
  explicit bad examples to reject ("Healthcare data is where wrong numbers...", "That is exactly
  the kind of environment")
- BEFORE RETURNING check 4 updated to flag openers that start from the argument

### New hard checks in `_hard_check()` (`verify.py`)
All of these previously survived generation and were never blocked:
- **Any sentence starting with "That"**: scans all sentences (not just paragraph openers);
  "That is exactly the kind of environment" now caught
- **Fake contrast "not X; it was/is Y"**: regex catches "Correctness was not a goal I aimed for;
  it was a baseline I enforced" and all variants
- **Opener first sentence has no "I"**: opener must open from the candidate's perspective; catches
  "Healthcare data is where wrong numbers have consequences..." style openers
- **New banned phrases**: "is where wrong numbers", "carries a particular kind of weight",
  "that is exactly the kind of environment", "at every stop i was the person"

### Seniority gap prompt made legible (`cli.py`)
- `[W]rite paragraph  [N]ote for regen  [S]kip` was completely opaque — user had no idea what
  each choice did
- Fix: added explanation lines before the prompt:
  - W = open Q&A to write a new paragraph on this topic
  - N = pass this as framing direction to the letter (no Q&A — uses content already in library)
  - S = skip

---

## Fixes from 2026-06-17 session (still in effect)

### Gap loop display overhaul (`cli.py` `_gap_loop`)
- Library-covered gaps were numbered alongside actionable ones — confusing
- Seniority gaps routed straight to Q&A even when framing existing content was all that was needed
- Fix: library-covered gaps shown as "Pulled in on regen (N):" — no numbers, separate section
- Fix: actionable gaps renumbered from 1
- Fix: seniority gaps now offer [W]rite / [N]ote / [S]kip

### Argument generator missing candidate motivation (`align.py`)
- `generate_argument()` was only passing `profile.as_goals_text()` — no working_style, values, differentiators
- Result: argument always came out as credential list with no mission connection
- Fix: candidate section now includes goals + working_style + values + differentiators

### Opener instruction — previous session
- Opener rule was stated three times with contradictory language
- ASSEMBLY RULES STEP A told model to scan JD for gaps — produced apology sentences
- Fix: single opener rule, SYNTHESIS MODE / LIBRARY MODE explicitly separated

### Hard checks (prior session)
- Progressive tense regex: catches "have been building", "was building", etc.
- Auto-fix flow: `_hard_check` runs post-generation, auto-proposes fix before rendering

---

## ✅ DONE (2026-06-21): driving_angle bug + paragraph_angles integrity

### driving_angle fix (`cli.py`)
`_gap_loop` was passing `driving_angle=kind` where `kind = "JD"` or `"Seniority"` (the loop
type). Column comment says "canonical angle the gap was filed under." Fix: call
`_suggest_angle(gap, cfg.voyage_api_key)` to derive the canonical angle from the gap text
before entering Q&A, then pass that as `driving_angle`. `paragraph_gap_provenance` was empty
(0 rows) so no existing data was corrupted.

### paragraph_angles explosion fix (`db.py`)
`assign_angles_canonical` had `secondary_threshold=0.25` and inserted a secondary row for
every angle above that threshold. With 18 angles and generic engineering text, nearly every
paragraph scored ≥0.25 against nearly every angle → avg 15 assignments per paragraph, 1803
rows for 119 paragraphs. Made angle-based retrieval meaningless.

Fix:
- Removed secondary angle insertion from `assign_angles_canonical` entirely. Only primary
  (top-1 above threshold) is assigned. One auto row per paragraph, invariant enforced by
  DELETE-before-INSERT.
- Human-labeled rows (angle_auto=0): auto rows deleted entirely when human primary exists.
- Added `purge_secondary_angles(conn)` to `db.py` — deletes `angle_auto=1 AND is_primary=0`.
- Added `clio fix-angles` command: purges secondaries + re-runs primary assignment + reports.

Ran `clio fix-angles` on live DB:
  Before: 1803 rows (187 primary) → After: 155 rows (122 primary, 0 auto secondaries)
  Invariant verified: every active paragraph has exactly 1 primary, no paragraph has >1.

---

## ✅ DONE (2026-06-21): Opener argument-claim leak fix

### The failure pattern
Opener starts correctly (personal connection, mission alignment) then adds evidence
claims as sentences 3-4: "I have built platforms where wrong data meant X, Y, Z. The
ownership instincts I developed are what this role requires." Those are body paragraph
sentences. They don't belong in the opener. The old rule said "does not START from the
argument" — model interpreted this as "start with something else, then bring in the
argument." The check only caught openers that began with argument framing.

### Fixes

**`prompt.py` — SYSTEM_PROMPT**
- Rule changed from "THE OPENER DOES NOT START FROM THE ARGUMENT" to "THE OPENER
  CONTAINS NO ARGUMENT CLAIMS" with explicit description of the failure mode
- Added bad example: two sentences of connection followed by two argument claims,
  showing that the last two belong in the first body paragraph
- Check #4 rewritten: now says "read each sentence of the opener — if it could open
  a body paragraph, move it or cut it." No longer just checks how the opener begins.

**`verify.py` — `_hard_check()`**
- New check: opener sentences 3+ that match evidence-claim patterns
  ("I have built...", "I have spent...", "The [ownership/instincts/standards] I...")
  are flagged as argument leakage into the opener
- The Talkiatry letter's bad sentence ("I have built platforms where wrong data...") 
  now gets caught before display and triggers the auto-fix flow

**`pyproject.toml` (`work-chronicle`)**
- Added `[tool.setuptools] packages = []` — fixes build crash caused by setuptools
  discovering `coverletter/` and `jds/` as packages in the work-chronicle wrapper project

---

## ✅ DONE (2026-06-21): Prompt structure cleanup — removed conflicting patches

### What was wrong
The prompt had accumulated conflicting and noisy patches:
1. Argument stated twice — GOVERNING CONSTRAINT + ARGUMENT REMINDER before the JD
2. Notes framing said "these do not add new argument threads" — defensive patch that tells model
   what not to do while still passing the multi-topic notes wholesale
3. SYSTEM_PROMPT opener section had a separate "APPLICATION NOTES do not add argument threads"
   paragraph — same defensive patch duplicated in the system prompt
4. Evidence block had 37 sentences from ALL paragraphs but stage 1 already selected 6 —
   the evidence didn't match the library the model was writing from

### Fixes

**`prompt.py` — SYSTEM_PROMPT**
- Removed the "APPLICATION NOTES do not add new argument threads" paragraph from opener section
- Replaced with clean positive: "use opener-relevant observation for first sentence; rest is tone"
- Shortened BEFORE RETURNING check #4 — removed repetitive overlap with the opener rules

**`prompt.py` — `build_user_message()` and `build_user_message_stage2()`**
- Removed `=== ARGUMENT REMINDER — READ BEFORE WRITING ===` block from both functions
  (argument stated once as GOVERNING CONSTRAINT is enough; second statement was noise)
- Replaced notes framing from defensive "these do not add argument threads" to positive:
  "use the opener-relevant observation as the first sentence; rest is tone signals"

**`cli.py` — evidence filtering after stage 1 selection**
- After stage 1 narrows to N paragraphs, filter `angle_evidence` to only sentences whose
  `(role, section)` matches the selected set
- Before: model saw 37 evidence sentences from 20+ source paragraphs but only 6 paragraphs
- After: evidence sentences come only from the paragraphs the model is actually writing from
- Same filtering applied to regen path

---

## ✅ DONE (2026-06-21): Argument-first evidence selection (build_argument_evidence)

### The problem
`build_angle_evidence` selected sentences by ranking ANGLES against the JD, then pulling 3
sentences per angle. This produced 30-37 sentences organized by angle — not by the argument.
The model wrote a "tour of angles" instead of building one argument from diverse evidence.
Also: sending 6 full paragraphs (stage 1 output) and asking the model to assemble from them
lost the point — the library paragraphs contain multiple interpretable facets; copying them
whole collapses them to one use.

### The fix: build_argument_evidence() in db.py
New function replaces the second (argument-focused) pass of build_angle_evidence.

**Scoring:** each sentence scored against argument (70%) + JD (30%). Argument is the
primary relevance signal — JD refines to this role's specific requirements.

**Selection (greedy MMR with diversity):**
- After each pick, penalize other sentences from the same paragraph (×0.15) — forces
  the model to draw from different stories
- Penalize same (role, section) experience if already used twice (×0.20) or once (×0.60)
- This enforces: 8 sentences from 6-8 different experiences, not 3 sentences from the
  same paragraph proving the same thing

**Output:** flat list of 8 dicts — no angle organization. Each entry has:
  text, role, section, angle (label only), argument_score, source_paragraph, context_after

**Why flat:** the argument governs the letter, not the angles. The angle tag is retained as
a label ("this sentence proves ownership") but doesn't drive paragraph structure.

### Flow in cli.py
1. First pass: build_angle_evidence (no argument yet) → evidence_sentences for generate_argument
2. Argument derived from evidence_sentences
3. Second pass: build_argument_evidence(argument, jd) → 8 sentences → what the writer gets
4. Regen path: same — build_argument_evidence with provisional_argument

### prompt.py changes
- build_user_message: detects flat vs legacy evidence format (key: "argument_score")
- Flat format rendered as numbered list with context sentence and source paragraph
- Writer instruction: "synthesize across all of them — do not write one paragraph per sentence"
- SYNTHESIS MODE in SYSTEM_PROMPT updated to match flat evidence semantics

---

## ✅ DONE (2026-06-21): Evidence cache + full-library prompt structure

### The problem
Every `clio generate` on the same JD re-ran: Voyage embed call (evidence), Haiku call
(argument), Haiku call (stage 1 paragraph selection), Sonnet (generation). None of the
intermediate results were stored. Same JD + same library = same outputs every time.

Also: the prompt cached a SELECTED subset of paragraphs (6, different per application),
so the cache never hit across applications — the bio block came after the library block
and was never independently cached.

### Fixes

**`db.py` — `jd_evidence_cache` table + helpers**
- New table: `PRIMARY KEY (jd_hash, library_checksum)` — invalidates when library changes
- `get_library_checksum(conn)` — sha256 of all active paragraph text_hashes
- `get_cached_evidence(conn, jd_hash, lib_checksum)` → `(argument, evidence_list) | None`
- `store_cached_evidence(conn, jd_hash, lib_checksum, argument, evidence)`

**`cli.py` — derivation path restructured around cache**
- Computes `_jd_hash` + `_lib_checksum` before any model calls
- Cache hit: loads argument + 8 evidence sentences, skips all derivation model calls
- Cache miss: runs full pipeline (build_angle_evidence pass 1 → generate_argument →
  build_argument_evidence pass 2), then stores result
- Regen after gap loop: always rebuilds evidence (library changed), stores with new checksum
- Stage 1 (`select_paragraphs` Haiku call) removed entirely — evidence selection replaces it
- `_library_for_prompt = role_paragraphs` — full library passed to build_user_message,
  not a selected subset

**`prompt.py` — block order + SYSTEM_PROMPT**
- Bio block is now block 1 (cached) — most stable, never changes → always hits
- Library block is now block 2 (cached) — stable per candidate → hits whenever library unchanged
- JD-specific content (evidence, argument, notes, JD) is uncached blocks 3+
- Library header now says explicitly: "voice reference — use evidence to know WHAT to argue,
  library to know HOW to sound"
- SYSTEM_PROMPT GENERATION MODE: ASSEMBLY MODE removed (stage 1 gone), SYNTHESIS MODE updated
  to say evidence = factual constraint, library = voice

### Cost structure after this change
- First run of a JD: full derivation cost (2 Voyage calls, 1 Haiku)
- Second run same JD + same library: zero derivation cost (cache hit)
- Each generation: prompt cache hit on bio (block 1) and library (block 2) if library unchanged
- The library block is now ~100 paragraphs × 200 words = ~20K tokens cached — hits every time

---

## Known issues / still to watch

- `clio outline` → `clio generate --from-outline` path not tested end-to-end
- Paragraphs without canonical angles: bulk-assign still needed
- The coaching judge (sentence coach) has separate context — not the same as QA judge
- Verb "actually" in draft paragraphs: sometimes survives because it appears in the user's original
  text and the draft fidelity coach preserves it; hard check catches it in letters but not in library

---

## Opener rule (canonical, do not regress)

The opener expresses CONNECTION between candidate and employer — not one then the other, but both
at once. Neither is introduced and then handed off.

**Source**: APPLICATION NOTES if present (in recency position, separate block before argument target).
If notes say "I believe in the mission" → first sentence uses that language, not paraphrased.
If no notes: read CANDIDATE GOALS and WORKING STYLE.

**Never**: start from argument framing, stakes of the employer's domain, or "Employer is asking for
someone who..." The opener starts from the candidate's genuine reason for writing.

**Hard-blocked**: opener first sentence with no "I"; sentences starting with "That"; fake contrast.
