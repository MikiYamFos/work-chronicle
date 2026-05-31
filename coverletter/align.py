from __future__ import annotations

import re
from dataclasses import dataclass, field

from coverletter.costs import record, supports_temperature
from coverletter.parser import Paragraph
from coverletter.profile import CandidateProfile

ARGUMENT_SYSTEM = """\
You are a cover letter strategist. Be direct and specific. No filler.
"""

ARGUMENT_PROMPT = """\
=== JOB DESCRIPTION ===
{jd}
{candidate_section}
What is the single strongest argument for this candidate at this role?

Complete this sentence:
"This letter should argue that [describe the candidate's specific capability or experience type] \
is exactly what this role needs because [what the JD is specifically seeking that this candidate \
uniquely provides]."

Rules:
- Name the specific technical or domain capability the JD centers on — not generic credentials
- Ground the claim in the JD's actual requirements, not resume summary language
- The candidate clause must describe a specific kind of work, role, or constraint — not a
  quality-adjective ("high-stakes data," "consequential systems," "critical environments").
  Adjectives are not arguments. What did they BUILD, OWN, or DECIDE that is specific to them?
- One sentence. Output only the sentence. No preamble.
"""

THESIS_SYSTEM = """\
You are a cover letter strategist.
{candidate_profile}
When evaluating a thesis, square THREE things simultaneously:
1. What the candidate wants from this role — goals, values, and what kind of work they find meaningful
2. What this JD is explicitly asking for
3. What angle the letter actually leads with

Mission alignment and values alignment count toward fit alongside technical goal overlap.
Express fit positively — what the role IS and what it offers the candidate.
Never frame fit as contrast, avoidance, or escape. Say what is true, not what it opposes.
Only name tensions that genuinely affect fit. Do not manufacture caveats.
Be direct and specific. No filler.
"""

THESIS_SYSTEM_EMPTY = """\
You are a cover letter strategist. Be direct and specific. No filler.
"""

THESIS_PROMPT = """\
=== JOB DESCRIPTION ===
{jd}

=== COVER LETTER ===
{letter}
{candidate_goals_section}{correction_section}
Write ONE sentence — the thesis of this cover letter. Complete this template:
"This letter argues that [candidate description] is the right fit for this role because \
[specific claim grounded in the letter's actual content]."

Rules:
- The claim must be specific to THIS letter and THIS JD. Name the actual experience or angle
  the letter leads with — not a generic description.
- Ground it in what the letter SAYS — specific experiences, decisions, or evidence named
  in the body paragraphs. Do not summarize goals or values not evidenced in the letter.
- One clause only. Do not add a second clause about why the role fits the candidate.
  That question belongs in the alignment report, not the thesis.
- Crisp enough that someone reading it could predict what evidence the body paragraphs contain.
{correction_rule}
Output only the one sentence. No preamble, no explanation.
"""

ALIGN_SYSTEM = """\
You are a job description analyst.

When seniority signals are provided, evaluate the letter against them. Flag a signal as
missing only if the letter genuinely doesn't address it — not if it is implicit. A letter
that describes owning a system through production incidents covers "production ownership"
without using that phrase.

Be direct, specific, and actionable. Do not be encouraging or add filler.
"""

SENIORITY_SIGNALS_BLOCK = """\
SENIORITY SIGNALS FOR THIS ROLE TYPE
{signals}
These are the dimensions that distinguish senior candidates from mid-level ones for this
role. Flag missing ones only if genuinely absent — not if they are implicit or understated.
"""

