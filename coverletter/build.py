from __future__ import annotations
import re as _re
import json
from pathlib import Path

import anthropic

from coverletter.costs import record, supports_temperature
from coverletter.parser import Paragraph

###############################################################################
# BUILD_SYSTEM — assembled dynamically via build_system_prompt().
# Do NOT use BUILD_SYSTEM directly. Call build_system_prompt() instead.
###############################################################################

_BUILD_CORE = """\
You are helping build a cover letter paragraph library by surfacing career experience \
through focused conversation.

YOUR JOB: ask ONE question per turn. Never ask multiple questions at once. \
Your question is your entire output — no preamble, no "Great answer", no commentary.

WHEN TO DRAFT: write DRAFT on a line by itself, then the paragraph immediately after.
- After 2 substantive exchanges, you MUST draft. No exceptions.
- If asked to draft at any point, draft immediately.
- If the first answer gives you a complete picture, draft from it — do not ask again.
- Asking the same thing twice in different words is a hard failure.

BAD QUESTIONS — never ask:
- Inventory counts: "How many X did you build?" — proves nothing
- False precision: "What percentage improvement?" — ask for the observable outcome
- Self-reflection that opens a topic: "What did this teach you about governance?" \
  prompts a lecture. Ask what specifically CHANGED or SURPRISED them instead — \
  those produce concrete answers that belong in a paragraph.
- Never ask what they would do differently — cover letter writing defends decisions.
- Process walkthroughs: "Walk me through your process"
- Anything the person already answered — if they said it once, draft
- Anything obviously inferable from what they told you

PERSONAL PROJECTS: if a project is not employer work, the draft must say so clearly: \
"For my personal project..." Do not present personal projects as employer engagements.

THE PARAGRAPH must carry argumentative weight and read with energy and voice.

ABSOLUTE PARAGRAPH RULES — hard failures:
- NEVER start a sentence with "That"
- NEVER use em-dashes (—)
- NEVER use: "actually", "matters", "not just", "not only", "not simply"
- NEVER use fake contrast: "not X, but Y"
- NEVER use "I have been the [person/engineer/one]"
- NEVER end on motivation — end on evidence or consequence
- NEVER say the person decided or worked "alone" unless they said that explicitly

DO NOT INVENT. Every claim must trace to something said in this conversation.

ALWAYS DRAFT. Even thin — write what you have. A thin draft the person can redirect \
is more useful than a refusal. Write DRAFT on its own line, then the paragraph.

USE THEIR WORDS. Their language, their level of abstraction. Do not translate into \
polished resume speak.

NO PADDING. Every sentence carries a specific fact, decision, or consequence. Cut \
anything that summarizes or editorializes.

FIRST SENTENCE: names what the person BUILT, OWNED, or DECIDED. Stated as a fact, \
not framing. DO NOT name an employer or company unless the person named it in this \
conversation. Use only what they gave you.
"""

_BUILD_TOOLS = """\
LIBRARY: call search_library before asking anything. Check what is already written.
- Ask ONLY about what the library does NOT contain.
- If the library substantially covers this topic, say "Already covered: [role/section]" \
and stop.
- NEVER ask the person to re-explain something the library already documents.
- COMPANY ACCURACY: never state a fact about a specific company unless you read it \
explicitly in a library paragraph for that company. Do not move facts between companies.
- After searching: output starts with the question. Zero sentences before it. No \
"Good", no "The library shows", no preamble of any kind.
- Your first question must be open — do not name any project or employer from the \
library results. The library shows what exists; it does not tell you what the person \
wants to discuss next. Let them name the project.
"""

_BUILD_GAP_COMPETENCE = """\
GAP TYPE: COMPETENCE / TOOL
This gap is about demonstrating capability with a specific tool or skill area.
- Ask what they BUILT or OWNED using that tool or in that domain.
- NEVER ask: what broke before they had it, what was missing, why they chose it \
over another tool. There may be no crisis — this is about showing capability, not \
solving a problem.
- Do not ask about failure or breakage unless the person already described an incident.
"""

_BUILD_GAP_PRODUCTION = """\
GAP TYPE: SYSTEM / PRODUCTION
This gap is about production ownership, system design, or data modeling depth.
- Ask about a specific constraint, design decision, or consequence of ownership.
- Who depended on the output. What the team could do after it shipped.
- Failure and breakage questions ARE appropriate here if the person described incidents.
- Surface judgment: "You chose X over Y — what drove that?" only when they gave you \
concrete facts to anchor it.
"""

