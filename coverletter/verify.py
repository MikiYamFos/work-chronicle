from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from coverletter.parser import Paragraph
from coverletter.provider import get_provider

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
tool. Do NOT re-check them. Focus only on these four:

1. OPENER PARAGRAPH
The first sentence of the opener must be about the candidate — their work, experience,
or perspective. A first sentence that makes a claim about an industry, a domain, a
problem space, or the employer's situation without the candidate present is a failed opener.
Flag if:
- The first sentence of the opener does not contain "I" or otherwise put the candidate
  as subject — it is about something other than the candidate
- The opener paragraph contains previous employer names (BritBox, UNITE HERE, Universe,
  Jigsaw Labs)
Pass: the first sentence puts the candidate as subject and the paragraph connects them
to this specific employer.

2. LIST-PILE ENDINGS
Does any paragraph end with a list of 3 or more items instead of landing a specific point?
Flag: quote the offending closing sentence.
Ignore: lists inside a sentence that end on a verb or claim.

3. GENERIC BODY OPENERS
Does any BODY paragraph (not the opener or closer) open with a generic topic statement
rather than a concrete fact from the candidate's experience?
Flag examples:
- "I am strongest in...", "I combine...", "Building systems that...", "My approach to X is..."
- "The [skill/span] this role requires..." — restating the JD requirement as a topic sentence
- "The [X] work this role requires... is the [X] I already do"
Pass: opens with a specific event, failure mode, role, employer, or named observation.

4. AI/TEMPLATE BODY PARAGRAPHS
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
    score: float  # 0.0–1.0, higher = closer to evidence


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
    l_words = {w for w in l_words if len(w) > 2}
    s_words = {w for w in s_words if len(w) > 2}
    if not l_words:
        return 1.0
    return len(l_words & s_words) / len(l_words)


def verbatim_check(
    letter_text: str,
    source_paragraphs: list[Paragraph],
    threshold: float = 0.50,
    evidence_sentences: list[str] | None = None,
) -> list[VerbatimViolation]:
    """
    Checks each letter body sentence for evidence grounding.

    In the new model the letter is WRITTEN from evidence, not copied — thresholds
    are calibrated to catch genuine invention (claims with no grounding in any
    evidence item), not to enforce verbatim copying.

    evidence_sentences: the evidence block the model was given. Sentences with no
    word overlap in any evidence item are flagged. Threshold 0.45.

    source_paragraphs: fallback when no evidence_sentences. Checks against full
    library. Threshold 0.50 by default.

    Skips the salutation, opener, and closer paragraphs.
    """
    # Always check against the full library — the model writes from all paragraphs, not
    # just the evidence block. Using only evidence_sentences misses anything synthesized
    # from library paragraphs that weren't surfaced in the angle evidence, causing false positives.
    source_sentences = []
    for p in source_paragraphs:
        source_sentences.extend(_split_sentences(p.text))
    if evidence_sentences is not None:
        source_sentences.extend(s for s in evidence_sentences if s.strip())
    effective_threshold = 0.20

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


_BANNED_PHRASES = [
    "actually", "not just", "not only", "not simply",
    "this matters because", "the hard part was not",
    "that experience fits", "this role aligns", "what stands out",
    "the clearest connection", "this is the kind of work",
    "i am strongest in",
    "i combine ",
    # "I have been the X" — invented LLM construction, no one writes this way
    "i have been the ",
    # Present-progressive chaining — hedged, indirect, not how this writer talks
    "i have been building",
    "i have been doing",
    "work i have been doing",
    "that is the work i have been",
    "it is the work i have been",
    "have been doing, in",
    # Participial infrastructure phrase
    "we've been building out",
    "has been building out",
    "responsible for ingesting",
    # AI filler — vague career-narrative constructions that replace actual evidence
    "career-long pattern",
    "building for the next",
    "for the next engineer",
    "for the next person",
    "not just for the immediate",
    "not just the immediate problem",
    # Meta-commentary — letter talking about itself instead of making the argument
    "i want to name because",
    "worth naming because",
    "is worth noting that",
    "something i want to name",
    # Abstract stakes-framing in opener — sets up employer's domain without the candidate
    "is where wrong numbers",
    "is where bad data",
    "is where incorrect data",
    "carries a particular kind of weight",
    "that is exactly the kind of environment",
    "that is the kind of environment",
    "at every stop i was the person",
    "at every stop, i was",
]

