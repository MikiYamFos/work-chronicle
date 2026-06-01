"""
Tests for _build_initial_context — injection order, resume block presence,
and that resume doesn't appear when empty.
"""
import sys, types
# Stub anthropic so build.py imports without the SDK installed in test env
if "anthropic" not in sys.modules:
    sys.modules["anthropic"] = types.ModuleType("anthropic")
from coverletter.build import _build_initial_context


def test_topic_always_present():
    ctx = _build_initial_context("Kafka pipeline")
    assert "Kafka pipeline" in ctx


def test_resume_block_injected_when_provided():
    ctx = _build_initial_context("Kafka", resume_context="Led data platform at Acme Corp.")
    assert "RESUME BLOCK" in ctx
    assert "Acme Corp" in ctx


def test_resume_block_absent_when_empty():
    ctx = _build_initial_context("Kafka", resume_context="")
    assert "RESUME BLOCK" not in ctx


def test_resume_block_absent_when_not_passed():
    ctx = _build_initial_context("Kafka")
    assert "RESUME BLOCK" not in ctx


def test_resume_before_gap_before_jd_before_topic():
    ctx = _build_initial_context(
        "Kafka",
        job_description="We need Kafka expertise.",
        gap_description="Real-time streaming",
        resume_context="Built Kafka at Acme Corp.",
    )
    resume_pos = ctx.index("RESUME BLOCK")
    gap_pos = ctx.index("JD gap")
    jd_pos = ctx.index("Job description")
    topic_pos = ctx.index("Topic to explore")
    assert resume_pos < gap_pos < jd_pos < topic_pos


def test_framing_before_resume():
    ctx = _build_initial_context(
        "Kafka",
        framing_context="EXPERIENCE: built pipeline",
        resume_context="Resume bullet here.",
    )
    framing_pos = ctx.index("EXPERIENCE")
    resume_pos = ctx.index("RESUME BLOCK")
    assert framing_pos < resume_pos


def test_jd_truncated_to_600_chars():
    long_jd = "x" * 1200
    ctx = _build_initial_context("topic", job_description=long_jd)
    # The injected JD excerpt must be at most 600 chars
    jd_start = ctx.index("Job description excerpt:") + len("Job description excerpt:\n")
    jd_section = ctx[jd_start:jd_start + 700]
    assert "x" * 601 not in jd_section


def test_library_search_instruction_when_use_tools():
    ctx = _build_initial_context("Kafka", use_tools=True)
    assert "search_library" in ctx


def test_no_library_search_when_no_tools():
    ctx = _build_initial_context("Kafka", use_tools=False)
    assert "search_library" not in ctx
