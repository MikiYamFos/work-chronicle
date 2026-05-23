from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from coverletter.parser import Paragraph


@dataclass
class CandidateProfile:
    goals: list[str] = field(default_factory=list)
    differentiators: list[str] = field(default_factory=list)
    focus_areas: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.goals or self.differentiators)

    def as_goals_text(self) -> str:
        if not self.goals:
            return ""
        lines = ["Goals for next role:"]
        lines += [f"- {g}" for g in self.goals]
        return "\n".join(lines)

    def as_differentiators_text(self) -> str:
        if not self.differentiators:
            return ""
        lines = ["Core differentiators:"]
        lines += [f"- {d}" for d in self.differentiators]
        return "\n".join(lines)

    def as_full_text(self) -> str:
        parts = [p for p in [self.as_goals_text(), self.as_differentiators_text()] if p]
        return "\n\n".join(parts)


def write_profile(path: Path, data: dict[str, list[str]]) -> None:
    """Write candidate_profile.toml from a dict of section -> list of strings."""
    section_comments = {
        "goals": (
            "# What you actually want from the next role.\n"
            "# Injected into the letter thesis and alignment goal-fit section.\n"
        ),
        "differentiators": (
            "# Your actual technical edge — specific technologies, scale, ownership.\n"
            "# No generic claims. Concrete evidence only.\n"
        ),
        "focus_areas": (
            "# Areas you want to go deeper in during this next role.\n"
        ),
        "avoid": (
            "# Roles or environments that are a poor fit.\n"
            "# Feeds honest goal-alignment assessment.\n"
        ),
    }
    lines = [
        "# Candidate Profile — drives thesis and alignment evaluation\n",
        "# Edit directly or run `coverletter profile` to rebuild.\n",
        "\n",
    ]
    for section, items in data.items():
        comment = section_comments.get(section, "")
        if comment:
            lines.append(comment)
        lines.append(f"[{section}]\n")
        if items:
            lines.append(f"{section} = [\n")
            for item in items:
                escaped = item.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'  "{escaped}",\n')
            lines.append("]\n")
        else:
            lines.append(f"{section} = []\n")
        lines.append("\n")
    path.write_text("".join(lines), encoding="utf-8")


def suggest_from_library(
    paragraphs: "list[Paragraph]",
    api_key: str,
    model: str,
) -> dict[str, list[str]]:
    """Use the LLM to suggest profile sections from the paragraph library."""
    import anthropic
    from coverletter.costs import record

    library_text = "\n\n".join(
        f"[{p.role} / {p.section}]\n{p.text}" for p in paragraphs
    )

    prompt = f"""\
You are reading someone's cover letter paragraph library. Based on the concrete evidence \
in these paragraphs, suggest specific, honest entries for each section of their candidate \
profile. Do not invent anything not evidenced in the paragraphs.

Return ONLY a JSON object with these keys: goals, differentiators, focus_areas, avoid.
Each key maps to a list of strings — 3-5 items each.

Rules for each section:
- goals: what this person's work trajectory points toward — scope, environment, type of \
  impact. Infer from what they've owned and what they've built.
- differentiators: their real technical edge. Name specific technologies, scale, \
  ownership level. No generic claims. Every item must be evidenced by the library.
- focus_areas: DE areas they've gone deep in and likely want to develop further.
- avoid: environments where their strengths would be wasted or their weaknesses amplified. \
  Honest, not negative.

PARAGRAPH LIBRARY:
{library_text}
"""

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    record(model, response.usage.input_tokens, response.usage.output_tokens)

    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            f"Model hit max_tokens limit ({response.usage.output_tokens} tokens). "
            "Response was truncated — JSON will be invalid. Increase max_tokens."
        )

    import json
    import re
    raw = response.content[0].text.strip()

    # Strategy 1: find the outermost JSON object by brace matching
    # This handles preamble text, trailing commentary, and any fence style
    def _extract_json_object(text: str) -> str | None:
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return None

    candidate = _extract_json_object(raw)
    if candidate is None:
        raise RuntimeError(
            f"No JSON object found in model response.\nRaw response:\n{raw}"
        )
    try:
        data = json.loads(candidate)
        return {
            "goals": data.get("goals", []),
            "differentiators": data.get("differentiators", []),
            "focus_areas": data.get("focus_areas", []),
            "avoid": data.get("avoid", []),
        }
    except Exception as e:
        raise RuntimeError(
            f"Could not parse suggestions from model response.\n"
            f"Parse error: {e}\n"
            f"Extracted candidate:\n{candidate}"
        ) from e


def load_profile(path: Path) -> CandidateProfile:
    if not path.exists():
        return CandidateProfile()
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return CandidateProfile()

    with path.open("rb") as f:
        data = tomllib.load(f)

    def _get(key: str) -> list[str]:
        val = data.get(key, [])
        # Support both flat list and [section]\nkey = [...] TOML styles
        if isinstance(val, dict):
            val = val.get(key, [])
        return val if isinstance(val, list) else []

    return CandidateProfile(
        goals=_get("goals"),
        differentiators=_get("differentiators"),
        focus_areas=_get("focus_areas"),
        avoid=_get("avoid"),
    )
