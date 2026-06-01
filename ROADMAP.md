# Roadmap

## Recently shipped

### Provider expansion + gap-driven build mode (May 2026)

**CohereProvider** — generation (`command-r-plus`), embeddings (`embed-v4.0`), and
reranking (`rerank-v3.5`) on one key. The reranker is a cross-encoder — sees the full
(query, document) pair, not just vector distance. Wired as Stage 3 in the claim
retrieval pipeline (`_category_aware_retrieval`). Canadian provider.

**BGEM3Provider** — local hybrid dense+sparse embeddings via `FlagEmbedding`. BGE-M3
outputs both dense vectors (semantic) and sparse vectors (lexical, BM25-like) from one
model. `hybrid_scores()` fuses them: `alpha * dense_cosine + (1-alpha) * sparse_dot`.
Activated via `EMBED_MODEL=bge-m3` — independent of generation provider. No API key.
Requires `uv add FlagEmbedding` and ~2GB model download on first use.

**Track 1 `embed_prefilter` now fully provider-aware**: BGE-M3 hybrid path, provider-
native dense path, Voyage, BM25 — in priority order. All three call sites in cli.py
updated. `EMBED_MODEL` env var selects embedding provider independently.

**Resume threading into build/QA**: `coverletter build --resume` passes the resume to
the Q&A coach. Coach treats resume bullets as established fact — asks about HOW/WHY/
WHAT CHANGED, not what the resume already states. Also flows through gap-fill sessions
during `coverletter generate`.

**Gap-driven build mode** (`coverletter build --jd`): takes a JD, uses the claims DB
to score which argument categories are covered and which aren't (embed JD → cosine
against category_embeddings and claim embeddings — no LLM scan of the library). Shows
covered/gap breakdown. One small LLM call generates a concrete build prompt per gap.
Walks through targeted Q&A. Syncs new paragraphs to DB after each accepted paragraph.

**`embed_query` moved to `db.py`**: was a private function in `outline.py`. Now public
in `db.py`. `outline._embed_query` delegates to it. No more cross-module private imports.

**`OPENAI_EMBED_MODEL` env var**: lets OpenAI-compat hosts (Regolo, local) specify
which embedding model to use. Defaults to `text-embedding-3-small` for OpenAI proper.

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

## Issue #1 — Multi-provider support *(partially shipped)*

### Understanding the two non-negotiables

**Prompt caching** is not optional. The paragraph library (12k+ tokens) is sent on
every API call. Without caching, a full session costs 3–5× more. Any provider that
can't cache is unviable for regular use.

**Semantic embeddings** are not optional for quality. BM25 keyword fallback works
but is noticeably worse for paragraph selection. Provider-native embeddings (or Voyage
as a standalone service) are required for the tool to work well.

### What's shipped

**Provider abstraction** (`coverletter/provider.py`) — `AnthropicProvider`,
`MistralProvider`, and `OpenAIProvider` implement `complete()`, `stream()`, and
`embed()`. `get_provider(model, api_key)` returns the right one.

**Model naming**: `provider/model-name` prefix. Bare names default to Anthropic.
Aliases: `mistral-large`, `mistral-small`, `gpt-4o`, `gpt-4o-mini` etc.

**Config**: reads the right API key for the active provider. Never requires keys
for providers you're not using.

**Extraction and judging**: `_fast_model_for()` maps each provider to its cheapest
model — Haiku for Anthropic, `mistral-small` for Mistral, `gpt-4o-mini` for OpenAI.

**Library building** (`coverletter build`, `reflect`, `intake`): non-Anthropic
providers use pre-search injection instead of tool calling. Same quality signal.

**Mistral is now fully self-contained**:
- Generation via `mistral-large-latest` or `mistral-small-latest`
- Caching via `cache_key` parameter — **90% discount** on cached tokens (same as Anthropic)
- Embeddings via `mistral-embed` ($0.10/1M tokens) — no Voyage key needed
- One API key covers everything

**OpenAI is largely self-contained**:
- Generation via `gpt-4o` or `gpt-4o-mini`
- Caching automatic — **50% discount**, activates for prompts ≥1024 tokens with no
  code changes required. Our prompts are structured correctly (system first, stable
  before dynamic) so cache hits happen automatically.
- Embeddings via `text-embedding-3-small` ($0.02/1M tokens) — no Voyage key needed
- One API key covers everything

**OpenAI-compatible providers work via `OPENAI_BASE_URL`**: any OpenAI-compatible
host can be targeted without code changes. Set `OPENAI_BASE_URL` in `.env`:
- **Regolo.ai** — Italian, 100% green energy, zero data retention, GDPR by design,
  open-source models only (Llama, Mistral weights). Transparent token pricing.
- **Hugging Face Inference** — open-source community, aggregates 15+ inference
  partners, free tier, embeddings via nomic-embed-text.

**Voyage AI** remains the default embedding provider for Anthropic users. It is a
separate key but reliable and cheap ($0.06/1M tokens). Anthropic users who don't want
a second key can switch to Mistral or OpenAI for a single-key stack.

### Caching status by provider

| Provider | Caching mechanism | Discount | Status |
|---|---|---|---|
| Anthropic | `cache_control` on system prompt | 90% | ✓ Implemented |
| Mistral | `cache_key` parameter | 90% | ✓ Implemented |
| OpenAI | Automatic prefix cache | 50% | ✓ Works automatically |
| Regolo.ai | Via hosted model (unknown discount) | Unknown | Via OpenAI provider |
| HuggingFace | Unknown | Unknown | Via OpenAI provider |
| Ollama | Keep-alive (local, free) | 100% (no API cost) | Not yet implemented |

### Embedding + reranking status by provider

| Provider | Embed (Track 1+2) | Model | Price | Rerank | Status |
|---|---|---|---|---|---|
| Anthropic | Via Voyage | voyage-3-lite | $0.06/1M | — | ✓ Works |
| Mistral | Same key | mistral-embed | $0.10/1M | — | ✓ Both tracks |
| OpenAI | Same key | text-embedding-3-small | $0.02/1M | — | ✓ Both tracks |
| Cohere | Same key | embed-v4.0 | $0.10/1M | rerank-v3.5 | ✓ Implemented (untested) |
| BGE-M3 | Local, hybrid | BAAI/bge-m3 | Free | — | ✓ Both tracks (untested) |
| Voyage AI | Standalone | voyage-3-lite | $0.06/1M | — | ✓ All providers |
| Ollama | Local | nomic-embed-text | Free | — | Not yet implemented |

### What's still needed

**Ollama**: local inference, nothing leaves the machine, zero API cost. Critical for
privacy-sensitive users. Uses nomic-embed-text for embeddings. The most architecturally
different provider — keep-alive for context instead of stateless API calls. Implement
after the tool is more stable.

**Cohere + BGE-M3 real-world testing**: both providers are implemented but untested
against real keys / real model downloads. Cohere `stream()` field names may need
adjustment. BGE-M3 `hybrid_scores()` logic is correct by inspection.

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
