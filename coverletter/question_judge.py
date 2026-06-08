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
    # Breakage/failure narrative imposed on tool competence gaps
    # These patterns assume a problem-solution story when none exists.
    (r"\bwhat (broke|was breaking|was failing|was missing|was wrong|stopped working|went wrong|went down|crashed|wasn.t working)\b", "assumes a breakage narrative — only ask about failures if the person described a production incident; for tool/competence gaps ask what they BUILT"),
    (r"\bwhat (became|was) impossible\b", "assumes a failure narrative — ask what they built or owned instead"),
    (r"\bwhat (couldn.t|could not|can.t|cannot) (you |the team |the business )?(do|happen|work)", "assumes something was blocked — for competence gaps ask what they built, not what couldn't happen without them"),
    (r"\bbefore you (introduced|added|implemented|set up|built|created)\b", "assumes the tool was introduced to fix a problem — ask what they built with it instead"),
    # Technology/service inventory questions
    (r"what specific (aws|gcp|azure|cloud) (services|tools|resources)", "asks for a service inventory — ask about a specific system they built in that environment instead"),
    (r"which (aws|gcp|azure|cloud) services", "asks for a service inventory — ask about a specific system they built instead"),
    # Asking why they chose a tool over another — produces rationale, not evidence
    (r"(what|why) (did|do|would) (the|that tool|prefect|airflow|dbt|spark|redshift|bigquery).{0,40}(couldn.t|could not|not handle|not have|not support|instead)", "asks why one tool was chosen over another — only ask this if they described a specific constraint that drove the choice; otherwise ask what they built"),
    # "X could not have handled Y as well" / "X just the right tool" phrasing
    (r"(could not|couldn.t) have (handled|done|supported).{0,40}(as well|instead|better)", "asks about tool limitations — for competence gaps ask what they built, not what the alternative couldn't do"),
    (r"(just the right|the better) tool for", "asks about tool selection rationale — for competence gaps ask what they built with the tool"),
    # "What would you do differently?" — undermines defensibility of past decisions
    (r"\bwhat would you (do|have done) differently\b", "asks the person to second-guess their own decisions — cover letter writing defends choices, it does not revisit them"),
    # Invented difficulty framing — assumes something was hard when the person never said so
    (r"what made .{3,60} (hard|difficult|challenging|tricky|complex) to (define|design|build|implement|structure|create)", "invents a difficulty the person never stated — ask what they built or decided, not what was hard about a specific sub-problem they never mentioned"),
    (r"what (difficulty|difficulties|challenge|challenges) did you (face|encounter|run into|have) (with|when|while|in)", "assumes difficulties — only ask about difficulty if the person described something that was hard; otherwise ask what they built"),
]


# ---------------------------------------------------------------------------
# Metadata clarification questions — always pass, never sent to the LLM judge.
# These fill required holes before a paragraph can be drafted or stored:
# personal project vs employer, which role/company, time period, scope.
# ---------------------------------------------------------------------------

_METADATA_PATTERNS: list[str] = [
    r"\b(personal project|side project|personal work|your own project)\b",
    r"\b(employer|company|organization|role)\b.{0,40}\?(.*)?$",
    r"^(is|was) this (a )?(personal|side|your own|an employer|a work|a paid|a volunteer)",
    r"^(which|what) (company|employer|organization|role|job|position)",
    r"^(was this|is this|is it|was it) (paid|employed|freelance|contractor|volunteer|personal)",
    r"^(did you|were you) (build|do|work on) this (at|for|as part of|while at|during)",
    r"\b(when did you|how long did you|what year|what period|over what)",
    r"^(who|what team|how many people).{0,40}(used|depended on|relied on|consumed)",
]


def _is_metadata_question(question: str) -> bool:
    """Return True if the question is asking for required paragraph metadata."""
    q = question.lower().strip()
    return any(re.search(p, q) for p in _METADATA_PATTERNS)


def check_patterns(question: str) -> str | None:
    """Return a rejection reason if the question matches a bad pattern, else None.

    Metadata clarification questions always pass — they fill required holes
    (personal project vs employer, which role, time period) before drafting.
    """
    # Metadata questions are exempt from all rejection patterns
    if _is_metadata_question(question):
        return None
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
for a cover letter paragraph. The context tells you what gap or topic is being covered.