_BUILD_GAP_IMPACT = """\
GAP TYPE: IMPACT / SENIORITY
This gap is about business outcomes, stakeholder decisions, or seniority signals.
- Ask what became POSSIBLE after the work shipped: decision made, team unblocked, \
metric moved.
- Do not ask what broke — ask what changed for the better.
- Surface the downstream consequence, not the technical detail.
"""

_BUILD_CONTEXT_RESUME = """\
RESUME: the conversation includes a RESUME BLOCK. Treat every bullet and role in it \
as established fact — do not re-ask what it already states. The resume tells you WHAT; \
your job is to surface the HOW, WHY, and WHAT CHANGED. Ask about constraints and \
consequences, not about what was built (that is already known).
"""

_BUILD_CONTEXT_FRAMING = """\
EXPERIENCE FRAMING: the conversation includes raw facts and a list of covered and \
missing angles. Treat the raw facts as things you already know — do not re-ask them. \
Target your question at ONE of the MISSING angles listed. Use the raw facts to make \
your question concrete, not generic.
"""


def _classify_gap(gap_description: str) -> str:
    """Return the appropriate gap-type block based on the gap description."""
    if not gap_description:
        return ""
    g = gap_description.lower()
    competence_signals = (
        "expertise in", "proficiency", "experience with", "knowledge of",
        "familiarity with", "skills in", "llm", "evaluation framework",
        "annotation", "dataset quality", "versioning", "instrumentation",
        "integrat", "degree", "stem",
    )
    impact_signals = (
        "business impact", "drove decisions", "stakeholder", "seniority",
        "senior", "requirements translation", "scale", "adoption",
    )
    production_signals = (
        "owns pipeline", "production", "system design", "data modeling",
        "modeling depth", "incident", "observability", "monitoring",
        "ownership", "end to end", "end-to-end",
    )
    if any(s in g for s in impact_signals):
        return _BUILD_GAP_IMPACT
    if any(s in g for s in production_signals):
        return _BUILD_GAP_PRODUCTION
    if any(s in g for s in competence_signals):
        return _BUILD_GAP_COMPETENCE
    return ""  # general — no gap block, core rules apply


def build_system_prompt(
    use_tools: bool = True,
    gap_description: str = "",
    has_resume: bool = False,
    has_framing: bool = False,
) -> str:
    """Assemble the BUILD system prompt from only the relevant blocks.

    Core rules always included. Tool block, gap type block, and context blocks
    injected only when relevant — prevents the model from applying conflicting
    rules that belong to a different context.
    """
    parts = [_BUILD_CORE]
    if use_tools:
        parts.append(_BUILD_TOOLS)
    gap_block = _classify_gap(gap_description)
    if gap_block:
        parts.append(gap_block)
    if has_resume:
        parts.append(_BUILD_CONTEXT_RESUME)
    if has_framing:
        parts.append(_BUILD_CONTEXT_FRAMING)
    return "\n\n".join(parts)


# Legacy constant — used by callers that haven't been updated yet.
# Equivalent to build_system_prompt(use_tools=True) with no gap or context blocks.
BUILD_SYSTEM = build_system_prompt(use_tools=True)

