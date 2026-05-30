# Roadmap

## Recently shipped

### Gap loop improvements (May 2026)

- **`all` option**: type `all` or `a` at the gap selection prompt to address every actionable gap in sequence, instead of entering numbers individually
- **Ctrl-C exits the gap loop**: pressing Ctrl-C during a Q&A session stops the loop and returns to the regeneration prompt. Previously it silently moved to the next gap. Any paragraphs saved before the interrupt are kept.
- **Editor escape hatch in Q&A**: type `e` + Enter on a blank line to open `$EDITOR` for your answer. This bypasses the macOS PTY canonical mode ~1024 byte line limit that was cutting off long answers mid-word.

### Library coverage detection (May 2026)

Removed the LLM-based `(library: [N])` tagging from the alignment prompt. Library coverage is now detected in Python using BM25 (`rank_bm25`) against the filtered paragraph library. This runs after the alignment LLM call, is deterministic, and catches matches the model was inconsistently missing. Falls back to term-overlap if `rank_bm25` is not installed.

The `has_library_coverage()` function and BM25 post-processing live in `align.py:_detect_library_coverage()`.

### Experience matcher reliability (May 2026)

The gap-to-experience matcher in `experiences.py` was matching on stop words, causing false positives — a gap about "dbt and Airflow" would match an unrelated experience that happened to share the word "and". Fixed by:

- `_words()` now filters a stop word list before scoring
- Minimum match threshold raised from `> 0` to `>= 2` meaningful overlapping words

### Q&A draft quality rules (May 2026)

