from __future__ import annotations

import json
import re
from pathlib import Path


SEED_SYSTEM = """\
You are organizing cover letter paragraphs from the writer's existing material.

YOUR ONLY JOB: identify which sentences from the source belong together as a paragraph,
and return those sentences quoted exactly. You do not write. You do not paraphrase.
You select and order.

HOW IT WORKS:
1. Read the source and identify distinct experiences or arguments
2. For each, select the sentences from the source that belong together
3. Return those sentences in the best order — most concrete claim first, filler cut
4. That is the paragraph. The writer's sentences. Nothing else.

WHAT YOU MAY DO:
- Reorder sentences within an experience (strongest claim first)
- Cut pure filler ("I am writing to apply for", "I look forward to hearing from you",
  "I hope to", generic sign-offs)
- Cut a sentence that adds nothing to the argument

WHAT YOU MAY NOT DO:
- Write any new sentence not present in the source
- Paraphrase or rephrase any sentence
- Add any word, phrase, or claim not in the source
- "Improve" the writing in any way — that is not your job
- Produce a paragraph for an experience when the source has no prose sentences about it.
  If an employer or project appears in a header or list but has no actual sentences,
  omit it entirely. Do NOT write placeholder text, refusal statements, or meta-commentary
  about missing content. Simply do not include that experience in the output array.

The strength rating reflects what is actually in the source:
- high: concrete claims with specifics, clear stakes, evidence
- medium: solid claims but missing key specifics
- low: present but needs Q&A to become argumentatively strong

Flag what Q&A would strengthen it — do not fill the gap yourself.
4. FLAG gaps as augmentation suggestions — specific, targeted questions about what
   would make the paragraph significantly stronger. These become Q&A prompts.

WRITING RULES (hard failures if violated):
- Open with a concrete, specific claim — not a generic topic statement like
  "I worked on X" or "My role involved Y"
- No em-dashes (—) anywhere — use commas, semicolons, or periods instead
- No banned words: "actually", "matters", "not just", "not only", "not simply"
- No injected evaluatives or superlatives: "strongest", "most meaningful", "most impactful",
  "deeply", "truly", "genuinely", "highly", "passionate" — use the writer's actual words
- No fake-contrast: "not X, but Y" or "not because X, but Y"
- No paragraph ending with a list
- No sentence starting with "That"
- 4–7 sentences per paragraph
- Every claim must trace to the source

GROUPING:
- Identify distinct experiences, projects, or accomplishments in the source
- Write one paragraph per experience/angle combination
- If a single experience has multiple strong angles, write multiple paragraphs
- Do not merge unrelated experiences into one paragraph

STRENGTH GUIDE:
- high: concrete claims with specifics (numbers, scale, ownership level), clear
  stakes, evidence of impact or decision-making
- medium: solid claims but missing key specifics or outcome evidence
- low: makes claims without grounding — needs significant strengthening via Q&A

AUGMENTATIONS — write 1–3 targeted questions per paragraph that would make the
argument significantly stronger. These questions will drive a Q&A session, so they
must be answerable from memory and generate a specific story or decision, not a
reflection or a hypothetical.

A good question names a gap — something the paragraph claims but doesn't prove —
and asks for the concrete moment that would prove it. The question should be
answerable by saying "yes, here's what happened" and then telling a story.

GOOD questions:
  - Ask what the person had to figure out that no one told them how to do
    ("When you built the consent pipeline at UNITE HERE, what data handling
    problem did you have to solve that wasn't in any spec or requirement?")
  - Ask about a real decision that had a real alternative
    ("When the Evergent fix came in broken, what did you do — escalate, work around
    it, or fix it yourself, and why?")
  - Ask what the person saw that others didn't
    ("What did you notice about the materialized views that the VP didn't —
    specifically what was wrong with the logic?")
  - Ask who else was in the room and what the dynamic was
    ("Who else was involved when you flagged the churn discrepancy, and what happened
    when you raised it?")

BAD questions (never write these):
  - Consequence hypotheticals: "What would have happened if X" or "What would have
    broken without it" — produces speculation, not stories
  - Superlative framing: "What was the most consequential / hardest / most complex X"
    — forces mental ranking before the person can answer; kills specificity
  - Binary forks: "Did you do A or B?" — answers itself, eliminates the story
  - Interrogating stated facts: asking "what specifically did you do" about something
    already described — produces restatement, not new material
  - Decontextualized jargon: quoting a phrase from the paragraph as the question premise
    without explaining what it means in context
  - "How many X did you build?" — inventory counts prove nothing about ownership
  - "What percentage improvement?" — false precision
  - "Can you add more detail?" — too vague
  - "What did you learn?" — produces generic answers
  - Any question the person could only answer by checking records they no longer have

The "role" field is the JOB TITLE this paragraph is relevant to — the actual role you would
apply for, e.g. "Senior Data Engineer", "Data Engineer", "Backend Engineer", "Solutions Engineer".
NOT a company name. NOT an experience category. NOT a department.
Use "General" for paragraphs that apply across all roles (motivational, through-line, voice, fit).
If a paragraph is relevant to multiple specific roles, pick the closest one or use "General".

The "section" field is the experience or project name, including company context
(e.g. "Acme Corp / Event Ingestion Pipeline", "Org / Voter Data Infrastructure").
The company name belongs in section, NOT in role.

Return ONLY a JSON array. No preamble, no commentary, no code fences:
[
  {
    "role": "Job title (e.g. Senior Data Engineer | Data Engineer | Backend Engineer | General)",
    "section": "Company / Experience or Project Name",
    "angle": "one of: production-ownership, system-design, business-impact, data-model,\ncross-functional, scope-opener, domain-expertise, reliability, leverage, through-line,\nownership, architecture, strategic-vision, financial-complexity",
    "strength": "high | medium | low",
    "via": "seed-notes if source is raw notes or bullets | seed-letter if source is existing written prose (cover letter, bio, resume)",
    "text": "The writer's own sentences from the source, selected and reordered. Quoted exactly. No new sentences. No paraphrasing.",
    "augmentations": [
      "Specific question that would surface a concrete missing detail",
      "Specific question about outcome, scale, or decision"
    ]
  }
]
"""