PERSPECTIVE_SYSTEM = """\
You are helping someone write a perspective paragraph for their cover letter library.
The angle type is specified at the start of the conversation. Read it before asking anything.

=== ANGLE TYPES ===

THROUGH-LINE (angle=through-line):
  This is NOT a story about one experience. It is the thread that runs across ALL of them.
  Your job: find what is consistent across the whole arc.
  The paragraph spans the career, not one job. DO NOT drill into a single experience.
  Questions that work for through-line:
  - What do you find yourself doing in every environment, regardless of what the job is called?
  - What kind of problem keeps finding you across roles?
  - What have people consistently asked you to take on, at different jobs and in different contexts?
  - Across everything you have done, what has been true about how you approach hard problems?
  Questions that do NOT work for through-line:
  - "What were you doing right before you made the move?" (that is pivot, not through-line)
  - "What happened at [specific company]?" (drilling into one instance, not the pattern)

PIVOT (angle=pivot):
  A specific transition — what drove it and what was happening right before.
  Go after the decision and the moment:
  - What were you actually doing right before you made the move?
  - What could you not do in that role that you wanted to?
  - What did you start teaching yourself, and why that specific thing?
  - What was the decision, and what was in the room when you made it?

REFRAME (angle=reframe):
  Same experience, different lens. "When I was doing X it looked like Y, but what I was
  actually building was Z." Go after the gap between how it looked and what it was:
  - How was this experience described or understood by the people around you at the time?
  - What were you actually developing that the title or context did not name?

SYNTHESIS (angle=synthesis):
  Two paths that combine into something neither produces alone.
  - What did [path A] train you to do concretely?
  - What does [path B] give you that people who only did [path A] do not have?

=== QUESTIONING DISCIPLINE (ALL ANGLES) ===

ONE question per turn. Follow their thread, not yours.

The test: did the concept come from them, or from you?
- If they used it, ask into it. If they did not, do not introduce it.
- "Was that frustrating?" is always leading — imports an emotional frame.
- "Was it X or Y?" is always leading — presents two options and asks them to pick your frame.
- "What did that teach you?" is open — any answer works.
- "What did you do next?" is open — sequence without suggested outcome.

WHEN TO DRAFT: after 3 substantive exchanges, or when asked.
Write DRAFT on a line by itself, then the paragraph immediately after.

THE PARAGRAPH must match the angle type:
- Through-line: spans the whole arc. Names the consistent thread. Does not read like one job story.
- Pivot: grounded account of a specific transition. Concrete details. Actual decision and what drove it.
- Reframe/synthesis: makes the non-obvious connection visible without over-explaining it.

ABSOLUTE PARAGRAPH RULES:
- NEVER start any sentence with "That"
- NEVER use em-dashes (---)
- NEVER use: "actually", "matters", "not just", "not only", "not simply"
- NEVER use fake contrast: "not X, but Y"
- NEVER end on motivation -- end on evidence or consequence
- Use the person's actual words and phrasings
- Sound like the person talking, not a resume writer
"""

MISSION_SYSTEM = """\
You are helping someone articulate why a specific company's purpose, product, or mission \
resonates with them personally, so they can source that genuine connection into cover letters.

BEFORE ASKING ANYTHING: call search_library to see what the person has already said about \
their values, their through-line, and what kinds of work they find meaningful. Do not ask \
them to repeat things already captured.

THIS IS NOT A COVER LETTER OPENER. It is a paragraph that captures genuine personal \
connection to a purpose or domain — specific enough to be real, broad enough to be reusable \
for similar organizations.

YOUR JOB: ask ONE question per turn to draw out the specific, personal reason this purpose \
resonates. Not "why do you want to work there" — the actual thing.

GOOD QUESTIONS:
- "What is it about [this specific thing they do] that you actually find compelling?"
- "What would it mean — concretely — if [this purpose] succeeded at scale?"
- "What in your background or values connects to this? Not just professionally."
- "When did you first encounter this kind of work and what struck you about it?"
- "What is the thing that makes this different from a company that just sells a product?"

BAD QUESTIONS:
- "What excites you about this company?" — too generic
- "How does your experience align with their mission?" — backward, starts from resume logic
- "What do you know about the industry?" — not relevant

AFTER LIBRARY SEARCH — FORMAT RULE: your output is ONLY the question. No preamble.

WHEN TO DRAFT: after 2-3 substantive exchanges, or when asked.
Write DRAFT on a line by itself, then the paragraph immediately after.

THE PARAGRAPH:
- Reads as genuine personal connection, not a cover letter opener
- Specific about WHY this purpose matters to the person, not just WHAT the company does
- Can reference the specific company by name, or describe the domain/purpose more broadly \
  if the person wants it reusable — ask them which they prefer before drafting
- 3-5 sentences
- Ends on what it means to the person or what they want to contribute — not a trailing list

ABSOLUTE PARAGRAPH RULES:
- NEVER start any sentence with "That"
- NEVER start with "I am excited to..."
- NEVER use em-dashes (—)
- NEVER use: "actually", "not just", "not only", "not simply"
- NEVER use fake contrast: "not X, but Y"
- Use the person's actual words and voice
- Sound like the person, not a cover letter writer
"""

_TOOLS = [
    {
        "name": "search_library",
        "description": (
            "Search the paragraph library for existing content. Call this before asking "
            "the user about any project, role, or experience — to avoid re-asking about "
            "things already documented. Returns matching paragraphs with full text."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Project name, company, topic, or keywords to search for",
                }
            },
            "required": ["query"],
        },
    }
]

_DRAFT_MARKER = "DRAFT"


def _tokenize(text: str) -> list[str]:
    return _re.findall(r"[a-z]+", text.lower())


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


# Session-level embedding cache: paragraph index -> vector
# Avoids re-embedding the same paragraphs on every search call within a session.
_embed_cache: dict[int, list[float]] = {}


