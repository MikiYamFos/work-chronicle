from coverletter.parser import Paragraph
from coverletter.verify import _hard_check, verbatim_check


# ── _hard_check ──────────────────────────────────────────────────────────────

def test_hard_check_clean_letter():
    letter = "Dear Hiring Manager,\n\nI built production pipelines.\n\nThank you."
    assert _hard_check(letter) == []


def test_hard_check_em_dash_flagged():
    failures = _hard_check("I built a pipeline — it was fast.")
    assert any("Em-dash" in f for f in failures)


def test_hard_check_em_dash_in_body():
    failures = _hard_check("Dear Hiring Manager,\n\nFirst paragraph — with dash.\n\nCloser.")
    assert any("Em-dash" in f for f in failures)


def test_hard_check_banned_phrase_not_just():
    failures = _hard_check("I am not just a data engineer.")
    assert any("not just" in f for f in failures)


def test_hard_check_banned_phrase_actually():
    failures = _hard_check("I actually built the pipeline from scratch.")
    assert any("actually" in f for f in failures)


def test_hard_check_banned_phrase_i_am_strongest():
    failures = _hard_check("I am strongest in Python and SQL.")
    assert any("i am strongest in" in f.lower() for f in failures)


def test_hard_check_that_paragraph_opener():
    letter = "First paragraph.\n\nThat experience shaped my approach."
    failures = _hard_check(letter)
    assert any("That" in f for f in failures)


def test_hard_check_that_only_flags_paragraph_start():
    # "That" in middle of paragraph is fine
    letter = "I built a pipeline. That pipeline processed a billion rows."
    failures = _hard_check(letter)
    assert not any("That" in f for f in failures)


def test_hard_check_multiple_issues():
    letter = "I am not just a builder — I also architect.\n\nThat was the key insight."
    failures = _hard_check(letter)
    assert len(failures) >= 3  # em-dash + not just + That paragraph


# ── verbatim_check ────────────────────────────────────────────────────────────

def _make_para(text: str, idx: int = 0) -> Paragraph:
    return Paragraph(role="General", section="Technical", text=text, meta={}, index=idx)


def _letter(body_paras: list[str]) -> str:
    """Wrap body paragraphs in a minimal letter structure."""
    parts = ["Dear Hiring Manager,", "", "Opener paragraph here."]
    for p in body_paras:
        parts += ["", p]
    parts += ["", "Thank you for your time."]
    return "\n".join(parts)


def test_verbatim_check_passes_source_sentence():
    source = _make_para("I built a Spark pipeline processing one billion events per day.")
    letter = _letter(["I built a Spark pipeline processing one billion events per day."])
    assert verbatim_check(letter, [source]) == []


def test_verbatim_check_flags_invented_sentence():
    source = _make_para("I built a simple batch job in Python.")
    letter = _letter([
        "I architected a distributed multi-region streaming system with advanced Kubernetes orchestration."
    ])
    violations = verbatim_check(letter, [source])
    assert len(violations) > 0


def test_verbatim_check_tolerates_trimming():
    source = _make_para(
        "I designed the subscriber-level metric grain, built the session-stitching logic, "
        "and created a cross-grain reconciliation framework to validate against the old output."
    )
    # Subset of words — should pass (high token coverage)
    letter = _letter([
        "I designed the subscriber-level metric grain and built the session-stitching logic."
    ])
    assert verbatim_check(letter, [source]) == []


def test_verbatim_check_skips_short_sentences():
    source = _make_para("I built pipelines.")
    letter = _letter(["This worked well."])  # short sentence, under 6 words
    assert verbatim_check(letter, [source]) == []


def test_verbatim_check_skips_opener_and_closer():
    source = _make_para("I built a complex pipeline at scale with Spark and Redshift on AWS.")
    # opener (para 2) and closer (last para) are skipped — only body paras [2:-1] checked
    # with only salutation + opener + closer, body_paras slice is empty
    letter = "Dear Hiring Manager,\n\nOpener here.\n\nI invented something completely fake at massive scale.\n\nThank you."
    # 4 paragraphs total: salutation, opener, body, closer → body_paras = [2:-1] = [body]
    violations = verbatim_check(letter, [source])
    assert len(violations) > 0


def test_verbatim_check_empty_source_returns_empty():
    letter = _letter(["I built a completely invented system with no source paragraph."])
    assert verbatim_check(letter, []) == []


def test_verbatim_check_too_few_paragraphs_skipped():
    source = _make_para("Short pipeline paragraph.")
    letter = "Dear Hiring Manager,\n\nOpener.\n\nCloser."  # only 3 paragraphs
    assert verbatim_check(letter, [source]) == []
