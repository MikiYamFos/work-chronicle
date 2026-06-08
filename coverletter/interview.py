"""Interview prep agent — builds a structured briefing from a JD + optional recruiter note.

The agent has three tools:
  search_library      — semantic search over paragraph library
  get_claims          — search claims DB by topic (library + resume sources)
  get_experience_facts — look up experiences.md register for a named experience

Produces a structured markdown briefing with four sections:
  1. Role snapshot
  2. What they're probing for (JD themes + recruiter signals)
  3. Your coverage (per theme: strongest claims/paragraphs + gaps)
  4. Likely questions with "lead with this" notes

--summary produces a shorter version: snapshot + themes + one match per theme.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from coverletter.parser import Paragraph
    from coverletter.experiences import Experience

_INTERVIEW_SYSTEM = """\
You are building a structured interview prep briefing for a job candidate.

You have three tools available:
- search_library: search the candidate's paragraph library for relevant experience
- get_claims: search the candidate's extracted claims DB for matching claims
- get_experience_facts: look up structured facts for a named experience or employer

Your job:
1. Analyze the JD (and recruiter note if provided) to identify 3-6 key themes the \
   interviewer will probe on.
2. For each theme, use ALL THREE tools to gather the candidate's relevant material.
3. Identify what is covered on the resume vs. what is only in the library (needs to \
   come out verbally).
4. Identify genuine gaps where the candidate has thin or no material.
5. Generate likely interview questions based on the JD and recruiter signals.

Output the briefing as structured markdown. Use exactly these section headers:

## Role Snapshot
(3-5 sentences. What this role is actually about — not a restatement of the JD.)

## What They're Probing For
(Themes ranked by signal strength. If a recruiter note was provided, call out \
those signals explicitly under a "Recruiter Signals" sub-header.)

## Your Coverage
(Per theme: strongest matching material. Mark each item as [RESUME] if it's on \
the resume, [LIBRARY] if it's only in the paragraph library and needs to come out \
verbally, or [GAP] if there's no strong material.)

## Likely Questions
(4-6 questions. For each: the question, then "Lead with:" pointing to the \
candidate's best material, or "Gap — be honest about:" if thin.)

Be direct and honest. Do not inflate coverage. A [GAP] is more useful than a \
weak match dressed up as coverage.
"""

_SUMMARY_SYSTEM = """\
You are building a SHORT interview prep summary — one page, fast to read before a call.

You have three tools: search_library, get_claims, get_experience_facts.

Output markdown with exactly these sections:

## Role Snapshot
(2-3 sentences max.)

## Key Themes
(Bullet list of 3-5 themes, each with the single strongest matching claim or \
paragraph from the candidate's material. Mark [RESUME], [LIBRARY], or [GAP].)
"""

_TOOLS = [
    {
        "name": "search_library",
        "description": (
            "Search the candidate's paragraph library for relevant experience. "
            "Call this for each theme to find matching prose paragraphs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Topic, skill, or requirement to search for"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_claims",
        "description": (
            "Search the claims DB for relevant claims (both library-extracted and resume-sourced). "
            "Returns matching claims tagged with their source so you can distinguish "
            "what's on the resume vs. what's only in the library."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic or requirement to find claims for"}
            },
            "required": ["topic"],
        },
    },
    {
        "name": "get_experience_facts",
        "description": (
            "Look up the experience register for a specific employer or project. "
            "Returns raw facts, angle inventory, and any seed Q&A targets."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "experience_name": {"type": "string", "description": "Employer name or project title"}
            },
            "required": ["experience_name"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _tool_search_library(
    query: str,
    paragraphs: list["Paragraph"],
    voyage_api_key: str = "",
) -> str:
    from coverletter.build import _search_library
    return _search_library(query, paragraphs, voyage_api_key=voyage_api_key)


def _tool_get_claims(topic: str, db_path: Path | None) -> str:
    if db_path is None or not db_path.exists():
        return "Claims DB not available."
    try:
        from coverletter.db import open_db
        conn = open_db(db_path)
        words = [w for w in re.findall(r"[a-z]+", topic.lower()) if len(w) > 3]
        if not words:
            return "Topic too short to search."
        like_clauses = " OR ".join(f"LOWER(text) LIKE ?" for _ in words)
        params = [f"%{w}%" for w in words]
        rows = conn.execute(
            f"SELECT text, source FROM claims WHERE ({like_clauses}) LIMIT 8",
            params,
        ).fetchall()
        conn.close()
        if not rows:
            return f"No claims found matching '{topic}'."
        lines = []
        for r in rows:
            tag = "[RESUME]" if r["source"] == "resume" else "[LIBRARY]"
            lines.append(f"{tag} {r['text']}")
        return f"Claims matching '{topic}':\n" + "\n".join(lines)
    except Exception as exc:
        return f"Claims DB error: {exc}"


def _tool_get_experience_facts(
    experience_name: str,
    experiences: list["Experience"],
    paragraphs: list["Paragraph"],
) -> str:
    if not experiences:
        return "No experience register available."
    from coverletter.experiences import find_experience, coverage_context
    exp = find_experience(experiences, experience_name)
    if not exp:
        names = ", ".join(e.name for e in experiences[:8])
        return f"No experience matching '{experience_name}'. Available: {names}"
    return coverage_context(exp, paragraphs)


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def _dispatch_tool(
    name: str,
    inputs: dict,
    paragraphs: list["Paragraph"],
    experiences: list["Experience"],
    db_path: Path | None,
    voyage_api_key: str,
) -> str:
    if name == "search_library":
        return _tool_search_library(inputs.get("query", ""), paragraphs, voyage_api_key)
    if name == "get_claims":
        return _tool_get_claims(inputs.get("topic", ""), db_path)
    if name == "get_experience_facts":
        return _tool_get_experience_facts(inputs.get("experience_name", ""), experiences, paragraphs)
    return f"Unknown tool: {name}"


def run_interview_agent(
    jd_text: str,
    recruiter_note: str,
    paragraphs: list["Paragraph"],
    experiences: list["Experience"],
    db_path: Path | None,
    api_key: str,
    model: str,
    voyage_api_key: str = "",
    summary: bool = False,
) -> str:
    """Run the interview prep agent. Returns the completed briefing markdown."""
    import anthropic
    from coverletter.costs import record, supports_temperature

    system = _SUMMARY_SYSTEM if summary else _INTERVIEW_SYSTEM

    user_content = f"Job Description:\n\n{jd_text}"
    if recruiter_note.strip():
        user_content += f"\n\n---\nRecruiter / HR Note:\n\n{recruiter_note.strip()}"
    user_content += (
        "\n\n---\nUse the tools to gather the candidate's relevant material for each "
        "theme, then write the briefing."
    )

    client = anthropic.Anthropic(api_key=api_key)
    messages: list[dict] = [{"role": "user", "content": user_content}]

    while True:
        kwargs: dict = dict(
            model=model,
            max_tokens=4096,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
            tools=_TOOLS,
        )
        if supports_temperature(model):
            kwargs["temperature"] = 0.2

        response = client.messages.create(**kwargs)
        usage = response.usage
        record(
            model,
            usage.input_tokens,
            usage.output_tokens,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            label="interview_agent",
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _dispatch_tool(
                        block.name, block.input,
                        paragraphs, experiences, db_path, voyage_api_key,
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # end_turn — extract the text
            return next(
                (block.text.strip() for block in response.content if hasattr(block, "text")),
                "",
            )