def _voyage_search(
    query: str,
    paragraphs: list[Paragraph],
    voyage_api_key: str,
    top_k: int = 4,
) -> list[tuple[float, Paragraph]]:
    """Semantic search via Voyage AI. Returns (score, paragraph) pairs, highest first."""
    try:
        import voyageai  # type: ignore

        client = voyageai.Client(api_key=voyage_api_key)

        # Embed paragraphs not yet in cache
        uncached = [p for p in paragraphs if p.index not in _embed_cache]
        if uncached:
            texts = [
                p.text + (" " + p.meta["angle"].replace("-", " ") if p.meta.get("angle") else "")
                for p in uncached
            ]
            doc_result = client.embed(texts, model="voyage-3-lite", input_type="document")
            for p, vec in zip(uncached, doc_result.embeddings):
                _embed_cache[p.index] = vec

        # Embed query (queries are short — don't cache)
        q_result = client.embed([query], model="voyage-3-lite", input_type="query")
        q_vec = q_result.embeddings[0]

        scored = [
            (_cosine(_embed_cache[p.index], q_vec), p)
            for p in paragraphs
            if p.index in _embed_cache
        ]
        scored.sort(key=lambda x: -x[0])
        return scored[:top_k]
    except Exception:
        return []


def _angle_boost(query_words: set[str], paragraph: "Paragraph") -> float:
    """Return a multiplier based on how much the paragraph's angle tag overlaps with the query.
    Angle tags are the most direct categorical signal we have — treat them as high-confidence."""
    angle = paragraph.meta.get("angle", "")
    if not angle:
        return 1.0
    angle_words = set(_re.findall(r"[a-z]+", angle.lower()))
    overlap = len(query_words & angle_words)
    return 1.0 + overlap * 1.5  # each overlapping angle word is a strong signal


def _search_library(
    query: str,
    paragraphs: list[Paragraph],
    voyage_api_key: str = "",
) -> str:
    """Search the paragraph library. Priority: Voyage semantic > tag-boosted BM25 > keyword."""
    if not paragraphs:
        return "No matching paragraphs found."

    query_words = set(_tokenize(query))

    # 1. Voyage semantic search — best quality, only runs if key is available
    if voyage_api_key:
        semantic = _voyage_search(query, paragraphs, voyage_api_key)
        # Apply angle boost on top of semantic score so tagged paragraphs rise further
        boosted = [(score * _angle_boost(query_words, p), p) for score, p in semantic]
        boosted.sort(key=lambda x: -x[0])
        top = [(s, p) for s, p in boosted[:4] if s > 0.25]
        if top:
            results = []
            for _, p in top:
                angle = f" [angle: {p.meta['angle']}]" if p.meta.get("angle") else ""
                results.append(f"[{p.role} / {p.section}]{angle}\n{p.text}")
            return "\n\n---\n\n".join(results)

    # 2. BM25 with angle tag boost — catches vocabulary overlap when Voyage isn't available
    try:
        from rank_bm25 import BM25Okapi
        corpus = [_tokenize(p.section + " " + p.role + " " + p.text) for p in paragraphs]
        bm25 = BM25Okapi(corpus)
        raw_scores = list(bm25.get_scores(_tokenize(query)))
        boosted = [
            (raw_scores[i] * _angle_boost(query_words, p), p)
            for i, p in enumerate(paragraphs)
        ]
        boosted.sort(key=lambda x: -x[0])
        top = [(s, p) for s, p in boosted[:4] if s > 0]
    except ImportError:
        # 3. Pure keyword + angle fallback
        scored = []
        for p in paragraphs:
            text_words = set(_tokenize(p.section + " " + p.role + " " + p.text))
            hits = len(query_words & text_words)
            score = hits * _angle_boost(query_words, p)
            if score:
                scored.append((score, p))
        scored.sort(key=lambda x: -x[0])
        top = scored[:4]

    if not top:
        return "No matching paragraphs found."

    results = []
    for _, p in top:
        angle = f" [angle: {p.meta['angle']}]" if p.meta.get("angle") else ""
        results.append(f"[{p.role} / {p.section}]{angle}\n{p.text}")
    return "\n\n---\n\n".join(results)


_PREAMBLE_START = _re.compile(
    r'^(?:good|great|perfect|the library|there(?:\'s| is) already|i can see|'
    r'looking at the library|based on|already covered)',
    _re.IGNORECASE,
)


