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
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_content}],
        )
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
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
        )
        if supports_temperature(self.model):
            kwargs["temperature"] = temperature

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
            client = self._client()
            result = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            return [e.embedding for e in result.data]
        except Exception:
            return None

    def supports_embed(self) -> bool:
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
    return AnthropicProvider(model_name, api_key)
