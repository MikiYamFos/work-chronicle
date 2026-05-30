import tempfile
from pathlib import Path

from coverletter.profile import CandidateProfile, load_profile, write_profile


FIXTURES = Path(__file__).parent / "fixtures"


# ── CandidateProfile ──────────────────────────────────────────────────────────

def test_empty_profile():
    p = CandidateProfile()
    assert p.is_empty


def test_not_empty_with_goals():
    p = CandidateProfile(goals=["Own production pipelines"])
    assert not p.is_empty


def test_not_empty_with_differentiators():
    p = CandidateProfile(differentiators=["PySpark at billion-row scale"])
    assert not p.is_empty


def test_as_goals_text_empty():
    assert CandidateProfile().as_goals_text() == ""


def test_as_goals_text_content():
    p = CandidateProfile(goals=["Goal one", "Goal two"])
    text = p.as_goals_text()
    assert "Goal one" in text
    assert "Goal two" in text


def test_as_differentiators_text():
    p = CandidateProfile(differentiators=["dbt at scale", "Spark ownership"])
    text = p.as_differentiators_text()
    assert "dbt at scale" in text


def test_as_fit_context_includes_goals():
    p = CandidateProfile(goals=["Work on consequential data"])
    assert "Work on consequential data" in p.as_fit_context()


def test_as_fit_context_includes_values():
    p = CandidateProfile(values=["I care about correctness"])
    assert "I care about correctness" in p.as_fit_context()


def test_as_fit_context_includes_avoid():
    p = CandidateProfile(avoid=["Pure analyst roles"])
    assert "Pure analyst roles" in p.as_fit_context()


def test_as_fit_context_empty_when_nothing():
    assert CandidateProfile().as_fit_context() == ""


def test_as_seniority_signals_text():
    p = CandidateProfile(seniority_signals=["Production ownership: incidents and SLAs"])
    text = p.as_seniority_signals_text()
    assert "Production ownership" in text


def test_as_working_style_text():
    p = CandidateProfile(working_style=["I build alerting in from day one"])
    text = p.as_working_style_text()
    assert "alerting" in text


# ── load_profile ──────────────────────────────────────────────────────────────

def test_load_missing_file_returns_empty():
    result = load_profile(Path("/nonexistent/path/profile.toml"))
    assert result.is_empty


def test_load_fixture_profile():
    result = load_profile(FIXTURES / "candidate_profile.toml")
    assert not result.is_empty
    assert any("clinical" in g.lower() or "consequen" in g.lower() for g in result.goals)
    assert any("research" in d.lower() or "clinical" in d.lower() for d in result.differentiators)
    assert len(result.seniority_signals) > 0
    assert len(result.working_style) > 0
    assert len(result.values) > 0


# ── write_profile roundtrip ───────────────────────────────────────────────────

def test_write_and_load_roundtrip():
    data = {
        "goals": ["Lead complex data projects"],
        "differentiators": ["PySpark at scale"],
        "focus_areas": ["dbt", "observability"],
        "avoid": ["Pure analyst roles"],
        "seniority_signals": ["Production ownership: incidents"],
        "working_style": ["I move between technical and non-technical audiences"],
        "values": ["I care about the craft"],
    }
    with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
        path = Path(f.name)
    try:
        write_profile(path, data)
        loaded = load_profile(path)
        assert "Lead complex data projects" in loaded.goals
        assert "PySpark at scale" in loaded.differentiators
        assert "Pure analyst roles" in loaded.avoid
        assert "Production ownership: incidents" in loaded.seniority_signals
        assert any("technical" in w for w in loaded.working_style)
        assert any("craft" in v for v in loaded.values)
    finally:
        path.unlink(missing_ok=True)


def test_write_profile_empty_sections():
    data = {k: [] for k in ["goals", "differentiators", "focus_areas", "avoid",
                              "seniority_signals", "working_style", "values"]}
    with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
        path = Path(f.name)
    try:
        write_profile(path, data)
        loaded = load_profile(path)
        assert loaded.is_empty
    finally:
        path.unlink(missing_ok=True)