def _extract_json_array(text: str) -> str | None:
    """Extract the outermost JSON array from a response, handling preamble/fences."""
    start = text.find("[")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start: i + 1]
    return None


def extract_from_material(
    material: str,
    api_key: str,
    model: str,
) -> list[dict]:
    """Send raw career material to the LLM editor. Returns list of paragraph dicts."""
    from coverletter.provider import get_provider

    user_content = (
        f"SOURCE MATERIAL:\n\n{material.strip()}\n\n"
        f"---\n"
        f"Return paragraphs built from the sentences above. "
        f"Quote the writer's sentences exactly as written. "
        f"Do not write any new sentences. Do not paraphrase. "
        f"Every word in 'text' must appear verbatim in the source above."
    )
    raw = get_provider(model, api_key).complete(SEED_SYSTEM, user_content, max_tokens=4096, temperature=0.2)
    candidate = _extract_json_array(raw)
    if candidate is None:
        raise RuntimeError(
            f"No JSON array found in model response.\nRaw response:\n{raw}"
        )
    try:
        from coverletter.question_judge import check_patterns
        from coverletter.paragraph_judge import validate_and_fix_paragraph
        items = json.loads(candidate)
        result = []
        for item in items:
            raw_text = item.get("text", "").strip()
            if not raw_text:
                continue
            # Layer 2: LLM judge + fixer — produces refined text
            # Layer 1: raw_text is preserved separately and never overwritten
            fixed_text, para_warnings = validate_and_fix_paragraph(
                raw_text, material, api_key, model,
                check_writing_rules=False,
            )
            # Filter augmentation questions through the deterministic judge
            raw_augs = item.get("augmentations", [])
            clean_augs = [q for q in raw_augs if not check_patterns(q)]
            result.append({
                "role": item.get("role", "General"),
                "section": item.get("section", "Untitled"),
                "angle": item.get("angle", ""),
                "strength": item.get("strength", "medium"),
                "via": item.get("via", "seed-letter"),
                "text": raw_text,        # Layer 1 — verbatim extraction
                "text_fixed": fixed_text, # Layer 2 — LLM-validated/fixed
                "augmentations": clean_augs,
                "_warnings": para_warnings,
            })
        return result
    except Exception as e:
        raise RuntimeError(
            f"Could not parse extracted paragraphs.\nError: {e}\nCandidate:\n{candidate}"
        ) from e


