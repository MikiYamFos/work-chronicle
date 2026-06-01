"""
Tests for config loading — env var wiring, new fields, provider routing.
Never touches real files or API keys.
"""
import os
import pytest


# ── embed_model field ─────────────────────────────────────────────────────────

def test_embed_model_defaults_empty(tmp_path, monkeypatch):
    monkeypatch.delenv("EMBED_MODEL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.setenv("AUTHOR_NAME", "Test")
    monkeypatch.chdir(tmp_path)
    from coverletter.config import load_config
    cfg = load_config()
    assert cfg.embed_model == ""


def test_embed_model_read_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("EMBED_MODEL", "bge-m3")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.setenv("AUTHOR_NAME", "Test")
    monkeypatch.chdir(tmp_path)
    from coverletter.config import load_config
    cfg = load_config()
    assert cfg.embed_model == "bge-m3"


def test_embed_model_lowercased(tmp_path, monkeypatch):
    monkeypatch.setenv("EMBED_MODEL", "BGE-M3")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.chdir(tmp_path)
    from coverletter.config import load_config
    cfg = load_config()
    assert cfg.embed_model == "bge-m3"


# ── Config dataclass defaults ─────────────────────────────────────────────────

def test_config_embed_model_has_default():
    from coverletter.config import Config
    from pathlib import Path
    cfg = Config(
        api_key="k", voyage_api_key="", paragraphs_files=[Path("/tmp/lib.md")],
        resume_file=Path("/tmp/r.pdf"), resume_typ_file=Path("/tmp/r.typ"),
        resume_bullets_file=Path("/tmp/rb.md"), output_dir=Path("/tmp/out"),
        model="claude-sonnet-4-6", top_n=20, author_name="Test",
    )
    assert cfg.embed_model == ""


# ── Cohere key routing ────────────────────────────────────────────────────────

def test_cohere_model_requires_cohere_key(tmp_path, monkeypatch):
    monkeypatch.setenv("COVERLETTER_MODEL", "cohere/command-r-plus")
    monkeypatch.delenv("COHERE_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    from coverletter.config import load_config
    with pytest.raises(SystemExit) as exc:
        load_config()
    assert "COHERE_API_KEY" in str(exc.value)


def test_cohere_key_accepted(tmp_path, monkeypatch):
    monkeypatch.setenv("COVERLETTER_MODEL", "cohere/command-r-plus")
    monkeypatch.setenv("COHERE_API_KEY", "test-cohere-key")
    monkeypatch.setenv("AUTHOR_NAME", "Test")
    monkeypatch.chdir(tmp_path)
    from coverletter.config import load_config
    cfg = load_config()
    assert cfg.api_key == "test-cohere-key"


# ── model aliases resolve correctly ──────────────────────────────────────────

def test_mistral_large_alias():
    from coverletter.costs import resolve_model
    assert resolve_model("mistral-large") == "mistral/mistral-large-latest"


def test_gpt4o_alias():
    from coverletter.costs import resolve_model
    assert resolve_model("gpt-4o") == "openai/gpt-4o"


def test_command_r_alias():
    from coverletter.costs import resolve_model
    assert resolve_model("command-r") == "cohere/command-r"


def test_command_r_plus_alias():
    from coverletter.costs import resolve_model
    assert resolve_model("command-r-plus") == "cohere/command-r-plus"


def test_bge_m3_alias():
    from coverletter.costs import resolve_model
    assert resolve_model("bge-m3") == "bge-m3/BAAI/bge-m3"


def test_unknown_model_passes_through():
    from coverletter.costs import resolve_model
    assert resolve_model("some/custom-model") == "some/custom-model"


# ── db_path contract via config ───────────────────────────────────────────────

def test_db_path_from_config_paragraphs_files(test_cfg):
    """Ensure db_path(cfg.paragraphs_files) never receives a non-list."""
    from coverletter.db import db_path
    result = db_path(test_cfg.paragraphs_files)
    assert result.name == "library.db"
    assert result.parent == test_cfg.paragraphs_files[0].parent