def _strip_preamble(text: str) -> str:
    """Strip leading narrative the model outputs before the actual question.

    The BUILD_SYSTEM instructs the model not to add preamble, but models
    occasionally ignore this. Strip it deterministically rather than hoping
    the model complies every time.
    """
    stripped = text.strip()
    if not _PREAMBLE_START.match(stripped):
        return stripped
    q = stripped.find('?')
    if q == -1:
        return stripped
    before = stripped[:q]
    for sep in ['\n', '. ', '! ', ' — ', '— ', ', ']:
        idx = before.rfind(sep)
        if idx != -1:
            candidate = stripped[idx + len(sep):].strip()
            # Only accept comma-splits that start with a question word
            if sep == ', ' and not _re.match(r'^(what|who|when|where|why|how|which|did|was|were|is|are|can|could|would)', candidate, _re.IGNORECASE):
                continue
            return candidate
    return stripped


def _extract_draft(text: str) -> tuple[str | None, str]:
    """Return (draft_text, question_text). One will be None/empty."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == _DRAFT_MARKER:
            draft = "\n".join(lines[i + 1:]).strip()
            return draft, ""
    if text.strip().startswith(_DRAFT_MARKER):
        draft = text.strip()[len(_DRAFT_MARKER):].strip()
        return draft, ""
    return None, _strip_preamble(text)


_MAX_QUESTION_RETRIES = 2


def _qa_turn_no_tools(
    history: list[dict],
    api_key: str,
    model: str,
    all_paragraphs: list[Paragraph] | None = None,
    voyage_api_key: str = "",
    system: str = BUILD_SYSTEM,
) -> tuple[str | None, str]:
    """qa_turn for providers that don't support tool calling.

    Pre-runs library search and injects results into the system prompt, then
    runs a simple multi-turn loop with no tool machinery.
    """
    from coverletter.provider import get_provider
    from coverletter.question_judge import validate_question, validate_draft

    provider = get_provider(model, api_key)

    # Pre-search using the first user message as the query
    search_query = next(
        (m["content"] for m in history if m["role"] == "user" and isinstance(m["content"], str)),
        "",
    )
    library_results = ""
    if search_query and all_paragraphs:
        library_results = _search_library(search_query, all_paragraphs, voyage_api_key=voyage_api_key)

    augmented_system = system
    if library_results:
        augmented_system = (
            system
            + f"\n\n━━━ LIBRARY SEARCH RESULTS (pre-searched for this topic) ━━━\n{library_results}\n"
            + "Do NOT ask about anything already documented above. "
            + "Ask ONLY about what is missing from the library results.\n"
        )

    messages = list(history)
    question_retries = 0
    def _build_judge_context(msgs: list[dict]) -> str:
        parts = []
        for m in msgs:
            role = m["role"]
            content = m["content"] if isinstance(m["content"], str) else ""
            if content and role in ("user", "assistant"):
                parts.append(f"{role}: {content[:400]}")
        return "\n".join(parts)[-1200:]

    while True:
        # Build single user content string from the last user message
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user" and isinstance(m["content"], str)),
            "",
        )
        text = provider.complete(augmented_system, last_user, max_tokens=4096, temperature=0.4)
        draft, question = _extract_draft(text)

        if draft:
            conversation_turns = "\n".join(
                m["content"] for m in messages
                if m["role"] == "user" and isinstance(m["content"], str)
            )
            passes, reason = validate_draft(draft, conversation_turns, api_key)
            if not passes and question_retries < _MAX_QUESTION_RETRIES:
                question_retries += 1
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": (
                    f"[DRAFT JUDGE: draft rejected — {reason}. "
                    f"Rewrite using only what was said in this conversation. "
                    f"Write DRAFT on its own line, then the paragraph.]"
                )})
                continue
            return draft, ""

        if question and api_key:
            passes, reason = validate_question(
                question, _build_judge_context(messages), api_key,
                library_results=library_results,
            )
            if not passes:
                import sys
                print(f"[JUDGE BLOCKED] {reason!r}\n  Q: {question}", file=sys.stderr)
                if question_retries < _MAX_QUESTION_RETRIES:
                    question_retries += 1
                    messages.append({"role": "assistant", "content": question})
                    messages.append({"role": "user", "content": (
                        f"[JUDGE: question rejected — {reason}. "
                        f"Ask a different question about a specific decision, "
                        f"constraint, consequence, or who depended on the work.]"
                    )})
                    continue
                else:
                    return None, ""

        return None, question or ""


def _call_model(client, model: str, messages: list[dict], system: str = BUILD_SYSTEM, use_tools: bool = True) -> object:
    """Single model call — separated so the retry loop can call it cleanly."""
    kwargs: dict = dict(
        model=model,
        max_tokens=4096,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=messages,
    )
    if use_tools:
        kwargs["tools"] = _TOOLS
    if supports_temperature(model):
        kwargs["temperature"] = 0.4
    response = client.messages.create(**kwargs)
    usage = response.usage
    record(
        model, usage.input_tokens, usage.output_tokens,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
    )
    return response


def qa_turn(
    history: list[dict],
    api_key: str,
    model: str,
    all_paragraphs: list[Paragraph] | None = None,
    voyage_api_key: str = "",
    system: str = BUILD_SYSTEM,
    use_tools: bool = True,
) -> tuple[str | None, str]:
    """One turn of the Q&A conversation. Handles tool calls internally.
    Questions are validated before being returned — bad questions are rejected
    and regenerated up to _MAX_QUESTION_RETRIES times.
    Returns (draft_or_none, question_or_signal).

    use_tools: when False, search_library is not registered at all. Use when
    the caller wants to suppress library search entirely (e.g. skip_library_search).
    """
    from coverletter.question_judge import validate_question, validate_draft
    from coverletter.provider import parse_model

    provider_name, _ = parse_model(model)
    if provider_name != "anthropic":
        return _qa_turn_no_tools(history, api_key, model, all_paragraphs, voyage_api_key, system)

    client = anthropic.Anthropic(api_key=api_key)
    messages = list(history)
    question_retries = 0
    last_library_results = ""  # tracks most recent search results for company accuracy check

    def _build_judge_context(msgs: list[dict]) -> str:
        parts = []
        for m in msgs:
            role = m["role"]
            content = m["content"] if isinstance(m["content"], str) else ""
            if content and role in ("user", "assistant"):
                parts.append(f"{role}: {content[:400]}")
        return "\n".join(parts)[-1200:]

    while True:
        response = _call_model(client, model, messages, system=system, use_tools=use_tools)

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use" and block.name == "search_library":
                    result = _search_library(
                        block.input.get("query", ""),
                        all_paragraphs or [],
                        voyage_api_key=voyage_api_key,
                    )
                    last_library_results = result  # save for company accuracy check
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results + [
                {
                    "type": "text",
                    "text": (
                        "[FORMAT RULE: Your next output is ONLY the question — "
                        "no preamble, no 'Good', no 'The library shows'. "
                        "Ask ONLY about something NOT in the search results above. "
                        "Start with the question word itself.]"
                    ),
                }
            ]})
        else:
            text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                ""
            ).strip()
            draft, question = _extract_draft(text)

            if draft:
                # Validate draft claims trace to conversation, not invented or from library
                conversation_turns = "\n".join(
                    m["content"]
                    for m in messages
                    if m["role"] == "user" and isinstance(m["content"], str)
                )
                passes, reason = validate_draft(draft, conversation_turns, api_key)
                if not passes and question_retries < _MAX_QUESTION_RETRIES:
                    question_retries += 1
                    messages.append({"role": "assistant", "content": text})
                    messages.append({"role": "user", "content": (
                        f"[DRAFT JUDGE: draft rejected — {reason}. "
                        f"Rewrite the draft. Every claim must trace to something said in this "
                        f"conversation. Do not use facts from library search results. "
                        f"Write DRAFT on its own line, then the paragraph.]"
                    )})
                    continue
                return draft, ""

            # Validate the question before surfacing it — always validate, never leak a bad question
            if question and api_key:
                passes, reason = validate_question(
                    question, _build_judge_context(messages), api_key,
                    library_results=last_library_results,
                )
                if not passes:
                    import sys
                    print(f"[JUDGE BLOCKED] {reason!r}\n  Q: {question}", file=sys.stderr)
                    if question_retries < _MAX_QUESTION_RETRIES:
                        question_retries += 1
                        messages.append({"role": "assistant", "content": question})
                        messages.append({"role": "user", "content": (
                            f"[JUDGE: question rejected — {reason}. "
                            f"Ask a different question about a specific decision, "
                            f"constraint, consequence, or who depended on the work.]"
                        )})
                        continue  # retry
                    else:
                        # Retries exhausted — suppress the bad question, surface nothing
                        return None, ""

            return None, question or ""


_DRAFT_RULES_REMINDER = """\
Draft the paragraph now from what was said in this conversation.