# Fake contrast — "not X; it was/is Y" or "not X, it is Y" or "not X — it is Y"
# These set up a straw man to make the second half sound important.
_FAKE_CONTRAST = re.compile(
    r'\bnot (a |the |an )?\w.{2,60}(;\s*it (was|is)|,\s*it (was|is))',
    re.IGNORECASE,
)

def _hard_check(letter_text: str) -> list[str]:
    """Deterministic checks that don't need an LLM."""
    failures = []

    # Em-dash overuse — LLMs use em-dashes as a lazy sentence connector.
    # One or two in a letter is fine; more than 2 is a crutch.
    em_dash_count = letter_text.count("—")
    if em_dash_count > 2:
        failures.append(
            f"Em-dash overuse: {em_dash_count} em-dashes in the letter. "
            "Rewrite the weakest ones as proper sentences."
        )

    # Banned phrases (exact, case-insensitive)
    lower = letter_text.lower()
    for phrase in _BANNED_PHRASES:
        if phrase in lower:
            for sent in re.split(r"(?<=[.!?])\s+", letter_text):
                if phrase in sent.lower():
                    failures.append(f"Banned phrase '{phrase}': {sent.strip()[:120]}")
                    break

    # Progressive tense — banned entirely. No exceptions.
    _PROGRESSIVE = re.compile(
        r"\b(have|has|had|was|were)\s+been\s+\w+ing\b"
        r"|\b(was|were)\s+\w+ing\b",
        re.IGNORECASE,
    )
    for sent in re.split(r"(?<=[.!?])\s+", letter_text):
        if _PROGRESSIVE.search(sent):
            failures.append(f"Progressive tense: {sent.strip()[:120]}")

    # Any sentence starting with "That" — banned without exception
    for sent in re.split(r"(?<=[.!?])\s+", letter_text):
        sent = sent.strip()
        if re.match(r'^that\b', sent, re.IGNORECASE):
            failures.append(f"Sentence starts with 'That': {sent[:100]}")

    # Paragraph-level transition openers (other than "That", already caught above)
    _TRANSITION_OPENERS = (
        "on that last point",
        "on a related note",
        "building on that",
        "with that in mind",
        "to that end",
        "turning to",
        "similarly,",
        "relatedly,",
    )
    for para in letter_text.split("\n\n"):
        para = para.strip()
        lower_para = para.lower()
        for opener in _TRANSITION_OPENERS:
            if lower_para.startswith(opener):
                failures.append(f"Transition paragraph opener '{para[:60].strip()}'")

    # Fake contrast — "not X; it was/is Y" construction
    for sent in re.split(r"(?<=[.!?])\s+", letter_text):
        if _FAKE_CONTRAST.search(sent):
            failures.append(f"Fake contrast ('not X; it was/is Y'): {sent.strip()[:120]}")

    # Opener first sentence must contain "I" — opener must open from the candidate
    paras = [p.strip() for p in letter_text.split("\n\n") if p.strip()]
    # Skip salutation (starts with "Dear")
    opener_para = next((p for p in paras if not p.lower().startswith("dear")), None)
    if opener_para:
        first_sent = re.split(r"(?<=[.!?])\s+", opener_para)[0].strip()
        if not re.search(r'\bI\b', first_sent):
            failures.append(
                f"Opener first sentence has no 'I' — opener must open from the candidate's perspective, "
                f"not from a description of the employer's domain or stakes: {first_sent[:120]}"
            )

    return failures


def verify_letter(letter_text: str, api_key: str, model: str) -> VerificationResult:
    hard_failures = _hard_check(letter_text)
    if hard_failures:
        return VerificationResult(verdict="FAIL", failures=hard_failures)

    prompt = VERIFY_PROMPT.format(letter=letter_text)
    try:
        raw = get_provider(model, api_key).complete(VERIFY_SYSTEM, prompt, max_tokens=512, temperature=0)
    except Exception:
        return VerificationResult(verdict="PASS", failures=[])
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
