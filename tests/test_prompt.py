from coverletter.parser import Paragraph
from coverletter.prompt import build_user_message, prefilter


PARAGRAPHS = [
    Paragraph(role="General", section="General", text="I have spent the last eight years building distributed systems.", meta={"strength": "high"}, index=0),
    Paragraph(role="Data Engineering", section="Technical", text="The migration I designed moved 40TB of legacy data using Python and Spark.", meta={"tech": "python", "strength": "high"}, index=1),
    Paragraph(role="Data Engineering", section="Opening", text="At Acme Corp I owned the business's largest, most complex pipelines.", meta={"strength": "medium"}, index=2),
    Paragraph(role="General", section="Closing", text="I would welcome the chance to discuss how my background fits.", meta={"tone": "closer"}, index=3),
]


def test_build_user_message_contains_sections() -> None:
    msg = build_user_message("We are hiring a Python data engineer.", PARAGRAPHS)
    assert "Technical" in msg
    assert "Closing" in msg
    assert "JOB DESCRIPTION" in msg
    assert "Python data engineer" in msg


def test_build_user_message_with_role() -> None:
    msg = build_user_message("Python data engineer role.", PARAGRAPHS, role="Data Engineering")
    assert "Target role: Data Engineering" in msg


def test_build_user_message_paragraph_index() -> None:
    msg = build_user_message("job", PARAGRAPHS)
    assert "[0]" in msg
    assert "[1]" in msg


def test_prefilter_returns_top_n() -> None:
    result = prefilter(PARAGRAPHS, "Python Spark data pipeline engineer", top_n=2)
    assert len(result) == 2


def test_prefilter_prefers_relevant_paragraphs() -> None:
    result = prefilter(PARAGRAPHS, "Python Spark data pipeline", top_n=2)
    texts = [p.text for p in result]
    assert any("Spark" in t for t in texts)


def test_prefilter_no_op_when_small() -> None:
    result = prefilter(PARAGRAPHS, "anything", top_n=100)
    assert len(result) == len(PARAGRAPHS)
