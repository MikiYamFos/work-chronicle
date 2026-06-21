"""Paragraph browser — browse, inspect, and edit all library paragraphs.

Shows all paragraphs across all library files. For each paragraph:
  - Full text (editable)
  - Raw Q&A session that produced it (from DB)
  - Which file it lives in and its meta tags
  - Save edits to library_approved.md (Layer 3 — highest priority)

Run:
  uv run streamlit run coverletter/library_browser.py
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from typing import NamedTuple

import streamlit as st

st.set_page_config(page_title="Paragraph Browser", page_icon="📚", layout="wide")

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

class Para(NamedTuple):
    role: str
    section: str
    meta_raw: str
    text: str
    source_file: str  # which library file this came from
    text_hash: str


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_library(path: Path, label: str) -> list[Para]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    paras: list[Para] = []
    current_role = "General"
    current_section = "General"
    meta_raw = ""
    lines = content.splitlines(keepends=True)
    i = 0
    in_block_comment = False
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal meta_raw, current_lines
        text = "".join(current_lines).strip()
        if text and not text.startswith("#") and not re.match(r"^\[.+\]$", text, re.DOTALL):
            paras.append(Para(current_role, current_section, meta_raw, text, label, _hash(text)))
        meta_raw = ""
        current_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("<!--") and "-->" not in stripped:
            in_block_comment = True
            flush()
            i += 1
            continue
        if in_block_comment:
            if stripped == "-->":
                in_block_comment = False
            i += 1
            continue
        if re.match(r"^## ", line):
            flush()
            current_role = line.strip().lstrip("#").strip()
            current_section = current_role
            i += 1
            continue
        if re.match(r"^### ", line):
            flush()
            current_section = line.strip().lstrip("#").strip()
            i += 1
            continue
        if re.match(r"^#\s", line):
            i += 1
            continue
        if re.match(r"<!--\s*meta:", stripped, re.IGNORECASE):
            flush()
            meta_raw = stripped
            i += 1
            continue
        if not stripped:
            flush()
            i += 1
            continue
        current_lines.append(line)
        i += 1
    flush()
    return paras


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_raw_qa(db_path: Path, text_hash: str, section: str) -> tuple[str, str] | None:
    """Return (session_topic, responses_md) or None."""
    if not db_path.exists():
        return None
    try:
        con = sqlite3.connect(db_path)
        row = con.execute(
            "SELECT session_topic, responses_md FROM raw_responses WHERE para_text_hash = ? LIMIT 1",
            (text_hash,)
        ).fetchone()
        if not row:
            row = con.execute(
                "SELECT session_topic, responses_md FROM raw_responses WHERE session_topic LIKE ? LIMIT 1",
                (f"%{section[:20]}%",)
            ).fetchone()
        con.close()
        return row
    except Exception:
        return None


def _append_approved(path: Path, role: str, section: str, text: str, meta_raw: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    meta_line = f"{meta_raw}\n" if meta_raw else ""
    text = text.strip()
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = "# Approved Library Paragraphs\n"
        path.write_text(existing, encoding="utf-8")

    h2 = f"## {role}"
    h3 = f"### {section}"
    if h2 in existing and h3 in existing:
        entry = f"\n{meta_line}{text}\n"
    elif h2 in existing:
        entry = f"\n{h3}\n\n{meta_line}{text}\n"
    else:
        entry = f"\n{h2}\n\n{h3}\n\n{meta_line}{text}\n"

    with path.open("a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------

project_root = Path(__file__).parent.parent
if not (project_root / "library.md").exists():
    # Try cwd
    project_root = Path.cwd()

# ---------------------------------------------------------------------------
# Sidebar — config
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("📚 Paragraph Browser")
    st.divider()

    raw_path = Path(st.text_input("Raw (library.md)", value=str(project_root / "library.md")))
    refined_path = Path(st.text_input("Refined (library_refined.md)", value=str(project_root / "library_refined.md")))
    approved_path = Path(st.text_input("Approved (library_approved.md)", value=str(project_root / "library_approved.md")))
    db_path = Path(st.text_input("DB (library.db)", value=str(project_root / "library.db")))

    st.divider()
    show_raw = st.checkbox("Show raw (library.md)", value=True)
    show_refined = st.checkbox("Show refined (library_refined.md)", value=True)
    show_approved = st.checkbox("Show approved (library_approved.md)", value=True)

# ---------------------------------------------------------------------------
# Load all paragraphs
# ---------------------------------------------------------------------------

@st.cache_data
def _load_all(r: str, ref: str, app: str) -> list[Para]:
    paras = []
    paras.extend(_parse_library(Path(r), "library.md"))
    paras.extend(_parse_library(Path(ref), "library_refined.md"))
    paras.extend(_parse_library(Path(app), "library_approved.md"))
    return paras

cache_key = f"{raw_path}|{refined_path}|{approved_path}"
if st.session_state.get("_cache_key") != cache_key:
    st.cache_data.clear()
    st.session_state["_cache_key"] = cache_key

all_paras = _load_all(str(raw_path), str(refined_path), str(approved_path))

# Filter by visible sources
visible_sources: set[str] = set()
if show_raw: visible_sources.add("library.md")
if show_refined: visible_sources.add("library_refined.md")
if show_approved: visible_sources.add("library_approved.md")

display_paras = [p for p in all_paras if p.source_file in visible_sources]

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

all_roles = ["(all)"] + sorted({p.role for p in display_paras})
all_sections = ["(all)"] + sorted({p.section for p in display_paras})

col_f1, col_f2, col_f3 = st.columns([2, 2, 3])
with col_f1:
    role_filter = st.selectbox("Role", all_roles)
with col_f2:
    section_filter = st.selectbox("Section", all_sections)
with col_f3:
    search = st.text_input("Search text", placeholder="keyword or phrase")

filtered = display_paras
if role_filter != "(all)":
    filtered = [p for p in filtered if p.role == role_filter]
if section_filter != "(all)":
    filtered = [p for p in filtered if p.section == section_filter]
if search:
    q = search.lower()
    filtered = [p for p in filtered if q in p.text.lower() or q in p.section.lower() or q in p.role.lower()]

if not filtered:
    st.warning("No paragraphs match the current filters.")
    st.stop()

# ---------------------------------------------------------------------------
# Paragraph list — left panel + detail right
# ---------------------------------------------------------------------------

st.markdown(f"**{len(filtered)} paragraph(s)** — click one to inspect and edit")
st.divider()

if "selected_idx" not in st.session_state:
    st.session_state["selected_idx"] = 0

# Clamp cursor
if st.session_state["selected_idx"] >= len(filtered):
    st.session_state["selected_idx"] = 0

list_col, detail_col = st.columns([1, 2])

with list_col:
    st.subheader("All paragraphs")
    for i, p in enumerate(filtered):
        source_badge = {"library.md": "🟡", "library_refined.md": "🟠", "library_approved.md": "🟢"}.get(p.source_file, "⚪")
        label = f"{source_badge} {p.role} / {p.section}"
        preview = p.text[:60].replace("\n", " ") + ("…" if len(p.text) > 60 else "")
        is_selected = st.session_state["selected_idx"] == i
        if st.button(
            f"{label}\n_{preview}_",
            key=f"para_btn_{i}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            st.session_state["selected_idx"] = i
            st.rerun()

with detail_col:
    para = filtered[st.session_state["selected_idx"]]
    st.subheader(f"{para.role} / {para.section}")
    st.caption(f"Source: `{para.source_file}`  |  Meta: `{para.meta_raw or 'none'}`")

    # Editable text
    edited = st.text_area(
        "Text (edit here)",
        value=para.text,
        height=280,
        key=f"edit_{st.session_state['selected_idx']}",
    )

    save_col, _, nav_col = st.columns([2, 1, 2])
    with save_col:
        if st.button("💾 Save to library_approved.md", use_container_width=True, type="primary"):
            _append_approved(approved_path, para.role, para.section, edited, para.meta_raw)
            st.success(f"Saved → {approved_path.name} under {para.role} / {para.section}")
            st.cache_data.clear()

    with nav_col:
        n1, n2 = st.columns(2)
        with n1:
            if st.button("← Prev", use_container_width=True) and st.session_state["selected_idx"] > 0:
                st.session_state["selected_idx"] -= 1
                st.rerun()
        with n2:
            if st.button("Next →", use_container_width=True) and st.session_state["selected_idx"] < len(filtered) - 1:
                st.session_state["selected_idx"] += 1
                st.rerun()

    # Raw Q&A
    with st.expander("💬 Raw Q&A — your exact words before this was drafted", expanded=False):
        qa = _get_raw_qa(db_path, para.text_hash, para.section)
        if qa:
            st.caption(f"Session: {qa[0]}")
            st.markdown(qa[1])
        else:
            st.info("No raw Q&A found. (Only build sessions save Q&A — seed paragraphs don't have it.)")

    # Source file snippet
    with st.expander("📄 Full source text (read-only)", expanded=False):
        st.text(para.text)

# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
st.divider()
st.caption("🟡 library.md (raw)  🟠 library_refined.md (coach draft)  🟢 library_approved.md (approved)")
st.caption("Saving writes to library_approved.md only. Raw and refined files are never modified.")
