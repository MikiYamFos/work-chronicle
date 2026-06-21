# Handoff — 2026-06-21

## Branch: `flow_bugs`

## Critical principle — DO NOT VIOLATE

**Diagnose root cause before writing any code. Never patch a symptom.**
When the user reports a pattern failure (judge blocking, rewrites ignoring input, content truncated), find
the actual structural cause in the code and fix that. Do not increase a number, add a filter, or inject
a workaround without understanding exactly what the flow does and why the symptom appears. The user pays
for every model call and cannot afford broken runs caused by wrong fixes.

---

## Next major work: Two-stage paragraph-commit generation

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

## Known issues / still to watch

- **Two-stage generation not yet implemented** — this is the next major work (documented above)
- `driving_angle` in provenance passes gap kind not canonical angle name
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
