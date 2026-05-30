from __future__ import annotations

import re
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

import anthropic

from coverletter.costs import supports_temperature
from coverletter.parser import Paragraph

EDITOR_SYSTEM = """\
You are a writing assistant helping improve a cover letter paragraph library.
The writer's voice is direct, specific, first person, and never generic.

ABSOLUTE RULES — never violate:
- No em-dashes (—). Use a period and a new sentence, or restructure the clause.
- Never use: "actually", "matters", "not just", "not only", "not simply",
  "the hard part was not", "data wrangling is hard"
- No fake-contrast: "not X, but Y" / "not because X, but because Y"
- No sentences starting with "That"
- No defensive tone ("I own my mistakes", "I do not ship work I do not trust")
- No generic openers ("This role aligns", "This experience connects", "Most formative")
- No weak hedging or apologetic phrasing
- No invented claims — stay within the original content

Rewrite only the paragraph given. Return only the rewritten paragraph — no preamble,
no commentary, no explanation.
"""

_REWRITE_PROMPT = """\
Paragraph context: {role} / {section}

Issue to fix: {issue}

Original:
{text}

Writer's direction: {direction}

Rewrite the paragraph, fixing the issue and following the direction.
Do not invent new claims. Stay close to the original content and voice.
"""


@dataclass
class Issue:
    type: str          # "em_dash" | "thin_claim" | "redundant"
    paragraph: Paragraph
    detail: str
    partner: Paragraph | None = None  # for redundant pairs only


ISSUE_LABELS = {
    "em_dash": "Em-dash usage",
    "redundant": "Redundant pairs (high word overlap)",
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return {w for w in words if len(w) > 3}


def _overlap(a: str, b: str) -> float:
    """Bidirectional token overlap — min of both coverage directions."""
    ta = _tokenize(a)
    tb = _tokenize(b)
    if not ta or not tb:
        return 0.0
    return min(len(ta & tb) / len(ta), len(ta & tb) / len(tb))


def scan_issues(paragraphs: list[Paragraph]) -> list[Issue]:
    issues: list[Issue] = []
    seen_redundant: set[frozenset[int]] = set()

    for p in paragraphs:
        if "—" in p.text:
            sample = next((ln for ln in p.text.splitlines() if "—" in ln), "")
            issues.append(Issue(type="em_dash", paragraph=p, detail=f'Contains em-dash: "{sample.strip()}"'))

    for i, p1 in enumerate(paragraphs):
        for p2 in paragraphs[i + 1:]:
            pair = frozenset([p1.index, p2.index])
            if pair in seen_redundant:
                continue
            score = _overlap(p1.text, p2.text)
            if score > 0.55:
                seen_redundant.add(pair)
                issues.append(Issue(
                    type="redundant",
                    paragraph=p1,
                    detail=f"{score:.0%} word overlap with paragraph in {p2.role} / {p2.section}",
                    partner=p2,
                ))

    return issues


def rewrite_paragraph(
    paragraph: Paragraph,
    issue: str,
    direction: str,
    api_key: str,
    model: str,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = _REWRITE_PROMPT.format(
        role=paragraph.role,
        section=paragraph.section,
        issue=issue,
        text=paragraph.text,
        direction=direction,
    )
    kwargs: dict = dict(
        model=model,
        max_tokens=1024,
        system=[{"type": "text", "text": EDITOR_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )
    if supports_temperature(model):
        kwargs["temperature"] = 0.3
    response = client.messages.create(**kwargs)
    return response.content[0].text.strip()


def wrap_text(text: str, width: int = 90) -> str:
    """Normalize line wrapping for writing back to file."""
    return textwrap.fill(text.replace("\n", " "), width=width)


def apply_edit(paragraphs_file: Path, old_text: str, new_text: str) -> bool:
    """Replace old_text with new_text in the paragraphs file in-place."""
    content = paragraphs_file.read_text(encoding="utf-8")
    if old_text not in content:
        return False
    paragraphs_file.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
    return True


def delete_paragraph(paragraphs_file: Path, paragraph: Paragraph) -> bool:
    """
    Mark paragraph as deleted. Replaces text with [deleted] which the parser
    already filters out via its placeholder rule.
    """
    return apply_edit(paragraphs_file, paragraph.text, "[deleted]")


def read_multiline(prompt: str) -> str:
    """Read lines until a blank line (Enter twice). Returns stripped text."""
    print(prompt)
    print("Press Enter twice when done.")
    lines = []
    try:
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                lines.pop()
                break
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        pass
    return "\n".join(lines).strip()
