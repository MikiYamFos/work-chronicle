from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from coverletter.parser import Paragraph


@dataclass
class Experience:
    name: str
    company: str = ""
    years: str = ""
    angles: list[str] = field(default_factory=list)
    raw_notes: str = ""
    qa_targets: list[str] = field(default_factory=list)  # questions seeded from augmentations


_KV_RE = re.compile(r"^(company|years|angles)\s*:\s*(.+)$", re.IGNORECASE)


def load_experiences(path: Path) -> list[Experience]:
    """Parse experiences.md into structured Experience objects."""
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    experiences: list[Experience] = []
    current: Experience | None = None
    note_lines: list[str] = []
    in_qa_targets = False

    def flush() -> None:
        nonlocal note_lines, in_qa_targets
        if current is not None:
            current.raw_notes = "\n".join(note_lines).strip()
            note_lines = []
            in_qa_targets = False

    for line in lines:
        stripped = line.strip()

        # Skip file title
        if stripped.startswith("# "):
            continue

        # Experience header
        if stripped.startswith("## "):
            flush()
            if current is not None:
                experiences.append(current)
            current = Experience(name=stripped[3:].strip())
            note_lines = []
            in_qa_targets = False
            continue

        if current is None:
            continue

        # Key-value metadata lines
        m = _KV_RE.match(stripped)
        if m:
            key = m.group(1).lower()
            val = m.group(2).strip()
            if key == "company":
                current.company = val
            elif key == "years":
                current.years = val
            elif key == "angles":
                current.angles = [a.strip() for a in val.split(",") if a.strip()]
            in_qa_targets = False
            continue

        # qa_targets block header
        if stripped.lower() == "qa_targets:":
            in_qa_targets = True
            continue

        # qa_targets list items
        if in_qa_targets:
            if stripped.startswith("- "):
                current.qa_targets.append(stripped[2:].strip())
                continue
            elif stripped == "":
                in_qa_targets = False
                continue
            else:
                # Non-list line ends the targets block
                in_qa_targets = False

        # Everything else is raw notes
        note_lines.append(line)

    flush()
    if current is not None:
        experiences.append(current)

    return experiences


_STOP = {
    "and", "or", "the", "a", "an", "in", "of", "for", "to", "with", "that",
    "this", "it", "is", "are", "not", "as", "at", "by", "be", "was", "were",
    "its", "on", "has", "have", "had", "from", "but", "so", "if", "when",
    "then", "than", "no", "do", "did", "does", "been", "both", "also",
    "listed", "required", "explicitly", "mentioned", "neither", "these",
    "lists", "addressed", "jd",
}


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower())) - _STOP


def find_experience(experiences: list[Experience], topic: str) -> Experience | None:
    """Find the single best matching experience. Returns None if no match above threshold."""
    matches = find_experiences(experiences, topic)
    return matches[0] if matches else None


def find_experiences(experiences: list[Experience], topic: str, min_score: int = 4) -> list[Experience]:
    """Return all experiences that match the topic above the score threshold, best first."""
    if not experiences:
        return []

    topic_words = _words(topic)
    scored: list[tuple[int, Experience]] = []

    for exp in experiences:
        name_words = _words(exp.name)
        company_words = _words(exp.company)

        score = len(topic_words & (name_words | company_words))

        if exp.name.lower() in topic.lower() or topic.lower() in exp.name.lower():
            score += 10
        if exp.company and exp.company.lower() in topic.lower():
            score += 5

        if score >= min_score:
            scored.append((score, exp))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [exp for _, exp in scored]


def framing_coverage(exp: Experience, paragraphs: list[Paragraph]) -> dict[str, bool]:
    """Return {angle: covered} for each desired angle in the experience.

    Coverage is detected by finding paragraphs whose section name overlaps with the
    experience name, then checking their angle tags.
    """
    if not exp.angles:
        return {}

    exp_words = _words(exp.name)

    # Match paragraphs by section name
    matching = [
        p for p in paragraphs
        if (
            len(_words(p.section) & exp_words) >= 2
            or exp.name.lower() in p.section.lower()
            or p.section.lower() in exp.name.lower()
            or (exp.company and exp.company.lower() in p.role.lower())
        )
    ]

    covered_angles: set[str] = set()
    for p in matching:
        angle = p.meta.get("angle", "")
        if angle:
            covered_angles.add(angle)

    return {angle: angle in covered_angles for angle in exp.angles}


def coverage_context(exp: Experience, paragraphs: list[Paragraph]) -> str:
    """Generate framing inventory text for injection into Q&A context.

    Tells the Q&A agent what's already written vs. what angles are missing,
    so it targets questions at the gaps instead of re-asking covered ground.
    """
    if not exp.angles:
        parts = []
        if exp.raw_notes:
            parts.append(f"Experience background — {exp.name}:\n{exp.raw_notes}")
        if exp.qa_targets:
            targets_text = "\n".join(f"- {q}" for q in exp.qa_targets)
            parts.append(
                f"Targeted questions for this session (ask about these specifically, "
                f"one at a time):\n{targets_text}"
            )
        return "\n\n".join(parts) if parts else ""

    coverage = framing_coverage(exp, paragraphs)
    covered = [a for a, c in coverage.items() if c]
    missing = [a for a, c in coverage.items() if not c]

    parts: list[str] = []

    header = f"Experience: {exp.name}"
    if exp.company:
        header += f" ({exp.company}"
        if exp.years:
            header += f", {exp.years}"
        header += ")"
    parts.append(header)

    if exp.raw_notes:
        parts.append(f"Raw facts (already known — do not re-ask these):\n{exp.raw_notes}")

    if exp.qa_targets:
        targets_text = "\n".join(f"- {q}" for q in exp.qa_targets)
        parts.append(
            f"Targeted questions for this session (flagged as gaps — ask about these "
            f"specifically, in your own words, one at a time):\n{targets_text}"
        )

    if covered:
        parts.append(f"Angles already written in library: {', '.join(covered)}")

    if missing:
        parts.append(
            f"Angles NOT yet written (these are the gaps — focus your questions here): "
            + ", ".join(missing)
        )
    else:
        parts.append("All defined angles are covered. You may explore a new angle not yet captured.")

    return "\n\n".join(parts)


def inventory_lines(exp: Experience, paragraphs: list[Paragraph]) -> list[tuple[str, bool]]:
    """Return [(angle, covered)] pairs for display in show-library."""
    coverage = framing_coverage(exp, paragraphs)
    return [(a, coverage.get(a, False)) for a in exp.angles]