ALIGN_PROMPT = """\
=== PARAGRAPH LIBRARY (available but may not all be in the letter) ===
{library}

=== JOB DESCRIPTION ===
{jd}

=== CURRENT LETTER ===
{letter}
{seniority_signals_section}{candidate_goals_section}
Analyze how well the letter addresses the JD. Output exactly {num_sections} sections with no extra text.

SCORE: [N covered] of [M total] JD requirements

COVERED
One line per covered requirement.
Format: ✓ [requirement] — [how the letter covers it]

GAPS
One line per gap. Only real gaps — things the JD explicitly requires or prefers that the letter
does not address.
Format: ✗ [requirement] — [why it matters for this role]
If a gap is addressed by a paragraph in the library above (even if not used in the current letter),
append: (library: [N]) using the exact paragraph index. Only tag it if a specific paragraph
genuinely covers that requirement — not just shares vocabulary with it.
{seniority_gaps_section}{goal_alignment_section}
Do not add encouragement, filler, or any sections beyond these {num_sections}.
"""

SENIORITY_GAPS_SECTION = """\

SENIORITY SIGNAL GAPS
One line per missing signal (see seniority signals above). Write "(none)" if all are covered.
These are not JD requirements — they are what separates senior candidates from mid-level ones.
Format: ✗ [signal] — [what's missing and why it matters]
"""

GOAL_ALIGNMENT_BLOCK = """\
GOAL ALIGNMENT
One line. Does this role serve the candidate's stated goals? Be direct — yes, partially, or no,
with one specific reason grounded in the JD and the candidate's goals.
"""


def has_library_coverage(gap_text: str) -> bool:
    """Return True if the gap text indicates the paragraph already exists in the library."""
    return bool(re.search(r'\(library:', gap_text, re.IGNORECASE))


_STOP_WORDS = {
    "and", "or", "the", "a", "an", "in", "of", "for", "to", "with", "that",
    "this", "it", "is", "are", "not", "as", "at", "by", "be", "but", "was",
    "its", "on", "no", "how", "from", "has", "does", "does", "does", "also",
    "role", "letter", "required", "explicitly", "addressed", "mentioned",
    "named", "listed", "absent", "missing", "not", "only", "across",
}


def _significant_terms(text: str) -> list[str]:
    """Extract meaningful terms from a gap description for library matching."""
    words = re.findall(r"[a-z][a-z0-9/+#]*", text.lower())
    return [w for w in words if len(w) > 2 and w not in _STOP_WORDS]


def _detect_library_coverage(
    gaps: list[str],
    paragraphs: list["Paragraph"],
) -> list[str]:
    """Post-process gap list: detect library coverage the LLM missed.

    For each gap not already tagged with (library: [N]), run BM25 against
    the paragraph library. If a paragraph scores strongly against the gap,
    append the tag. Runs in Python — not a second LLM call.
    """
    if not paragraphs or not gaps:
        return gaps

    try:
        from rank_bm25 import BM25Okapi

        corpus = [
            _significant_terms(p.section + " " + p.role + " " + p.text)
            for p in paragraphs
        ]
        bm25 = BM25Okapi(corpus)

        result = []
        for gap in gaps:
            if has_library_coverage(gap):
                result.append(gap)
                continue

            query = _significant_terms(gap)
            if not query:
                result.append(gap)
                continue

            scores = bm25.get_scores(query)
            best_i = int(max(range(len(scores)), key=lambda i: scores[i]))
            best_score = float(scores[best_i])

            # Threshold calibrated so a paragraph must share several meaningful
            # terms with the gap description — not just a single word match.
            if best_score >= 2.0:
                result.append(f"{gap} (library: [{paragraphs[best_i].index}])")
            else:
                result.append(gap)

        return result

    except ImportError:
        # rank_bm25 not available — fall back to simple term overlap
        result = []
        for gap in gaps:
            if has_library_coverage(gap):
                result.append(gap)
                continue

            gap_terms = set(_significant_terms(gap))
            if not gap_terms:
                result.append(gap)
                continue

            best_score = 0.0
            best_idx = None
            for p in paragraphs:
                p_terms = set(_significant_terms(p.section + " " + p.role + " " + p.text))
                overlap = len(gap_terms & p_terms) / len(gap_terms)
                if overlap > best_score:
                    best_score = overlap
                    best_idx = p.index

            if best_score >= 0.35 and best_idx is not None:
                result.append(f"{gap} (library: [{best_idx}])")
            else:
                result.append(gap)

        return result