def upsert_experience_targets(
    path: Path,
    name: str,
    company: str,
    angle: str,
    augmentations: list[str],
) -> None:
    """Write augmentation questions into experiences.md as qa_targets.

    If an entry for this experience exists: replace its qa_targets block.
    If not: append a new minimal entry with the questions.
    """
    if not augmentations:
        return

    targets_block = "qa_targets:\n" + "\n".join(f"- {q}" for q in augmentations)

    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = "# Experience Register\n"

    h2 = f"## {name}"

    if h2 in text:
        # Entry exists — replace or append qa_targets block
        lines = text.splitlines()
        out: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Find the right ## section
            if line.strip() == h2:
                out.append(line)
                i += 1
                # Copy until we hit another ## or end of file, stripping old qa_targets
                in_targets = False
                section_lines: list[str] = []
                while i < len(lines):
                    if lines[i].strip().startswith("## "):
                        break
                    if lines[i].strip().lower() == "qa_targets:":
                        in_targets = True
                        i += 1
                        continue
                    if in_targets:
                        if lines[i].strip().startswith("- ") or lines[i].strip() == "":
                            i += 1
                            continue
                        else:
                            in_targets = False
                    section_lines.append(lines[i])
                    i += 1
                # Write section content + new targets block
                out.extend(section_lines)
                out.append("")
                out.extend(targets_block.splitlines())
                out.append("")
            else:
                out.append(line)
                i += 1
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
    else:
        # No entry — append a new one
        angle_line = f"angles: {angle}" if angle else ""
        company_line = f"company: {company}" if company else ""
        new_entry_lines = [f"\n{h2}"]
        if company_line:
            new_entry_lines.append(company_line)
        if angle_line:
            new_entry_lines.append(angle_line)
        new_entry_lines.append("")
        new_entry_lines.extend(targets_block.splitlines())
        new_entry_lines.append("")
        path.write_text(text.rstrip() + "\n" + "\n".join(new_entry_lines) + "\n", encoding="utf-8")


def append_paragraphs_to_file(
    path: Path,
    paragraphs: list[dict],
) -> None:
    """Append accepted paragraphs to the library file under correct headers."""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = ""

    lines = [existing.rstrip(), ""]

    # Group by role so headers aren't repeated
    by_role: dict[str, list[dict]] = {}
    for p in paragraphs:
        by_role.setdefault(p["role"], []).append(p)

    for role, paras in by_role.items():
        h2 = f"## {role}"
        if h2 not in existing:
            lines.append(f"\n{h2}")

        for p in paras:
            h3 = f"### {p['section']}"
            meta_parts = []
            if p.get("strength"):
                meta_parts.append(f"strength={p['strength']}")
            if p.get("via"):
                meta_parts.append(f"via={p['via']}")
            if p.get("angle"):
                meta_parts.append(f"angle={p['angle']}")
            meta_line = f"<!-- meta: {', '.join(meta_parts)} -->\n" if meta_parts else ""
            text = p["text"].replace("\n", " ").strip()
            lines.append(f"\n{h3}\n")
            lines.append(meta_line + text)

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
