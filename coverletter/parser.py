import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Paragraph:
    role: str             # H2 — e.g. "General", "Data Engineering", "Acme Corp"
    section: str          # H3 — e.g. "Opening", "Technical", "Why This Role"
    text: str
    meta: dict[str, str] = field(default_factory=dict)
    index: int = 0
    layer: int = 0        # source file priority — 0 is highest (loaded first)
    db_id: int | None = None  # stable DB id — set after sync, used in prompt labels


_META_RE = re.compile(r"<!--\s*meta:\s*(.+?)\s*-->", re.IGNORECASE)
_H2_RE = re.compile(r"^##\s+(.+)$")
_H3_RE = re.compile(r"^###\s+(.+)$")


def _parse_meta(comment_line: str) -> dict[str, str]:
    m = _META_RE.match(comment_line.strip())
    if not m:
        return {}
    result = {}
    for part in m.group(1).split(","):
        part = part.strip()
        if "=" in part:
            k, _, v = part.partition("=")
            result[k.strip()] = v.strip()
    return result


def _load_one(path: Path, layer: int, start_index: int) -> list[Paragraph]:
    """Parse a single paragraphs file, assigning the given layer and starting index."""
    if not path.exists():
        raise SystemExit(
            f"\nParagraph library not found: {path}\n"
            "Create it and add your source paragraphs, or use --paragraphs to point at another file.\n"
        )

    text = path.read_text(encoding="utf-8")
    paragraphs: list[Paragraph] = []
    index = start_index
    current_role = "General"
    current_section = "General"
    pending_meta: dict[str, str] = {}
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal index, pending_meta, current_lines
        joined = "\n".join(current_lines).strip()
        if joined and not joined.startswith("#") and not re.match(r"^\[.+\]$", joined, re.DOTALL):
            paragraphs.append(
                Paragraph(
                    role=current_role,
                    section=current_section,
                    text=joined,
                    meta=pending_meta,
                    index=index,
                    layer=layer,
                )
            )
            index += 1
            pending_meta = {}
        current_lines = []

    in_block_comment = False

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("<!--") and "-->" not in stripped:
            in_block_comment = True
            flush()
            continue
        if in_block_comment:
            if stripped == "-->":
                in_block_comment = False
            continue

        if _H2_RE.match(line):
            flush()
            current_role = _H2_RE.match(line).group(1).strip()
            current_section = current_role
            continue

        if _H3_RE.match(line):
            flush()
            current_section = _H3_RE.match(line).group(1).strip()
            continue

        if _META_RE.match(stripped):
            flush()
            pending_meta = _parse_meta(stripped)
            continue

        if re.match(r"^#\s", line):
            continue

        if not stripped:
            flush()
            continue

        current_lines.append(line)

    flush()
    return paragraphs


def load_paragraphs(paths: "Path | list[Path]") -> list[Paragraph]:
    """Load paragraphs from one or more files. Earlier files have lower layer numbers (higher priority)."""
    if isinstance(paths, Path):
        paths = [paths]
    all_paragraphs: list[Paragraph] = []
    for layer, path in enumerate(paths):
        all_paragraphs.extend(_load_one(path, layer=layer, start_index=len(all_paragraphs)))
    return all_paragraphs


def available_roles(paragraphs: list[Paragraph]) -> list[str]:
    seen: dict[str, None] = {}
    for p in paragraphs:
        seen[p.role] = None
    return list(seen.keys())


def filter_by_role(paragraphs: list[Paragraph], role: str) -> list[Paragraph]:
    """Return paragraphs for the chosen role plus anything in General."""
    return [p for p in paragraphs if p.role == role or p.role == "General"]


def library_stats(paragraphs: list[Paragraph]) -> dict[str, dict[str, int]]:
    """Returns {role: {section: count}}."""
    stats: dict[str, dict[str, int]] = {}
    for p in paragraphs:
        stats.setdefault(p.role, {})
        stats[p.role][p.section] = stats[p.role].get(p.section, 0) + 1
    return stats