@dataclass
class AlignmentResult:
    raw_text: str
    covered: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    seniority_gaps: list[str] = field(default_factory=list)
    goal_alignment: str = ""
    score_pct: int = 0
    perspective_note: str = ""  # set when no narrative frame paragraphs are in the library

    def score_line(self) -> str:
        n = len(self.covered)
        m = n + len(self.gaps)
        base = f"{self.score_pct}% aligned ({n} covered, {len(self.gaps)} gap(s))"
        if self.seniority_gaps:
            base += f", {len(self.seniority_gaps)} seniority signal gap(s)"
        return base


def _parse_alignment(text: str) -> AlignmentResult:
    covered: list[str] = []
    gaps: list[str] = []
    seniority_gaps: list[str] = []
    goal_alignment = ""
    score_pct = 0

    score_match = re.search(r"SCORE:\s*(\d+)\s*covered.*?(\d+)\s*total", text, re.IGNORECASE)
    if score_match:
        n_covered = int(score_match.group(1))
        n_total = int(score_match.group(2))
        score_pct = round(100 * n_covered / n_total) if n_total else 0

    section = None
    for line in text.splitlines():
        stripped = line.strip()
        upper = stripped.upper()
        if "SENIORITY SIGNAL" in upper:
            section = "seniority"
            continue
        elif "GOAL ALIGNMENT" in upper:
            section = "goal"
            continue
        elif upper.startswith("COVERED"):
            section = "covered"
            continue
        elif upper.startswith("GAPS") and "GOAL" not in upper:
            section = "gaps"
            continue

        if stripped.startswith("✓"):
            covered.append(stripped[1:].strip())
        elif stripped.startswith("✗"):
            if section == "seniority":
                seniority_gaps.append(stripped[1:].strip())
            else:
                gaps.append(stripped[1:].strip())
        elif section == "goal" and stripped and not stripped.startswith("SCORE"):
            if goal_alignment:
                goal_alignment += " " + stripped
            else:
                goal_alignment = stripped

    if not score_pct and (covered or gaps):
        total = len(covered) + len(gaps)
        score_pct = round(100 * len(covered) / total) if total else 0

    return AlignmentResult(
        raw_text=text,
        covered=covered,
        gaps=gaps,
        seniority_gaps=seniority_gaps,
        goal_alignment=goal_alignment,
        score_pct=score_pct,
    )


def generate_thesis(
    jd: str,
    letter: str,
    api_key: str,
    model: str,
    profile: CandidateProfile | None = None,
    correction: str | None = None,
) -> str:

    if profile and not profile.is_empty:
        system = THESIS_SYSTEM.format(candidate_profile=profile.as_full_text())
        fit_context = profile.as_fit_context()
        candidate_goals_section = f"\n=== CANDIDATE FIT CONTEXT (background only — do not include in thesis) ===\n{fit_context}\n"
    else:
        system = THESIS_SYSTEM_EMPTY
        candidate_goals_section = ""

    correction_section = (
        f"\n=== CANDIDATE CORRECTION ===\n{correction}\n"
        "Revise the thesis to address this correction while keeping it grounded in the letter.\n"
        if correction else ""
    )

    correction_rule = (
        "- Address the candidate's correction above."
        if correction else
        "- If there is genuine tension between the letter's angle and the JD, name it briefly."
    )

    prompt = THESIS_PROMPT.format(
        jd=jd.strip(),
        letter=letter.strip(),
        candidate_goals_section=candidate_goals_section,
        correction_section=correction_section,
        correction_rule=correction_rule,
    )

    from coverletter.provider import get_provider
    return get_provider(model, api_key).complete(system, prompt, max_tokens=300)


