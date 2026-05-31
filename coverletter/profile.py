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
    seniority_signals: list[str] = field(default_factory=list)
    working_style: list[str] = field(default_factory=list)
    values: list[str] = field(default_factory=list)

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

    def as_seniority_signals_text(self) -> str:
        if not self.seniority_signals:
            return ""
        lines = ["Seniority signals for this role type:"]
        lines += [f"- {s}" for s in self.seniority_signals]
        return "\n".join(lines)

    def as_working_style_text(self) -> str:
        if not self.working_style:
            return ""
        lines = ["How I work and what I value:"]
        lines += [f"- {w}" for w in self.working_style]
        return "\n".join(lines)

    def as_avoid_text(self) -> str:
        if not self.avoid:
            return ""
        lines = ["Poor-fit environments (use to recognize strong fit when a role is the opposite):"]
        lines += [f"- {a}" for a in self.avoid]
        return "\n".join(lines)

    def as_values_text(self) -> str:
        if not self.values:
            return ""
        lines = ["Core values:"]
        lines += [f"- {v}" for v in self.values]
        return "\n".join(lines)

    def as_fit_context(self) -> str:
        """Goals + avoid + values — everything relevant to evaluating role fit."""
        parts = [p for p in [
            self.as_goals_text(),
            self.as_avoid_text(),
            self.as_values_text(),
        ] if p]
        return "\n\n".join(parts)

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
        "seniority_signals": (
            "# What separates senior candidates from mid-level ones in your domain and level.\n"
            "# These reflect YOUR expertise, not the job title on any specific posting.\n"
            "# A senior DE applying to 'AI Engineer' or 'Staff Analytics Engineer' roles uses\n"
            "# the same signals — they travel with you across applications.\n"
            "# Only revisit if your career direction genuinely shifts.\n"
            "# Example (senior data engineering background):\n"
            "#   \"Business impact: quantified outcomes, not just 'built X'\"\n"
            "#   \"Production ownership: SLAs, incidents, reliability decisions\"\n"
            "#   \"System design judgment: trade-offs made and why\"\n"
            "#   \"Data modeling depth: schema decisions, SCD handling, warehouse design\"\n"
            "#   \"Cross-functional effectiveness: translating infra needs to business context\"\n"
        ),
        "working_style": (
            "# How you work, how you think, and what you value as an engineer.\n"
            "# This is biographical material — not skill claims, not what you've built.\n"
            "# Used when answering 'about me' and biographical application prompts.\n"
            "# Write these as honest self-characterizations in your own voice.\n"
            "# The library paragraphs prove the claims; these shape the framing.\n"
            "# Example entries:\n"
            "#   \"I'm the person people think through a problem with to figure out how to build it\"\n"
            "#   \"I move naturally between technical and non-technical audiences — I translate, not present\"\n"
            "#   \"I think creatively about data problems; my background gives me angles engineers without\n"
            "#    that history don't have\"\n"
            "#   \"I care about the craft — I want the pipeline to be right, not just running\"\n"
        ),
        "values": (
            "# What you believe and care about — as a programmer, as a teammate, as a person.\n"
            "# Not skill claims. Not goals. The things that orient how you work with others\n"
            "# and what kind of engineer you are at a deeper level.\n"
            "# Used in biographical responses alongside working_style.\n"
            "# Write in your own voice, affirmatively.\n"
            "# Example entries:\n"
            "#   \"I believe in open-source development and contribute to the commons where I can\"\n"
            "#   \"I care about mentorship — I have benefited from people who made time for me\n"
            "#    and I pay that forward\"\n"
            "#   \"I write tests not because I am told to but because I have been burned by not doing it\"\n"
            "#   \"I am direct and honest with teammates even when it is uncomfortable — I learned early\n"
            "#    that clarity and directness build trust and cut through wasted effort\"\n"
            "#   \"I think the best engineering teams are ones where people can say what they see\"\n"
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
    from coverletter.provider import get_provider

    library_text = "\n\n".join(
        f"[{p.role} / {p.section}]\n{p.text}" for p in paragraphs
    )

    prompt = f"""\
You are reading someone's cover letter paragraph library. Based on the concrete evidence \
in these paragraphs, suggest specific, honest entries for each section of their candidate \
profile. Do not invent anything not evidenced in the paragraphs.

Return ONLY a JSON object with these keys: goals, differentiators, focus_areas, avoid, seniority_signals, values.
Each key maps to a list of strings — 3-5 items each.

Rules for each section:
- goals: what this person's work trajectory points toward — scope, environment, type of \
  impact. Infer from what they've owned and what they've built.
- differentiators: their real technical edge. Name specific technologies, scale, \
  ownership level. No generic claims. Every item must be evidenced by the library.
- focus_areas: areas they've gone deep in and likely want to develop further.
- avoid: environments where their strengths would be wasted or their weaknesses amplified. \
  Honest, not negative.
- seniority_signals: the 4-6 dimensions that distinguish senior candidates from mid-level \
  ones in this person's specific role type. Infer the role type from the library. \
  Each entry must be a short label followed by a colon and a one-line description of \
  what evidence looks like. Example: "Production ownership: SLAs, incidents, reliability \
  decisions — not just building greenfield." Write these for the actual role type evident \
  in the library, not generically.
- values: what this person cares about as a programmer and teammate — inferred from how \
  they describe their work, what they emphasize, what they built even when not required to. \
  Examples: open-source orientation, test discipline, mentorship, honesty on teams, \
  care about correctness over shipping fast. Write in first person as self-characterizations. \
  Every item must be grounded in the library evidence.

PARAGRAPH LIBRARY:
{library_text}
"""

    import json
    import re
    raw = get_provider(model, api_key).complete("", prompt, max_tokens=2048)

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
            "seniority_signals": data.get("seniority_signals", []),
            "working_style": data.get("working_style", []),
            "values": data.get("values", []),
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
        seniority_signals=_get("seniority_signals"),
        working_style=_get("working_style"),
        values=_get("values"),
    )