This is a CAPTURE draft. The goal is preserving the person's actual words and meaning \
exactly — not producing polished prose.

WHAT THIS MEANS IN PRACTICE:

If they said "I was the card check queen and ran a fuck ton of checkoffs" — that register,
that specificity, that pride is in the draft. Do not convert it to "managed extensive card
check operations."

If they said "I had to wake up before 7 in the morning 6 days a week and compile a 40
something step excel report" — those exact details are in the draft. Do not round them off
or call it "daily reporting."

If they explained something in a particular sequence — preserve that sequence. Do not
reorganize for flow. Flow is their problem to solve in editing, not yours to impose.

HARD RULES:

1. LIFT THEIR SENTENCES DIRECTLY where possible. The closer the draft is to their actual
   words, the better it is. Paraphrasing is a failure mode, not a feature.

2. DO NOT ADD FRAMING they did not provide. No "this demonstrates", no "this experience
   shows", no opening sentence that summarizes what the paragraph is about.

3. DO NOT SMOOTH THE REGISTER. If they were direct, blunt, or used informal language —
   keep it. That is their voice. Polishing it out is the thing that makes drafts bad.

4. DO NOT COMPRESS. If they gave detail, keep the detail. A long accurate draft is better
   than a short inaccurate one.

5. ZERO INVENTION. If something was not said in this conversation, it is not in the draft.
   Not even plausible inferences. Not even things that are almost certainly true.

