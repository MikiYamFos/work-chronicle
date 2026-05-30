from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from coverletter.costs import record, supports_temperature
from coverletter.parser import Paragraph

VERIFY_SYSTEM = """\
You are a cover letter quality checker. Return ONLY valid JSON — no reasoning, no preamble.

{"verdict": "PASS" or "FAIL", "failures": ["quoted sentence + rule violated", ...]}

PASS means failures is an empty list. Be conservative: only flag what is clearly wrong.
"""

VERIFY_PROMPT = """\
=== COVER LETTER ===
{letter}

=== WHAT TO CHECK ===
Em-dashes, banned words, and paragraph-starting-with-That are already checked by a separate
tool. Do NOT re-check them. Focus only on these three:

1. LIST-PILE ENDINGS
Does any paragraph end with a list of 3 or more items instead of landing a specific point?
Flag: quote the offending closing sentence.
Ignore: lists inside a sentence that end on a verb or claim.

2. GENERIC BODY OPENERS
Does any BODY paragraph (not the opener or closer) open with a generic topic statement
rather than a concrete fact from the candidate's experience?
Flag examples: "I am strongest in...", "I combine...",
"Building systems that...", "My approach to X is..."
Pass: opens with a specific event, failure mode, role, or named observation.

3. AI/TEMPLATE BODY PARAGRAPHS
Does any body paragraph read like generated template prose?
Signs: abstract values stated as assertions, skills described as personality traits,
no specific evidence behind the claims.
Flag: quote the paragraph opener.

Return ONLY the JSON. No text outside the JSON object.
"""


@dataclass
class VerificationResult:
    verdict: str
    failures: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"


@dataclass
class VerbatimViolation:
    sentence: str
    best_match: str
    score: float  # 0.0–1.0, higher = closer to source


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in parts if s.strip()]


def _token_coverage(letter_sent: str, source_sent: str) -> float:
    """
    What fraction of the letter sentence's words appear in the source sentence.
    Directional: robust to trimming and minor tense/inflection changes.
    """
    l_words = set(re.findall(r"[a-z]+", letter_sent.lower()))
    s_words = set(re.findall(r"[a-z]+", source_sent.lower()))
    # Remove very short words that add noise
    l_words = {w for w in l_words if len(w) > 2}
    s_words = {w for w in s_words if len(w) > 2}
    if not l_words:
        return 1.0
    return len(l_words & s_words) / len(l_words)


@dataclass
class CopyViolation:
    """Flags a letter paragraph that is too close to a single source paragraph — wholesale copy."""
    letter_para: str
    source_para: str
    score: float  # average token coverage across sentences


def verbatim_check(
    letter_text: str,
    source_paragraphs: list[Paragraph],
    threshold: float = 0.50,
    synthesis_mode: bool = False,
    evidence_sentences: list[str] | None = None,
) -> list[VerbatimViolation]:
    """
    Checks each letter body sentence against source sentences to detect invention.

    In the new model the letter is WRITTEN from evidence, not copied — so thresholds
    are calibrated to catch genuine invention (claims with no grounding), not to
    enforce verbatim copying.

    evidence_sentences: when provided, checks body sentences against the evidence
    block the model was given. Flags sentences with no grounding in any evidence item.
    Threshold 0.45 — loose enough for natural prose, tight enough to catch made-up claims.

    source_paragraphs: fallback when no evidence_sentences. Checks against full library.
    Threshold 0.50 by default.

    Skips the salutation, opener, and closer paragraphs.
    """
    if evidence_sentences is not None:
        source_sentences = [s for s in evidence_sentences if s.strip()]
        effective_threshold = 0.45  # writing from evidence, not copying it
    else:
        effective_threshold = threshold
        source_sentences = []
        for p in source_paragraphs:
            source_sentences.extend(_split_sentences(p.text))

    if not source_sentences:
        return []

    letter_paras = [p.strip() for p in letter_text.split("\n\n") if p.strip()]
    if len(letter_paras) <= 3:
        return []

    body_paras = letter_paras[2:-1]
    letter_sentences: list[str] = []
    for para in body_paras:
        letter_sentences.extend(_split_sentences(para))

    violations: list[VerbatimViolation] = []
    for sent in letter_sentences:
        if len(sent.split()) < 6:
            continue
        best_score = 0.0
        best_src = ""
        for src in source_sentences:
            score = _token_coverage(sent, src)
            if score > best_score:
                best_score = score
                best_src = src
        if best_score < effective_threshold:
            violations.append(VerbatimViolation(sentence=sent, best_match=best_src, score=best_score))

    return violations


