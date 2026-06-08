"""
Guard against raw input() being used for free-form text entry in cli.py.

macOS caps canonical terminal input at 1023 chars. Any prompt that collects
free-form user content (paragraphs, directions, descriptions) must use
_read_multiline(), which goes through prompt_toolkit and has no length limit.

Single-token responses (Y/N, numbers, short names, choice letters) are fine
as raw input() — they will never exceed the limit.
"""
from pathlib import Path
import re
import ast

CLI = Path(__file__).parent.parent / "coverletter" / "cli.py"

# Patterns that indicate a raw input() call is collecting free-form text.
# These are the exact strings that were broken and fixed.
_FREE_FORM_PATTERNS = [
    r'input\("> "\)',                           # bare > prompt
    r'input\(".*as much detail.*"\)',           # "as much detail as you want"
    r'input\(".*free text.*"\)',                # "free text"
    r'input\(".*How to revise.*"\)',            # revision direction
    r'input\(".*Application notes.*"\)',        # application notes
]


def test_no_raw_input_for_free_form_text():
    source = CLI.read_text()
    violations = []
    for pattern in _FREE_FORM_PATTERNS:
        for m in re.finditer(pattern, source):
            lineno = source[: m.start()].count("\n") + 1
            violations.append(f"  line {lineno}: {m.group()}")
    assert not violations, (
        "Found raw input() collecting free-form text in cli.py — "
        "use _read_multiline() instead (prompt_toolkit, no 1023-char limit):\n"
        + "\n".join(violations)
    )


def test_read_multiline_uses_prompt_toolkit():
    """_read_multiline must import and call prompt_toolkit, not just input()."""
    source = CLI.read_text()
    # Extract the _read_multiline function body
    match = re.search(
        r"def _read_multiline\(.*?\n(?=def |\Z)", source, re.DOTALL
    )
    assert match, "_read_multiline not found in cli.py"
    body = match.group()
    assert "prompt_toolkit" in body, (
        "_read_multiline does not use prompt_toolkit — "
        "long pastes will be truncated at 1023 chars on macOS"
    )


def test_read_multiline_has_fallback():
    """_read_multiline must have a fallback for environments without prompt_toolkit."""
    source = CLI.read_text()
    match = re.search(
        r"def _read_multiline\(.*?\n(?=def |\Z)", source, re.DOTALL
    )
    assert match, "_read_multiline not found in cli.py"
    body = match.group()
    assert "except" in body, (
        "_read_multiline has no fallback — if prompt_toolkit import fails "
        "the function will crash instead of degrading gracefully"
    )
