from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Layer 1: Deterministic pattern filter
# Catches the most common bad question shapes before any LLM cost is incurred.
# ---------------------------------------------------------------------------

_BAD_PATTERNS: list[tuple[str, str]] = [
    # Inventory counts with no specific anchor — person can't reliably recall, proves nothing
    (r"\bhow many\b(?!.{0,60}(specific|particular|exact|that|which|the \w+))", "asks for an inventory count with no specific anchor — ask about consequence or ownership instead"),
    (r"how often did you\b", "asks for frequency — ask about what broke or was at stake instead"),
    # False precision on metrics
    (r"what (percent|percentage|fraction|ratio) (of|did|improvement)", "asks for a metric the person likely can't recall — ask for the observable outcome instead"),
    # Pure unanchored reflection — no specific system, decision, or situation named
    (r"^what did you (learn|take away|gain) (from this|from that|overall|in general|working (there|here))\??$", "too generic — ask what a specific failure or constraint revealed about the system"),
    (r"^what (are|were) you (most )?proud of\??$", "too generic — ask about who depended on it or what specifically changed"),
    (r"^(describe|tell me about) your (overall |general )?(role|background|experience)\??$", "too generic — ask about a specific thing they owned or decided"),
    (r"^what (was|is) your (biggest|greatest|main) (strength|weakness)\??$", "too generic — ask about a specific situation or constraint instead"),
    # Feelings
    (r"how (did|do) you feel about", "asks for feelings — ask about decisions or consequences instead"),
    # Open-ended "walk me through" process questions — produce summaries, not evidence
    (r"^(can you )?(walk me through|take me through|describe the process of)", "asks for a process walkthrough — ask about a specific decision, failure, or consequence instead"),
]


def check_patterns(question: str) -> str | None:
    """Return a rejection reason if the question matches a bad pattern, else None."""
    q = question.lower().strip()
    for pattern, reason in _BAD_PATTERNS:
        if re.search(pattern, q):
            return reason
    return None


# ---------------------------------------------------------------------------
# Layer 2: LLM judge (Haiku — fast, cheap, binary classification)
# Only runs on questions that pass the pattern filter.
# Judging is a more reliable LLM task than rule-following generation.
# ---------------------------------------------------------------------------

_JUDGE_SYSTEM = """\
You are judging whether a Q&A question will surface concrete, memorable evidence \
for a cover letter paragraph.

A GOOD question:
- Is answerable from memory without needing to check records
- Surfaces something that proves ownership, stakes, decision-making, or impact
- Gets a specific answer (a situation, a consequence, a constraint, a decision)
- Could produce a sentence that would belong in a strong cover letter

A BAD question:
- Asks for counts, numbers, or metrics the person likely can't recall
- Asks for process descriptions ("walk me through") that produce summaries
- Asks for self-reflection ("what did you learn", "what are you proud of")
- Is so vague the answer could apply to any job
- Would produce a generic, interchangeable answer

Return ONLY valid JSON: {"pass": true} or {"pass": false, "reason": "one sentence"}
"""

_JUDGE_MODEL = "claude-haiku-4-5-20251001"


