"""
Tests for provider routing, factory functions, and capability flags.
These run without API keys — no network calls.
"""
from coverletter.provider import (
    AnthropicProvider,
    BGEM3Provider,
    CohereProvider,
    MistralProvider,
    OpenAIProvider,
    Provider,
    get_embed_provider,
    get_provider,
    parse_model,
)


# ── parse_model ───────────────────────────────────────────────────────────────

def test_parse_bare_name_defaults_to_anthropic():
    provider, model = parse_model("claude-sonnet-4-6")
    assert provider == "anthropic"
    assert model == "claude-sonnet-4-6"


def test_parse_prefixed_mistral():
    provider, model = parse_model("mistral/mistral-large-latest")
    assert provider == "mistral"
    assert model == "mistral-large-latest"


def test_parse_prefixed_openai():
    provider, model = parse_model("openai/gpt-4o")
    assert provider == "openai"
    assert model == "gpt-4o"


def test_parse_prefixed_cohere():
    provider, model = parse_model("cohere/command-r-plus")
    assert provider == "cohere"
    assert model == "command-r-plus"


def test_parse_prefixed_bge_m3():
    provider, model = parse_model("bge-m3/BAAI/bge-m3")
    assert provider == "bge-m3"


# ── get_provider routing ──────────────────────────────────────────────────────

def test_get_provider_anthropic():
    p = get_provider("claude-sonnet-4-6", "key")
    assert isinstance(p, AnthropicProvider)


def test_get_provider_mistral():
    p = get_provider("mistral/mistral-large-latest", "key")
    assert isinstance(p, MistralProvider)


def test_get_provider_openai():
    p = get_provider("openai/gpt-4o", "key")
    assert isinstance(p, OpenAIProvider)


def test_get_provider_cohere():
    p = get_provider("cohere/command-r-plus", "key")
    assert isinstance(p, CohereProvider)


def test_get_provider_bge_m3():
    p = get_provider("bge-m3/BAAI/bge-m3", "")
    assert isinstance(p, BGEM3Provider)


# ── get_embed_provider ────────────────────────────────────────────────────────

def test_get_embed_provider_bge_m3():
    p = get_embed_provider("bge-m3")
    assert isinstance(p, BGEM3Provider)


def test_get_embed_provider_empty_returns_none():
    assert get_embed_provider("") is None


def test_get_embed_provider_unknown_returns_none():
    assert get_embed_provider("voyage") is None
    assert get_embed_provider("something-random") is None


# ── capability flags — no API calls ──────────────────────────────────────────

def test_anthropic_does_not_support_embed():
    p = AnthropicProvider("claude-sonnet-4-6", "key")
    assert not p.supports_embed()
    assert not p.supports_rerank()
    assert not p.supports_hybrid()


def test_anthropic_embed_returns_none():
    p = AnthropicProvider("claude-sonnet-4-6", "key")
    assert p.embed(["text"]) is None
    assert p.rerank("q", ["doc"]) is None
    assert p.hybrid_scores("q", ["doc"]) is None


def test_mistral_supports_embed():
    p = MistralProvider("mistral-large-latest", "key")
    assert p.supports_embed()
    assert not p.supports_rerank()
    assert not p.supports_hybrid()


def test_openai_supports_embed():
    p = OpenAIProvider("gpt-4o", "key")
    assert p.supports_embed()
    assert not p.supports_rerank()
    assert not p.supports_hybrid()


def test_cohere_supports_embed_and_rerank():
    p = CohereProvider("command-r-plus", "key")
    assert p.supports_embed()
    assert p.supports_rerank()
    assert not p.supports_hybrid()


def test_bgem3_supports_embed_and_hybrid():
    p = BGEM3Provider()
    assert p.supports_embed()
    assert p.supports_hybrid()
    assert not p.supports_rerank()


def test_bgem3_complete_raises():
    p = BGEM3Provider()
    try:
        p.complete("sys", "user")
        assert False, "should have raised"
    except NotImplementedError:
        pass


def test_bgem3_stream_raises():
    p = BGEM3Provider()
    try:
        list(p.stream("sys", []))
        assert False, "should have raised"
    except NotImplementedError:
        pass


# ── base Provider defaults ────────────────────────────────────────────────────

def test_base_provider_all_flags_false():
    class Bare(Provider):
        def complete(self, s, u, **kw): return ""
        def stream(self, s, m, **kw): return iter([])
    p = Bare("m", "k")
    assert not p.supports_embed()
    assert not p.supports_rerank()
    assert not p.supports_hybrid()
    assert p.embed(["x"]) is None
    assert p.rerank("q", ["d"]) is None
    assert p.hybrid_scores("q", ["d"]) is None
