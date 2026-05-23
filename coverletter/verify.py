from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
import anthropic

from coverletter.costs import record, supports_temperature
from coverletter.parser import Paragraph

VERIFY_SYSTEM = """\
You are a strict cover letter quality checker. You apply a checklist of rules to a
cover letter draft and return a JSON verdict. You do not rewrite. You only evaluate.

Return ONLY valid JSON with this shape:
{
  "verdict": "PASS" or "FAIL",
  "failures": ["description of failure 1", "description of failure 2", ...]
}

If verdict is PASS, failures must be an empty list.
If verdict is FAIL, failures must name the specific sentence or structure that failed
and cite which rule it violated. Be specific — quote the offending text.
"""

VERIFY_PROMPT = """\
Evaluate the following cover letter against all rules below.

=== COVER LETTER TO EVALUATE ===
{letter}

=== RULES ===

CHECK 1 — HARD FAIL SCAN
Immediately fail if the letter contains any of:
- Any em-dash character (—) anywhere in the letter body. This is an absolute ban.
  Quote the exact sentence containing it.
- The words: "actually", "matters", "this matters because", "not just", "not only",
  "more than", "not simply", "the hard part was not"
- Any fake-contrast structure: defines work by first saying what it was not
  (e.g., "This was not about X — it was about Y")
- Any paragraph starting with "That"
- Generic bridge openers: "That experience fits," "This role aligns,"
  "What stands out," "The clearest connection," "This is the kind of work"
- A paragraph that ends with a list (list-pile ending)
- More than one list in the entire letter
- Invented metaphors, slogans, or polished abstractions not traceable to source material
- Any sentence whose core claim cannot be traced to the source material or the job description

CHECK 2 — SOURCE-CONTROL SCAN (BODY PARAGRAPHS ONLY)
The opening paragraph and closing paragraph are intentionally synthesized fresh for each
application — do NOT flag them for source-traceability.
For all BODY paragraphs (everything between opener and closer): every sentence must map
to source material or the job description.
Flag any body sentence that appears invented, generic, or AI-generated.

CHECK 3 — PARAGRAPH OPENER SCAN
Every paragraph must open with a concrete, source-based claim.
Flag openers that are generic topic statements or mirrors of the job description.

CHECK 4 — PARAGRAPH CLOSER SCAN
Every paragraph must close by landing its point.
Flag paragraphs that trail off, end on a list, or end on a vague summary.

CHECK 5 — COVER-LETTER APPROPRIATENESS SCAN
The letter must not read like: a résumé summary, an AI essay, a generic template,
a stack of topic blocks, a list of skills, or a job description mirror.
Flag anything that sounds like it was written by a template.

CHECK 6 — ADVERSARIAL CHECK
Would the writer immediately call this out as generic, invented, weak, listy,
or not source-based? If yes, flag it.

STRUCTURE CHECK
- OPENER: Is it synthesized specifically for this role and company (not a generic paragraph
  dropped in)? Does it lead with a concrete claim? Does it avoid "I am excited to apply"
  and avoid restating the job title? Does it sound like the same voice as the body?
- BODY: Do body paragraphs each prove one specific point with evidence? Does each open
  with a concrete claim and close by landing its point?
- CLOSER: Is it specific to this company? Does it thank the reader and express genuine
  interest in speaking further? Does it end on a forward, confident note?

Return ONLY the JSON verdict. No explanation outside the JSON.
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


def verbatim_check(
    letter_text: str,
    source_paragraphs: list[Paragraph],
    threshold: float = 0.72,
) -> list[VerbatimViolation]:
    """
    Checks each letter sentence against all source sentences.
    Returns sentences where less than `threshold` fraction of words
    appear in any source sentence — catches wholesale invention while
    tolerating trimming and minor tense/inflection changes.
    Skips the salutation line and the final paragraph (closer).
    """
    # Collect all source sentences
    source_sentences: list[str] = []
    for p in source_paragraphs:
        source_sentences.extend(_split_sentences(p.text))

    if not source_sentences:
        return []

    # Split letter into paragraphs, skip salutation (first), opener (second),
    # and closer (last) — opener and closer are synthesized fresh, not source-checked.
    letter_paras = [p.strip() for p in letter_text.split("\n\n") if p.strip()]
    if len(letter_paras) <= 3:
        return []

    body_paras = letter_paras[2:-1]  # skip salutation, opener, and closer
    letter_sentences: list[str] = []
    for para in body_paras:
        letter_sentences.extend(_split_sentences(para))

    violations: list[VerbatimViolation] = []
    for sent in letter_sentences:
        # Skip very short sentences — likely fragments or transitions
        if len(sent.split()) < 6:
            continue
        best_score = 0.0
        best_src = ""
        for src in source_sentences:
            score = _token_coverage(sent, src)
            if score > best_score:
                best_score = score
                best_src = src
        if best_score < threshold:
            violations.append(VerbatimViolation(sentence=sent, best_match=best_src, score=best_score))

    return violations


def _hard_check(letter_text: str) -> list[str]:
    """Deterministic checks that don't need an LLM."""
    failures = []
    for line in letter_text.splitlines():
        if "—" in line:
            failures.append(f"Em-dash found: {line.strip()[:120]}")
    return failures


def verify_letter(letter_text: str, api_key: str, model: str) -> VerificationResult:
    hard_failures = _hard_check(letter_text)
    if hard_failures:
        return VerificationResult(verdict="FAIL", failures=hard_failures)

    client = anthropic.Anthropic(api_key=api_key)
    prompt = VERIFY_PROMPT.format(letter=letter_text)
    kwargs: dict = dict(
        model=model,
        max_tokens=1024,
        system=[{"type": "text", "text": VERIFY_SYSTEM, "cache_control": {"type": "ephemeral"}}],
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