- `BUILD_SYSTEM` in `build.py` now explicitly bars the model from copying language or phrases from library search results into new drafts. Library search is for reference (what's already documented) not source material for the new paragraph.
- `force_draft()` now sends a comprehensive rules reminder covering first-sentence structure, no-invention constraint, voice preservation, and banned constructs.
- The 120-word "rich answer" threshold was removed — it was an arbitrary cap that forced premature drafts on answers that weren't yet complete.

---

## Issue #1 — Multi-provider support

The tool is currently Anthropic-only. Every API call uses the Anthropic SDK directly,
model aliases map to Claude model strings, and prompt caching uses Anthropic-specific
`cache_control` message blocks. This is the top priority to fix.

### Why this is hard

Prompt caching isn't a detail — it's what makes the economics work. The paragraph
library (12k+ tokens) gets sent on every API call in a session. Caching it after the
first call drops subsequent call costs to ~10% (Anthropic) or ~50% (OpenAI automatic).
Without caching, a full letter session costs 3–5x more.

A generic wrapper like LiteLLM doesn't solve this — its caching abstraction is for
full response memoization, not provider-level prompt prefix caching. Each provider
exposes caching differently and needs its own implementation.

### Target providers

**Mistral**
- Explicit caching API, most similar to Anthropic's model
- Strong writing quality, competitive pricing
- European data residency — meaningful for users with GDPR concerns
- Implement second (after Anthropic) to stress-test the abstraction

**Cohere**
- Interesting because it collapses two dependencies into one: Command R+ for
  generation AND Cohere embeddings to replace Voyage AI
- Currently the tool requires two API keys (Anthropic + Voyage). Cohere users
  would need only one
- Retrieval-trained models are relevant to how this tool works (library search
  drives paragraph selection)

**Ollama**
- Local inference — zero API cost, nothing leaves the machine
- Career material is sensitive; some users will care a lot about this
- Caching works differently (context stays in memory, keep-alive handles it)
- OpenAI-compatible locally, no auth
- The most architecturally different provider — implement third to find
  abstraction gaps before adding more

**Together AI / Fireworks AI**
- Hosts open source models (Llama, Mixtral, etc.) at low cost
- Good fit for users who want model transparency or want to run open weights
- To evaluate: writing quality for this specific task (cover letter generation
  requires nuance that not all open source models handle well)

### Planned architecture

A thin `Provider` protocol that each provider implements:

```python
class Provider(Protocol):
    def complete(self, system: str, messages: list, tools: list | None) -> Response: ...
    def stream(self, system: str, messages: list) -> Iterator[str]: ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...  # replaces Voyage
    def supports_caching(self) -> bool: ...
    def wrap_cached(self, content: str) -> dict: ...  # provider-specific cache block
```

Each provider handles caching in its own way:
- **Anthropic**: inject `cache_control: {"type": "ephemeral"}` on library block
- **Mistral**: explicit cache API call before session, reference by ID
- **OpenAI**: automatic prefix caching, just structure prompts correctly (library first)
- **Ollama**: keep-alive, no explicit caching needed
- **Others**: degrade gracefully — send full context, costs more, still works

### Also needed

- The question judge is hardcoded to `claude-haiku-4-5-20251001` — needs to become
  a configurable cheap model per provider
- Voyage AI embedding dependency needs to become optional with a provider-native
  fallback (Cohere embeddings, Ollama embeddings, or BM25 keyword fallback as last resort)
- `COVERLETTER_MODEL` env var would accept provider-prefixed model names:
  `anthropic/claude-sonnet-4-6`, `mistral/mistral-large-latest`, `ollama/llama3.3`, etc.

---

## Issue #2 — `coverletter intake` command

A structured cold-start interview that builds library and profile simultaneously,
for users who have no existing material and don't know where to start. The current
flow (seed → profile) requires existing material or willingness to freeform Q&A.
Intake would be a guided session that walks someone through their career in order,
extracts paragraphs as it goes, and produces a profile at the end.

---

## Issue #4 — Perspective paragraphs: through-lines, pivots, and reframes *(partially implemented)*

### What's shipped

- `coverletter reflect` command: captures through-line, pivot, reframe, or synthesis through Q&A. Angle-specific context — through-line Q&A is explicitly not a drill-into-one-job session. Saves to `library_refined.md` with `via=reflect`.
- Perspective paragraphs are pinned in prefilter (never filtered out by relevance scoring) and labeled `[NARRATIVE FRAME]` in the library block so the assembler knows their role.
- Alignment report surfaces a `perspective_note` when no perspective paragraph exists in the filtered library: "No through-line, pivot, reframe, or synthesis paragraph. The letter has evidence but no narrative frame."
- `--angle` and `--about` flags to skip the topic and angle prompts.
- `[CLOSER ONLY]` label on paragraphs with `tone=closer` or under "Why This Role"/"Closing" sections — the assembler is explicitly forbidden from placing these as the first or second body paragraph.

### What's still needed

### The problem

The tool is good at capturing evidence — what you built, what you owned, what broke, what
shipped. It is bad at capturing interpretation — the candidate's own understanding of their
arc, what connects disparate experiences, why a non-obvious background is actually exactly
right for a role.

This matters because hiring managers read resumes cold. The through-line that is obvious
to the candidate is invisible on the surface. Without an explicit paragraph that bridges
the gap, the hiring manager makes their own inference — and it's usually wrong.

Examples of where this shows up:

- A data analyst background that feeds directly into data engineering work in ways that
  pure-backend engineers miss — but "analyst" and "engineer" look like different tracks
- A technical degree that doesn't announce itself as technical — the label misleads,
  the actual foundation is real, but the candidate has to explain it or it gets filtered out
- A career pivot where the reason and the through-line make the shift credible, but
  without that context it looks like a random direction change
- Two experiences from different fields that combine into an unusual and specific capability
  that neither field produces on its own

In all of these cases, the candidate's perspective is the thing that makes the experience
legible. The raw facts don't tell the story. The interpretation does.

### The proposed tag: `via=perspective`

Perspective paragraphs are a distinct category in the library. They are not evidence of
a skill — they are the candidate's voice connecting dots. They need to be tagged so the
tool knows to handle them differently.

Proposed meta tag: `angle=through-line | pivot | reframe | synthesis`

- **through-line**: the consistent thread running across the whole arc — what has always
  been true about how you work or what you care about, even across different titles and orgs
- **pivot**: a deliberate change in direction with a reason. Not just "I moved from X to Y"
  but why, and what made it a coherent choice rather than a random one
- **reframe**: same experience, different lens. "When I was doing X it looked like Y, but
  what I was actually building was Z" — often used to make an older or unusual credential
  make sense in a new context
- **synthesis**: two seemingly unrelated experiences that combine into something unusual.
  The capability that only exists because of the specific combination of paths taken

### Why the Q&A must be different

The standard `build` Q&A goes after concrete evidence: what broke, who depended on it,
what changed after it shipped. Those questions don't work for perspective paragraphs.

Perspective Q&A still follows the same rule as regular build Q&A: go after a specific
moment or decision, not the insight directly. The perspective emerges from the answer.

Good perspective questions look like:

- "What is one thing your degree actually trained you to do — concretely — that shows up
  in how you work now?"
- "What were you actually doing in the previous role right before you made the move?"
- "What could you not do in that role that you wanted to be able to do?"
- "What did you start teaching yourself, and why that thing specifically?"

Bad perspective questions ask for the reflection directly:
- "What did working as an analyst teach you?" → produces generic clichés
- "What makes your background unique?" → produces performance, not evidence
- "How do your experiences connect?" → the candidate can't answer this without
  already having done the synthesis the question is trying to surface

The Q&A session needs to hold space for longer, more worked-through answers. The number
of questions should follow the material, not a preset cap.

### How perspective paragraphs work in letter generation

Perspective paragraphs are not supplementary material added after the letter is assembled.
They are the narrative frame — the argument about who this person is and why their arc
makes them right for this role. The thesis depends on them. Evidence paragraphs land
differently when the reader already understands the through-line.

This means perspective paragraphs must be present when the model writes the letter, not
surfaced afterward as a gap. But they are not a separate block sitting above the evidence —
they are woven through. The model sees perspective and evidence together, knows which is
which, and uses the perspective material to shape how evidence is selected and framed.

The prompt structure needs to reflect this:
- Perspective paragraphs are passed alongside evidence paragraphs in the library block
- They are explicitly tagged so the model knows they are narrative frame, not skill proof
- The model is instructed: perspective paragraphs establish the argument; evidence
  paragraphs substantiate it; both are needed and neither replaces the other
- The thesis is generated with awareness of what perspective material exists — a letter
  with a through-line paragraph argues differently than one without

The alignment report should flag when perspective material is absent — not as a JD gap
or seniority signal gap, but as a separate signal: "No through-line or pivot paragraph
present — the letter has evidence but no narrative frame."

### What this connects to

Career shifts specifically: when a candidate re-runs `coverletter profile` and their
goals have changed, that shift is itself a perspective moment worth capturing through
Q&A. The archived old profile is a starting point — "here is what you said you wanted,
here is what changed, here is why" — and the resulting paragraph(s) belong in the
library as pivot or through-line material.

A career shift generates multiple angles, not one paragraph:
- What the previous chapter actually built (through-line)
- What drove the shift and why this direction specifically (pivot)
- What carries over from the previous track and makes the shift credible (synthesis)

### Handling difficulty, constraint, and forces beyond control

Some of the most important experiences to capture are the ones where things were hard
not because of a skill gap but because of structure — a team set up to fail, a mandate
that contradicted itself, a leadership dynamic that made good work impossible. These
experiences shaped the person and they deserve to be in the library, but they require
careful handling.

The wrong framing turns them into complaints or excuses. The right framing shows
judgment — someone who can articulate clearly what the difficulty actually was, what
they tried, and what they learned about what actually moves things is showing more
senior-level thinking than someone who only has success stories.

**Q&A approach for these experiences:**
- The distinction is not concrete vs. reflective — it is open vs. leading
- A leading question imports a frame the person didn't introduce. A good question
  follows the person's own thread — their words, their framing, their emphasis.
- The test: did the concept come from them, or from the questioner?
  - If they described something as a turning point, asking "how did that become the
    turning point?" is following their thread — not leading
  - If they didn't use the word, asking "was that a turning point?" imports a frame
    they may not have intended — that's leading
  - "Was that frustrating?" is leading regardless of context — it introduces an
    emotional interpretation and asks for confirmation
  - "What did that teach you?" is open — the answer could be anything, and it goes
    directly after the learning without presupposing what kind it was
  - "What did you try first?" is open — sequence without suggested outcome
- The Q&A should be willing to go into reflection and learning — that is where the
  richest material lives — as long as the questions follow the person's own thread
  rather than importing the agent's interpretation of what the experience meant
- The writer decides what to do with what surfaces — the Q&A's job is to create
  the conditions for honest reflection, not to steer it toward a particular story

**Coaching pass awareness:**
- Recognize when a paragraph is carrying this kind of weight — systemic difficulty,
  real constraints, forces beyond control — and give honest signal about whether the
  writing is handling it with the right tone
- The target register: grounded and clear, not dramatic, not self-congratulatory,
  not defensive
- A paragraph that articulates difficulty well is more powerful than one that only
  describes success — the coaching pass should recognize this and protect it, not
  flatten it back into generic "overcame challenges" language

### Coaching pass redesign (connects to Issue #4)

The current coaching pass (`coach.py`) is purely mechanical — sentence-level weakness
scanning with no narrative awareness. It needs two passes:

1. **Narrative pass** — read the whole letter to name what it's doing: what story is
   being told, where the power is, where it's leaking. Output this to the writer so
   they can see what the letter is actually arguing before evaluating individual sentences.

2. **Sentence pass** — evaluate sentences against the narrative understanding. Not just
   "this is vague" but "this sentence undercuts the resilience story running through
   paragraphs 2 and 3" or "this is where the real learning moment is but it's buried
   in the middle of the sentence."

The coaching pass should reflect back to the writer what their letter is doing — not
as validation, but as useful signal that helps them make real decisions about the letter.

### Q&A narrative awareness

When a Q&A answer contains something with weight — a real difficulty, a genuine
decision, a moment that cost something — the agent should ask toward the specificity
of that moment rather than moving to the next question. Concrete follow-ups only:
"What did you do next?" or "What were you working with at that point?" The depth
comes from staying in the moment, not from asking the person to reflect on its meaning.

### Also needed

- The profile archiving added in the seniority_signals work (May 2026) creates a natural
  trigger: when an archived profile exists and goals have changed, offer a dedicated
  perspective Q&A session before saving the new profile
- `show-library` should surface perspective paragraphs separately so the candidate can
  see what connective material they have and what's missing

---

## Issue #5 — Short application response quality (`coverletter blurb`)

### The argument model

The blurb command uses a layered model where narrative and evidence work together rather than one driving the other:

- **`working_style` + `values`** are the argument — the thesis about who the candidate is, how they work, what they believe. These are not optional framing or decorative additions. For biographical prompts they are the spine of the response.
- **Library paragraphs** are evidence — they prove specific claims made by the biographical argument. Without the argument, they're a resume. Without the evidence, the argument is just assertion.
- **`avoid`** is values inference — each entry states a constraint but reveals a positive value. The model infers the claim; it doesn't quote the constraint.
- **`goals`** is motivation material — used for "why this role" prompts only, not biographical framing.

The biographical section is positioned as the last thing the model reads before the JD and application prompt — recency matters. The instruction to the model: read the biographical argument first, understand what it claims, then reach into the library for evidence that proves specific claims. Claim + proof is one unit. Do not assemble evidence and add voice on top.

### What's shipped

- Two-input flow: JD (paragraph selection) then application prompt (response type detection) — separate Ctrl-D reads
- Prompt type detection: biographical, behavioral, motivation, approach
- Biographical argument model: `working_style` + `values` as thesis, library as evidence, `avoid` as values inference
- Biographical content positioned after library in message (recency)
- Plain text output block for clean copying
- Revision loop with full conversation history — rejected drafts retained so model knows what was tried
- `BIOGRAPHICAL_GAPS` signal: model outputs gaps when material is thin; tool surfaces them and offers to add `working_style` or `values` entries on the spot
- `values` profile section added: what you believe as a programmer and teammate

### What still needs work

- Behavioral and approach prompts aren't tested as thoroughly as biographical — check that they apply the same voice discipline (use source language, no AI-generated filler)
- When the application prompt has a character/word limit constraint, the model should compress the biographical argument first and preserve voice — currently it drops voice and keeps credentials
- The gap detection is model-produced (BIOGRAPHICAL_GAPS marker) — could be tightened with a Python-level check before generation that warns when working_style + values is below a minimum threshold

---

## Issue #3 — Resume generation integrated into main flow

`coverletter resume` exists but is disconnected from the main letter flow. After
saving a letter, the tool should offer to generate a tailored resume for the same
company in the same step.
