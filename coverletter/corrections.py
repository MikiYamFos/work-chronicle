from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from coverletter.parser import Paragraph


@dataclass
class Correction:
    role: str
    section: str
    old: str
    new: str
    source_file: str  # which file the paragraph came from


_HEADER_RE = re.compile(r"^##\s+\[([^\]]+)\]\s+(.+?)\s*/\s+(.+)$")


def load_corrections(path: Path) -> list[Correction]:
    if not path.exists():
        return []

    corrections: list[Correction] = []
    source_file = ""
    role = ""
    section = ""
    old_lines: list[str] = []
    new_lines: list[str] = []
    state = "idle"  # idle | old | new

    def flush() -> None:
        old = " ".join(old_lines).strip()
        new = " ".join(new_lines).strip()
        if old and new and role and section:
            corrections.append(Correction(role=role, section=section, old=old, new=new, source_file=source_file))

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()

        m = _HEADER_RE.match(stripped)
        if m:
            flush()
            source_file, role, section = m.group(1), m.group(2), m.group(3)
            old_lines, new_lines = [], []
            state = "idle"
            continue

        if stripped == "### old":
            flush()
            old_lines, new_lines = [], []
            state = "old"
            continue

        if stripped == "### new":
            state = "new"
            continue

        if stripped.startswith("##") or stripped.startswith("#"):
            continue

        if state == "old" and stripped:
            old_lines.append(stripped)
        elif state == "new" and stripped:
            new_lines.append(stripped)

    flush()
    return corrections


def apply_corrections(paragraphs: list[Paragraph], corrections: list[Correction]) -> list[Paragraph]:
    """Return paragraphs with known corrections applied. Originals are not mutated."""
    if not corrections:
        return paragraphs

    result = []
    for p in paragraphs:
        text = p.text
        for c in corrections:
            if c.role == p.role and c.section == p.section and c.old in text:
                text = text.replace(c.old, c.new, 1)
        if text != p.text:
            from dataclasses import replace
            p = replace(p, text=text)
        result.append(p)
    return result


def save_correction(path: Path, paragraph: Paragraph, old_sentence: str, new_sentence: str, source_file: str) -> None:
    """Append a new correction entry to corrections.md."""
    header = f"## [{source_file}] {paragraph.role} / {paragraph.section}"
    entry = f"\n{header}\n### old\n{old_sentence}\n### new\n{new_sentence}\n"

    if not path.exists():
        path.write_text("# Corrections\n" + entry, encoding="utf-8")
    else:
        with path.open("a", encoding="utf-8") as f:
            f.write(entry)


def find_source_paragraph(sentence: str, paragraphs: list[Paragraph]) -> Paragraph | None:
    """Find which source paragraph contains this exact sentence."""
    for p in paragraphs:
        if sentence in p.text:
            return p
    return None
