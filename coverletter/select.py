"""Stage 1 paragraph selector — commits to source material before generation begins.

Receives the prefiltered library plus any gap-pinned paragraphs, the argument target,
and the JD. Returns a ranked list of (paragraph, reason) pairs.

Gap-pinned paragraphs (written during a gap loop for this specific JD) are never cut —
they are passed to the selector with a [PINNED — written for this JD's gap] marker so
the selector knows to include them. The selector's job is to fill the remaining slots.
"""
from __future__ import annotations

import json
import re

from coverletter.parser import Paragraph
from coverletter.provider import get_provider

_SELECTOR_SYSTEM = """\
You are a paragraph selector for a cover letter assembly system.

Given an argument target, job description, and a set of candidate paragraphs, choose
the 4-6 paragraphs that together best support making that argument to this employer.

Selection rules:
- Paragraphs marked [PINNED] MUST be included — they were written specifically for this job
- Include opener/closer paragraphs if present (tone=opener or tone=closer) — always needed
- Choose 2-4 additional body paragraphs that directly address the argument and JD requirements
- Prefer paragraphs tagged strength=high
- Do not select two paragraphs from the same section unless they argue very different things
- The selected set should cover distinct facets — no redundancy

Return ONLY valid JSON in this exact format, nothing else:
{"selected": [{"id": <integer>, "reason": "<one sentence why this paragraph serves the argument>"}]}
"""


def select_paragraphs(
    paragraphs: list[Paragraph],
    argument: str | None,
    job_description: str,
    api_key: str,
    pinned_ids: set[object] | None = None,
    model: str = "claude-haiku-4-5-20251001",
) -> list[tuple[Paragraph, str]]:
    """Stage 1: call Haiku to select 4-6 paragraphs from the prefiltered library.

    pinned_ids: set of paragraph db_ids (or index ints) that must not be cut.
    These come from paragraph_gap_provenance for this JD — gap-written paragraphs
    that scored low on JD vocabulary but are exactly what the letter needs.

    Returns list of (paragraph, reason) pairs in selection order.
    Falls back to returning all paragraphs (empty reasons) if the call fails.
    """
    pinned_ids = pinned_ids or set()

    lines: list[str] = []
    if argument:
        lines.append(f"=== ARGUMENT TARGET ===\n{argument}\n")
    lines.append(f"=== JD REQUIREMENTS (first 400 chars) ===\n{job_description[:400]}\n")
    lines.append("=== AVAILABLE PARAGRAPHS ===\n")

    for p in paragraphs:
        pid = p.db_id if p.db_id is not None else p.index
        is_pinned = pid in pinned_ids or str(pid) in {str(x) for x in pinned_ids}
        meta_parts: list[str] = []
        for key in ("angle", "strength", "tone"):
            if p.meta.get(key):
                meta_parts.append(f"{key}={p.meta[key]}")
        if is_pinned:
            meta_parts.insert(0, "PINNED — written for this JD's gap")
        meta_str = f" [{', '.join(meta_parts)}]" if meta_parts else ""
        role_label = f"{p.role} / " if p.role else ""
        lines.append(f"[{pid}] {role_label}{p.section}{meta_str}")
        lines.append(p.text[:150] + ("..." if len(p.text) > 150 else ""))
        lines.append("")

    lines.append(
        'Select 4-6 paragraphs. All PINNED paragraphs must be included. Return JSON only:\n'
        '{"selected": [{"id": N, "reason": "one sentence"}]}'
    )

    user_content = "\n".join(lines)

    try:
        provider = get_provider(model, api_key)
        raw = provider.complete(_SELECTOR_SYSTEM, user_content, max_tokens=600)

        raw = raw.strip()
        m = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
        if m:
            raw = m.group(1).strip()

        data = json.loads(raw)
        entries: list[dict] = data.get("selected", [])

        id_map: dict[object, Paragraph] = {}
        for p in paragraphs:
            pid = p.db_id if p.db_id is not None else p.index
            id_map[pid] = p
            id_map[str(pid)] = p

        result: list[tuple[Paragraph, str]] = []
        seen: set[int] = set()
        for entry in entries:
            pid = entry.get("id")
            reason = entry.get("reason", "")
            para = id_map.get(pid) or id_map.get(str(pid) if pid is not None else "")
            if para is not None and id(para) not in seen:
                result.append((para, reason))
                seen.add(id(para))

        # Enforce: any pinned paragraph not returned by the selector gets appended.
        # The selector was told to include them but may have missed one.
        selected_pids = {p.db_id if p.db_id is not None else p.index for p, _ in result}
        for p in paragraphs:
            pid = p.db_id if p.db_id is not None else p.index
            if pid in pinned_ids and pid not in selected_pids and id(p) not in seen:
                result.append((p, "pinned — written for this JD's gap"))
                seen.add(id(p))

        if result:
            return result
    except Exception:
        pass

    return [(p, "") for p in paragraphs]
