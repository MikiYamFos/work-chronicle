from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Layer 1: Deterministic pattern filter
# Catches hard writing rule violations before any LLM cost.
# ---------------------------------------------------------------------------

_BAD_PATTERNS: list[tuple[str, str]] = [
    # Em-dash
    (r"—", "contains em-dash — use a comma, semicolon, or period instead"),
    # Banned words
    (r"\bactually\b", "contains banned word: 'actually'"),
    (r"\bmatters\b", "contains banned word: 'matters'"),
    (r"\bnot just\b", "contains banned phrase: 'not just'"),
    (r"\bnot only\b", "contains banned phrase: 'not only'"),
    (r"\bnot simply\b", "contains banned phrase: 'not simply'"),
    # Sentence starting with "That"
    (r"(?:^|\.\s+)That\s", "a sentence starts with 'That'"),
    # Fake contrast
    (r"\bnot\b[^.]{1,40}\bbut\b", "fake contrast structure ('not X but Y')"),
    # Superlatives the model loves to inject
    (r"\bstrongest\b", "injected superlative: 'strongest' — use the writer's own words"),
    (r"\bmost meaningful\b", "injected superlative: 'most meaningful'"),
    (r"\bmost impactful\b", "injected superlative: 'most impactful'"),
    (r"\bdeep(ly|er|est)?\b", "injected intensity word: 'deep/deeply' — cut or use source language"),
    (r"\btruly\b", "injected filler: 'truly'"),
    (r"\bgenuinely\b", "injected filler: 'genuinely'"),
    (r"\bhighly\b", "injected filler: 'highly'"),
    (r"\bpassionate(ly)?\b", "injected cliché: 'passionate' — use concrete evidence instead"),
]


def check_paragraph_patterns(text: str) -> str | None:
    """Return a rejection reason if the paragraph matches a bad pattern, else None."""
    for pattern, reason in _BAD_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return reason
    return None


# ---------------------------------------------------------------------------
# Layer 2: LLM source-fidelity judge (Haiku)
# Checks whether the paragraph introduces claims or characterizations
# not present in the source material.
# ---------------------------------------------------------------------------

_JUDGE_SYSTEM = """\
You are checking whether a generated cover letter paragraph faithfully preserves \
the writer's voice and specific language — not just their facts, but how they \
actually speak and what they actually said.

FAIL if the paragraph contains ANY of:
- Generic professional or sector rhetoric replacing the writer's personal, specific \
language. Example: writer said "There is no more freeing thing than building projects \
driven by creativity" and the model wrote "Game design is one of the strongest ways \
to help students experience computer science" — that is a voice replacement, not \
an extraction.
- Evaluative or superlative words not used in the source ("strongest", "best", \
"most meaningful", "most impactful", "excellent", "exceptional", or similar) unless \
the writer actually used them.
- Third-person-style observations about the writer's own experience that the writer \
did not make ("The most meaningful teaching I have done..." when the writer never \
framed it that way).
- Abstract category statements replacing concrete personal claims the writer made.
- Any sentence that reads like it could have been written by any applicant in this \
field, when the source contained a personal, specific statement instead.

PASS if the paragraph is a tighter version of what the writer actually wrote, \
in their own voice and words. Structural tightening is fine. Voice replacement is not.

Return ONLY valid JSON:
{"pass": true}
or
{"pass": false, "reason": "one sentence describing the voice replacement", "offending_phrases": ["phrase1", "phrase2"]}
"""

_JUDGE_MODEL = "claude-haiku-4-5-20251001"


def judge_paragraph(
    paragraph: str,
    source: str,
    api_key: str,
) -> tuple[bool, str, list[str]]:
    """LLM source-fidelity judge. Returns (passes, reason, offending_phrases)."""
    import json
    from coverletter.provider import get_provider

    prompt = (
        f"SOURCE MATERIAL:\n{source[:2000]}\n\n"
        f"GENERATED PARAGRAPH:\n{paragraph}"
    )
    raw = get_provider(_JUDGE_MODEL, api_key).complete(_JUDGE_SYSTEM, prompt, max_tokens=256)
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        if data.get("pass"):
            return True, "", []
        return False, data.get("reason", "paragraph introduces content not in source"), data.get("offending_phrases", [])
    except Exception:
        return True, "", []  # parse failure — don't block


