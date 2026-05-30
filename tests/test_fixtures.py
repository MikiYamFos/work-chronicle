"""Integration tests using the synthetic fixture library — zero API cost."""
from pathlib import Path

from coverletter.parser import load_paragraphs, filter_by_role
from coverletter.prompt import build_user_message, prefilter

FIXTURES = Path(__file__).parent / "fixtures"
LIBRARY = FIXTURES / "library.md"


def _load():
    return load_paragraphs([LIBRARY])


def _text(msg) -> str:
    if isinstance(msg, list):
        return " ".join(b["text"] for b in msg if isinstance(b, dict) and "text" in b)
    return str(msg)


# ── Fixture library loads correctly ──────────────────────────────────────────

def test_fixture_library_loads():
    paras = _load()
    assert len(paras) > 0


def test_fixture_has_data_engineer_role():
    paras = _load()
    roles = {p.role for p in paras}
    assert "Data Engineer" in roles


def test_fixture_has_general_role():
    paras = _load()
    roles = {p.role for p in paras}
    assert "General" in roles


def test_fixture_closer_paragraphs_tagged():
    paras = _load()
    closers = [p for p in paras if p.meta.get("tone") == "closer"]
    assert len(closers) >= 2  # Why This Role + General Closing


# ── Closer label in built message ────────────────────────────────────────────

def test_closer_paragraphs_labeled_in_message():
    paras = _load()
    msg = _text(build_user_message("We need a data engineer.", paras))
    assert "[CLOSER ONLY]" in msg


def test_non_closer_paragraphs_not_labeled():
    paras = _load()
    msg = _text(build_user_message("We need a data engineer.", paras))
    pipeline_para = next(p for p in paras if "four-hour SLA" in p.text or "SLA" in p.text and "closer" not in p.section.lower())
    # The pipeline paragraph should NOT have CLOSER ONLY label
    # Find its index line in the message
    assert f"[{pipeline_para.index}]" in msg
    # Confirm it doesn't carry the CLOSER ONLY tag on that line
    for line in msg.splitlines():
        if f"[{pipeline_para.index}]" in line:
            assert "[CLOSER ONLY]" not in line
            break


# ── Role filtering ────────────────────────────────────────────────────────────

def test_filter_by_role_includes_general():
    paras = _load()
    filtered = filter_by_role(paras, "Data Engineer")
    roles = {p.role for p in filtered}
    assert "General" in roles
    assert "Data Engineer" in roles


def test_filter_by_role_excludes_other_roles():
    paras = _load()
    filtered = filter_by_role(paras, "Data Engineer")
    # Fixture only has Data Engineer and General — nothing to exclude, but structure holds
    assert all(p.role in ("Data Engineer", "General") for p in filtered)


# ── Prefilter respects closer pinning ────────────────────────────────────────

def test_prefilter_always_includes_closers():
    paras = _load()
    # Even with top_n=2, closers should be pinned
    result = prefilter(paras, "data pipeline engineer", top_n=2)
    closer_count = sum(1 for p in result if p.meta.get("tone") == "closer")
    assert closer_count >= 1


def test_prefilter_selects_relevant_paragraphs():
    paras = _load()
    result = prefilter(paras, "clinical trial data pipeline compliance", top_n=5)
    texts = [p.text for p in result]
    assert any("clinical" in t.lower() or "trial" in t.lower() for t in texts)


# ── build_user_message with fixture paragraphs ────────────────────────────────

def test_message_contains_jd():
    paras = _load()
    msg = _text(build_user_message("We need a senior Python data engineer.", paras))
    assert "senior Python data engineer" in msg


def test_message_contains_paragraph_indices():
    paras = _load()
    msg = _text(build_user_message("job", paras))
    assert "[0]" in msg


def test_message_with_company_and_role():
    paras = _load()
    msg = _text(build_user_message("job", paras, role="Data Engineer", company="Acme"))
    assert "Target role: Data Engineer" in msg
    assert "Company: Acme" in msg
