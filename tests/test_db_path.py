"""
Tests for db_path — the bug that kept recurring was passing a single Path
instead of list[Path]. These tests lock down the contract.
"""
from pathlib import Path
import pytest
from coverletter.db import db_path


def test_db_path_returns_sibling_of_first_file():
    files = [Path("/home/user/cover-letters/library.md")]
    assert db_path(files) == Path("/home/user/cover-letters/library.db")


def test_db_path_uses_first_file_when_multiple():
    files = [
        Path("/home/user/cover-letters/library_refined.md"),
        Path("/home/user/cover-letters/library.md"),
    ]
    assert db_path(files) == Path("/home/user/cover-letters/library.db")


def test_db_path_requires_list_not_bare_path():
    """Passing a bare Path raises TypeError — catches the recurring bug."""
    with pytest.raises((TypeError, AttributeError)):
        db_path(Path("/home/user/cover-letters/library.md"))  # type: ignore


def test_db_path_requires_list_not_string():
    """Passing a string raises — catches the ctx.obj["paragraphs"] pattern."""
    with pytest.raises((TypeError, AttributeError)):
        db_path("/home/user/cover-letters/library.md")  # type: ignore