def judge_question(
    question: str,
    context: str,
    api_key: str,
) -> tuple[bool, str]:
    """LLM judge: returns (passes, rejection_reason_or_empty).
    Uses Haiku — fast and cheap for binary classification.
    """
    import json
    import anthropic
    from coverletter.costs import record

    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"Context: {context[:300]}\n\nQuestion to judge: {question}"

    response = client.messages.create(
        model=_JUDGE_MODEL,
        max_tokens=128,
        system=_JUDGE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    record(_JUDGE_MODEL, response.usage.input_tokens, response.usage.output_tokens)

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        if data.get("pass"):
            return True, ""
        return False, data.get("reason", "question unlikely to surface useful evidence")
    except Exception:
        return True, ""  # parse failure — don't block, let it through


_COMPANY_JUDGE_SYSTEM = """\
You are a fact-accuracy checker for interview questions.

A question FAILS if it states or implies a specific fact about a named company
(e.g., "At Acme Corp, the dashboards were failing") that does NOT appear in the
library search results provided.

A question PASSES if:
- It makes no company-specific factual claims, OR
- Every company-specific claim it makes is directly supported by the library results

Return ONLY valid JSON: {"pass": true} or {"pass": false, "reason": "one sentence \
naming the unsupported claim and the company it was wrongly attributed to"}
"""

_DRAFT_JUDGE_SYSTEM = """\
You are checking whether a cover letter paragraph draft stays within the bounds of \
what was said in the conversation.

A draft FAILS if it contains specific factual claims that were NOT stated by the person \
in their conversation responses — e.g., invented metrics, company facts not mentioned, \
outcomes the person never described, details that appear to come from library search \
results rather than the conversation.

A draft PASSES if every specific claim traces to something the person actually said.

Return ONLY valid JSON: {"pass": true} or \
{"pass": false, "reason": "one sentence naming the specific invented claim"}
"""


def _parse_judge_response(raw: str) -> tuple[bool, str]:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    try:
        data = __import__("json").loads(raw)
        if data.get("pass"):
            return True, ""
        return False, data.get("reason", "failed accuracy check")
    except Exception:
        return True, ""  # parse failure — don't block


def _extract_library_companies(library_results: str) -> set[str]:
    """Extract company/role names from library result headers like '[Acme Corp / ingestion]'."""
    return {m.strip() for m in re.findall(r'\[([^/\]]+?)\s*/', library_results)}


def company_accuracy_check(
    question: str,
    library_results: str,
    api_key: str,
) -> tuple[bool, str]:
    """Check that company-specific claims in the question appear in the library results.

    Only runs if the question mentions a company name that appears in library headers.
    Returns (passes, rejection_reason_or_empty).
    """
    if not api_key or not library_results or library_results == "No matching paragraphs found.":
        return True, ""
    companies = _extract_library_companies(library_results)
    if not companies:
        return True, ""
    q_lower = question.lower()
    mentioned = [c for c in companies if c.lower() in q_lower]
    if not mentioned:
        return True, ""  # question names no company from library — skip LLM check

    import anthropic
    from coverletter.costs import record

    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"Library search results:\n{library_results[:2000]}\n\n"
        f"Question: {question}"
    )
    response = client.messages.create(
        model=_JUDGE_MODEL,
        max_tokens=128,
        system=_COMPANY_JUDGE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    record(_JUDGE_MODEL, response.usage.input_tokens, response.usage.output_tokens)
    return _parse_judge_response(response.content[0].text)


def validate_draft(
    draft: str,
    conversation_turns: str,
    api_key: str,
) -> tuple[bool, str]:
    """Check that draft claims trace to the conversation, not invented or from library.

    conversation_turns: the user's direct replies in the session (not system messages).
    Returns (passes, rejection_reason_or_empty).
    """
    if not api_key or not conversation_turns.strip():
        return True, ""

    import anthropic
    from coverletter.costs import record

    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"What the person said in this conversation:\n{conversation_turns[:2000]}\n\n"
        f"Draft paragraph:\n{draft}"
    )
    response = client.messages.create(
        model=_JUDGE_MODEL,
        max_tokens=160,
        system=_DRAFT_JUDGE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    record(_JUDGE_MODEL, response.usage.input_tokens, response.usage.output_tokens)
    return _parse_judge_response(response.content[0].text)


def validate_question(
    question: str,
    context: str,
    api_key: str,
    use_llm_judge: bool = True,
    library_results: str = "",
) -> tuple[bool, str]:
    """Two-layer validation: deterministic patterns, then LLM judge.

    Company accuracy is NOT checked at the question level — questions may legitimately
    ask about experience at multiple companies, or ask which company an experience
    belongs to when it's a gap. Company fact accuracy is caught by the draft judge.

    Returns (passes, rejection_reason_or_empty).
    """
    # Layer 1: free, instant
    reason = check_patterns(question)
    if reason:
        return False, reason

    # Layer 2: LLM quality judge (Haiku)
    if use_llm_judge and api_key:
        return judge_question(question, context, api_key)

    return True, ""
