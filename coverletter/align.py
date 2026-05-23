from __future__ import annotations

import re
from dataclasses import dataclass, field

from coverletter.costs import record, supports_temperature
from coverletter.parser import Paragraph
from coverletter.profile import CandidateProfile

THESIS_SYSTEM = """\
You are a cover letter strategist for a senior data engineer.
{candidate_profile}
When evaluating a thesis, square THREE things simultaneously:
1. What the candidate wants from this role (goals above)
2. What this JD is explicitly asking for
3. What angle the letter actually leads with

A thesis that ignores any of the three is wrong, even if it sounds polished.
If there is genuine tension between the JD and the candidate's goals — name it.
A thesis that honestly acknowledges fit limits is more useful than one that oversells.
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
{candidate_goals_section}
Write ONE sentence — the thesis of this cover letter. Complete this template:
"This letter argues that [candidate description] is the right fit for this role because \
[specific claim grounded in the letter's content]{goal_fit_clause}."

Rules:
- The claim must be specific to THIS letter and THIS JD. Name the actual experience or angle
  the letter leads with — not a generic description.
{goal_fit_rule}
Output only the one sentence. No preamble, no explanation.
"""

ALIGN_SYSTEM = """\
You are a job description analyst specializing in data engineering roles.

In addition to explicit JD requirements, evaluate the letter against the seniority signals
that distinguish senior data engineers from mid-level ones. These are not soft preferences —
they are the dimensions where senior candidates are actually evaluated and disqualified.

SENIOR DE SENIORITY SIGNALS:
- Business impact: does the letter quantify outcomes? (pipeline throughput, latency, cost,
  downstream product effects) — not just "built X" but "X enabled Y"
- Production ownership: evidence of owning systems in production — SLAs, incident response,
  on-call, reliability decisions — not just building greenfield
- System design judgment: did they make architectural trade-offs and articulate why? Choosing
  a tool or approach because it was right for the problem, not because it was available
- Data modeling depth: schema design, modeling decisions, SCD handling, or warehouse design
  — the dimension practitioners consistently identify as the make-or-break for senior roles
- Cross-functional effectiveness: translating between data infrastructure and business/product
  needs — not just collaborating with other engineers

Flag missing signals as gaps only if the letter genuinely doesn't address them — not if they
are implicit. A letter that describes owning a pipeline through production incidents covers
"production ownership" even without using that phrase.

Be direct, specific, and actionable. Do not be encouraging or add filler.
"""

ALIGN_PROMPT = """\
=== PARAGRAPH LIBRARY (available but may not all be in the letter) ===
{library}

=== JOB DESCRIPTION ===
{jd}

=== CURRENT LETTER ===
{letter}
{candidate_goals_section}
Analyze how well the letter addresses the JD. Output exactly {num_sections} sections with no extra text.

SCORE: [N covered] of [M total] JD requirements

COVERED
One line per covered requirement.
Format: ✓ [requirement] — [how the letter covers it]

GAPS
One line per gap. Only real gaps — things the JD explicitly requires or prefers that the letter
does not address.
Format: ✗ [requirement] — [why it matters for this role]

SENIORITY SIGNAL GAPS
One line per missing senior DE signal (see system prompt). Omit this section entirely if the
letter demonstrates all five signals — write "SENIORITY SIGNAL GAPS\n(none)" in that case.
These are not JD requirements — they are what separates senior candidates from mid-level ones.
Format: ✗ [signal] — [what's missing and why it matters for a senior role]
{goal_alignment_section}
Do not add encouragement, filler, or any sections beyond these {num_sections}.
"""

GOAL_ALIGNMENT_BLOCK = """\
GOAL ALIGNMENT
One line. Does this role serve the candidate's stated goals? Be direct — yes, partially, or no,
with one specific reason grounded in the JD and the candidate's goals.
"""


@dataclass
class AlignmentResult:
    raw_text: str
    covered: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    seniority_gaps: list[str] = field(default_factory=list)
    goal_alignment: str = ""
    score_pct: int = 0

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
) -> str:
    import anthropic

    if profile and not profile.is_empty:
        system = THESIS_SYSTEM.format(candidate_profile=profile.as_full_text())
        candidate_goals_section = f"\n=== CANDIDATE GOALS ===\n{profile.as_goals_text()}\n"
        goal_fit_clause = ", and this role fits the candidate because [how it serves their stated goals]"
        goal_fit_rule = (
            "- The 'fits the candidate' clause must be honest. If the role only partially "
            "serves their goals, say so.\n"
            "- If the letter's angle doesn't align well with the JD or the candidate's goals, "
            "note the tension rather than pretending it doesn't exist."
        )
    else:
        system = THESIS_SYSTEM_EMPTY
        candidate_goals_section = ""
        goal_fit_clause = ""
        goal_fit_rule = "- If there is tension between the letter's angle and the JD, name it."

    prompt = THESIS_PROMPT.format(
        jd=jd.strip(),
        letter=letter.strip(),
        candidate_goals_section=candidate_goals_section,
        goal_fit_clause=goal_fit_clause,
        goal_fit_rule=goal_fit_rule,
    )

    client = anthropic.Anthropic(api_key=api_key)
    kwargs: dict = dict(
        model=model,
        max_tokens=300,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )
    if supports_temperature(model):
        kwargs["temperature"] = 0
    response = client.messages.create(**kwargs)
    usage = response.usage
    record(
        model, usage.input_tokens, usage.output_tokens,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
    )
    return response.content[0].text.strip()


def alignment_report(
    jd: str,
    letter: str,
    filtered_paragraphs: list[Paragraph],
    api_key: str,
    model: str,
    profile: CandidateProfile | None = None,
) -> AlignmentResult:
    import anthropic

    library_lines = []
    for p in filtered_paragraphs:
        library_lines.append(f"[{p.index}] {p.role} / {p.section}")
        library_lines.append(p.text)
        library_lines.append("")
    library_text = "\n".join(library_lines)

    has_profile = profile and not profile.is_empty
    if has_profile:
        candidate_goals_section = f"\n=== CANDIDATE GOALS ===\n{profile.as_goals_text()}\n"
        goal_alignment_section = GOAL_ALIGNMENT_BLOCK
        num_sections = "four"
    else:
        candidate_goals_section = ""
        goal_alignment_section = ""
        num_sections = "three"

    # Library is the stable part — cache it. JD + letter change per call.
    library_block = f"=== PARAGRAPH LIBRARY (available but may not all be in the letter) ===\n{library_text}"
    jd_block = ALIGN_PROMPT.format(
        jd=jd.strip(),
        letter=letter.strip(),
        candidate_goals_section=candidate_goals_section,
        library="",  # library is in its own cached block above
        goal_alignment_section=goal_alignment_section,
        num_sections=num_sections,
    ).replace("=== PARAGRAPH LIBRARY (available but may not all be in the letter) ===\n\n", "")

    user_content = [
        {"type": "text", "text": library_block, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": jd_block},
    ]

    client = anthropic.Anthropic(api_key=api_key)
    kwargs: dict = dict(
        model=model,
        max_tokens=1200,
        system=[{"type": "text", "text": ALIGN_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_content}],
    )
    if supports_temperature(model):
        kwargs["temperature"] = 0
    response = client.messages.create(**kwargs)
    usage = response.usage
    record(
        model, usage.input_tokens, usage.output_tokens,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
    )
    return _parse_alignment(response.content[0].text.strip())
