# Roadmap

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

## Issue #3 — Resume generation integrated into main flow

`coverletter resume` exists but is disconnected from the main letter flow. After
saving a letter, the tool should offer to generate a tailored resume for the same
company in the same step.
