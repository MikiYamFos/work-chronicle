"""Side-by-side library diff tool.

Three sources of material:
  library.md          — your raw text, source of truth
  library_refined.md  — Claude-damaged, being corrected
  story_notes.md      — abandoned raw material, quotes and context

Output goes to library_salvaged.md — paragraphs you have reviewed and approved.

Run:
  uv run streamlit run coverletter/library_diff.py
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

import streamlit as st

st.set_page_config(page_title="Library Diff", page_icon="📝", layout="wide")

# ---------------------------------------------------------------------------
# Paragraph parsing — library files (<!-- meta: --> blocks)
# ---------------------------------------------------------------------------

class Para(NamedTuple):
    role: str
    section: str
    meta_raw: str
    text: str


def _parse_library(path: Path) -> list[Para]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    paras: list[Para] = []
    current_role = "General"
    current_section = "General"
    lines = content.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^## ", line):
            current_role = line.strip().lstrip("#").strip()
            i += 1
            continue
        if re.match(r"^### ", line):
            current_section = line.strip().lstrip("#").strip()
            i += 1
            continue
        if "<!-- meta:" in line:
            meta_raw = line.strip()
            body_lines: list[str] = []
            i += 1
            while i < len(lines):
                nl = lines[i]
                if "<!-- meta:" in nl or re.match(r"^## |^### ", nl):
                    break
                body_lines.append(nl)
                i += 1
            text = "".join(body_lines).strip()
            if text:
                paras.append(Para(current_role, current_section, meta_raw, text))
            continue
        i += 1
    return paras


# ---------------------------------------------------------------------------
# Story notes parsing — ## sections, no meta blocks
# ---------------------------------------------------------------------------

class Note(NamedTuple):
    heading: str
    text: str


def _parse_notes(path: Path) -> list[Note]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    notes: list[Note] = []
    current_heading = ""
    body_lines: list[str] = []
    for line in content.splitlines(keepends=True):
        if re.match(r"^## ", line):
            if current_heading and "".join(body_lines).strip():
                notes.append(Note(current_heading, "".join(body_lines).strip()))
            current_heading = line.strip().lstrip("#").strip()
            body_lines = []
        else:
            body_lines.append(line)
    if current_heading and "".join(body_lines).strip():
        notes.append(Note(current_heading, "".join(body_lines).strip()))
    return notes


_NOTES_STOP = {
    "that", "this", "with", "from", "have", "been", "they", "their", "what",
    "when", "where", "which", "work", "data", "also", "more", "some", "into",
    "would", "could", "were", "about", "there", "then", "than", "just", "very",
}


def _relevant_notes(para: Para, notes: list[Note]) -> list[Note]:
    """Return story_notes sections relevant to this paragraph.

    Uses a stop-word-filtered overlap with a proportional threshold so common
    words don't produce false matches. Requires at least 4 meaningful shared
    words OR >15% overlap relative to the shorter set.
    """
    def _words(text: str) -> set[str]:
        return {
            w for w in re.findall(r"[a-z]{4,}", text.lower())
            if w not in _NOTES_STOP
        }

    para_words = _words(para.role + " " + para.section + " " + para.text)
    scored = []
    for note in notes:
        note_words = _words(note.heading + " " + note.text)
        overlap = len(para_words & note_words)
        shorter = min(len(para_words), len(note_words))
        pct = overlap / shorter if shorter else 0
        if overlap >= 4 or pct >= 0.15:
            scored.append((overlap, note))
    scored.sort(key=lambda x: -x[0])
    return [n for _, n in scored[:2]]


# ---------------------------------------------------------------------------
# Output writer
# ---------------------------------------------------------------------------

def _write_library(path: Path, paras: list[Para]) -> None:
    lines: list[str] = []
    # Preserve the file's existing header block (everything before the first ##)
    # so the descriptive comment at the top of library_salvaged.md is kept.
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        header_lines = []
        for line in existing.splitlines(keepends=True):
            if re.match(r"^## ", line):
                break
            header_lines.append(line)
        header = "".join(header_lines).rstrip("\n") + "\n\n"
    else:
        header = f"# {path.stem}\n\n"
    lines.append(header)
    current_role = None
    current_section = None
    for para in paras:
        if para.role != current_role:
            current_role = para.role
            current_section = None
            lines.append(f"## {para.role}\n\n")
        if para.section != current_section:
            current_section = para.section
            lines.append(f"### {para.section}\n\n")
        lines.append(para.meta_raw + "\n")
        lines.append(para.text + "\n\n")
    path.write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------

project_root = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Sidebar — file config
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("📝 Library Diff")
    st.divider()

    st.subheader("Source files")
    raw_path = Path(st.text_input(
        "Raw (source of truth)",
        value=str(project_root / "library.md"),
    ))
    damaged_path = Path(st.text_input(
        "Damaged refined (Claude-corrupted)",
        value=str(project_root / "library_refined.md"),
    ))
    notes_path = Path(st.text_input(
        "Story notes (abandoned material)",
        value=str(project_root / "story_notes.md"),
    ))

    st.divider()
    st.subheader("Output file")
    output_path = Path(st.text_input(
        "Salvaged output",
        value=str(project_root / "library_salvaged.md"),
    ))
    st.caption("Approved paragraphs write here. Raw and damaged files are never modified.")

    st.divider()
    import os as _os
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv()
    _default_key = _os.getenv("ANTHROPIC_API_KEY", "")
    coach_api_key = st.text_input(
        "Anthropic API key (for coaching)",
        type="password",
        value=st.session_state.get("diff_api_key", _default_key),
    )
    if coach_api_key:
        st.session_state["diff_api_key"] = coach_api_key
    coach_model = st.selectbox(
        "Coach model",
        ["claude-haiku-4-5-20251001", "claude-sonnet-4-5-20251022"],
        index=0,
        help="Haiku is cheaper. Sonnet gives sharper suggestions.",
    )

    st.divider()
    if st.button("💾 Save to output file", type="primary"):
        if "salvaged_paras" in st.session_state and st.session_state.salvaged_paras:
            _write_library(output_path, st.session_state.salvaged_paras)
            st.success(f"Saved {len(st.session_state.salvaged_paras)} paragraph(s) to {output_path.name}")
        else:
            st.warning("Nothing approved yet.")

# ---------------------------------------------------------------------------
# Load files
# ---------------------------------------------------------------------------

cache_key = f"{raw_path}|{damaged_path}|{notes_path}|{output_path}"
if st.session_state.get("_cache_key") != cache_key:
    # Warn if there are unsaved approved paragraphs before switching files
    unsaved = st.session_state.get("salvaged_paras", [])
    if unsaved and st.session_state.get("_cache_key"):
        st.warning(
            f"⚠️ You have {len(unsaved)} approved paragraph(s) not yet saved. "
            f"**Save to output file before switching files** or they will be lost."
        )
        if not st.button("I understand — switch anyway"):
            st.stop()

    st.session_state._cache_key = cache_key
    st.session_state.raw_paras = _parse_library(raw_path)
    st.session_state.damaged_paras = _parse_library(damaged_path)
    st.session_state.notes = _parse_notes(notes_path)
    st.session_state.cursor = 0
    st.session_state.salvaged_paras = []
    # Load previously saved progress
    progress_path = output_path.with_suffix(".progress.txt")
    if progress_path.exists():
        st.session_state.reviewed = set(
            int(x) for x in progress_path.read_text().split() if x.strip().isdigit()
        )
    else:
        st.session_state.reviewed = set()

raw_paras: list[Para] = st.session_state.raw_paras
damaged_paras: list[Para] = st.session_state.damaged_paras
notes: list[Note] = st.session_state.notes

if not raw_paras and not damaged_paras:
    st.error("No paragraphs found. Check file paths in sidebar.")
    st.stop()

# Build damaged lookup by (role, section)
damaged_lookup: dict[tuple[str, str], list[Para]] = {}
for p in damaged_paras:
    key = (p.role.lower().strip(), p.section.lower().strip())
    damaged_lookup.setdefault(key, []).append(p)

# Work from raw paragraphs as the canonical list
all_paras = raw_paras if raw_paras else damaged_paras
total = len(all_paras)
reviewed: set[int] = st.session_state.reviewed
pending_indices = [i for i in range(total) if i not in reviewed]

# Sidebar continued — progress + navigation
with st.sidebar:
    st.divider()
    st.progress(len(reviewed) / total if total else 0)
    st.markdown(f"**{len(reviewed)} / {total}** reviewed")
    st.caption(f"{len(pending_indices)} remaining")
    st.divider()

    filter_mode = st.radio("Show", ["Unreviewed only", "All"], index=0)
    if st.button("⏭ Next unreviewed"):
        if pending_indices:
            st.session_state.cursor = 0
            st.rerun()

    section_labels = [f"{p.role} / {p.section}" for p in all_paras]
    jump = st.selectbox("Jump to", range(total), format_func=lambda i: section_labels[i])
    if st.button("Go"):
        display = pending_indices if filter_mode == "Unreviewed only" else list(range(total))
        if jump in display:
            st.session_state.cursor = display.index(jump)
        st.rerun()

    st.divider()
    saved_count = len(st.session_state.get("salvaged_paras", []))
    st.caption(f"{saved_count} paragraph(s) approved and queued for output.")

# ---------------------------------------------------------------------------
# Display list
# ---------------------------------------------------------------------------

display_indices = pending_indices if filter_mode == "Unreviewed only" else list(range(total))

if not display_indices:
    st.success("All paragraphs reviewed.")
    if st.button("💾 Save library_salvaged.md"):
        _write_library(output_path, st.session_state.salvaged_paras)
        st.success("Saved.")
    st.stop()

cursor = st.session_state.get("cursor", 0)
if cursor >= len(display_indices):
    cursor = 0
    st.session_state.cursor = 0

flat_idx = display_indices[cursor]
para = all_paras[flat_idx]

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

n1, n2, n3 = st.columns([1, 4, 1])
with n1:
    if st.button("← Prev") and cursor > 0:
        st.session_state.cursor -= 1
        st.rerun()
with n2:
    marker = "✓" if flat_idx in reviewed else "○"
    st.markdown(
        f"<center><b>{marker} {cursor + 1} / {len(display_indices)} &nbsp; "
        f"{para.role} / {para.section}</b></center>",
        unsafe_allow_html=True,
    )
with n3:
    if st.button("Next →") and cursor < len(display_indices) - 1:
        st.session_state.cursor += 1
        st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Three-source display
# ---------------------------------------------------------------------------

key = (para.role.lower().strip(), para.section.lower().strip())
damaged_matches = damaged_lookup.get(key, [])
relevant_notes = _relevant_notes(para, notes)

col_raw, col_damaged, col_notes = st.columns(3)

with col_raw:
    st.subheader("📄 Raw — library.md")
    st.caption("Your words. Source of truth.")
    st.text_area(
        "raw",
        value=para.text,
        height=280,
        key=f"raw_{flat_idx}",
        disabled=True,
        label_visibility="collapsed",
    )

with col_damaged:
    st.subheader("⚠️ Damaged — library_refined.md")
    st.caption("Claude-corrupted. Reference only.")
    if damaged_matches:
        for di, dp in enumerate(damaged_matches):
            st.text_area(
                f"damaged_{di}",
                value=dp.text,
                height=280,
                key=f"dam_{flat_idx}_{di}",
                disabled=True,
                label_visibility="collapsed",
            )
    else:
        st.info("No matching section in library_refined.md.")

with col_notes:
    st.subheader("📓 Story notes")
    st.caption("Abandoned material that may be relevant.")
    if relevant_notes:
        for ni, note in enumerate(relevant_notes):
            with st.expander(note.heading, expanded=(ni == 0)):
                st.markdown(note.text)
    else:
        st.info("No relevant story notes found for this section.")

# ---------------------------------------------------------------------------
# Edit area — what goes to library_salvaged.md
# ---------------------------------------------------------------------------

st.divider()
st.subheader("✏️ Your version — goes to library_salvaged.md")
st.caption("Edit here. Use raw as base, pull from damaged or notes what's worth keeping.")

edited = st.text_area(
    "edit",
    value=para.text,
    height=220,
    key=f"edit_{flat_idx}",
    label_visibility="collapsed",
)
st.caption(f"Meta: `{para.meta_raw}`")

# ---------------------------------------------------------------------------
# Coaching buttons — manual trigger, not automatic
# ---------------------------------------------------------------------------

st.divider()
c1, c2 = st.columns(2)
api_key = st.session_state.get("diff_api_key", "")
model = st.session_state.get("coach_model_sel", "claude-haiku-4-5-20251001")

with c1:
    st.markdown("#### Did the damaged version lose your words?")
    st.markdown(
        "Compares the **damaged column** against your **raw text**. "
        "Finds where Claude swapped your words for worse ones, added sentences you never wrote, "
        "or dropped things you said. Run this before editing if you want to know what got corrupted."
    )
    if not api_key:
        st.warning("Add Anthropic API key in sidebar to enable coaching.")
    if st.button("🔍 Check what the draft got wrong", width="stretch", disabled=not api_key):
        damaged_text = damaged_matches[0].text if damaged_matches else edited
        with st.spinner("Comparing draft against your raw text..."):
            from coverletter.coach import analyze_draft
            issues = analyze_draft(para.text, damaged_text, api_key, model)
        if not issues:
            st.success("Draft stayed faithful to your source text.")
        else:
            type_labels = {
                "word_swap": "🔄 Word swap — your language got replaced",
                "invented": "⚠️ Invented — Claude added this, you never said it",
                "meaning_shift": "↔️ Meaning shifted — reorganized into a different point",
                "coverage_gap": "📭 Missing — this was in your raw text but not the draft",
            }
            for issue in issues:
                label = type_labels.get(issue.type, issue.type)
                with st.expander(f"{label}"):
                    if issue.draft_sentence:
                        st.markdown(f"**What the draft says:** {issue.draft_sentence}")
                    if issue.raw_reference:
                        st.markdown(f"**What you said:** {issue.raw_reference}")
                    st.markdown(f"**Problem:** {issue.issue}")
                    if issue.suggestion:
                        st.info(f"**One way to fix it** (your call): {issue.suggestion}")

with c2:
    # Parse via and angle from meta_raw for perspective detection
    _via = re.search(r"via=(\S+?)[\s,>]", para.meta_raw + " ")
    _angle = re.search(r"angle=(\S+?)[\s,>]", para.meta_raw + " ")
    via_val = _via.group(1) if _via else ""
    angle_val = _angle.group(1) if _angle else ""

    st.markdown("#### Is your edited version ready to save?")
    st.markdown(
        "Checks **your edit** (the text area below) for specific problems before it goes into the library: "
        "a weak opener that doesn't do any work, AI writing constructs that lose precision, "
        "or a main claim sentence written in passive voice. "
        "Run this after you've edited, before you save."
    )
    if not api_key:
        st.warning("Add Anthropic API key in sidebar to enable coaching.")
    if st.button("🔍 Check my edited version", width="stretch", disabled=not api_key):
        with st.spinner("Checking your paragraph..."):
            from coverletter.coach import analyze_library_paragraph
            issues = analyze_library_paragraph(edited, api_key, model, via=via_val, angle=angle_val)
        if not issues:
            st.success("No issues found — looks good to save.")
        else:
            type_labels = {
                "opener": "🚪 Opener doesn't do enough work",
                "banned_construct": "🚫 AI writing construct — loses precision",
                "passive_claim": "😶 Main claim is passive — hides who did it",
            }
            for issue in issues:
                label = type_labels.get(issue.type, issue.type)
                with st.expander(f"{label}"):
                    st.markdown(f"**Sentence:** {issue.sentence}")
                    st.markdown(f"**Problem:** {issue.issue}")
                    if issue.suggestion:
                        st.info(f"**One way to fix it** (your call): {issue.suggestion}")

# ---------------------------------------------------------------------------
# Action buttons
# ---------------------------------------------------------------------------

st.divider()
b1, b2, b3, b4, b5 = st.columns(5)

def _save_progress() -> None:
    progress_path = output_path.with_suffix(".progress.txt")
    progress_path.write_text("\n".join(str(i) for i in sorted(st.session_state.reviewed)))

def _approve(text: str) -> None:
    approved = Para(para.role, para.section, para.meta_raw, text)
    # Replace if already approved this session
    existing = [i for i, p in enumerate(st.session_state.salvaged_paras)
                if p.role == para.role and p.section == para.section and p.meta_raw == para.meta_raw]
    if existing:
        st.session_state.salvaged_paras[existing[0]] = approved
    else:
        st.session_state.salvaged_paras.append(approved)
    st.session_state.reviewed.add(flat_idx)
    _save_progress()
    if cursor < len(display_indices) - 1:
        st.session_state.cursor += 1

with b1:
    if st.button("✅ Use raw & next", width="stretch"):
        _approve(para.text)
        st.rerun()

with b2:
    if damaged_matches and st.button("⬅️ Use damaged & next", width="stretch"):
        _approve(damaged_matches[0].text)
        st.rerun()

with b3:
    if st.button("💾 Save edit & next", width="stretch"):
        _approve(edited)
        st.rerun()

with b4:
    if st.button("⏭ Skip", width="stretch"):
        if cursor < len(display_indices) - 1:
            st.session_state.cursor += 1
        st.rerun()

with b5:
    if st.button("🗑️ Exclude", width="stretch",
                  help="Mark as reviewed without saving to output — paragraph won't appear in library_salvaged.md"):
        st.session_state.reviewed.add(flat_idx)
        _save_progress()
        if cursor < len(display_indices) - 1:
            st.session_state.cursor += 1
        st.rerun()

# ---------------------------------------------------------------------------
# Paragraphs in damaged not matched in raw
# ---------------------------------------------------------------------------

with st.expander("📋 Paragraphs in library_refined.md with no match in library.md"):
    raw_keys = {(p.role.lower().strip(), p.section.lower().strip()) for p in raw_paras}
    unmatched = [p for p in damaged_paras
                 if (p.role.lower().strip(), p.section.lower().strip()) not in raw_keys]
    if unmatched:
        for up in unmatched:
            st.markdown(f"**{up.role} / {up.section}**")
            st.text(up.text[:200] + ("..." if len(up.text) > 200 else ""))
            if st.button(f"Add to output ↑", key=f"add_{up.role}_{up.section}_{up.meta_raw[:20]}"):
                st.session_state.salvaged_paras.append(up)
                st.rerun()
    else:
        st.caption("All sections in library_refined.md have a match in library.md.")
