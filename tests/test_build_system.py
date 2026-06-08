"""
Tests for the refactored BUILD_SYSTEM dynamic assembly.

Guards:
- build_system_prompt() includes correct blocks for each context
- _classify_gap() returns the right block for each gap type
- No stale BUILD_SYSTEM references remain in cli.py (all paths use dynamic prompt)
- Core rules always present; gap/context blocks only when relevant
"""
from pathlib import Path
import re
import sys, types

if "anthropic" not in sys.modules:
    sys.modules["anthropic"] = types.ModuleType("anthropic")

from coverletter.build import (
    build_system_prompt,
    _classify_gap,
    _BUILD_CORE,
    _BUILD_TOOLS,
    _BUILD_GAP_COMPETENCE,
    _BUILD_GAP_PRODUCTION,
    _BUILD_GAP_IMPACT,
    _BUILD_CONTEXT_RESUME,
    _BUILD_CONTEXT_FRAMING,
)

CLI = Path(__file__).parent.parent / "coverletter" / "cli.py"


# ---------------------------------------------------------------------------
# Gap classifier
# ---------------------------------------------------------------------------

def test_classify_gap_competence():
    gaps = [
        "LLM-enabled workflows and annotation pipelines",
        "Automated evaluation frameworks and dataset quality measurement",
        "Dataset versioning and workflow instrumentation",
        "Integrations between data systems and LLM services",
        "experience with dbt and Airflow",
        "proficiency in Python and SQL",
    ]
    for g in gaps:
        result = _classify_gap(g)
        assert result == _BUILD_GAP_COMPETENCE, f"expected COMPETENCE for {g!r}, got different block"


def test_classify_gap_production():
    gaps = [
        "Production ownership — SLAs, incident response",
        "System design judgment — grain decisions",
        "Data modeling depth — subscription reporting",
        "observability and monitoring patterns",
    ]
    for g in gaps:
        result = _classify_gap(g)
        assert result == _BUILD_GAP_PRODUCTION, f"expected PRODUCTION for {g!r}"


def test_classify_gap_impact():
    gaps = [
        "Business impact — letter describes what was built but never states what it enabled",
        "Requirements translation — stakeholder needs into production decisions",
        "seniority signals — drove decisions across teams",
    ]
    for g in gaps:
        result = _classify_gap(g)
        assert result == _BUILD_GAP_IMPACT, f"expected IMPACT for {g!r}"


def test_classify_gap_empty():
    assert _classify_gap("") == ""
    assert _classify_gap("some general topic") == ""


# ---------------------------------------------------------------------------
# build_system_prompt assembly
# ---------------------------------------------------------------------------

def test_core_always_present():
    for kwargs in [
        {},
        {"use_tools": False},
        {"gap_description": "proficiency in dbt"},
        {"has_resume": True},
        {"has_framing": True},
    ]:
        prompt = build_system_prompt(**kwargs)
        assert _BUILD_CORE.strip()[:80] in prompt, f"core missing for {kwargs}"


def test_tools_block_only_when_use_tools():
    with_tools = build_system_prompt(use_tools=True)
    without_tools = build_system_prompt(use_tools=False)
    assert "search_library" in with_tools
    assert "search_library" not in without_tools


def test_gap_block_injected_correctly():
    competence = build_system_prompt(gap_description="experience with LLM annotation pipelines")
    production = build_system_prompt(gap_description="production ownership and system design")
    impact = build_system_prompt(gap_description="business impact and stakeholder decisions")
    general = build_system_prompt(gap_description="")

    assert "COMPETENCE" in competence
    assert "PRODUCTION" not in competence
    assert "IMPACT" not in competence

    assert "PRODUCTION" in production
    assert "COMPETENCE" not in production

    assert "IMPACT" in impact
    assert "COMPETENCE" not in impact

    assert "COMPETENCE" not in general
    assert "PRODUCTION" not in general
    assert "IMPACT" not in general


def test_only_one_gap_block_per_prompt():
    prompt = build_system_prompt(gap_description="LLM evaluation frameworks and dataset quality")
    assert prompt.count("GAP TYPE:") == 1


def test_context_blocks_injected_only_when_present():
    with_resume = build_system_prompt(has_resume=True)
    without_resume = build_system_prompt(has_resume=False)
    assert "RESUME BLOCK" in with_resume
    assert "RESUME BLOCK" not in without_resume

    with_framing = build_system_prompt(has_framing=True)
    without_framing = build_system_prompt(has_framing=False)
    assert "EXPERIENCE FRAMING" in with_framing
    assert "EXPERIENCE FRAMING" not in without_framing


def test_no_conflicting_gap_rules_in_competence_prompt():
    prompt = build_system_prompt(gap_description="proficiency with Airflow and dbt")
    # Competence gaps must not tell model to ask about breakage/failure
    assert "Failure and breakage questions ARE appropriate" not in prompt
    assert "ask what broke" not in prompt.lower()


def test_production_prompt_allows_failure_questions():
    prompt = build_system_prompt(gap_description="production ownership and incident response")
    assert "Failure and breakage questions ARE appropriate" in prompt


# ---------------------------------------------------------------------------
# cli.py — no stale BUILD_SYSTEM references
# ---------------------------------------------------------------------------

def test_no_build_system_import_in_cli():
    source = CLI.read_text()
    # Direct import of BUILD_SYSTEM constant is banned — all paths use build_system_prompt()
    bad = re.findall(r"from coverletter\.build import.*\bBUILD_SYSTEM\b", source)
    assert not bad, (
        "cli.py imports BUILD_SYSTEM directly — use build_system_prompt() instead:\n"
        + "\n".join(bad)
    )


def test_no_system_build_system_kwarg_in_cli():
    source = CLI.read_text()
    bad_lines = []
    for i, line in enumerate(source.splitlines(), 1):
        if "system=BUILD_SYSTEM" in line:
            bad_lines.append(f"  line {i}: {line.strip()}")
    assert not bad_lines, (
        "cli.py passes system=BUILD_SYSTEM directly — use _system from build_system_prompt():\n"
        + "\n".join(bad_lines)
    )
