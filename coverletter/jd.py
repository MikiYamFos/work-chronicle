"""
JD preprocessing — cleaning and company context extraction.

clean_jd()             — strips EEO/legal boilerplate before embedding or sending to LLM
extract_company_values() — pulls values/mission from JD via a cheap LLM call
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Section headers that signal the start of boilerplate to strip
# ---------------------------------------------------------------------------

_STRIP_HEADERS = re.compile(
    r"""
    (?:^|\n)                        # start of string or newline
    [^\n]{0,60}                     # optional lead-in text on same line (short)
    (?:
        equal\s+opportunity
        | eeo\b
        | affirmative\s+action
        | voluntary\s+self.?identif
        | self.?identif(?:ication)?(?:\s+of\s+disability)?
        | disability\s+disclosure
        | reasonable\s+accommodat
        | protected\s+veteran
        | veteran\s+status
        | gender\s+identity
        | sexual\s+orientation(?:\s+disclosure)?
        | race[,\s]+color[,\s]+religion    # classic EEO sentence
        | we\s+do\s+not\s+discriminate
        | applicants?\s+will\s+receive\s+consideration
        | employment\s+is\s+at.will
        | background\s+check\s+required
        | e-?verify
    )
    [^\n]*                          # rest of that line
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Paragraph-level patterns — strip any paragraph (blank-line-delimited chunk)
# that is predominantly boilerplate regardless of header
_BOILERPLATE_PARAGRAPH = re.compile(
    r"""
    (?:
        equal\s+opportunity\s+employer
        | eeo\b
        | affirmative\s+action
        | voluntary\s+self.?identif
        | omb\s+control\s+number        # federal disclosure form reference
        | section\s+503\b               # Rehabilitation Act section
        | vevraa\b                      # Vietnam Era Veterans' Readjustment
        | vietnam\s+era\s+veteran
        | we\s+do\s+not\s+discriminate
        | disability\s+status
        | protected\s+veteran\s+status
        | race[,\s]+color[,\s]+religion
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)


def clean_jd(text: str) -> str:
    """Strip EEO, voluntary disclosure, and legal boilerplate from a job description.

    Strategy:
    1. Find the first line that signals a boilerplate section.
    2. If it's in the last 40% of the text, truncate there — most JDs end with boilerplate.
    3. Otherwise, remove only the offending paragraph(s) and continue.

    Returns the cleaned text, stripped of leading/trailing whitespace.
    """
    if not text:
        return text

    lines = text.splitlines()
    total = len(lines)
    tail_zone = int(total * 0.70)  # last 30% of document

    # Find first boilerplate line
    first_hit = None
    for i, line in enumerate(lines):
        if _STRIP_HEADERS.search("\n" + line):
            first_hit = i
            break

    if first_hit is not None and first_hit >= tail_zone:
        # Boilerplate in the tail — only truncate if there's no real content after it.
        # "Real content" = non-boilerplate text after the hit line.
        after_lines = lines[first_hit + 1:]
        has_real_content_after = any(
            l.strip()
            and not _STRIP_HEADERS.search("\n" + l)
            and not _BOILERPLATE_PARAGRAPH.search(l)
            for l in after_lines
        )
        if not has_real_content_after:
            # Nothing real follows — truncate cleanly before the boilerplate
            cut = first_hit
            while cut > 0 and lines[cut - 1].strip():
                cut -= 1
            text = "\n".join(lines[:cut]).strip()

    # Always run paragraph-level stripping to catch any remaining boilerplate
    paragraphs = re.split(r"\n\s*\n", text)
    cleaned = []
    for para in paragraphs:
        if _BOILERPLATE_PARAGRAPH.search(para):
            continue
        cleaned.append(para)
    return "\n\n".join(cleaned).strip()


# ---------------------------------------------------------------------------
# Company values / mission extraction
# ---------------------------------------------------------------------------

_VALUES_SYSTEM = """\
You are reading a job description. Extract any company values, mission statement, or
cultural principles the company states about itself — in their own words.

Return a single short paragraph (2–4 sentences) summarising what the company says it
stands for, what it values, or what its mission is. Use their language, not yours.

If the JD contains no values, mission, or cultural content, return exactly: NONE
"""


def extract_company_values(text: str, api_key: str, model: str) -> str | None:
    """Extract company values/mission from a JD via a cheap LLM call.

    Returns a short summary string, or None if no values content is found.
    Caller should cache the result — call get_or_company_values() in db.py instead.
    """
    from coverletter.provider import get_provider
    # Use a fast/cheap model — this is a simple extraction task
    from coverletter.costs import resolve_model
    provider_name = model.split("/")[0] if "/" in model else "anthropic"
    fast_model = {
        "anthropic": "claude-haiku-4-5-20251001",
        "mistral": "mistral/mistral-small-latest",
        "openai": "openai/gpt-4o-mini",
        "cohere": "cohere/command-r",
    }.get(provider_name, model)

    raw = get_provider(fast_model, api_key).complete(
        _VALUES_SYSTEM, text.strip()[:3000], max_tokens=200
    )
    cleaned = raw.strip()
    if not cleaned or cleaned.upper() == "NONE":
        return None
    return cleaned
