"""
Tests for JD preprocessing — clean_jd().

Guards against:
- EEO/disability boilerplate making it into embeddings or LLM context
- Clean JDs being accidentally truncated
- Values/mission content being stripped when it shouldn't be
"""
from coverletter.jd import clean_jd

# ── EEO boilerplate in the tail (most common case) ───────────────────────────

REAL_JD = """\
We are looking for a senior data engineer to join our platform team.

You will own our Kafka-based event pipeline and dbt transformation layer.

Requirements:
- 5+ years data engineering experience
- Strong Python and SQL
- Experience with Airflow or similar orchestration

We offer competitive compensation and remote-first culture.
"""

EEO_SUFFIX = """\
Equal Opportunity Employer

We are an equal opportunity employer and do not discriminate on the basis of
race, color, religion, sex, national origin, age, disability, or any other
characteristic protected by applicable law.

Voluntary Self-Identification of Disability

Form CC-305, OMB Control Number 1250-0005, Expires 04/30/2026.

Why are you being asked to complete this form? We are a federal contractor or
subcontractor required by law to provide equal employment opportunity to
qualified people with disabilities.
"""


def test_eeo_tail_stripped():
    jd = REAL_JD + EEO_SUFFIX
    result = clean_jd(jd)
    assert "Equal Opportunity Employer" not in result
    assert "Voluntary Self-Identification" not in result
    assert "OMB Control Number" not in result


def test_actual_jd_content_preserved():
    jd = REAL_JD + EEO_SUFFIX
    result = clean_jd(jd)
    assert "Kafka" in result
    assert "dbt" in result
    assert "Airflow" in result
    assert "senior data engineer" in result


def test_clean_jd_with_no_boilerplate_unchanged():
    result = clean_jd(REAL_JD)
    assert result.strip() == REAL_JD.strip()


def test_we_do_not_discriminate_stripped():
    jd = REAL_JD + "\n\nWe do not discriminate on the basis of race, color, religion.\n"
    result = clean_jd(jd)
    assert "do not discriminate" not in result
    assert "Kafka" in result


def test_vevraa_stripped():
    jd = REAL_JD + "\n\nVEVRAA Federal Contractor. Protected veteran status applies.\n"
    result = clean_jd(jd)
    assert "VEVRAA" not in result
    assert "veteran status" not in result
    assert "Kafka" in result


def test_empty_string_handled():
    assert clean_jd("") == ""


def test_whitespace_only_handled():
    assert clean_jd("   \n  ") == ""


def test_boilerplate_only_jd_returns_empty_or_short():
    """A JD that is entirely boilerplate should not return the boilerplate."""
    result = clean_jd("We are an Equal Opportunity Employer. We do not discriminate.")
    assert "Equal Opportunity" not in result


# ── Values/mission content must NOT be stripped ──────────────────────────────

def test_company_values_not_stripped():
    jd = REAL_JD + "\n\nOur mission is to make healthcare data trustworthy and actionable.\n"
    result = clean_jd(jd)
    assert "mission" in result
    assert "healthcare" in result


def test_company_values_section_preserved():
    jd = """\
Senior Data Engineer

We build tools that help scientists make better decisions.

Our values:
- Rigorous over fast
- Transparent about uncertainty
- Data as a shared resource

Requirements: Python, SQL, 4+ years experience.
"""
    result = clean_jd(jd)
    assert "Rigorous over fast" in result
    assert "Transparent about uncertainty" in result


# ── Boilerplate mixed into middle (paragraph stripping) ──────────────────────

def test_mid_document_eeo_paragraph_stripped():
    jd = """\
Senior Data Engineer

We build real-time data infrastructure.

We are an Equal Opportunity Employer committed to diversity and inclusion.

Responsibilities: own the Kafka pipeline, maintain dbt models.
"""
    result = clean_jd(jd)
    assert "Equal Opportunity Employer" not in result
    assert "Kafka" in result
    assert "dbt" in result


def test_disability_disclosure_paragraph_stripped():
    jd = """\
Data Platform Engineer

Own our data warehouse and pipeline infrastructure.

Voluntary Self-Identification of Disability: We are required by law to ask
whether you have a disability as defined under the Americans with Disabilities Act.

Requirements: 3+ years, Python, SQL.
"""
    result = clean_jd(jd)
    assert "Voluntary Self-Identification" not in result
    assert "data warehouse" in result
    assert "Python" in result
