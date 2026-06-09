"""
Tests for coverletter init — the .env scaffold and next-steps output.
Guards against uv/pip regression and missing provider documentation.
"""
from pathlib import Path
import pytest


def _run_init(tmp_path):
    """Run init command in tmp_path. Returns .env content."""
    import os
    orig = os.getcwd()
    os.chdir(tmp_path)
    try:
        from coverletter.cli import init
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(init, [])
        return result, (tmp_path / ".env").read_text(encoding="utf-8")
    finally:
        os.chdir(orig)


def test_init_creates_env_file(tmp_path):
    result, env = _run_init(tmp_path)
    assert (tmp_path / ".env").exists()


def test_init_creates_library_md(tmp_path):
    _run_init(tmp_path)
    assert (tmp_path / "library.md").exists()


def test_env_uses_uv_not_pip(tmp_path):
    _, env = _run_init(tmp_path)
    assert "pip install" not in env
    assert "pip add" not in env


def test_env_contains_anthropic_key(tmp_path):
    _, env = _run_init(tmp_path)
    assert "ANTHROPIC_API_KEY" in env


def test_env_contains_mistral_key_commented(tmp_path):
    _, env = _run_init(tmp_path)
    assert "MISTRAL_API_KEY" in env


def test_env_contains_openai_key_commented(tmp_path):
    _, env = _run_init(tmp_path)
    assert "OPENAI_API_KEY" in env


def test_env_contains_cohere_key_commented(tmp_path):
    _, env = _run_init(tmp_path)
    assert "COHERE_API_KEY" in env


def test_env_contains_embed_model(tmp_path):
    _, env = _run_init(tmp_path)
    assert "EMBED_MODEL" in env


def test_env_contains_voyage_key(tmp_path):
    _, env = _run_init(tmp_path)
    assert "VOYAGE_API_KEY" in env


def test_next_steps_uses_uv_run(tmp_path):
    result, _ = _run_init(tmp_path)
    assert "uv run clio" in result.output


def test_next_steps_mentions_build_jd(tmp_path):
    result, _ = _run_init(tmp_path)
    assert "build --jd" in result.output


def test_next_steps_mentions_seed(tmp_path):
    result, _ = _run_init(tmp_path)
    assert "seed" in result.output


def test_init_skips_existing_env(tmp_path):
    (tmp_path / ".env").write_text("EXISTING=1")
    _, env = _run_init(tmp_path)
    assert env == "EXISTING=1"


def test_init_skips_existing_library(tmp_path):
    (tmp_path / "library.md").write_text("# Existing")
    _run_init(tmp_path)
    assert (tmp_path / "library.md").read_text() == "# Existing"
