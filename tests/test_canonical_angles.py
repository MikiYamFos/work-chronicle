"""Tests for CANONICAL_ANGLES — definition quality and completeness."""
from __future__ import annotations

import re

import pytest

from coverletter.db import CANONICAL_ANGLES

EXPECTED_ANGLES = {
    "through-line", "autonomy", "ownership", "business-impact", "system-design",
    "requirements-translation", "compliance", "technical-depth", "precision",
    "communication", "leadership", "strategic-vision", "resilience",
    "problem-solving", "problem-definition", "trust", "recovery", "scope-expansion",
}

_FIRST_PERSON = re.compile(r"\bI\b|\bmy\b|\bmine\b|\bI've\b|\bI'm\b", re.IGNORECASE)

# Employer/tool names that should not appear in canonical descriptions
_PERSONAL_TOKENS = [
    "subscriber", "viewership", "CEO", "CFO", "campaign", "BritBox", "Universe",
    "UNITE HERE", "union membership", "health fund", "dues records",
    "Spark", "Redshift", "dbt", "Airflow", "BigQuery", "Prefect",
    "Elasticsearch", "Snowflake", "PySpark", "Glue", "midnight",
]


def test_all_expected_angles_present():
    assert set(CANONICAL_ANGLES.keys()) == EXPECTED_ANGLES


def test_no_missing_descriptions():
    for name, desc in CANONICAL_ANGLES.items():
        assert desc and desc.strip(), f"Empty description for '{name}'"


def test_minimum_description_length():
    for name, desc in CANONICAL_ANGLES.items():
        assert len(desc) >= 80, f"Description for '{name}' is too short ({len(desc)} chars)"


def test_no_first_person_pronouns():
    """Descriptions must be general, not first-person narrative."""
    for name, desc in CANONICAL_ANGLES.items():
        # Allow 'I' only inside words (like 'Identifying') — match standalone only
        matches = re.findall(r"(?<!\w)I(?!\w)|(?<!\w)[Mm]y(?!\w)", desc)
        assert not matches, (
            f"'{name}' contains first-person language: {matches}\n"
            f"Description: {desc[:100]}"
        )


def test_no_personal_employer_or_tool_examples():
    """Descriptions must not reference specific employers or tools from one person's history."""
    for name, desc in CANONICAL_ANGLES.items():
        for token in _PERSONAL_TOKENS:
            assert token.lower() not in desc.lower(), (
                f"'{name}' contains personal example '{token}'"
            )


def test_no_repeated_sentences(  ):
    """strategic-vision was previously broken with a repeated sentence — guard against recurrence."""
    for name, desc in CANONICAL_ANGLES.items():
        sentences = [s.strip() for s in desc.replace("—", ".").split(".") if len(s.strip()) > 20]
        seen = set()
        for s in sentences:
            normalized = re.sub(r"\s+", " ", s.lower())
            assert normalized not in seen, (
                f"'{name}' contains a repeated sentence fragment: '{s[:60]}'"
            )
            seen.add(normalized)


def test_descriptions_are_distinct():
    """No two descriptions should be near-identical (catches copy-paste errors)."""
    items = list(CANONICAL_ANGLES.items())
    for i, (name_a, desc_a) in enumerate(items):
        for name_b, desc_b in items[i + 1:]:
            words_a = set(re.findall(r"[a-z]+", desc_a.lower()))
            words_b = set(re.findall(r"[a-z]+", desc_b.lower()))
            if not words_a or not words_b:
                continue
            overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
            assert overlap < 0.85, (
                f"'{name_a}' and '{name_b}' descriptions are too similar "
                f"(word overlap: {overlap:.0%})"
            )
