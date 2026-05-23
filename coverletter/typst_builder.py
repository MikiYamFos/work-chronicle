from __future__ import annotations

import re
import subprocess
from pathlib import Path

from coverletter.resume_parser import BulletOption


def _escape_typst(text: str) -> str:
    """Escape text for use inside a Typst content block [...]."""
    text = text.replace("\\", "\\\\")
    text = text.replace("]", "\\]")
    text = text.replace("@", "\\@")
    return text


def _make_bullets_block(options: list[BulletOption]) -> list[str]:
    """Return lines for a #bullets((...)) block from selected options."""
    lines = ["#bullets(("]
    for opt in options:
        lines.append(f"  [{_escape_typst(opt.text)}],")
    lines.append("))")
    return lines


def _find_bullets_span(lines: list[str], company: str) -> tuple[int, int] | None:
    """
    Find the (start, end) line indices (inclusive) of the #bullets((...)) block
    that follows the #role() call containing `company`.
    """
    role_pat = re.compile(r'#role\(\s*"' + re.escape(company) + r'"')
    found_role = False
    bullets_start: int | None = None

    for i, line in enumerate(lines):
        if role_pat.search(line):
            found_role = True
        if found_role and line.strip().startswith("#bullets(("):
            bullets_start = i
        if bullets_start is not None and i >= bullets_start and line.strip() == "))":
            return (bullets_start, i)

    return None


def replace_company_bullets(typ_content: str, company: str, selected: list[BulletOption]) -> str:
    """Replace the #bullets block for a given company with selected bullet options."""
    lines = typ_content.splitlines()
    span = _find_bullets_span(lines, company)
    if span is None:
        return typ_content
    start, end = span
    new_block = _make_bullets_block(selected)
    return "\n".join(lines[:start] + new_block + lines[end + 1:])


def extract_companies_from_typ(typ_content: str) -> list[str]:
    """Return company names in the order they appear in the .typ file."""
    return re.findall(r'#role\(\s*"([^"]+)"', typ_content)


def compile_typst(typ_path: Path, output_path: Path) -> bool:
    """Run typst compile. Returns True on success."""
    try:
        result = subprocess.run(
            ["typst", "compile", str(typ_path), str(output_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            from rich.console import Console
            Console().print(f"[red]typst error:[/red]\n{result.stderr.strip()}")
            return False
        return True
    except FileNotFoundError:
        from rich.console import Console
        Console().print(
            "[red]typst not found.[/red] Install it: https://typst.app\n"
            "  brew install typst"
        )
        return False
    except subprocess.TimeoutExpired:
        from rich.console import Console
        Console().print("[red]typst compile timed out.[/red]")
        return False
