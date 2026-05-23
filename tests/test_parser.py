import textwrap
from pathlib import Path

import pytest

from coverletter.parser import Paragraph, available_roles, filter_by_role, load_paragraphs, library_stats


SAMPLE_MD = textwrap.dedent("""\
    # My Cover Letter Paragraphs

    ## General

    <!-- meta: tone=opener, strength=high -->
    I have spent the last eight years building distributed systems.

    ### Closing

    <!-- meta: tone=closer -->
    I would welcome the chance to discuss how my background fits.

    ## Data Engineering

    ### Opening

    <!-- meta: strength=high -->
    At Acme Corp I owned the business's largest, most complex pipelines.

    ### Technical

    <!-- meta: tech=python, strength=high -->
    The migration I designed moved 40TB of legacy data.

    I believe good data work starts with understanding the source.
""")


@pytest.fixture
def paragraphs_file(tmp_path: Path) -> Path:
    p = tmp_path / "paragraphs.md"
    p.write_text(SAMPLE_MD, encoding="utf-8")
    return p


def test_load_paragraphs_count(paragraphs_file: Path) -> None:
    paras = load_paragraphs(paragraphs_file)
    assert len(paras) == 5


def test_roles_detected(paragraphs_file: Path) -> None:
    paras = load_paragraphs(paragraphs_file)
    roles = available_roles(paras)
    assert "General" in roles
    assert "Data Engineering" in roles


def test_general_section_defaults(paragraphs_file: Path) -> None:
    paras = load_paragraphs(paragraphs_file)
    # Paragraph before any H3 inside ## General should use role name as section
    general_no_h3 = [p for p in paras if p.role == "General" and "eight years" in p.text]
    assert len(general_no_h3) == 1
    assert general_no_h3[0].section == "General"


def test_h3_section_parsed(paragraphs_file: Path) -> None:
    paras = load_paragraphs(paragraphs_file)
    closing = [p for p in paras if "welcome the chance" in p.text]
    assert len(closing) == 1
    assert closing[0].role == "General"
    assert closing[0].section == "Closing"


def test_meta_parsed(paragraphs_file: Path) -> None:
    paras = load_paragraphs(paragraphs_file)
    opener = next(p for p in paras if "eight years" in p.text)
    assert opener.meta == {"tone": "opener", "strength": "high"}


def test_paragraph_without_meta(paragraphs_file: Path) -> None:
    paras = load_paragraphs(paragraphs_file)
    no_meta = [p for p in paras if "understanding the source" in p.text]
    assert len(no_meta) == 1
    assert no_meta[0].meta == {}


def test_filter_by_role_includes_general(paragraphs_file: Path) -> None:
    paras = load_paragraphs(paragraphs_file)
    filtered = filter_by_role(paras, "Data Engineering")
    roles = {p.role for p in filtered}
    assert "Data Engineering" in roles
    assert "General" in roles


def test_filter_by_role_excludes_other_roles(paragraphs_file: Path) -> None:
    paras = load_paragraphs(paragraphs_file)
    filtered = filter_by_role(paras, "General")
    assert all(p.role == "General" for p in filtered)


def test_library_stats_structure(paragraphs_file: Path) -> None:
    paras = load_paragraphs(paragraphs_file)
    stats = library_stats(paras)
    assert "General" in stats
    assert "Data Engineering" in stats
    assert stats["Data Engineering"]["Technical"] == 2


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        load_paragraphs(tmp_path / "nonexistent.md")
