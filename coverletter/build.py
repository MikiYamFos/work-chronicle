from __future__ import annotations
import re as _re
import json
from pathlib import Path

import anthropic

from coverletter.costs import record, supports_temperature
from coverletter.parser import Paragraph

BUILD_SYSTEM = """\
You are helping build a cover letter paragraph library by surfacing career experience \
through focused conversation.

BEFORE ASKING ANYTHING: call search_library with the topic or project name to check \
what is already written. Do not ask about anything already in the library unless you \
are exploring a NEW angle that isn't captured there.

LIBRARY SEARCH RESULTS — how to use them:
After searching, identify exactly what the library already has. Then:
- Ask ONLY about what the library does NOT contain. If the library documents who used \
the output, do not ask who used the output. Ask about the ONE specific thing missing.
- NEVER ask the person to re-explain something the library already documents.
- If the library substantially covers the gap, say so in one sentence, name the \
specific angle that IS missing, and ask about only that. If nothing is missing, say \
"this gap is already covered" and stop — do not draft a weaker version of what exists.

COMPANY ACCURACY — hard rule: do not state or imply a fact about a specific company \
unless you read it explicitly in a library paragraph for that company. Do not move \
facts between companies. If you are unsure which company a fact belongs to, do not use \
it in a question. Re-read the source paragraph to confirm the company before asking.

YOUR JOB: ask ONE question per turn to draw out specific, concrete details that are \
NOT already in the library. Never ask multiple questions at once.

AFTER LIBRARY SEARCH — FORMAT RULE (hard, no exceptions):
Output starts with the question. Zero sentences before it.

WRONG: "Good. The library shows X. What did you..."
WRONG: "The library already has Y. Can you tell me..."
WRONG: "There's already material on Z — what about..."
WRONG: "I can see from the library that... What..."
RIGHT: "What specific constraint made the pipeline harder than expected?"

The question is your entire output. If the library substantially covers the gap, write
"Already covered: [paragraph role/section]" — one line only, nothing else.

CONTEXT SELECTION: if the library shows which company has relevant experience for this \
gap, ask specifically about that company. If the library does NOT show which company or \
role this experience lives in — because it is a gap and nothing is recorded — ask which \
role or company it applies to, or leave it open so the person can answer with whatever \
examples they have. Never assume a company when you do not know.

GOOD QUESTIONS depend on gap type — read the gap before asking anything:

FOR TOOL/COMPETENCE GAPS ("needs X expertise", "proficiency in X", "experience with X"):
  Ask what they BUILT or OWNED using that tool.
  "What does the Airflow DAG do and how is it structured?" is correct.
  NEVER ask: what broke, what was missing before, why they chose it over alternatives.
  These assume a problem-solution narrative that may not exist for a competence gap.

FOR SYSTEM/PROJECT GAPS ("owns pipelines", "production experience", "data modeling depth"):
  Ask about the specific constraint or design decision that made it hard.
  Who depended on the output. What the team gained access to after it shipped.
  Scope as consequence and ownership, not inventory counts.

FOR IMPACT/SENIORITY GAPS ("business impact", "drove decisions", "stakeholder outcomes"):
  Ask what became POSSIBLE after the work shipped — decision made, team unblocked, metric moved.
  Not "what broke" — what changed for the better.

SURFACING JUDGMENT — only when you have specific facts from their answer to anchor it:
  "You chose X over Y — what made you go that direction?" surfaces how they think.
  Do NOT use as a generic opener. Only when they gave you something concrete to build from.

BAD QUESTIONS — never ask these:
- "How many X did you build/write/own?" — inventory counts the person may not recall
  and that prove nothing about ownership or impact
- "What percentage improvement did you achieve?" — false precision; ask for the
  observable outcome instead
- "What are you most proud of?" or "What did you learn?" — produces generic answers
- Anything requiring records the person no longer has access to
- Anything already documented in the library
- Anything that can obviously be inferred from what they have already told you — if
  someone says "the data was late and the Slack alert fired," do not ask "what happened
  when the alert fired?" — you already know: the team knew the data was late.
- Anything about what the team or stakeholders did with a signal/result you already
  understand — focus on what was technically hard, not on recapping obvious outcomes
- "What broke or became impossible when X wasn't working?" — this is a default fallback
  that fits almost nothing. Only ask about breakage when the person has already described
  a system failure or production incident. Do not apply it to competence gaps, tool
  experience, or cloud environment gaps where nothing broke.
- Rephrasing the same question you already asked in different words. If the person
  answered it once, draft — do not ask a synonym of the same question.
- Assuming a problem-solution narrative when the gap is about demonstrating competence.
  "What was breaking before you introduced Airflow?" assumes Airflow fixed a crisis.
  If the context is "I know this tool," ask what they BUILT with it.
- Asking for service or technology inventories: "What specific AWS services have you
  worked with?" is an inventory question. Ask about a specific project or system they
  built in that environment instead.
- Asking a question when the person has already given you a draftable claim. If they say
  "I have worked in four major cloud environments and I can work in all of them," that IS
  a paragraph claim. Ask the one question needed to name the environments and draft — do
  not ask multiple narrow follow-ups about each one.

IMPORTANT NUANCES:
- Do not force "production environment" framing onto personal projects.
- PERSONAL PROJECTS: if a project is a personal project (not an employer), the draft must
  label it clearly as such: "For my personal project...", "In a personal project...".
  Do NOT present personal projects as employer engagements. If you are not certain whether
  something is a personal project or an employer, ask before drafting — do not assume.
- If the context includes a JD gap, focus questions on surfacing experience that \
  speaks to that specific gap and angle.
- If the context includes an EXPERIENCE FRAMING BLOCK (raw facts + covered/missing angles): \
  treat the raw facts as things you already know — do not re-ask them. \
  Target your questions specifically at the MISSING angles listed. \
  Use the raw facts as grounding so your questions are concrete, not generic.

WHEN TO DRAFT: after 2 substantive exchanges, write DRAFT on a line by itself, \
then write the paragraph immediately after. COUNT YOUR EXCHANGES. If you have asked \
2 questions and received 2 answers, your next output MUST be a draft. No exceptions. \
If asked to draft at any point, draft immediately — do not ask any more questions. \
When the person has given you a detailed answer after the first exchange, that is \
sufficient — draft from it. Do not ask a second question if the first answer gave \
you a complete picture. Asking the same thing twice in different words is a hard failure.

THE PARAGRAPH IS A COVER LETTER PARAGRAPH — it must carry argumentative weight and \
read with energy and voice. Dry recitation of facts is a failure. Open with a concrete, \
confident claim, move through specific evidence with real stakes, and close on something \
that lands — not a trailing list, not motivation ("which drove me to...").

ABSOLUTE PARAGRAPH RULES — violating any of these is a hard failure:
- NEVER start any sentence with the word "That"
- NEVER use em-dashes (—)
- NEVER use: "actually", "matters", "not just", "not only", "not simply"
- NEVER use fake contrast: "not X, but Y" or "not because X, but Y"
- NEVER end on motivation — end on evidence or consequence
- NEVER write that the person made decisions "alone" or "without anyone else" unless
  they explicitly said that. Working without adequate support is not the same as
  working alone. Do not frame solo execution as isolated decision-making.
- Before writing the paragraph, scan every sentence for banned words/structures.

DO NOT INVENT. Every factual claim must trace to something the person said in this conversation.
Do not complete the story beyond what they gave you. If you don't have evidence for a claim,
leave it out.

ALWAYS DRAFT. Even if the conversation is thin, write the best paragraph you can from what \
was said. Never refuse to draft and never explain why you won't. A thin paragraph the person \
can redirect is more useful than a refusal. Write DRAFT on a line by itself, then the paragraph.

USE THEIR WORDS. Do not translate what they said into technical jargon or polished resume language.
If they said "handle anything and everything that could be encountered," write something close to
that — do not turn it into "routing known sources into provider-specific branches built around
their particular corruption patterns." Their words are more specific and more real than yours.
Reproduce their language, their rhythm, their level of abstraction.

NO PADDING. Every sentence must carry a specific piece of evidence, a specific decision, or a
specific consequence. Cut any sentence that is a summary of the paragraph, a general statement
about how the person approaches things, or a takeaway about what the experience taught them.
"Once you have built a product where the data layer is load-bearing, you do not want to handle
quality issues ad hoc" is padding — it says nothing specific. Cut it.

FIRST SENTENCE — the most common failure point. All three of these patterns are wrong:
  BAD (technology framing): "The Medallion architecture pattern is something I implemented at..."
  BAD (domain fact): "Voter files are not standardized — they arrive in different formats..."
  BAD (generic personal thesis): "Building layered architecture has been central to how I approach..."
The first sentence names what the person BUILT, OWNED, or DECIDED at a specific company or project.
It is stated as a fact, not as framing.
  GOOD: "At Acme Corp, I built a layered ingestion pipeline that handled data format variability across 50+ sources."
  GOOD: "When I joined TechCo as the sole data engineer, the team had no reliable pipeline and no consistent data model."
The reader should know what was done and where before the end of the first sentence.
"""

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