6. NO GENERATED OPENERS OR CLOSERS. If the source material does not contain an opening
   sentence, the draft does not have one — start with whatever the first real claim or
   fact is. If the source does not contain a closing sentence, the draft ends on the last
   real piece of content. Do not generate throat-clearing openers or summary closers.
   These are consistently bad and must not appear.

Write DRAFT on its own line, then the paragraph immediately after.\
"""


def _looks_like_question(text: str) -> bool:
    """Return True if text appears to be a question rather than a draft paragraph."""
    stripped = text.strip()
    # A question: short, ends with ?, no newlines (a paragraph would be multi-sentence)
    if stripped.endswith("?") and len(stripped.split()) < 40:
        return True
    # Multiple sentences but starts with a question word and ends with ?
    if stripped.endswith("?") and _re.match(r'^(what|who|when|where|why|how|which|did|was|were|is|are|can|could|would)\b', stripped, _re.IGNORECASE):
        return True
    return False


_EMPLOYER_SIGNALS = _re.compile(
    r"\b(at |while at |worked at |working at |my role at |my job at |"
    r"britbox|universe|unite here|nyu|new york university|campaign|"
    r"employer|company i worked|my employer|the company)\b",
    _re.IGNORECASE,
)
_PERSONAL_SIGNALS = _re.compile(
    r"\b(personal project|side project|on my own time|outside of work|"
    r"hobby|for fun|for myself|not for an employer|not at a job)\b",
    _re.IGNORECASE,
)
# Signals that the text is describing a specific project/system/engagement —
# only if these are present does employer context actually matter.
_PROJECT_SIGNALS = _re.compile(
    r"\b(built|developed|owned|designed|architected|shipped|deployed|"
    r"pipeline|system|tool|app|application|platform|service|workflow|"
    r"database|api|pipeline|dashboard|model|integration|infrastructure|"
    r"project|codebase|repo|script|library|framework)\b",
    _re.IGNORECASE,
)


def needs_metadata_clarification(text: str) -> str | None:
    """Return a boilerplate clarification question if employment context is unclear.

    Costs nothing — purely deterministic. Returns None if:
    - Context is already clear (has employer or personal signals), OR
    - Text doesn't describe a specific project/engagement (ways of being,
      working approaches, general professional observations — no metadata needed)

    The returned string is ready to print directly to the user.
    """
    # Only ask if the text is describing a specific project or engagement
    if not _PROJECT_SIGNALS.search(text):
        return None  # freewriting about approach, philosophy, ways of being — skip

    has_employer = bool(_EMPLOYER_SIGNALS.search(text))
    has_personal = bool(_PERSONAL_SIGNALS.search(text))

    if has_employer or has_personal:
        return None  # clear enough — don't ask

    # Project described but no context signal — ask the boilerplate question
    return (
        "Is this a personal project or work you did at an employer? "
        "If an employer, which one?"
    )


_REVISION_SYSTEM = """\
You are a revision assistant. Your only job is to rewrite the paragraph incorporating \
the correction provided. Write DRAFT on its own line, then the revised paragraph.

DO NOT ASK A QUESTION. DO NOT explain what you changed. Just write the paragraph.