def generate_argument(
    jd: str,
    api_key: str,
    model: str,
    profile: CandidateProfile | None = None,
) -> str:
    """Generate a provisional argument target from the JD alone — before the letter exists.

    This is the beacon: a single sentence stating what the letter SHOULD argue.
    Used to focus sentence retrieval and anchor the model's assembly.
    """

    if profile and not profile.is_empty:
        candidate_section = f"\n=== CANDIDATE PROFILE ===\n{profile.as_goals_text()}\n"
    else:
        candidate_section = ""

    prompt = ARGUMENT_PROMPT.format(jd=jd.strip(), candidate_section=candidate_section)
    from coverletter.provider import get_provider
    return get_provider(model, api_key).complete(ARGUMENT_SYSTEM, prompt, max_tokens=200)


def alignment_report(
    jd: str,
    letter: str,
    filtered_paragraphs: list[Paragraph],
    api_key: str,
    model: str,
    profile: CandidateProfile | None = None,
) -> AlignmentResult:

    library_lines = []
    for p in filtered_paragraphs:
        library_lines.append(f"[{p.index}] {p.role} / {p.section}")
        library_lines.append(p.text)
        library_lines.append("")
    library_text = "\n".join(library_lines)

    has_profile = profile and not profile.is_empty
    has_signals = profile and bool(profile.seniority_signals)

    if has_profile:
        candidate_goals_section = f"\n=== CANDIDATE GOALS ===\n{profile.as_goals_text()}\n"
        goal_alignment_section = GOAL_ALIGNMENT_BLOCK
    else:
        candidate_goals_section = ""
        goal_alignment_section = ""

    if has_signals:
        signal_lines = "\n".join(f"- {s}" for s in profile.seniority_signals)
        seniority_signals_section = (
            f"\n=== SENIORITY SIGNALS ===\n{signal_lines}\n"
        )
        seniority_gaps_section = SENIORITY_GAPS_SECTION
    else:
        seniority_signals_section = ""
        seniority_gaps_section = ""

    num_sections_count = 2  # COVERED + GAPS always present
    if has_signals:
        num_sections_count += 1
    if has_profile:
        num_sections_count += 1
    num_sections = {2: "two", 3: "three", 4: "four"}.get(num_sections_count, str(num_sections_count))

    # Library is the stable part — cache it. JD + letter change per call.
    library_block = f"=== PARAGRAPH LIBRARY (available but may not all be in the letter) ===\n{library_text}"
    jd_block = ALIGN_PROMPT.format(
        jd=jd.strip(),
        letter=letter.strip(),
        seniority_signals_section=seniority_signals_section,
        candidate_goals_section=candidate_goals_section,
        library="",  # library is in its own cached block above
        seniority_gaps_section=seniority_gaps_section,
        goal_alignment_section=goal_alignment_section,
        num_sections=num_sections,
    ).replace("=== PARAGRAPH LIBRARY (available but may not all be in the letter) ===\n\n", "")

    user_content = [
        {"type": "text", "text": library_block, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": jd_block},
    ]

    from coverletter.provider import get_provider
    result = _parse_alignment(
        get_provider(model, api_key).complete(ALIGN_SYSTEM, user_content, max_tokens=1200)
    )

    # Perspective frame check — Python level, no LLM call needed.
    # If the library has no through-line, pivot, reframe, or synthesis paragraphs,
    # the letter has evidence but no narrative frame.
    from coverletter.prompt import PERSPECTIVE_ANGLES
    has_perspective = any(
        p.meta.get("angle", "").lower() in PERSPECTIVE_ANGLES
        for p in filtered_paragraphs
    )
    if not has_perspective:
        result.perspective_note = (
            "No through-line, pivot, reframe, or synthesis paragraph in library. "
            "The letter has evidence but no narrative frame. "
            "Run: coverletter reflect"
        )

    return result
