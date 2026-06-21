from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from coverletter.provider import get_provider

# ---------------------------------------------------------------------------
# Level 3 — finished letter coach (existing)
# ---------------------------------------------------------------------------

COACH_SYSTEM = """\
You are a cover letter coach who evaluates individual sentences for impact, clarity, and persuasive force.
You flag weak sentences and suggest specific directions for improvement.
Return only valid JSON. No commentary outside the JSON.
"""

COACH_PROMPT = """\
Review this cover letter sentence by sentence. Flag sentences that are weak, vague, generic,
trail off, or miss an opportunity to land a stronger point. Do not flag sentences that are
already strong and specific.

Do NOT flag:
- The salutation ("Dear ... Hiring Manager,")
- The closing paragraph (thanks/sign-off) — it serves a structural, conventional role and should not be flagged
- Transition sentences that are intentionally brief and functional

For each weak sentence, return:
- "sentence": the exact sentence as it appears
- "issue": one short sentence saying what's wrong (vague, trails off, no consequence, generic claim, etc.)

Return JSON array. If nothing is weak, return [].

=== LETTER ===
{letter}
"""

REWRITE_SYSTEM = """\
You are a cover letter editor. Rewrite the flagged passage according to a direction.
The passage may be one sentence or several. Output only the rewritten passage — nothing else.
Preserve the factual content and the writer's voice. If the content requires multiple sentences, write multiple sentences.

ABSOLUTE CONSTRAINTS — these apply to every rewrite, no exceptions:

No em-dash (—) anywhere. Use a comma, semicolon, or period instead.

No present progressive or progressive chains. This is the most common failure mode in rewrites.
WRONG: "I have been building toward", "work I have been doing", "I have been developing"
RIGHT: "I built", "I have built", "this is work I have done", "I have spent years building"
The writer speaks declaratively. Simple past or simple present. Never progressive.

No filler adjectives before verbs: "genuinely welcome", "truly appreciate" — cut the adverb.

No "actually", "not just", "not only", "not simply".

No fake contrast structure: "not X; they are Y", "not X, but Y", "not X — they are Y".
These are AI rhetorical moves. Cut them entirely.

No sentence starting with "That".

The user's direction often mixes three things in one message:
1. Reactions and frustration ("I hate this", "this says nothing", "this is vague bullshit")
2. Instructions about what to do ("delete this", "replace with a bold claim", "don't rephrase so much")
3. Actual prose they want in the letter

Your job: identify which parts are prose and use those. Ignore the reactions and instructions — they tell
you what to do, not what to write. Do not include instructions or reactions as sentences in the rewrite.

If the direction contains prose that sounds like it belongs in a cover letter, use it directly or shape it
minimally to fit. Do not discard the user's words and invent something else. The user's prose is the source.
Your job is to shape it, not replace it.
"""

REWRITE_PROMPT = """\
Original sentence: {sentence}

Surrounding context (do not rewrite this, just use it for tone and flow):
{context}

Direction: {direction}

Rewrite the passage according to the direction. Output only the rewritten passage — no preamble, no commentary.
"""

REWRITE_DIRECTION = """\
Fix the issue identified. Use the user's input as your guide — if they wrote a direction
(e.g. "make this hit harder", "add the consequence"), rewrite accordingly. If they wrote
replacement content, use it directly or refine it to fit the context. The rewrite may be
one sentence or several — however many the content requires. Output only the revised passage."""


@dataclass
class WeakSentence:
    sentence: str
    issue: str


def analyze_letter(letter: str, api_key: str, model: str) -> list[WeakSentence]:
    prompt = COACH_PROMPT.format(letter=letter)
    raw = get_provider(model, api_key).complete(COACH_SYSTEM, prompt, max_tokens=1024, temperature=0)
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        items = json.loads(raw)
        return [WeakSentence(sentence=i["sentence"], issue=i["issue"]) for i in items]
    except Exception:
        return []