# ---------------------------------------------------------------------------
# Rewrite: ask the model to fix a failing paragraph
# ---------------------------------------------------------------------------

_REWRITE_SYSTEM = """\
You are fixing a cover letter paragraph that was rejected for replacing the writer's \
voice with generic professional language.

The writer's own words and how they said things are the only raw material. \
Your job is to produce a tighter version of what they actually wrote — not a \
cleaner-sounding substitute.

RULES — the rewrite must:
1. Remove or replace every offending phrase listed — typically generic sector rhetoric \
or superlatives the writer did not use
2. Return to the writer's actual language from the source material
3. Not add evaluative words, superlatives, or intensity adverbs the writer did not use
4. Keep the structural improvement (concrete claim first, filler cut) but in the \
writer's own words
5. Follow all writing rules: no em-dashes, no banned words (actually/matters/not just/\
not only/not simply), no sentences starting with 'That', no fake contrast

Return ONLY the rewritten paragraph text. No preamble, no explanation.
"""


def rewrite_paragraph(
    paragraph: str,
    source: str,
    reason: str,
    offending_phrases: list[str],
    api_key: str,
    model: str,
) -> str | None:
    """Ask the model to rewrite a paragraph that failed validation.
    Returns the rewritten text, or None if it can't be extracted."""
    from coverletter.provider import get_provider

    phrases_str = "\n".join(f"- {p}" for p in offending_phrases) if offending_phrases else "(see reason)"
    prompt = (
        f"SOURCE MATERIAL:\n{source[:2000]}\n\n"
        f"REJECTED PARAGRAPH:\n{paragraph}\n\n"
        f"REJECTION REASON: {reason}\n\n"
        f"OFFENDING PHRASES TO REMOVE:\n{phrases_str}\n\n"
        f"Rewrite the paragraph using only the writer's own language from the source."
    )
    text = get_provider(model, api_key).complete(_REWRITE_SYSTEM, prompt, max_tokens=1024, temperature=0.2)
    return text if text else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_MAX_RETRIES = 2


def validate_and_fix_paragraph(
    paragraph: str,
    source: str,
    api_key: str,
    model: str,
    use_llm_judge: bool = True,
) -> tuple[str, list[str]]:
    """Validate a paragraph and attempt to fix it if it fails.

    Returns (final_paragraph_text, warnings).
    warnings is empty if the paragraph passed (original or fixed).
    If it still fails after retries, returns the original with warnings so
    the user can see what the model kept getting wrong.
    """
    warnings: list[str] = []

    for attempt in range(_MAX_RETRIES + 1):
        # Layer 1: deterministic
        reason = check_paragraph_patterns(paragraph)
        if reason:
            if attempt < _MAX_RETRIES:
                fixed = rewrite_paragraph(paragraph, source, reason, [], api_key, model)
                if fixed:
                    paragraph = fixed
                    continue
            warnings.append(f"Writing rule violation (could not auto-fix): {reason}")
            break

        # Layer 2: LLM judge
        if use_llm_judge and api_key:
            passes, reason, offending = judge_paragraph(paragraph, source, api_key)
            if not passes:
                if attempt < _MAX_RETRIES:
                    fixed = rewrite_paragraph(paragraph, source, reason, offending, api_key, model)
                    if fixed:
                        paragraph = fixed
                        continue
                warnings.append(f"Source fidelity issue (could not auto-fix): {reason}")
                if offending:
                    warnings.append(f"Phrases to watch: {', '.join(offending)}")
                break

        # Passed both layers
        break

    return paragraph, warnings