GAP TYPE CHANGES WHAT A GOOD QUESTION LOOKS LIKE:

COMPETENCE/TOOL GAPS — context mentions "expertise in X", "proficiency with X", \
"experience with X", or names specific tools (dbt, Airflow, GCP, AWS, Spark, etc.):
  GOOD: asks what they built or owned using that tool — "What does the Airflow DAG do?"
  BAD: asks what broke, what was missing before, why they chose it over another tool,
       what the tool replaced, what became impossible without it.
  Competence gaps are about demonstrating capability, not solving a crisis.

PROJECT/PRODUCTION GAPS — context mentions "owns pipelines", "production experience", \
"system design", "data modeling", incident response:
  GOOD: specific constraint, failure mode, design decision, or production consequence.
  Breakage and failure questions ARE appropriate here.

IMPACT/SENIORITY GAPS — context mentions "business impact", "drove decisions", \
"stakeholder outcomes", "seniority signals":
  GOOD: what changed or became possible after the work — decision made, team unblocked.
  BAD: what broke, what was missing — ask about what was ENABLED.

A GOOD question regardless of gap type:
- Is answerable from memory without needing to check records
- Gets a specific answer (situation, consequence, constraint, decision, or system)
- Could produce a sentence that belongs in a strong cover letter

A BAD question regardless of gap type:
- Asks for counts, numbers, or percentages
- Asks for process walkthroughs ("walk me through")
- Self-reflection that opens a topic for exploration — "what did this teach you about \
  how X works?", "what did you learn about governance/scale/leadership?" These prompt \
  the person to philosophize about a domain, not tell an experience. \
  GOOD reflection asks what specifically CHANGED or SURPRISED them — those produce \
  concrete answers. \
  BAD reflection asks what something taught them ABOUT A TOPIC — that produces a lecture.
- Is so vague the answer could apply to any job
- Is a rephrasing of a question already asked in this conversation
- Invents a premise the person never stated — "what made X hard to design" when \
  they never said X was hard; "what difficulties did you face with Y" when they \
  never described Y as difficult. If the question assumes a specific constraint, \
  failure, or difficulty that does not appear in the conversation, reject it.

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
    from coverletter.provider import get_provider

    prompt = f"Context: {context[:300]}\n\nQuestion to judge: {question}"
    raw = get_provider(_JUDGE_MODEL, api_key).complete(_JUDGE_SYSTEM, prompt, max_tokens=128)
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

    from coverletter.provider import get_provider

    prompt = (
        f"Library search results:\n{library_results[:2000]}\n\n"
        f"Question: {question}"
    )
    raw = get_provider(_JUDGE_MODEL, api_key).complete(_COMPANY_JUDGE_SYSTEM, prompt, max_tokens=128)
    return _parse_judge_response(raw)


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

    from coverletter.provider import get_provider

    prompt = (
        f"What the person said in this conversation:\n{conversation_turns[:2000]}\n\n"
        f"Draft paragraph:\n{draft}"
    )
    raw = get_provider(_JUDGE_MODEL, api_key).complete(_DRAFT_JUDGE_SYSTEM, prompt, max_tokens=160)
    return _parse_judge_response(raw)


def validate_question(
    question: str,
    context: str,
    api_key: str,
    use_llm_judge: bool = True,
    library_results: str = "",
) -> tuple[bool, str]:
    """Two-layer validation: deterministic patterns, then LLM judge.

    Metadata clarification questions (personal project vs employer, which role,
    time period) always pass both layers — they fill required holes before drafting.

    Company accuracy is NOT checked at the question level. Company fact accuracy
    is caught by the draft judge.

    Returns (passes, rejection_reason_or_empty).
    """
    # Metadata questions always pass — never sent to the judge
    if _is_metadata_question(question):
        return True, ""

    # Layer 1: free, instant
    reason = check_patterns(question)
    if reason:
        return False, reason

    # Layer 2: LLM quality judge (Haiku)
    if use_llm_judge and api_key:
        return judge_question(question, context, api_key)

    return True, ""