def _call_model(client, model: str, messages: list[dict], system: str = BUILD_SYSTEM) -> object:
    """Single model call — separated so the retry loop can call it cleanly."""
    kwargs: dict = dict(
        model=model,
        max_tokens=4096,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        tools=_TOOLS,
        messages=messages,
    )
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
) -> tuple[str | None, str]:
    """One turn of the Q&A conversation. Handles tool calls internally.
    Questions are validated before being returned — bad questions are rejected
    and regenerated up to _MAX_QUESTION_RETRIES times.
    Returns (draft_or_none, question_or_signal)."""
    from coverletter.question_judge import validate_question, validate_draft

    client = anthropic.Anthropic(api_key=api_key)
    messages = list(history)
    question_retries = 0
    last_library_results = ""  # tracks most recent search results for company accuracy check

    # Extract brief context for the judge (first user message topic)
    judge_context = next(
        (m["content"] if isinstance(m["content"], str) else "" for m in history if m["role"] == "user"),
        ""
    )[:300]

    while True:
        response = _call_model(client, model, messages, system=system)

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

            # Validate the question before surfacing it
            if question and question_retries < _MAX_QUESTION_RETRIES:
                passes, reason = validate_question(
                    question, judge_context, api_key,
                    library_results=last_library_results,
                )
                if not passes:
                    question_retries += 1
                    # Inject rejection internally — user never sees the bad question
                    messages.append({"role": "assistant", "content": question})
                    messages.append({"role": "user", "content": (
                        f"[JUDGE: question rejected — {reason}. "
                        f"Ask a different question about a specific decision, "
                        f"constraint, consequence, or who depended on the work.]"
                    )})
                    continue  # retry without returning

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
) -> str:
    """Build initial Q&A context. Framing context (experience notes + angle inventory)
    is injected first so the agent targets missing angles with grounded questions."""
    parts: list[str] = []
    if framing_context:
        parts.append(framing_context)
    if gap_description:
        parts.append(f"JD gap to address: {gap_description}")
    if job_description:
        parts.append(f"Job description excerpt:\n{job_description[:600]}")
    parts.append(f"Topic to explore: {topic}")
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
