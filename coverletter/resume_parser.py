from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BulletOption:
    label: str          # "Option A — leads with outcome"
    angle: str          # from meta comment
    tech: list[str]     # from meta comment
    text: str           # full bullet text, normalized to single line


@dataclass
class ResumeSection:
    name: str
    options: list[BulletOption] = field(default_factory=list)


@dataclass
class ResumeRole:
    company: str        # "Acme Corp" — may be a substring of the name in resume.typ
    role_title: str
    years: str
    sections: list[ResumeSection] = field(default_factory=list)


def _parse_meta(line: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    m = re.search(r"<!--\s*meta:\s*(.+?)\s*-->", line)
    if not m:
        return meta
    for part in m.group(1).split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            meta[k.strip()] = v.strip()
    return meta


def load_resume_bullets(path: Path) -> list[ResumeRole]:
    """Parse resume_bullets.md into structured objects."""
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    roles: list[ResumeRole] = []
    current_role: ResumeRole | None = None
    current_section: ResumeSection | None = None
    current_meta: dict[str, str] = {}
    current_label: str = ""
    current_text: list[str] = []
    in_block_comment = False

    def save() -> None:
        """Save accumulated text as a BulletOption. Does NOT clear current_meta."""
        nonlocal current_text, current_label
        if current_text and current_section is not None and current_label:
            text = re.sub(r"\s+", " ", " ".join(current_text)).strip()
            if text:
                current_section.options.append(BulletOption(
                    label=current_label,
                    angle=current_meta.get("angle", ""),
                    tech=[t.strip() for t in current_meta.get("tech", "").split(",") if t.strip()],
                    text=text,
                ))
        current_text.clear()
        current_label = ""

    def reset() -> None:
        """Full reset including meta — for section/company boundaries."""
        nonlocal current_meta
        save()
        current_meta = {}

    for line in lines:
        s = line.strip()

        # Multi-line block comment detection (the how-to header block)
        if not in_block_comment and s == "<!--":
            in_block_comment = True
            continue
        if in_block_comment:
            if "-->" in s:
                in_block_comment = False
            continue

        # Skip file title and blank lines with no accumulated text
        if s.startswith("# ") or (not s and not current_text):
            continue

        # Blank line mid-text — treat as a paragraph separator within same bullet
        # (don't flush; just skip)
        if not s:
            continue

        # Company: ## Acme Corp (Data Engineer, 2021–2023)
        if re.match(r"^## [^#]", s):
            reset()
            header = s[3:].strip()
            m = re.match(r"^(.+?)\s*\(([^,]+),\s*(.+)\)\s*$", header)
            if m:
                company = m.group(1).strip()
                role_title = m.group(2).strip()
                years = m.group(3).strip()
            else:
                company, role_title, years = header, "", ""
            current_role = ResumeRole(company=company, role_title=role_title, years=years)
            roles.append(current_role)
            current_section = None
            continue

        # Section: ### Watch-Duration Pipeline
        if re.match(r"^### ", s):
            reset()
            current_section = ResumeSection(name=s[4:].strip())
            if current_role is not None:
                current_role.sections.append(current_section)
            continue

        # Meta comment — save previous option, then set meta for the next one
        if "<!-- meta:" in s:
            save()                       # save previous (meta NOT cleared by save())
            current_meta = _parse_meta(s)  # overwrite with new meta
            continue

        # Option label: **Option A — description**
        if s.startswith("**") and s.endswith("**") and current_section is not None:
            save()                       # save any previous text (meta stays)
            current_label = s.strip("*").strip()
            continue

        # Bullet text body
        if s and current_label and current_section is not None:
            current_text.append(s)

    reset()
    return roles


def find_role_for_company(roles: list[ResumeRole], typ_company: str) -> ResumeRole | None:
    """Match a company name from resume.typ against loaded roles (substring match)."""
    typ_lower = typ_company.lower()
    for role in roles:
        if role.company.lower() in typ_lower or typ_lower in role.company.lower():
            return role
    return None
