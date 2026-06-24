"""Provider abstraction for LLM API calls.

Each provider handles its own caching, streaming, and cost recording.
New providers implement the complete() and stream() methods.

Model naming convention:
  "mistral/mistral-large-latest"  → MistralProvider
  "anthropic/claude-sonnet-4-6"   → AnthropicProvider
  bare model names                → AnthropicProvider (backwards compatible)

Usage:
  provider = get_provider(model, api_key)
  text = provider.complete(system, user_content, max_tokens=512)
  for chunk in provider.stream(system, messages):
      ...
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any


# ---------------------------------------------------------------------------
# Provider base
# ---------------------------------------------------------------------------

class Provider:
    """Base class. Subclasses override complete() and stream()."""

    def __init__(self, model: str, api_key: str) -> None:
        self.model = model
        self.api_key = api_key

    def complete(
        self,
        system: str,
        user_content: str,
        max_tokens: int = 512,
        temperature: float = 0,
    ) -> str:
        raise NotImplementedError

    def stream(
        self,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> Iterator[str]:
        raise NotImplementedError

    def embed(self, texts: list[str], input_type: str = "document") -> list[list[float]] | None:
        """Return embedding vectors for texts, or None if not supported by this provider.

        input_type: 'document' for library content, 'query' for JD/search queries.
        Providers that don't distinguish can ignore it.
        """
        return None

    def supports_embed(self) -> bool:
        return False

    def rerank(self, query: str, documents: list[str]) -> list[float] | None:
        """Return relevance scores for each document given the query (cross-encoder).

        Returns a list of floats, one per document, in original document order.
        Returns None if reranking is not supported.
        """
        return None

    def supports_rerank(self) -> bool:
        return False

    def hybrid_scores(
        self,
        query: str,
        documents: list[str],
        alpha: float = 0.5,
    ) -> list[float] | None:
        """Return hybrid (dense + sparse) relevance scores, one per document.

        alpha controls the dense weight: score = alpha * dense + (1-alpha) * sparse.
        Returns None if hybrid scoring is not supported.
        """
        return None

    def supports_hybrid(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------

class AnthropicProvider(Provider):

    def complete(self, system: str, user_content: str, max_tokens: int = 512, temperature: float = 0) -> str:
        import anthropic
        from coverletter.costs import record, supports_temperature

        client = anthropic.Anthropic(api_key=self.api_key)
        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user_content}],
        )
        if system:
            kwargs["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        if supports_temperature(self.model) and temperature != 0:
            kwargs["temperature"] = temperature
        elif supports_temperature(self.model):
            kwargs["temperature"] = 0

        response = client.messages.create(**kwargs)
        record(
            self.model,
            response.usage.input_tokens,
            response.usage.output_tokens,
            cache_creation_tokens=getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
            cache_read_tokens=getattr(response.usage, "cache_read_input_tokens", 0) or 0,
        )
        return response.content[0].text.strip()

    def stream(self, system: str, messages: list[dict[str, Any]], max_tokens: int = 2048, temperature: float = 0.3) -> Iterator[str]:
        import anthropic
        from coverletter.costs import record, supports_temperature

        client = anthropic.Anthropic(api_key=self.api_key)
        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
        )
        if system:
            kwargs["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        if supports_temperature(self.model):
            kwargs["temperature"] = temperature

        import time
        last_exc = None
        for attempt in range(3):
            try:
                with client.messages.stream(**kwargs) as s:
                    for text in s.text_stream:
                        yield text
                    final = s.get_final_message()
                    usage = final.usage
                    record(
                        self.model,
                        usage.input_tokens,
                        usage.output_tokens,
                        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
                        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
                    )
                return
            except anthropic.APIStatusError as e:
                if e.status_code in (500, 529) and attempt < 2:
                    last_exc = e
                    time.sleep(3 * (attempt + 1))
                    continue
                raise
        raise last_exc


# ---------------------------------------------------------------------------
# Mistral
# ---------------------------------------------------------------------------

class MistralProvider(Provider):
    """Mistral AI provider using the mistralai SDK.

    Caching: Mistral supports explicit prefix caching. The system prompt is
    sent as a separate cached message rather than a system field, which is
    the Mistral-recommended pattern for long reused content.

    Pricing: https://mistral.ai/technology/#pricing
    """

    def _cache_key(self, system: str) -> str:
        """Stable cache key derived from the system prompt — same prompt = same key."""
        import hashlib
        return hashlib.md5(system.encode()).hexdigest()[:16]

    def complete(self, system: str, user_content: str, max_tokens: int = 512, temperature: float = 0) -> str:
        from mistralai import Mistral
        from coverletter.costs import record

        client = Mistral(api_key=self.api_key)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]
        response = client.chat.complete(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            cache_key=self._cache_key(system),
        )
        usage = response.usage
        record(self.model, usage.prompt_tokens, usage.completion_tokens)
        return response.choices[0].message.content.strip()

    def stream(self, system: str, messages: list[dict[str, Any]], max_tokens: int = 2048, temperature: float = 0.3) -> Iterator[str]:
        from mistralai import Mistral
        from coverletter.costs import record

        client = Mistral(api_key=self.api_key)
        full_messages = [{"role": "system", "content": system}] + messages

        total_in = total_out = 0
        with client.chat.stream(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            cache_key=self._cache_key(system),
        ) as stream:
            for event in stream:
                delta = event.data.choices[0].delta.content if event.data.choices else None
                if delta:
                    yield delta
            final = stream.get_final_completion()
            if final and final.usage:
                total_in = final.usage.prompt_tokens
                total_out = final.usage.completion_tokens

        record(self.model, total_in, total_out)

    def embed(self, texts: list[str], input_type: str = "document") -> list[list[float]] | None:
        from mistralai import Mistral
        try:
            client = Mistral(api_key=self.api_key)
            result = client.embeddings.create(model="mistral-embed", inputs=texts)
            return [e.embedding for e in result.data]
        except Exception:
            return None

    def supports_embed(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# OpenAI-compatible (OpenAI, Together AI, Fireworks, local OpenAI-compat servers)
# ---------------------------------------------------------------------------

class OpenAIProvider(Provider):
    """OpenAI and OpenAI-compatible providers.

    Pass base_url to target a different endpoint (Together AI, Fireworks, etc.).
    Automatic prefix caching is active on OpenAI when prompts are structured
    correctly (system prompt first, stable content before dynamic content).

    Pricing: https://openai.com/pricing
    """

    def __init__(self, model: str, api_key: str, base_url: str | None = None) -> None:
        super().__init__(model, api_key)
        self.base_url = base_url

    def _client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def complete(self, system: str, user_content: str, max_tokens: int = 512, temperature: float = 0) -> str:
        from coverletter.costs import record

        client = self._client()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_content})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        usage = response.usage
        record(self.model, usage.prompt_tokens, usage.completion_tokens)
        return response.choices[0].message.content.strip()

    def stream(self, system: str, messages: list[dict], max_tokens: int = 2048, temperature: float = 0.3) -> Iterator[str]:
        from coverletter.costs import record

        client = self._client()
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        total_in = total_out = 0
        with client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            stream_options={"include_usage": True},
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
                if chunk.usage:
                    total_in = chunk.usage.prompt_tokens
                    total_out = chunk.usage.completion_tokens

        record(self.model, total_in, total_out)

    def embed(self, texts: list[str], input_type: str = "document") -> list[list[float]] | None:
        try:
            import os
            client = self._client()
            # OPENAI_EMBED_MODEL lets compatible hosts (Regolo, local) specify
            # their embedding model; defaults to text-embedding-3-small for OpenAI.
            embed_model = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
            result = client.embeddings.create(model=embed_model, input=texts)
            return [e.embedding for e in result.data]
        except Exception:
            return None

    def supports_embed(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Cohere — embed-v4 + rerank-v3
# ---------------------------------------------------------------------------

class CohereProvider(Provider):
    """Cohere generation, embeddings (embed-v4), and reranking (rerank-v3).

    Reranker is a cross-encoder: sees (query, document) pairs jointly, not as
    separate vectors. Can't be pre-cached, but is highly precise for small
    candidate sets (e.g. top-N claims per category).

    Pricing: https://cohere.com/pricing
    """

    def complete(self, system: str, user_content: str, max_tokens: int = 512, temperature: float = 0) -> str:
        import cohere  # type: ignore
        from coverletter.costs import record

        client = cohere.ClientV2(api_key=self.api_key)
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_content})
        response = client.chat(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        usage = response.usage
        if usage:
            record(self.model, getattr(usage, "input_tokens", 0) or 0, getattr(usage, "output_tokens", 0) or 0)
        return response.message.content[0].text.strip()

    def stream(self, system: str, messages: list[dict], max_tokens: int = 2048, temperature: float = 0.3) -> Iterator[str]:
        import cohere  # type: ignore

        client = cohere.ClientV2(api_key=self.api_key)
        full_messages: list[dict] = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)
        with client.chat_stream(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        ) as stream:
            for event in stream:
                if event.type == "content-delta":
                    try:
                        text = event.delta.message.content.text
                    except AttributeError:
                        # SDK may return content as a list
                        try:
                            text = event.delta.message.content[0].text
                        except (AttributeError, IndexError, TypeError):
                            continue
                    if text:
                        yield text

    def embed(self, texts: list[str], input_type: str = "document") -> list[list[float]] | None:
        try:
            import cohere  # type: ignore

            client = cohere.ClientV2(api_key=self.api_key)
            cohere_type = "search_query" if input_type == "query" else "search_document"
            response = client.embed(
                texts=texts,
                model="embed-v4.0",
                input_type=cohere_type,
                embedding_types=["float"],
            )
            return response.embeddings.float_
        except Exception:
            return None

    def supports_embed(self) -> bool:
        return True

    def rerank(self, query: str, documents: list[str]) -> list[float] | None:
        try:
            import cohere  # type: ignore

            client = cohere.ClientV2(api_key=self.api_key)
            response = client.rerank(
                model="rerank-v3.5",
                query=query,
                documents=documents,
                return_documents=False,
            )
            scores = [0.0] * len(documents)
            for result in response.results:
                scores[result.index] = result.relevance_score
            return scores
        except Exception:
            return None

    def supports_rerank(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# BGE-M3 (local, embed-only)
# ---------------------------------------------------------------------------

class BGEM3Provider(Provider):
    """BGE-M3 local embeddings with hybrid dense+sparse scoring.

    Uses the FlagEmbedding library (uv add FlagEmbedding) to run
    BAAI/bge-m3 locally. Requires ~2 GB disk for the model download on first use.

    No API key needed — runs fully offline.

    Hybrid score = alpha * dense_cosine + (1-alpha) * sparse_dot_product.
    The sparse component gives lexical precision ("Kafka" matches "Kafka")
    while the dense component gives semantic generalization.

    This provider is embed-only: complete() and stream() raise NotImplementedError.
    Pair it with any generation provider via EMBED_MODEL=bge-m3.
    """

    _model_name = "BAAI/bge-m3"
    _alpha = 0.5  # dense weight in hybrid score

    def __init__(self, model: str = "BAAI/bge-m3", api_key: str = "") -> None:
        super().__init__(model or "BAAI/bge-m3", api_key)
        self._flag_model = None  # lazy-loaded

    def _load(self):
        if self._flag_model is None:
            from FlagEmbedding import BGEM3FlagModel  # type: ignore
            self._flag_model = BGEM3FlagModel(self.model, use_fp16=True)
        return self._flag_model

    def complete(self, system: str, user_content: str, max_tokens: int = 512, temperature: float = 0) -> str:
        raise NotImplementedError("BGEM3Provider is embed-only. Use a generation provider for completions.")

    def stream(self, system: str, messages: list[dict], max_tokens: int = 2048, temperature: float = 0.3) -> Iterator[str]:
        raise NotImplementedError("BGEM3Provider is embed-only. Use a generation provider for streaming.")

    def embed(self, texts: list[str], input_type: str = "document") -> list[list[float]] | None:
        """Return dense vectors (for DB storage and cosine similarity)."""
        try:
            model = self._load()
            output = model.encode(texts, return_dense=True, return_sparse=False)
            return [v.tolist() for v in output["dense_vecs"]]
        except Exception:
            return None

    def supports_embed(self) -> bool:
        return True

    def hybrid_scores(
        self,
        query: str,
        documents: list[str],
        alpha: float | None = None,
    ) -> list[float] | None:
        """Hybrid dense+sparse scores: alpha * dense_cosine + (1-alpha) * sparse_dot."""
        if alpha is None:
            alpha = self._alpha
        try:
            import numpy as np  # type: ignore

            model = self._load()
            # Encode query + all documents together for efficiency
            all_texts = [query] + documents
            output = model.encode(all_texts, return_dense=True, return_sparse=True)

            dense_vecs = output["dense_vecs"]          # shape: (1+N, dim)
            sparse_vecs = output["lexical_weights"]    # list of dicts {token: weight}

            q_dense = dense_vecs[0]
            q_sparse = sparse_vecs[0]
            doc_dense = dense_vecs[1:]
            doc_sparse = sparse_vecs[1:]

            scores = []
            for d_dense, d_sparse in zip(doc_dense, doc_sparse):
                # Dense cosine (BGE-M3 outputs normalized vectors, so dot product = cosine)
                dense_score = float(np.dot(q_dense, d_dense))
                # Sparse dot product over shared tokens
                sparse_score = sum(
                    float(q_sparse.get(tok, 0)) * float(weight)
                    for tok, weight in d_sparse.items()
                    if tok in q_sparse
                )
                scores.append(alpha * dense_score + (1.0 - alpha) * sparse_score)
            return scores
        except Exception:
            return None

    def supports_hybrid(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def parse_model(model: str) -> tuple[str, str]:
    """Split 'provider/model-name' into (provider, model).

    Bare names (no slash) default to 'anthropic' for backwards compatibility.
    """
    if "/" in model:
        provider, _, name = model.partition("/")
        return provider.lower(), name
    return "anthropic", model


def get_provider(model: str, api_key: str) -> Provider:
    """Return the right Provider instance for a model string."""
    provider_name, model_name = parse_model(model)
    if provider_name == "mistral":
        return MistralProvider(model_name, api_key)
    if provider_name == "openai":
        import os
        base_url = os.environ.get("OPENAI_BASE_URL") or None
        return OpenAIProvider(model_name, api_key, base_url=base_url)
    if provider_name == "cohere":
        return CohereProvider(model_name, api_key)
    if provider_name == "bge-m3":
        return BGEM3Provider(model_name or "BAAI/bge-m3")
    return AnthropicProvider(model_name, api_key)


def get_embed_provider(embed_model: str) -> "Provider | None":
    """Return an embed-capable Provider for the given EMBED_MODEL string.

    Returns None if embed_model is empty (caller uses generation provider's embed).

    Supported values:
      bge-m3   → BGEM3Provider (local, hybrid dense+sparse, no API key)
    """
    if not embed_model:
        return None
    if embed_model.lower() == "bge-m3":
        return BGEM3Provider()
    return None
