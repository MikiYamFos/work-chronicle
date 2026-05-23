from __future__ import annotations

import json
import textwrap
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

YOUR JOB: ask ONE question per turn to draw out specific, concrete details that are \
NOT already in the library. Never ask multiple questions at once.

GOOD QUESTIONS ask about:
- The specific constraint, failure, or decision that made this harder than it looked
- Who depended on the output and what they could not do without it
- What broke or was at risk when something went wrong
- What the team or business gained access to after it shipped
- Scope expressed as consequence and ownership, not inventory counts

BAD QUESTIONS — never ask these:
- "How many X did you build/write/own?" — inventory counts the person may not recall
  and that prove nothing about ownership or impact
- "What percentage improvement did you achieve?" — false precision; ask for the
  observable outcome instead
- "What are you most proud of?" or "What did you learn?" — produces generic answers
- Anything requiring records the person no longer has access to
- Anything already documented in the library

IMPORTANT NUANCES:
- Do not force "production environment" framing onto personal projects.
- If the context includes a JD gap, focus questions on surfacing experience that \
  speaks to that specific gap and angle.
- If the context includes an EXPERIENCE FRAMING BLOCK (raw facts + covered/missing angles): \
  treat the raw facts as things you already know — do not re-ask them. \
  Target your questions specifically at the MISSING angles listed. \
  Use the raw facts as grounding so your questions are concrete, not generic.

WHEN TO DRAFT: after 3 substantive exchanges, write DRAFT on a line by itself, \
then write the paragraph immediately after. COUNT YOUR EXCHANGES. If you have asked \
3 questions and received 3 answers, your next output MUST be a draft. \
If asked to draft at any point, draft immediately. When the person has given you \
a detailed answer describing what they built, who used it, and what it did, \
that counts as sufficient — draft from it.

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
- Use the person's actual words and phrasings where possible
- Be specific and concrete — real decisions, real stakes, real details
- Sound like the person talking, not a resume writer
- Before writing the paragraph, scan every sentence for banned words/structures.
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


import re as _re

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
    return None, text


_MAX_QUESTION_RETRIES = 2


def _call_model(client, model: str, messages: list[dict]) -> object:
    """Single model call — separated so the retry loop can call it cleanly."""
    kwargs: dict = dict(
        model=model,
        max_tokens=2048,
        system=[{"type": "text", "text": BUILD_SYSTEM, "cache_control": {"type": "ephemeral"}}],
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
) -> tuple[str | None, str]:
    """One turn of the Q&A conversation. Handles tool calls internally.
    Questions are validated before being returned — bad questions are rejected
    and regenerated up to _MAX_QUESTION_RETRIES times.
    Returns (draft_or_none, question_or_signal)."""
    from coverletter.question_judge import validate_question

    client = anthropic.Anthropic(api_key=api_key)
    messages = list(history)
    question_retries = 0

    # Extract brief context for the judge (first user message topic)
    judge_context = next(
        (m["content"] if isinstance(m["content"], str) else "" for m in history if m["role"] == "user"),
        ""
    )[:300]

    while True:
        response = _call_model(client, model, messages)

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use" and block.name == "search_library":
                    result = _search_library(
                        block.input.get("query", ""),
                        all_paragraphs or [],
                        voyage_api_key=voyage_api_key,
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                ""
            ).strip()
            draft, question = _extract_draft(text)

            if draft:
                return draft, ""

            # Validate the question before surfacing it
            if question and question_retries < _MAX_QUESTION_RETRIES:
                passes, reason = validate_question(question, judge_context, api_key)
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


def force_draft(
    history: list[dict],
    api_key: str,
    model: str,
    all_paragraphs: list[Paragraph] | None = None,
    voyage_api_key: str = "",
) -> str:
    """Force a draft from current history regardless of exchange count."""
    forced = history + [{"role": "user", "content": "Please draft the paragraph now from everything we've discussed."}]
    draft, _ = qa_turn(forced, api_key, model, all_paragraphs, voyage_api_key=voyage_api_key)
    return draft or ""


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
    wrapped = textwrap.fill(text.replace("\n", " "), width=90)

    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = "# New Paragraphs (built from scratch)\n"

    h2 = f"## {role}"
    h3 = f"### {section}"

    if h2 in existing and h3 in existing:
        entry = f"\n{meta_line}{wrapped}\n"
    elif h2 in existing:
        entry = f"\n{h3}\n\n{meta_line}{wrapped}\n"
    else:
        entry = f"\n{h2}\n\n{h3}\n\n{meta_line}{wrapped}\n"

    if path.exists():
        with path.open("a", encoding="utf-8") as f:
            f.write(entry)
    else:
        path.write_text(existing + entry, encoding="utf-8")