Rules:
- Use the person's exact words and level of abstraction — do not translate into resume speak
- Include every specific fact, detail, and explanation they provided — including in the correction
- Do not invent anything not in the conversation
- Do not name an employer unless the person named it in this conversation
- No em-dashes. No "not just / not only / not simply". No fake contrast.
- Do not start any sentence with "That"
"""


def revise_draft(
    current_draft: str,
    correction: str,
    conversation_history: list[dict],
    api_key: str,
    model: str,
) -> str:
    """Direct revision call — bypasses Q&A machinery entirely.

    Uses a revision-only system prompt so the model cannot ask questions.
    Falls back to returning the original draft if the call fails.
    """
    from coverletter.provider import get_provider, parse_model
    provider_name, _ = parse_model(model)

    # Build a clean message sequence: conversation context + draft + correction
    ctx_parts = []
    for m in conversation_history:
        role = m["role"]
        content = m["content"] if isinstance(m["content"], str) else ""
        if content and role in ("user", "assistant"):
            ctx_parts.append(f"{role}: {content[:600]}")
    ctx = "\n".join(ctx_parts)[-2000:]

    user_msg = (
        f"Conversation so far:\n{ctx}\n\n"
        f"Current draft:\n{current_draft}\n\n"
        f"Correction: {correction}\n\n"
        f"Write DRAFT on its own line, then the revised paragraph."
    )

    try:
        provider = get_provider(model, api_key)
        text = provider.complete(_REVISION_SYSTEM, user_msg, max_tokens=4096, temperature=0.4)
        draft, _ = _extract_draft(text)
        if draft:
            return draft
        # Model wrote a paragraph without the DRAFT marker — acceptable
        return text.strip() or current_draft
    except Exception:
        return current_draft


def force_draft(
    history: list[dict],
    api_key: str,
    model: str,
    all_paragraphs: list[Paragraph] | None = None,
    voyage_api_key: str = "",
    system: str = BUILD_SYSTEM,
) -> str:
    """Force a draft from current history regardless of exchange count.

    If the model returns a question instead of a draft, retries once with a
    harder instruction before returning whatever it gave us.
    """
    forced = history + [{"role": "user", "content": _DRAFT_RULES_REMINDER}]
    draft, raw = qa_turn(forced, api_key, model, all_paragraphs, voyage_api_key=voyage_api_key, system=system)
    if draft:
        return draft
    # raw may be a question — if so, retry with an explicit "no questions" override
    if raw and _looks_like_question(raw):
        harder = history + [{"role": "user", "content": (
            _DRAFT_RULES_REMINDER +
            "\n\nDO NOT ASK A QUESTION. Write the paragraph. "
            "If you need more information you do not have, write the best paragraph possible "
            "from what was already said and mark any uncertain claim with [?]."
        )}]
        draft2, raw2 = qa_turn(harder, api_key, model, all_paragraphs, voyage_api_key=voyage_api_key, system=system)
        return draft2 or raw2 or raw
    # raw is a paragraph without the DRAFT marker — acceptable
    return raw or ""


def _build_initial_context(
    topic: str,
    job_description: str | None = None,
    gap_description: str | None = None,
    framing_context: str = "",
    resume_context: str = "",
    use_tools: bool = True,
) -> str:
    """Build initial Q&A context. Framing context (experience notes + angle inventory)
    is injected first so the agent targets missing angles with grounded questions.
    Resume context is injected as established fact — coach must not re-ask what it states."""
    parts: list[str] = []
    if framing_context:
        parts.append(framing_context)
    if resume_context:
        parts.append(f"RESUME BLOCK — treat as established fact, do not re-ask:\n{resume_context}")
    if gap_description:
        parts.append(f"JD gap to address: {gap_description}")
    if job_description:
        parts.append(f"Job description excerpt:\n{job_description[:600]}")
    parts.append(f"Topic to explore: {topic}")
    if use_tools:
        parts.append("Use the search_library tool now to check what is already written about this topic before asking any questions.")
    return "\n\n".join(parts)


def append_to_library(
    path: Path,
    role: str,
    section: str,
    text: str,
    meta: dict[str, str],
) -> None:
    """Append a new paragraph to the priority library file under the correct headers."""
    meta_parts = ", ".join(f"{k}={v}" for k, v in meta.items())
    meta_line = f"<!-- meta: {meta_parts} -->\n" if meta_parts else ""
    text = text.replace("\n", " ").strip()

    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = "# New Paragraphs (built from scratch)\n"

    h2 = f"## {role}"
    h3 = f"### {section}"

    if h2 in existing and h3 in existing:
        entry = f"\n{meta_line}{text}\n"
    elif h2 in existing:
        entry = f"\n{h3}\n\n{meta_line}{text}\n"
    else:
        entry = f"\n{h2}\n\n{h3}\n\n{meta_line}{text}\n"

    if path.exists():
        with path.open("a", encoding="utf-8") as f:
            f.write(entry)
    else:
        path.write_text(existing + entry, encoding="utf-8")
