from collections.abc import Iterator
from typing import Any

import anthropic

from coverletter.costs import record, supports_temperature

Message = dict[str, Any]


def _cached_system(text: str) -> list[dict]:
    """Wrap a system prompt as a cacheable content block."""
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def _stream(system_prompt: str, messages: list[Message], api_key: str, model: str) -> Iterator[str]:
    client = anthropic.Anthropic(api_key=api_key)
    kwargs: dict[str, Any] = dict(
        model=model,
        max_tokens=2048,
        system=_cached_system(system_prompt),
        messages=messages,
    )
    if supports_temperature(model):
        kwargs["temperature"] = 0.3
    with client.messages.stream(**kwargs) as stream:
        for text in stream.text_stream:
            yield text
        final = stream.get_final_message()
        usage = final.usage
        record(
            model,
            usage.input_tokens,
            usage.output_tokens,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        )


def stream_cover_letter(
    system_prompt: str,
    user_content: list[dict] | str,
    api_key: str,
    model: str,
) -> Iterator[str]:
    return _stream(system_prompt, [{"role": "user", "content": user_content}], api_key, model)


def stream_revision(
    system_prompt: str,
    messages: list[Message],
    feedback: str,
    api_key: str,
    model: str,
) -> Iterator[str]:
    revised_messages = messages + [{"role": "user", "content": feedback}]
    return _stream(system_prompt, revised_messages, api_key, model)
