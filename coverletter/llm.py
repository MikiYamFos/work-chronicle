from collections.abc import Iterator
from typing import Any

from coverletter.provider import get_provider

Message = dict[str, Any]


def stream_cover_letter(
    system_prompt: str,
    user_content: list[dict] | str,
    api_key: str,
    model: str,
) -> Iterator[str]:
    provider = get_provider(model, api_key)
    messages = [{"role": "user", "content": user_content}]
    return provider.stream(system_prompt, messages)


def stream_revision(
    system_prompt: str,
    messages: list[Message],
    feedback: str,
    api_key: str,
    model: str,
) -> Iterator[str]:
    provider = get_provider(model, api_key)
    revised_messages = messages + [{"role": "user", "content": feedback}]
    return provider.stream(system_prompt, revised_messages)
