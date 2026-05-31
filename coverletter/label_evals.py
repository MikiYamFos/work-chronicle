"""Streamlit labeling app for reviewing extracted claims.

Run:
  uv run streamlit run coverletter/label_evals.py

Workflow:
  1. coverletter extract --dry-run  →  generates extractions_review.json
  2. uv run streamlit run coverletter/label_evals.py
  3. Approve / reject claims — approved claims insert directly into DB
  4. Edit source paragraph text inline if the extracted claims are wrong
  5. At end of session, re-extract edited paragraphs in one batch — new claims
     go into a judge queue you can action now or come back to later
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Claim Review", page_icon="🔍", layout="wide")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_review(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_review(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _all_claims(data: dict) -> list[tuple[int, int, dict, dict]]:
    result = []
    for pi, para in enumerate(data.get("paragraphs", [])):
        for ci, claim in enumerate(para.get("claims", [])):
            result.append((pi, ci, claim, para))
    return result


def _pending_indices(all_claims: list) -> list[int]:
    return [i for i, (_, _, c, _) in enumerate(all_claims) if c.get("status") == "pending"]


def _counts(all_claims: list) -> dict[str, int]:
    counts: dict[str, int] = {"pending": 0, "approved": 0, "rejected": 0}
    for _, _, c, _ in all_claims:
        counts[c.get("status", "pending")] += 1
    return counts


_GS_PATH = Path(__file__).parent / "evals" / "gold_standard_claims.json"

try:
    from coverletter.extract import _GS_MIN_APPROVED, _GS_MIN_REJECTED
except ImportError:
    _GS_MIN_APPROVED = 5
    _GS_MIN_REJECTED = 5


def _load_gold_standard() -> dict:
    if _GS_PATH.exists():
        return json.loads(_GS_PATH.read_text(encoding="utf-8"))
    return {"description": "Gold standard claim examples for judge alignment.", "version": "1", "examples": []}


def _save_gold_standard(gs: dict) -> None:
    _GS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _GS_PATH.write_text(json.dumps(gs, indent=2), encoding="utf-8")


def _add_to_gold_standard(claim_text: str, label: str, note: str, failure_categories: list[str]) -> None:
    gs = _load_gold_standard()
    existing_texts = {ex["claim_text"] for ex in gs.get("examples", [])}
    if claim_text in existing_texts:
        return
    new_id = f"gs_{len(gs.get('examples', [])) + 1:03d}"
    gs.setdefault("examples", []).append({
        "id": new_id,
        "label": label,
        "claim_text": claim_text,
        "contexts": [],
        "source_note": note,
        "failure_categories": failure_categories if label == "rejected" else [],
    })
    _save_gold_standard(gs)


def _gs_status() -> tuple[int, int]:
    if not _GS_PATH.exists():
        return 0, 0
    gs = json.loads(_GS_PATH.read_text(encoding="utf-8"))
    approved = sum(1 for e in gs.get("examples", []) if e["label"] == "approved")
    rejected = sum(1 for e in gs.get("examples", []) if e["label"] == "rejected")
    return approved, rejected


def _insert_claim_to_db(db_path: Path, para_hash: str, claim: dict, conclusion: str | None) -> bool:
    try:
        from coverletter.extract import insert_from_review
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        review_data = {
            "paragraphs": [{
                "para_hash": para_hash,
                "claims": [claim],
                "conclusion": conclusion,
            }]
        }
        voyage_key = st.session_state.get("voyage_api_key", "")
        n, _ = insert_from_review(conn, review_data, voyage_api_key=voyage_key)
        conn.close()
        return n > 0
    except Exception as e:
        st.error(f"DB insert failed: {e}")
        return False


def _reextract_paragraph(para_text: str, api_key: str) -> tuple[list[dict], dict[int, tuple[bool, str]]]:
    """Re-extract and judge claims from edited paragraph text. Returns (claims, judge_results)."""
    from coverletter.extract import (
        _extract_from_paragraph, _judge_claims_concurrent, _EXTRACT_MODEL,
    )
    data = _extract_from_paragraph(para_text, None, api_key, _EXTRACT_MODEL)
    claims = data.get("claims", [])
    judge_results = _judge_claims_concurrent(claims, para_text, api_key, max_workers=4)
    return claims, judge_results


# ---------------------------------------------------------------------------
# Sidebar — files + config
# ---------------------------------------------------------------------------

st.title("🔍 Claim Extraction Review")

with st.sidebar:
    st.header("Files")

    default_path = ""
    search_dirs = [Path.cwd(), Path.cwd().parent] + list(Path.cwd().parents)[:2]
    for d in search_dirs:
        candidate = d / "extractions_review.json"
        if candidate.exists():
            default_path = str(candidate)
            break

    file_path_str = st.text_input("extractions_review.json", value=default_path)
    file_path = Path(file_path_str) if file_path_str else None

    if not file_path or not file_path.exists():
        st.warning("No review file found.\n\nRun:\n```\ncoverletter extract --dry-run\n```")
        st.stop()

    default_db = ""
    if file_path:
        candidate_db = file_path.parent / "library.db"
        if candidate_db.exists():
            default_db = str(candidate_db)

    db_path_str = st.text_input("library.db (for direct insertion)", value=default_db)
    db_path_val = Path(db_path_str) if db_path_str else None
    db_available = db_path_val and db_path_val.exists()

    if db_available:
        st.success("DB connected — approvals insert directly")
    else:
        st.caption("DB not found — approvals save to JSON only")

    voyage_key = st.text_input(
        "Voyage API key (embeddings, optional)", type="password",
        value=st.session_state.get("voyage_api_key", ""),
    )
    if voyage_key:
        st.session_state["voyage_api_key"] = voyage_key

    # API key for re-extraction — load from .env automatically
    default_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_key = st.text_input(
        "Anthropic API key (for re-extraction)", type="password",
        value=st.session_state.get("anthropic_api_key", default_api_key),
    )
    if anthropic_key:
        st.session_state["anthropic_api_key"] = anthropic_key

    # Load review file — restore cursor position if saved
    if "data" not in st.session_state or st.session_state.get("loaded_path") != str(file_path):
        loaded = load_review(file_path)
        st.session_state.data = loaded
        st.session_state.loaded_path = str(file_path)
        # Restore saved cursor position — jump to first pending at or after it
        saved_cursor = loaded.get("_session_cursor", 0)
        st.session_state.cursor = saved_cursor
        # Track which paragraphs have been edited this session
        st.session_state.edited_para_indices = set()

    data = st.session_state.data
    all_claims = _all_claims(data)
    counts = _counts(all_claims)
    total = len(all_claims)
    done = counts["approved"] + counts["rejected"]

    st.divider()
    st.progress(done / total if total else 0)
    st.markdown(
        f"**{done} / {total}** labeled  \n"
        f"✅ {counts['approved']} approved  "
        f"❌ {counts['rejected']} rejected  "
        f"⏳ {counts['pending']} pending"
    )

    if data.get("judge_accuracy"):
        st.caption(f"Judge alignment: {data['judge_accuracy']}")

    # Gold standard status
    st.divider()
    gs_approved, gs_rejected = _gs_status()
    gs_total = gs_approved + gs_rejected
    needs_approved = max(0, _GS_MIN_APPROVED - gs_approved)
    needs_rejected = max(0, _GS_MIN_REJECTED - gs_rejected)
    st.caption(
        "The judge is validated against these before each extraction run. "
        "Only add clear, unambiguous examples. "
        f"Need ≥{_GS_MIN_APPROVED} approved + ≥{_GS_MIN_REJECTED} rejected to enable validation."
    )
    if gs_total == 0:
        st.warning(f"No examples yet. Add clear approved and rejected cases as you label.")
    elif needs_approved > 0 or needs_rejected > 0:
        parts = []
        if needs_approved:
            parts.append(f"{needs_approved} more approved")
        if needs_rejected:
            parts.append(f"{needs_rejected} more rejected")
        st.info(f"{gs_approved} ✅ {gs_rejected} ❌ — need {', '.join(parts)}")
    else:
        st.success(f"Validation active: {gs_approved} ✅ {gs_rejected} ❌")

    st.divider()
    st.header("Navigate")
    filter_mode = st.radio("Show", ["Pending only", "All"], index=0)

    # Jump to paragraph selector
    para_labels = [
        f"{p['role']} / {p['section'][:35]}"
        for p in data.get("paragraphs", [])
    ]
    if para_labels:
        jump_para = st.selectbox("Jump to paragraph", options=range(len(para_labels)),
                                  format_func=lambda i: para_labels[i])
        if st.button("Go"):
            # Find first claim in that paragraph
            for flat_i, (pi, ci, c, _) in enumerate(all_claims):
                if pi == jump_para:
                    st.session_state.cursor = flat_i
                    st.rerun()

    if st.button("⏭ Next pending"):
        pending = _pending_indices(all_claims)
        if pending:
            st.session_state.cursor = pending[0]
            st.rerun()

    # Edited paragraphs summary
    edited = st.session_state.get("edited_para_indices", set())
    if edited:
        st.divider()
        st.warning(f"**{len(edited)} paragraph(s) edited** this session")
        st.caption("Re-extract at end of session to update claims.")

    # Gold standard reference
    gs_path = Path(__file__).parent / "evals" / "gold_standard_claims.json"
    if gs_path.exists():
        st.divider()
        with st.expander("📚 Gold standard reference"):
            gs = json.loads(gs_path.read_text(encoding="utf-8"))
            for ex in gs["examples"]:
                icon = "✅" if ex["label"] == "approved" else "❌"
                st.markdown(f"{icon} **{ex['label'].upper()}**")
                st.markdown(f"> {ex['claim_text']}")
                st.caption(ex["source_note"])
                if ex.get("failure_categories"):
                    st.caption(f"_{', '.join(ex['failure_categories'])}_")
                st.divider()

# ---------------------------------------------------------------------------
# Build display list
# ---------------------------------------------------------------------------

display_indices = _pending_indices(all_claims) if filter_mode == "Pending only" else list(range(len(all_claims)))

# ---------------------------------------------------------------------------
# End-of-session: re-extract edited paragraphs
# ---------------------------------------------------------------------------

edited_paras = st.session_state.get("edited_para_indices", set())
judge_queue = data.get("_judge_queue", [])

if not display_indices or judge_queue:
    if not display_indices:
        st.success("All claims labeled!")
        if db_available:
            st.info("Approved claims were inserted into the DB as you labeled them.")

    # Show judge queue if it exists
    if judge_queue:
        st.divider()
        st.subheader(f"⚖️ Judge queue — {len(judge_queue)} new claim(s) from re-extracted paragraphs")
        st.caption("These came from paragraphs you edited. Approve or reject to insert.")
        for qi, qitem in enumerate(judge_queue):
            with st.expander(f"[{qitem.get('para_role', '')} / {qitem.get('para_section', '')}] {qitem['claim']['text'][:80]}"):
                judge = qitem["claim"].get("judge", {})
                if judge.get("pass"):
                    st.success("Judge: PASS")
                else:
                    st.error(f"Judge: FAIL — {judge.get('reason', '')}")
                st.markdown(f"**Claim:** {qitem['claim']['text']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"q_approve_{qi}"):
                        qitem["claim"]["status"] = "approved"
                        if db_available:
                            _insert_claim_to_db(db_path_val, qitem["para_hash"], qitem["claim"], None)
                        data["_judge_queue"][qi] = qitem
                        save_review(data, file_path)
                        st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"q_reject_{qi}"):
                        qitem["claim"]["status"] = "rejected"
                        data["_judge_queue"][qi] = qitem
                        save_review(data, file_path)
                        st.rerun()

    # Re-extract button for edited paragraphs
    if edited_paras:
        st.divider()
        api_key = st.session_state.get("anthropic_api_key", "")
        if not api_key:
            st.warning("Add Anthropic API key in sidebar to re-extract edited paragraphs.")
        else:
            if st.button(f"🔄 Re-extract {len(edited_paras)} edited paragraph(s)"):
                new_queue = list(data.get("_judge_queue", []))
                progress = st.progress(0)
                para_list = list(edited_paras)
                for idx, pi in enumerate(para_list):
                    para = data["paragraphs"][pi]
                    para_text = para["para_text"]
                    try:
                        new_claims, judge_results = _reextract_paragraph(para_text, api_key)
                        for i, claim in enumerate(new_claims):
                            passed, reason = judge_results.get(i, (True, ""))
                            claim["judge"] = {"pass": passed, "reason": reason or None}
                            claim["status"] = "pending" if passed else "rejected"
                            new_queue.append({
                                "para_hash": para["para_hash"],
                                "para_role": para.get("role", ""),
                                "para_section": para.get("section", ""),
                                "claim": claim,
                            })
                    except Exception as e:
                        st.error(f"Re-extract failed for {para.get('section', 'unknown')}: {e}")
                    progress.progress((idx + 1) / len(para_list))
                data["_judge_queue"] = new_queue
                save_review(data, file_path)
                st.session_state.edited_para_indices = set()
                st.success(f"Re-extracted {len(para_list)} paragraph(s). {len(new_queue)} claim(s) in judge queue.")
                st.rerun()

    # Gold standard candidates — surfaced at end of session, not mid-flow.
    # Both approved and rejected claims are candidates.
    if not display_indices:
        already_in_gs = {ex["claim_text"] for ex in _load_gold_standard().get("examples", [])}

        approved_candidates = [
            (pi, ci, c, p)
            for pi, ci, c, p in _all_claims(data)
            if c.get("status") == "approved"
            and c["text"] not in already_in_gs
        ]
        rejected_candidates = [
            (pi, ci, c, p)
            for pi, ci, c, p in _all_claims(data)
            if c.get("status") == "rejected"
            and c.get("failure_categories")
            and c["text"] not in already_in_gs
        ]

        if approved_candidates or rejected_candidates:
            st.divider()
            st.subheader("⭐ Gold standard candidates")
            st.caption(
                "Claims you labeled this session that could calibrate the judge. "
                "The judge is validated against approved AND rejected examples — both matter. "
                "Only add the clearest, most unambiguous cases. "
                "A borderline case is not a good calibration example."
            )

            gs_added_this_pass = False

            if approved_candidates:
                with st.expander(f"✅ Approved — {len(approved_candidates)} candidate(s)", expanded=False):
                    st.caption("Clear ownership, method, disposition, or motivation claims at the right level.")
                    for pi, ci, c, p in approved_candidates:
                        st.markdown(f"> {c['text']}")
                        st.caption(f"{p.get('role', '')} / {p.get('section', '')}")
                        note = st.text_input(
                            "Why is this obviously correct? (one sentence)",
                            key=f"gs_end_note_a_{pi}_{ci}",
                            placeholder="e.g. 'specific employer, specific system, ownership verb — right level'",
                        )
                        if st.button("Add to gold standard", key=f"gs_end_add_a_{pi}_{ci}"):
                            _add_to_gold_standard(c["text"], "approved", note or "approved claim at correct level", [])
                            gs_added_this_pass = True
                            st.success("Added.")
                        st.divider()

            if rejected_candidates:
                # Group by failure category
                by_cat: dict[str, list] = {}
                for pi, ci, c, p in rejected_candidates:
                    for cat in c.get("failure_categories", []):
                        by_cat.setdefault(cat, []).append((pi, ci, c, p))

                cat_descriptions = {
                    "too_generic": "No employer, no deliverable, no specific action — just said.",
                    "capability_statement": "Claims a skill without showing it. Cannot be proven.",
                    "wrong_context_type": "Personal project listed as employer or vice versa.",
                    "should_be_support_item": "Describes what a system did, not what the person owned.",
                    "should_be_sub_detail": "Implementation detail — belongs nested under a support item.",
                    "summary_not_claim": "Summarizes rather than asserts. 'Demonstrates' is the tell.",
                    "resume_speak": "Generic polished language with no specific evidence behind it.",
                    "negative_framing": "Claims what was avoided rather than what was done.",
                    "hallucinated": "Fact not present in the source paragraph.",
                    "wrong_employer": "Attributed to the wrong company.",
                }

                for cat, items in sorted(by_cat.items()):
                    with st.expander(f"❌ {cat} — {len(items)} claim(s)", expanded=False):
                        st.caption(cat_descriptions.get(cat, ""))
                        for pi, ci, c, p in items:
                            st.markdown(f"> {c['text']}")
                            st.caption(f"{p.get('role', '')} / {p.get('section', '')}")
                            note = st.text_input(
                                "Why is this obviously wrong? (one sentence)",
                                key=f"gs_end_note_r_{pi}_{ci}",
                                placeholder=f"e.g. 'pure {cat} — no specific action, cannot be proven'",
                            )
                            if st.button("Add to gold standard", key=f"gs_end_add_r_{pi}_{ci}"):
                                _add_to_gold_standard(
                                    c["text"], "rejected",
                                    note or f"rejected: {cat}",
                                    c.get("failure_categories", []),
                                )
                                gs_added_this_pass = True
                                st.success("Added.")
                            st.divider()

            if gs_added_this_pass:
                gs_a, gs_r = _gs_status()
                st.info(f"Gold standard now: {gs_a} ✅ {gs_r} ❌")

    if not display_indices:
        st.stop()

# ---------------------------------------------------------------------------
# Cursor bounds
# ---------------------------------------------------------------------------

if st.session_state.cursor >= len(display_indices):
    st.session_state.cursor = len(display_indices) - 1
if st.session_state.cursor < 0:
    st.session_state.cursor = 0

flat_idx = display_indices[st.session_state.cursor]
pi, ci, claim, para = all_claims[flat_idx]

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

nav1, nav2, nav3 = st.columns([1, 4, 1])
with nav1:
    if st.button("← Prev") and st.session_state.cursor > 0:
        st.session_state.cursor -= 1
        st.rerun()
with nav2:
    label = f"Claim {st.session_state.cursor + 1} of {len(display_indices)}"
    if filter_mode == "Pending only":
        label += " (pending)"
    st.markdown(f"<center><b>{label}</b></center>", unsafe_allow_html=True)
with nav3:
    if st.button("Next →") and st.session_state.cursor < len(display_indices) - 1:
        st.session_state.cursor += 1
        st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Main display
# ---------------------------------------------------------------------------

left, right = st.columns([3, 2])

with left:
    st.subheader(f"📄 {para['role']} / {para['section']}")
    if para.get("warning"):
        st.error(f"⚠️ {para['warning']}")

    # Editable source paragraph
    edited_text = st.text_area(
        "Source paragraph (edit directly if claims are wrong)",
        value=para["para_text"],
        height=180,
        key=f"para_edit_{pi}",
    )
    if edited_text != para["para_text"]:
        if st.button("💾 Save paragraph edits", key=f"save_para_{pi}"):
            data["paragraphs"][pi]["para_text"] = edited_text
            data["paragraphs"][pi]["_edited"] = True
            save_review(data, file_path)
            st.session_state.data = data
            st.session_state.edited_para_indices = (
                st.session_state.get("edited_para_indices", set()) | {pi}
            )
            st.success("Paragraph saved. Claims will be re-extracted at end of session.")

    st.subheader("🎯 Claim")
    status = claim.get("status", "pending")
    status_icon = {"approved": "✅", "rejected": "❌", "pending": "⏳"}.get(status, "⏳")
    st.markdown(f"### {status_icon} {claim['text']}")

    ctxs = claim.get("contexts", [])
    if ctxs:
        st.markdown("**Contexts:** " + "  ".join(f"`{c['type']}: {c['name']}`" for c in ctxs))
    else:
        st.markdown("**Contexts:** general")

    judge = claim.get("judge", {})
    if judge:
        if judge.get("pass"):
            st.success("Judge: PASS")
        else:
            st.error(f"Judge: FAIL — {judge.get('reason', '')}")

    support = claim.get("support", [])
    if support:
        st.subheader("🔗 Evidence")
        for s in support:
            st.markdown(f"**•** {s['text']}")
            for d in s.get("details", []):
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;↳ {d}")

    if para.get("conclusion"):
        st.subheader("💡 Conclusion")
        st.markdown(f"_{para['conclusion']}_")

with right:
    st.subheader("🏷️ Label")

    current_status = claim.get("status", "pending")
    label_choice = st.radio(
        "Decision",
        ["pending", "approved", "rejected"],
        index=["pending", "approved", "rejected"].index(current_status),
        key=f"label_{flat_idx}",
    )

    comment = st.text_area(
        "Comments",
        value=claim.get("comment", ""),
        placeholder="Why rejected? Wrong granularity? Which failure category?",
        key=f"comment_{flat_idx}",
        height=100,
    )

    failure_cats = st.multiselect(
        "Failure categories (if rejected)",
        options=[
            "too_generic", "capability_statement", "wrong_context_type",
            "should_be_support_item", "should_be_sub_detail", "summary_not_claim",
            "resume_speak", "negative_framing", "hallucinated", "wrong_employer",
        ],
        default=claim.get("failure_categories", []),
        key=f"cats_{flat_idx}",
    )

    st.divider()

    # Gold standard section
    gs_approved, gs_rejected = _gs_status()
    already_in_gs = claim["text"] in {
        ex["claim_text"] for ex in _load_gold_standard().get("examples", [])
    }

    with st.expander(
        "⭐ Add to gold standard" + (" — ✓ already added" if already_in_gs else ""),
        expanded=False,
    ):
        st.caption(
            "**What the gold standard is:** a set of reference examples the system uses to "
            "check whether the judge is calibrated. Before each extraction run, the judge's "
            "decisions are compared against these. If accuracy drops below 80%, you get a warning.\n\n"
            "**When to add something here:** only when the decision is completely obvious — "
            "no ambiguity, no 'it depends'. A clear ownership claim at the right level. "
            "A pure capability statement that obviously cannot be proven. Do not add borderline cases.\n\n"
            "**For rejected examples, the failure category is required** — that is the signal "
            "that tells the system what pattern to watch for. 'Rejected' alone is not useful."
        )

        if already_in_gs:
            st.success("Already in gold standard.")
            add_to_gs = False
            gs_note = ""
        else:
            add_to_gs = st.checkbox(
                "This is a clear, unambiguous example — add it",
                value=False,
                key=f"gs_{flat_idx}",
            )
            gs_note = ""
            if add_to_gs:
                gs_note = st.text_input(
                    "Why is this decision obvious? (one sentence)",
                    value="",
                    key=f"gs_note_{flat_idx}",
                    placeholder=(
                        "Approved: 'specific employer, specific system, ownership verb — right level' / "
                        "Rejected: 'no employer, no deliverable, just says it has experience'"
                    ),
                )
                if label_choice == "rejected" and not failure_cats:
                    st.warning("Select at least one failure category above before adding a rejected example to the gold standard.")

    st.divider()

    def _save_label(new_status: str, advance: bool) -> None:
        data["paragraphs"][pi]["claims"][ci]["status"] = new_status
        data["paragraphs"][pi]["claims"][ci]["comment"] = comment
        if failure_cats:
            data["paragraphs"][pi]["claims"][ci]["failure_categories"] = failure_cats

        # Save cursor position so session can be resumed
        data["_session_cursor"] = st.session_state.cursor

        save_review(data, file_path)
        st.session_state.data = data

        if add_to_gs and not already_in_gs and new_status in ("approved", "rejected"):
            note = gs_note or (
                "ownership/decision claim at the right level" if new_status == "approved"
                else f"rejected: {', '.join(failure_cats)}" if failure_cats
                else "rejected claim"
            )
            _add_to_gold_standard(claim["text"], new_status, note, failure_cats)

        if new_status == "approved" and db_available:
            claim_to_insert = data["paragraphs"][pi]["claims"][ci]
            _insert_claim_to_db(db_path_val, para["para_hash"], claim_to_insert, para.get("conclusion"))

        if advance and st.session_state.cursor < len(display_indices) - 1:
            st.session_state.cursor += 1
        st.rerun()

    col_a, col_r = st.columns(2)
    with col_a:
        if st.button("✅ Approve & Next", width="stretch"):
            _save_label("approved", advance=True)
    with col_r:
        if st.button("❌ Reject & Next", width="stretch"):
            _save_label("rejected", advance=True)

    st.divider()
    col_s, col_sn = st.columns(2)
    with col_s:
        if st.button("💾 Save", width="stretch"):
            _save_label(label_choice, advance=False)
    with col_sn:
        if st.button("💾 Save & Next", width="stretch"):
            _save_label(label_choice, advance=True)

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

st.divider()
with st.expander("📊 All claims"):
    filter_status = st.selectbox("Filter", ["all", "pending", "approved", "rejected"])
    rows = []
    for _, _, c, p in all_claims:
        if filter_status != "all" and c.get("status") != filter_status:
            continue
        j = c.get("judge", {}) or {}
        rows.append({
            "Para": f"{p['role']} / {p['section'][:30]}",
            "Claim": c["text"][:80],
            "Status": c.get("status", "pending"),
            "Judge": "✅" if j.get("pass") else ("❌" if j else "—"),
            "Comment": c.get("comment", "")[:50],
        })
    st.dataframe(rows, width="stretch")