def rewrite_sentence(sentence: str, context: str, issue: str, user_input: str, api_key: str, model: str) -> str:
    direction = f"Issue: {issue}\nUser input: {user_input}\n\n{REWRITE_DIRECTION}"
    prompt = REWRITE_PROMPT.format(sentence=sentence, context=context, direction=direction)
    return get_provider(model, api_key).complete(REWRITE_SYSTEM, prompt, max_tokens=512, temperature=0.3)


def get_context(letter: str, sentence: str, window: int = 200) -> str:
    idx = letter.find(sentence)
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(letter), idx + len(sentence) + window)
    return letter[start:end]


# ---------------------------------------------------------------------------
# Level 1 — draft fidelity coach
#
# Runs on a Claude-generated draft paragraph against the writer's raw source.
# Checks: fidelity to source words, invented sentences, coverage gaps.
# Does NOT rewrite — flags issues and offers suggestions rooted in raw text.
# ---------------------------------------------------------------------------

_DRAFT_COACH_SYSTEM = """\
You are reviewing a draft paragraph for fidelity to the writer's raw source material.

The draft was generated by an AI from the writer's raw text. Your job is to find where
the draft departed from the writer's actual words and meaning.

The writer's voice and specific language are the standard. The draft is judged against them.

Return only valid JSON. No commentary outside the JSON.
"""

_DRAFT_COACH_PROMPT = """\
=== WRITER'S RAW TEXT (source of truth) ===
{raw_text}

=== DRAFT PARAGRAPH (generated — check against raw) ===
{draft_text}

Review the draft sentence by sentence against the raw text. Flag these problems:

1. WORD SWAP — the draft replaced the writer's specific words with weaker, vaguer, or more
   corporate alternatives. The nuance, register, or precision was lost.
   Example: writer said "I was the card check queen" → draft says "I managed card check operations"

2. INVENTED SENTENCE — the draft added a sentence (often an opener or closer) that has no
   basis in the raw text. The writer didn't say it.

3. MEANING SHIFT — the draft reorganized the writer's content into a different point than
   they made. The structure changed what was being said.

4. COVERAGE GAP — something significant in the raw text (a specific fact, claim, or piece
   of evidence) did not make it into the draft at all.

For each problem found, return:
- "type": one of "word_swap" | "invented" | "meaning_shift" | "coverage_gap"
- "draft_sentence": the exact draft sentence with the problem (null for coverage_gap)
- "raw_reference": the relevant raw text this should have come from (null if invented)
- "issue": one sentence naming the specific problem
- "suggestion": a suggested fix rooted in the writer's actual words. For coverage_gap,
  suggest the sentence or phrase from the raw text that should be added.
  Hold this lightly — it is a starting point, not a prescription.

Return JSON array. If the draft is faithful to the raw text, return [].
"""


@dataclass
class DraftIssue:
    type: str           # word_swap | invented | meaning_shift | coverage_gap
    draft_sentence: str | None
    raw_reference: str | None
    issue: str
    suggestion: str


