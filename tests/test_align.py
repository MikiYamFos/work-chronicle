from coverletter.align import _parse_alignment, has_library_coverage


# ── _has_library_coverage ─────────────────────────────────────────────────────

def test_library_coverage_detected():
    assert has_library_coverage("dbt experience — JD requires it (library: [15])")


def test_library_coverage_detected_different_index():
    assert has_library_coverage("Kafka knowledge (library: [3])")


def test_library_coverage_not_present():
    assert not has_library_coverage("Kafka knowledge — not mentioned in letter")


def test_library_coverage_case_insensitive():
    assert has_library_coverage("Missing skill (Library: [7])")


def test_library_coverage_empty_string():
    assert not has_library_coverage("")


# ── _parse_alignment ──────────────────────────────────────────────────────────

_BASIC_REPORT = """\
SCORE: 3 covered of 5 total

COVERED
✓ Python experience — candidate has strong Python background
✓ SQL proficiency — demonstrated through Redshift work
✓ AWS services — EC2, Glue, Redshift all mentioned

GAPS
✗ dbt experience — JD lists dbt as primary tool (library: [15])
✗ Kafka knowledge — streaming experience not addressed
"""


def test_parse_covered_count():
    result = _parse_alignment(_BASIC_REPORT)
    assert len(result.covered) == 3


def test_parse_gaps_count():
    result = _parse_alignment(_BASIC_REPORT)
    assert len(result.gaps) == 2


def test_parse_score_pct():
    result = _parse_alignment(_BASIC_REPORT)
    assert result.score_pct == 60


def test_parse_covered_content():
    result = _parse_alignment(_BASIC_REPORT)
    assert any("Python" in c for c in result.covered)


def test_parse_gaps_content():
    result = _parse_alignment(_BASIC_REPORT)
    assert any("dbt" in g for g in result.gaps)


_SENIORITY_REPORT = """\
SCORE: 2 covered of 3 total

COVERED
✓ Python — present throughout

GAPS
✗ Kafka — not addressed

SENIORITY SIGNAL GAPS
✗ Production ownership — no incident response described
✗ System design judgment — no trade-off articulation
"""


def test_parse_seniority_gaps():
    result = _parse_alignment(_SENIORITY_REPORT)
    assert len(result.seniority_gaps) == 2


def test_parse_seniority_not_mixed_with_gaps():
    result = _parse_alignment(_SENIORITY_REPORT)
    assert len(result.gaps) == 1  # only Kafka, not seniority items
    assert all("Production" not in g for g in result.gaps)


_GOAL_REPORT = """\
SCORE: 4 covered of 4 total

COVERED
✓ Python — present

GAPS
(none)

GOAL ALIGNMENT
Partially — role offers production ownership but no AI/LLM work mentioned.
"""


def test_parse_goal_alignment():
    result = _parse_alignment(_GOAL_REPORT)
    assert "Partially" in result.goal_alignment


def test_parse_score_fallback_from_covered_gaps():
    # No explicit SCORE line — should compute from covered/gaps
    text = "COVERED\n✓ Python\n✓ SQL\n\nGAPS\n✗ Kafka\n"
    result = _parse_alignment(text)
    assert result.score_pct == round(100 * 2 / 3)


def test_parse_empty_report():
    result = _parse_alignment("")
    assert result.covered == []
    assert result.gaps == []
    assert result.score_pct == 0
