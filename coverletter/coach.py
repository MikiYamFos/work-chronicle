from __future__ import annotations

import json
import re
from dataclasses import dataclass

from coverletter.costs import record, supports_temperature

COACH_SYSTEM = """\
You are a cover letter coach who evaluates individual sentences for impact, clarity, and persuasive force.
You flag weak sentences and suggest specific directions for improvement.
Return only valid JSON. No commentary outside the JSON.
"""

COACH_PROMPT = """\
Review this cover letter sentence by sentence. Flag sentences that are weak, vague, generic,
trail off, or miss an opportunity to land a stronger point. Do not flag sentences that are
already strong and specific.

Do NOT flag:
- The salutation ("Dear ... Hiring Manager,")
- The closing paragraph (thanks/sign-off) — it serves a structural, conventional role and should not be flagged
- Transition sentences that are intentionally brief and functional

For each weak sentence, return:
- "sentence": the exact sentence as it appears
- "issue": one short sentence saying what's wrong (vague, trails off, no consequence, generic claim, etc.)

Return JSON array. If nothing is weak, return [].

=== LETTER ===
{letter}
"""

REWRITE_SYSTEM = """\
You are a cover letter editor. Rewrite a single sentence according to a direction.
Preserve the factual content and the writer's voice. Output only the rewritten sentence — nothing else.
"""

REWRITE_PROMPT = """\
Original sentence: {sentence}

Surrounding context (do not rewrite this, just use it for tone and flow):
{context}

Direction: {direction}

Rewrite the sentence according to the direction. Output only the rewritten sentence.
"""

REWRITE_DIRECTION = """\
Fix the issue identified. Use the user's input as your guide — if they wrote a direction
(e.g. "make this hit harder", "add the consequence"), rewrite accordingly. If they wrote
a replacement sentence, use it directly or refine it to fit the context. Output only the
revised sentence."""


@dataclass
class WeakSentence:
    sentence: str
    issue: str


def analyze_letter(letter: str, api_key: str, model: str) -> list[WeakSentence]:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    prompt = COACH_PROMPT.format(letter=letter)
    kwargs: dict = dict(
        model=model,
        max_tokens=1024,
        system=[{"type": "text", "text": COACH_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )
    if supports_temperature(model):
        kwargs["temperature"] = 0
    response = client.messages.create(**kwargs)
    usage = response.usage
    record(
        model, usage.input_tokens, usage.output_tokens,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        items = json.loads(raw)
        return [WeakSentence(sentence=i["sentence"], issue=i["issue"]) for i in items]
    except Exception:
        return []


def rewrite_sentence(sentence: str, context: str, issue: str, user_input: str, api_key: str, model: str) -> str:
    import anthropic
    direction = f"Issue: {issue}\nUser input: {user_input}\n\n{REWRITE_DIRECTION}"
    client = anthropic.Anthropic(api_key=api_key)
    prompt = REWRITE_PROMPT.format(sentence=sentence, context=context, direction=direction)
    kwargs: dict = dict(
        model=model,
        max_tokens=256,
        system=[{"type": "text", "text": REWRITE_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )
    if supports_temperature(model):
        kwargs["temperature"] = 0.3
    response = client.messages.create(**kwargs)
    usage = response.usage
    record(
        model, usage.input_tokens, usage.output_tokens,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
    )
    return response.content[0].text.strip()


def get_context(letter: str, sentence: str, window: int = 200) -> str:
    idx = letter.find(sentence)
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(letter), idx + len(sentence) + window)
    return letter[start:end]