def analyze_draft(raw_text: str, draft_text: str, api_key: str, model: str) -> list[DraftIssue]:
    """Level 1 coach — check draft fidelity against raw source text."""
    prompt = _DRAFT_COACH_PROMPT.format(raw_text=raw_text.strip(), draft_text=draft_text.strip())
    raw = get_provider(model, api_key).complete(_DRAFT_COACH_SYSTEM, prompt, max_tokens=2048, temperature=0)
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        items = json.loads(raw)
        return [
            DraftIssue(
                type=i.get("type", "word_swap"),
                draft_sentence=i.get("draft_sentence"),
                raw_reference=i.get("raw_reference"),
                issue=i.get("issue", ""),
                suggestion=i.get("suggestion", ""),
            )
            for i in items
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Level 2 — library paragraph coach
#
# Runs on a paragraph the writer has edited and approved before it goes into
# library_salvaged.md or library_rebuilt.md.
#
# Checks: opener quality, banned AI constructs, passive voice in claim sentences.
# Perspective paragraphs (via=reflect or perspective angles) use relaxed opener rules.
# ---------------------------------------------------------------------------

_PERSPECTIVE_ANGLES = {"through-line", "pivot", "reframe", "synthesis"}

_LIBRARY_COACH_SYSTEM = """\
You are reviewing a library paragraph for specific problems before it goes into a
cover letter paragraph library. Your job is to flag concrete, rule-based issues only.

Do not flag style preferences. Do not flag things that are strong. Do not rewrite.
Return only valid JSON. No commentary outside the JSON.
"""

_LIBRARY_COACH_PROMPT = """\
=== PARAGRAPH ===
{para_text}

Paragraph type: {para_type}

Review this paragraph for the following specific problems only:

━━━ OPENER ━━━
{opener_rule}

A bad opener:
- Is so vague it could apply to anyone
- Could be cut entirely without changing what the paragraph says
- Is purely throat-clearing — it exists to begin, not to make a point
- Is so long it buries the actual claim

A good opener:
- Names the employer, claim, or specific situation immediately
- Creates a connection — it drives into what matters
- Could not be cut without losing something real

━━━ BANNED CONSTRUCTS ━━━
Flag any of these — they are AI writing crutches that lose precision:
- False contrast: "not just X but Y", "not only X", "not simply X", "not X, but Y"
- Em-dash used as sentence structure (—)
- The words: "actually", "matters" (used as emphasis), "not just", "not only", "not simply"
- Any sentence starting with "That"
- Fake comparisons that set up a distinction not grounded in a real difference

━━━ PASSIVE VOICE ━━━
Flag passive voice ONLY in sentences that are making the main claim or assertion —
the sentence that states what the person owned, built, or decided.
Do NOT flag passive voice in evidentiary sentences about past experiences
("I was given", "I was responsible for", "I was taught" are fine).

For each problem found, return:
- "type": one of "opener" | "banned_construct" | "passive_claim"
- "sentence": the exact sentence with the problem
- "issue": one sentence naming the specific problem
- "suggestion": a concrete suggestion for fixing it, held lightly

Return JSON array. If nothing is wrong, return [].
"""

_OPENER_RULE_EVIDENCE = """\
For evidence paragraphs: the opener should name the employer or specific situation
immediately. "At UNITE HERE, I..." is correct. A vague opener that doesn't ground
the paragraph in a specific context is wrong."""

_OPENER_RULE_PERSPECTIVE = """\
For perspective/narrative paragraphs (through-line, pivot, reframe, synthesis):
the opener should create a meaningful connection and serve the argument.
It does not need to name an employer. It DOES need to do real work —
a sentence that could be cut without losing anything is still bad."""


@dataclass
class LibraryIssue:
    type: str           # opener | banned_construct | passive_claim
    sentence: str
    issue: str
    suggestion: str


def analyze_library_paragraph(
    para_text: str,
    api_key: str,
    model: str,
    via: str = "",
    angle: str = "",
) -> list[LibraryIssue]:
    """Level 2 coach — check a library paragraph for rule-based issues."""
    is_perspective = (
        via == "reflect"
        or angle.lower() in _PERSPECTIVE_ANGLES
    )
    opener_rule = _OPENER_RULE_PERSPECTIVE if is_perspective else _OPENER_RULE_EVIDENCE
    para_type = "perspective/narrative" if is_perspective else "evidence"

    prompt = _LIBRARY_COACH_PROMPT.format(
        para_text=para_text.strip(),
        para_type=para_type,
        opener_rule=opener_rule,
    )
    raw = get_provider(model, api_key).complete(_LIBRARY_COACH_SYSTEM, prompt, max_tokens=1024, temperature=0)
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        items = json.loads(raw)
        return [
            LibraryIssue(
                type=i.get("type", "opener"),
                sentence=i.get("sentence", ""),
                issue=i.get("issue", ""),
                suggestion=i.get("suggestion", ""),
            )
            for i in items
        ]
    except Exception:
        return []
