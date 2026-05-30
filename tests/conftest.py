"""
Shared pytest fixtures.

test_cfg     — Config pointing to tests/fixtures/ (Jordan Reyes persona, standard library)
sparse_cfg   — Config pointing to tests/fixtures/personas/sparse/ (thin library, edge cases)
canned       — Dict of pre-written LLM response strings, keyed by filename stem
mock_llm     — Factory for MockAnthropicClient: returns canned responses without any API calls

Never call load_config() directly in tests — it resolves real env paths and can touch your
actual data directory.
"""
import os
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
PERSONAS = FIXTURES / "personas"
RESPONSES = FIXTURES / "responses"


# ── API key safety net ────────────────────────────────────────────────────────

@pytest.fixture(autouse=True, scope="session")
def _fake_api_key():
    """Prevent load_config() from raising if indirectly called."""
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-fake")


# ── Config fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def test_cfg(tmp_path):
    """Config wired to Jordan Reyes standard fixtures — reads from tests/fixtures/,
    writes to tmp_path. Safe to use in any test."""
    from coverletter.config import Config
    return Config(
        api_key="test-key-fake",
        voyage_api_key="",
        paragraphs_files=[FIXTURES / "library.md"],
        resume_file=FIXTURES / "resume.md",
        resume_typ_file=FIXTURES / "resume.typ",
        resume_bullets_file=FIXTURES / "resume_bullets.md",
        output_dir=tmp_path / "output",
        model="claude-sonnet-4-6",
        top_n=20,
        author_name="Test User",
        profile_file=FIXTURES / "candidate_profile.toml",
        experiences_file=FIXTURES / "experiences.md",
    )


@pytest.fixture
def sparse_cfg(tmp_path):
    """Config wired to the sparse persona — minimal library, thin profile.
    Use to test edge cases: no perspective paragraphs, no strong evidence,
    near-empty prefilter results."""
    from coverletter.config import Config
    sparse = PERSONAS / "sparse"
    return Config(
        api_key="test-key-fake",
        voyage_api_key="",
        paragraphs_files=[sparse / "library.md"],
        resume_file=sparse / "resume.md",
        resume_typ_file=sparse / "resume.typ",
        resume_bullets_file=sparse / "resume_bullets.md",
        output_dir=tmp_path / "output",
        model="claude-sonnet-4-6",
        top_n=20,
        author_name="Test User",
        profile_file=sparse / "candidate_profile.toml",
        experiences_file=sparse / "experiences.md",
    )


# ── Canned response fixtures ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def canned():
    """Pre-written LLM response strings, keyed by filename stem (no extension).

    Available keys:
      alignment_clean            — high score, one gap, no seniority section
      alignment_with_gaps        — 3 gaps including one with (library: [N]), seniority gap
      alignment_with_goal_fit    — includes GOAL ALIGNMENT section
      verify_pass                — {"verdict": "PASS", "failures": []}
      verify_fail                — {"verdict": "FAIL", "failures": [...]}
      thesis                     — one-sentence thesis string
      qa_question                — a single Q&A question
      qa_draft                   — DRAFT marker + paragraph text
      judge_pass                 — {"pass": true}
      judge_fail                 — {"pass": false, "reason": "..."}

    Usage:
        def test_something(canned):
            result = _parse_alignment(canned["alignment_with_gaps"])
            assert len(result.gaps) == 3
    """
    return {p.stem: p.read_text(encoding="utf-8") for p in RESPONSES.glob("*") if p.is_file()}


# ── Mock LLM client ───────────────────────────────────────────────────────────

class _MockBlock:
    """Minimal stand-in for an Anthropic content block."""
    def __init__(self, text: str):
        self.text = text
        self.type = "text"


class _MockUsage:
    input_tokens = 100
    output_tokens = 50
    cache_creation_input_tokens = 0
    cache_read_input_tokens = 0


class _MockResponse:
    """Minimal stand-in for an Anthropic Message response."""
    def __init__(self, text: str, stop_reason: str = "end_turn"):
        self.content = [_MockBlock(text)]
        self.stop_reason = stop_reason
        self.usage = _MockUsage()


class MockAnthropicClient:
    """
    Drop-in replacement for anthropic.Anthropic(api_key=...) in tests.

    Takes an ordered list of response strings. Each call to messages.create()
    pops the next string from the queue and returns it wrapped in a mock
    response object. After the queue is empty, returns _default for all
    subsequent calls.

    Usage:
        def test_parse_verify(mock_llm, canned, monkeypatch):
            client = mock_llm([canned["verify_pass"]])
            monkeypatch.setattr("coverletter.verify.anthropic.Anthropic",
                                lambda **kw: client)
            result = verify_letter("Letter text.", api_key="x", model="m")
            assert result.passed
    """
    def __init__(self, responses: list[str], default: str = "Mock default response."):
        self._queue = list(responses)
        self._default = default
        self.messages = self  # so client.messages.create(...) works

    def create(self, **kwargs) -> _MockResponse:
        text = self._queue.pop(0) if self._queue else self._default
        return _MockResponse(text)


@pytest.fixture
def mock_llm():
    """Factory that returns a MockAnthropicClient configured with the given responses.

    Usage:
        client = mock_llm([canned["verify_pass"]])
        monkeypatch.setattr("coverletter.verify.anthropic.Anthropic",
                            lambda **kw: client)
    """
    return MockAnthropicClient
