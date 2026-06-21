# Handoff — 2026-06-17

## Branch: `flow_bugs`

## Critical principle — DO NOT VIOLATE

**Diagnose root cause before writing any code. Never patch a symptom.**
When the user reports a pattern failure (judge blocking, rewrites ignoring input, content truncated), find
the actual structural cause in the code and fix that. Do not increase a number, add a filter, or inject
a workaround without understanding exactly what the flow does and why the symptom appears. The user pays
for every model call and cannot afford broken runs caused by wrong fixes.

---

## Fixes this session (2026-06-17)

### Gap loop display overhaul (`cli.py` `_gap_loop`)
- Library-covered gaps were numbered alongside actionable ones — confusing because typing "all"
  only processed actionable items but the user didn't know which numbers those were
- Seniority gaps were routed straight to Q&A ("what experience to draw on?") even when the
  issue was framing existing content more explicitly, not missing material — the user had no
  idea what paragraph to write
- Fix: library-covered gaps shown separately as "Pulled in on regen (N):" bullet list — no
  numbers, no action needed, completely separate from the actionable section
- Fix: actionable gaps renumbered starting from 1 so "1,2" maps to exactly what user sees
- Fix: seniority gaps now offer [W]rite paragraph / [N]ote for regen / [S]kip — "Note" adds
  the gap to covered_gaps so regen receives it as editorial direction without opening Q&A

### Argument generator missing candidate motivation (`align.py`)
- `generate_argument()` was passing only `profile.as_goals_text()` as the candidate section
- working_style, values, and differentiators were not included — the model had no access to
  the candidate's drives, what draws them to certain work, or their perspective on data quality
- Result: argument always came out as a purely technical credential list with no connection
  to employer mission, so the letter opener had nothing authentic to open from
- Fix: candidate section now includes goals + working_style + values + differentiators
- ARGUMENT_PROMPT updated: candidate clause rules now explicitly instruct the model to read
  the candidate's drives and working style to find mission overlap, not just list credentials

### ARGUMENT_PROMPT mission connection rule added (`align.py`)
- Employer clause already had a rule to read the full JD including mission sections (prior session)
- Candidate clause had no corresponding instruction — model defaulted to listing outputs
- Fix: added explicit instruction to read working style and values, find overlap with employer
  mission, and use that overlap as the argument (not a credential list)

### SYSTEM_PROMPT bio block framing (`prompt.py`)
- Bio block was labeled "for biographical prompts" — model skipped it when writing letters
- Fix: relabeled as source of genuine opener connection; explicit instruction to read before
  writing the opener

### VERIFY_PROMPT opener check (`verify.py`)
- Added check 1: opener paragraph — flags generic industry statements with no candidate present,
  or opener containing previous employer names

### Hard check additions (`verify.py`)
- Progressive tense regex: catches "have been building", "was building", etc.
- Auto-fix flow in cli.py: `_hard_check` runs post-generation; if violations found,
  auto-propose-fix before rendering the letter to user

### Propose-fix output constraint (`cli.py`)
- Model was leaking chain-of-thought ("Wait. Let me re-read...") into propose-fix output
- Fix: feedback string now ends with explicit output-only constraint

---

## Prior session fixes (still in effect)

### Revision context truncation (`build.py` ~line 923)
- `_revise_paragraph` (direct revision bypass) was truncating user messages to 600 chars, total context to 2000
- Fix: 2000 chars per message, 6000 total

### Judge context — wrong approach then correct fix (`build.py`)
- Initial (wrong) fix: bumped `[-4000:]` to `[-12000:]` — still the full bloated conversation
- User identified the real design error: the judge only needs to know what the user actually said
- Correct fix: `_build_judge_context` now includes ONLY user-role messages that are real answers
  — skips `[JUDGE:...]` and `[DRAFT JUDGE:...]` injections (code noise, not user content)
  — skips non-string content (tool results)
  — no total truncation: user answers are small, the judge gets all of them
- Both instances of `_build_judge_context` in build.py fixed identically (lines ~569 and ~688)

### Coaching redirect loses prior content (`cli.py` `_coaching_pass`)
- When user hit [R]edirect, `new_direction` was passed to `rewrite_sentence` with no memory of the
  original direction — "keep more of my response" had no response to reference
- Also: redirect used `input()` (single-line) instead of `_read_multiline`
- Fix: redirect now accumulates `f"Prior direction: {user_input}\n\nPrevious rewrite: {rewritten}\n\nNew direction: {new_direction}"`
  and updates `user_input` so each subsequent redirect carries the full history
- Fix: `_read_multiline` instead of `input()` for the redirect prompt

### Coaching constrained to single sentence (`coach.py`)
- `REWRITE_SYSTEM` said "rewrite a single sentence" — output was always forced to one sentence
  even when the original content or user's direction spanned multiple sentences
- `REWRITE_PROMPT` and `REWRITE_DIRECTION` also said "sentence" throughout
- Fix: all three updated to "passage" — output is however many sentences the content requires
- `max_tokens` bumped 256 → 512

---

## Prior session fixes (still in effect)

### SYSTEM_PROMPT full rewrite (`prompt.py`)
- Prior prompt had opener rule stated THREE times with contradictory language
- ASSEMBLY RULES STEP A told model to scan JD for gaps — produced gap apology sentences
- Rewrite: single opener rule, SYNTHESIS MODE and LIBRARY MODE explicitly separated,
  "do NOT scan the JD for gaps" in synthesis mode, foundational "ARGUMENT IS THE COMPASS" section

### Gap apology logic (`cli.py`, `prompt.py`)
- Gaps user skips after seeing them → `skipped_gap_topics` → `unaddressed_gaps` param
  → model may acknowledge one sentence only
- Gaps model infers from JD on its own → hard banned

### `_gap_has_library_ref` negation fix (`cli.py`)
- Was matching `paragraph [N]` inside "paragraph [4] does not cover this"
- Fix: checks 30 chars before citation for negation words

### Semantic pre-classification removed (`cli.py`)
- Semantic search was matching Snowflake gap to Redshift/BigQuery paragraph
- Fix: only explicit alignment citations mark a gap as library-covered

### 500 retry (`build.py`)
- `_call_model` now retries up to 3 times with exponential backoff on status 500

### Argument prompt (`align.py`)
- False comparisons banned in thesis
- Stakes-grounding required in candidate clause

### Coaching loop delete (`cli.py`)
- Added `[D]elete` option at initial prompt and after seeing a rewrite

---

## Still to watch
- Letter quality with new SYSTEM_PROMPT — needs a clean end-to-end test run
- `driving_angle` in provenance passes gap kind not canonical angle name
- `clio outline` → `clio generate --from-outline` path not tested end-to-end
- Paragraphs without canonical angles: bulk-assign still needed
- Coaching judge (the sentence coach `analyze_letter`) has separate context — not the same as QA judge
