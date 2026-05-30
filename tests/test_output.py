import tempfile
from pathlib import Path

from coverletter.output import _append_signoff, _strip_markdown, save_letter


# ── _append_signoff ───────────────────────────────────────────────────────────

def test_append_signoff_adds_signoff():
    text = "Dear Hiring Manager,\n\nLetter body."
    result = _append_signoff(text, "Alex Chen")
    assert "Sincerely," in result
    assert "Alex Chen" in result


def test_append_signoff_without_name():
    result = _append_signoff("Body text.", "")
    assert "Sincerely," in result


def test_append_signoff_no_duplicate_name():
    text = "Body.\n\nSincerely,\n\nAlex Chen"
    result = _append_signoff(text, "Alex Chen")
    assert result.count("Alex Chen") == 1


def test_append_signoff_no_duplicate_sincerely():
    text = "Body.\n\nSincerely,"
    result = _append_signoff(text, "")
    assert result.count("Sincerely,") == 1


# ── _strip_markdown ───────────────────────────────────────────────────────────

def test_strip_markdown_em_dash_to_hyphen():
    result = _strip_markdown("This — that")
    assert "—" not in result
    assert "-" in result


def test_strip_markdown_removes_bold():
    result = _strip_markdown("This is **bold** text.")
    assert "**" not in result
    assert "bold" in result


def test_strip_markdown_removes_italic():
    result = _strip_markdown("This is *italic* text.")
    assert "*italic*" not in result
    assert "italic" in result


def test_strip_markdown_removes_headers():
    result = _strip_markdown("## Section Header\n\nBody text.")
    assert "##" not in result
    assert "Section Header" in result


def test_strip_markdown_removes_inline_code():
    result = _strip_markdown("Run `dbt run` to build.")
    assert "`" not in result
    assert "dbt run" in result


def test_strip_markdown_curly_quotes():
    result = _strip_markdown("“quoted” and ‘single’")
    assert "“" not in result
    assert "”" not in result


def test_strip_markdown_collapses_blank_lines():
    result = _strip_markdown("Para one.\n\n\n\nPara two.")
    assert "\n\n\n" not in result


# ── save_letter ───────────────────────────────────────────────────────────────

def test_save_letter_creates_file():
    with tempfile.TemporaryDirectory() as d:
        path = save_letter("Letter content.", Path(d), "TestCo", "Alex Chen")
        assert path.exists()
        content = path.read_text()
        assert "Letter content." in content
        assert "Alex Chen" in content


def test_save_letter_filename_contains_company():
    with tempfile.TemporaryDirectory() as d:
        path = save_letter("Content.", Path(d), "Acme Corp", "")
        assert "Acme_Corp" in path.name


def test_save_letter_filename_contains_date():
    import datetime
    with tempfile.TemporaryDirectory() as d:
        path = save_letter("Content.", Path(d), "Acme", "")
        assert datetime.date.today().isoformat() in path.name


def test_save_letter_creates_output_dir():
    with tempfile.TemporaryDirectory() as d:
        subdir = Path(d) / "nested" / "output"
        path = save_letter("Content.", subdir, "Co", "")
        assert subdir.exists()
        assert path.exists()