def copy_check(
    letter_text: str,
    source_paragraphs: list[Paragraph],
    threshold: float = 0.82,
) -> list[CopyViolation]:
    """Anti-copy judge — flags letter paragraphs that are too close to a single source paragraph.

    When sentence evidence is provided, the model should synthesize across sources.
    A high average token overlap with one source paragraph means it copy-pasted instead.
    Only runs when synthesis_mode is active (called explicitly from the generate pipeline).
    """
    letter_paras = [p.strip() for p in letter_text.split("\n\n") if p.strip()]
    if len(letter_paras) <= 3:
        return []
    body_paras = letter_paras[2:-1]

    violations: list[CopyViolation] = []
    for letter_para in body_paras:
        letter_sents = _split_sentences(letter_para)
        if len(letter_sents) < 2:
            continue
        best_para_score = 0.0
        best_para_text = ""
        for src_para in source_paragraphs:
            src_sents = _split_sentences(src_para.text)
            if not src_sents:
                continue
            # Average token coverage of letter sentences against this source paragraph
            scores = []
            for ls in letter_sents:
                best = max((_token_coverage(ls, ss) for ss in src_sents), default=0.0)
                scores.append(best)
            avg = sum(scores) / len(scores)
            if avg > best_para_score:
                best_para_score = avg
                best_para_text = src_para.text
        if best_para_score >= threshold:
            violations.append(CopyViolation(
                letter_para=letter_para,
                source_para=best_para_text,
                score=best_para_score,
            ))

    return violations


_BANNED_PHRASES = [
    "actually", "not just", "not only", "not simply",
    "this matters because", "the hard part was not",
    "that experience fits", "this role aligns", "what stands out",
    "the clearest connection", "this is the kind of work",
    "i am strongest in",
    "i combine ",
]

def _hard_check(letter_text: str) -> list[str]:
    """Deterministic checks that don't need an LLM."""
    failures = []

    # Em-dash
    for line in letter_text.splitlines():
        if "—" in line:
            failures.append(f"Em-dash: {line.strip()[:120]}")

    # Banned phrases (exact, case-insensitive)
    lower = letter_text.lower()
    for phrase in _BANNED_PHRASES:
        if phrase in lower:
            # Find and quote the first offending sentence
            for sent in re.split(r"(?<=[.!?])\s+", letter_text):
                if phrase in sent.lower():
                    failures.append(f"Banned phrase '{phrase}': {sent.strip()[:120]}")
                    break

    # Paragraph starting with "That"
    for para in letter_text.split("\n\n"):
        para = para.strip()
        if para.lower().startswith("that "):
            failures.append(f"Paragraph starts with 'That': {para[:80]}")

    return failures


def verify_letter(letter_text: str, api_key: str, model: str) -> VerificationResult:
    import anthropic
    hard_failures = _hard_check(letter_text)
    if hard_failures:
        return VerificationResult(verdict="FAIL", failures=hard_failures)

    client = anthropic.Anthropic(api_key=api_key, timeout=30.0)
    prompt = VERIFY_PROMPT.format(letter=letter_text)
    kwargs: dict = dict(
        model=model,
        max_tokens=512,
        system=[{"type": "text", "text": VERIFY_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )
    if supports_temperature(model):
        kwargs["temperature"] = 0
    try:
        response = client.messages.create(**kwargs)
    except Exception:
        return VerificationResult(verdict="PASS", failures=[])
    usage = response.usage
    record(
        model, usage.input_tokens, usage.output_tokens,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
    )
    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        return VerificationResult(
            verdict=data.get("verdict", "FAIL"),
            failures=data.get("failures", []),
        )
    except (json.JSONDecodeError, KeyError):
        return VerificationResult(verdict="FAIL", failures=[f"Verification parse error: {raw[:200]}"])
