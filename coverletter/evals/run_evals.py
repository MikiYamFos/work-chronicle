"""Extraction pipeline evaluation script.

Measures the overall quality of the extraction pipeline as a single number:
the percentage of extracted claims the judge approves.

Run with:
  uv run python coverletter/evals/run_evals.py
  uv run python coverletter/evals/run_evals.py --limit 5   # test on first 5 paragraphs

Three phases:
  Phase 1: run extraction on every paragraph in the library
  Phase 2: apply the judge to every extracted claim
  Phase 3: report % good with cost and time breakdown

This number is comparable across runs. When you change the extraction prompt,
judge prompt, or model, run this again and compare. As long as you use the same
judge, the relative numbers are meaningful even if absolute numbers aren't perfect.

Also reports trajectory length (claims extracted per paragraph) — paragraphs
that produce 0 claims or unusually many are worth investigating.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

# Load .env the same way the rest of the codebase does
from dotenv import load_dotenv
load_dotenv(override=True)

import coverletter.costs as _costs_module
from coverletter.extract import (
    _extract_from_paragraph,
    _judge_claim,
    _EXTRACT_MODEL,
    _JUDGE_MODEL,
)


# ---------------------------------------------------------------------------
# Cost tracking — reads directly from the costs module session globals
# so no monkey-patching needed
# ---------------------------------------------------------------------------

@dataclass
class CostAccumulator:
    """Snapshots coverletter.costs session globals to measure cost of a phase."""
    _start_cost: float = field(default_factory=lambda: _costs_module._session_cost)
    _start_in: int = field(default_factory=lambda: _costs_module._session_input_tokens)
    _start_out: int = field(default_factory=lambda: _costs_module._session_output_tokens)

    @property
    def total_cost(self) -> float:
        return _costs_module._session_cost - self._start_cost

    @property
    def input_tokens(self) -> int:
        return _costs_module._session_input_tokens - self._start_in

    @property
    def output_tokens(self) -> int:
        return _costs_module._session_output_tokens - self._start_out


# ---------------------------------------------------------------------------
# Phase 1: extraction
# ---------------------------------------------------------------------------

def load_paragraphs(db_path: Path, limit: int | None = None) -> list[dict]:
    """Load paragraphs and their raw Q&A from the DB."""
    from coverletter.db import open_db
    conn = open_db(db_path)  # ensures schema is applied including raw_responses
    rows = conn.execute(
        "SELECT text_hash, text, role, section FROM paragraphs WHERE active = 1"
    ).fetchall()
    result = []
    for row in rows:
        raw_row = conn.execute(
            "SELECT responses_md FROM raw_responses WHERE para_text_hash = ? "
            "ORDER BY captured_at DESC LIMIT 1",
            (row["text_hash"],),
        ).fetchone()
        result.append({
            "para_hash": row["text_hash"],
            "para_text": row["text"],
            "role": row["role"],
            "section": row["section"],
            "raw": raw_row["responses_md"] if raw_row else None,
        })
    conn.close()
    if limit:
        result = result[:limit]
    return result


def run_extraction_on_paragraph(para: dict, api_key: str, model: str) -> list[dict]:
    """Extract claims from one paragraph. Returns flat list of claim dicts."""
    data = _extract_from_paragraph(para["para_text"], para["raw"], api_key, model)
    flat_claims = []
    for claim in data.get("claims", []):
        flat_claims.append({
            "text": claim.get("text", ""),
            "contexts": claim.get("contexts", []),
            "support_count": len(claim.get("support", [])),
            "detail_count": sum(len(s.get("details", [])) for s in claim.get("support", [])),
        })
    return flat_claims


def run_extraction_on_all(
    paragraphs: list[dict],
    api_key: str,
    model: str,
) -> list[dict]:
    """Phase 1: extract claims from all paragraphs."""
    results = []
    total = len(paragraphs)

    for i, para in enumerate(paragraphs, 1):
        label = f"{para['role']} / {para['section']}"
        print(f"\n[{i}/{total}] Extracting: {label[:60]}", end="", flush=True)
        try:
            t0 = time.perf_counter()
            claims = run_extraction_on_paragraph(para, api_key, model)
            elapsed = time.perf_counter() - t0
            print(f"  → {len(claims)} claim(s)  {elapsed:.1f}s")
        except Exception as exc:
            print(f"  ERROR: {exc}")
            claims = []

        results.append({
            "para_hash": para["para_hash"],
            "para_text": para["para_text"],
            "role": para["role"],
            "section": para["section"],
            "claims": claims,
            "claim_count": len(claims),
        })

    return results


# ---------------------------------------------------------------------------
# Phase 2: judge each extracted claim
# ---------------------------------------------------------------------------

def judge_all_claims(
    extraction_results: list[dict],
    api_key: str,
) -> list[dict]:
    """Phase 2: apply judge to every extracted claim."""
    judged = []
    total_claims = sum(r["claim_count"] for r in extraction_results)
    claim_num = 0

    for para_result in extraction_results:
        judged_claims = []
        for claim in para_result["claims"]:
            claim_num += 1
            text = claim.get("text", "")
            if not text:
                continue

            print(f"\n  [{claim_num}/{total_claims}] Judging: {text[:70]}", end="", flush=True)
            try:
                judge_pass, judge_reason = _judge_claim(text, para_result["para_text"], api_key)
                label = "approved" if judge_pass else "rejected"
                print(f"  → {label.upper()}")
            except Exception as exc:
                print(f"  ERROR: {exc}")
                judge_pass, judge_reason = False, f"judge error: {exc}"
                label = "rejected"

            judged_claims.append({
                **claim,
                "judge_label": label,
                "judge_reason": judge_reason,
            })

        judged.append({**para_result, "claims": judged_claims})

    return judged


# ---------------------------------------------------------------------------
# Phase 3: report
# ---------------------------------------------------------------------------

def fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s" if m else f"{s}s"


def report(
    judged_results: list[dict],
    extract_cost: CostAccumulator,
    judge_cost: CostAccumulator,
    extract_elapsed: float,
    judge_elapsed: float,
) -> None:
    all_claims = [c for r in judged_results for c in r["claims"]]
    total_claims = len(all_claims)
    approved = sum(1 for c in all_claims if c["judge_label"] == "approved")
    rejected = total_claims - approved
    pct_good = approved / total_claims * 100 if total_claims else 0

    total_cost = extract_cost.total_cost + judge_cost.total_cost
    total_elapsed = extract_elapsed + judge_elapsed

    print("\n" + "=" * 60)
    print("EXTRACTION PIPELINE EVALUATION")
    print("=" * 60)
    print(f"  Paragraphs processed: {len(judged_results)}")
    print(f"  Claims extracted:     {total_claims}")
    print(f"  Approved by judge:    {approved} ({pct_good:.1f}%)")
    print(f"  Rejected by judge:    {rejected}")
    print()
    print(f"  Extract cost: ${extract_cost.total_cost:.4f}   time: {fmt_time(extract_elapsed)}")
    print(f"  Judge cost:   ${judge_cost.total_cost:.4f}   time: {fmt_time(judge_elapsed)}")
    print(f"  Total:        ${total_cost:.4f}   time: {fmt_time(total_elapsed)}")

    # Trajectory analysis — paragraphs with 0 claims or unusually many
    print(f"\n{'─' * 60}")
    print("TRAJECTORY ANALYSIS")
    zero_claim_paras = [r for r in judged_results if r["claim_count"] == 0]
    high_claim_paras = [r for r in judged_results if r["claim_count"] > 4]

    if zero_claim_paras:
        print(f"\n⚠️  {len(zero_claim_paras)} paragraph(s) produced NO claims:")
        for r in zero_claim_paras:
            print(f"  - {r['role']} / {r['section']}")

    if high_claim_paras:
        print(f"\n⚠️  {len(high_claim_paras)} paragraph(s) produced >4 claims (possible over-extraction):")
        for r in high_claim_paras:
            print(f"  - {r['role']} / {r['section']} ({r['claim_count']} claims)")

    # Rejected claims — what patterns
    rejected_claims = [c for r in judged_results for c in r["claims"] if c["judge_label"] == "rejected"]
    if rejected_claims:
        print(f"\n{'─' * 60}")
        print(f"REJECTED CLAIMS ({len(rejected_claims)}) — review these for prompt improvements")
        for r in judged_results:
            for c in r["claims"]:
                if c["judge_label"] == "rejected":
                    print(f"\n  ❌ [{r['section'][:30]}] {c['text'][:80]}")
                    if c.get("judge_reason"):
                        print(f"     Reason: {c['judge_reason']}")

    print(f"\n{'=' * 60}")
    print(f"QUALITY SCORE: {approved}/{total_claims} ({pct_good:.1f}%) claims approved")

    color = "✅" if pct_good >= 80 else "⚠️ " if pct_good >= 60 else "❌"
    print(f"{color} Target: ≥ 80% approved")
    print()


def save_results(judged: list[dict], path: Path) -> None:
    path.write_text(json.dumps(judged, indent=2), encoding="utf-8")

    csv_path = path.with_suffix(".csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "para_section", "claim_text", "judge_label", "judge_reason",
            "contexts", "support_count", "detail_count",
        ])
        writer.writeheader()
        for r in judged:
            for c in r["claims"]:
                writer.writerow({
                    "para_section": f"{r['role']} / {r['section']}",
                    "claim_text": c.get("text", ""),
                    "judge_label": c.get("judge_label", ""),
                    "judge_reason": c.get("judge_reason", ""),
                    "contexts": json.dumps(c.get("contexts", [])),
                    "support_count": c.get("support_count", 0),
                    "detail_count": c.get("detail_count", 0),
                })

    print(f"Results saved:")
    print(f"  {path}")
    print(f"  {csv_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Run extraction pipeline evaluation")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only process first N paragraphs (for quick checks)")
    parser.add_argument("--db", type=str, default=None,
                        help="Path to library.db (auto-detected if not set)")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in environment or .env file")
        sys.exit(1)

    # Find DB
    if args.db:
        db_path = Path(args.db)
    else:
        candidates = list(Path.cwd().glob("*.db")) + list((Path.cwd() / "data").glob("*.db"))
        db_path = candidates[0] if candidates else None

    if not db_path or not db_path.exists():
        print("ERROR: Could not find library.db. Use --db <path>")
        sys.exit(1)

    print(f"DB: {db_path}")
    paragraphs = load_paragraphs(db_path, limit=args.limit)
    print(f"Loaded {len(paragraphs)} paragraph(s)"
          + (f" (limited to {args.limit})" if args.limit else ""))

    if not paragraphs:
        print("No paragraphs found. Run `coverletter sync` first.")
        sys.exit(1)

    # Phase 1: extraction
    print(f"\n{'─' * 60}")
    print("PHASE 1: EXTRACTION")
    extract_cost = CostAccumulator()
    t0 = time.perf_counter()
    extraction_results = run_extraction_on_all(paragraphs, api_key, _EXTRACT_MODEL)
    extract_elapsed = time.perf_counter() - t0

    total_extracted = sum(r["claim_count"] for r in extraction_results)
    print(f"\nExtracted {total_extracted} claim(s) from {len(paragraphs)} paragraph(s)")

    if total_extracted == 0:
        print("No claims extracted in selected paragraphs — try with more paragraphs or different section")
        sys.exit(0)

    # Phase 2: judge
    print(f"\n{'─' * 60}")
    print("PHASE 2: JUDGE")
    judge_cost = CostAccumulator()
    t1 = time.perf_counter()
    judged = judge_all_claims(extraction_results, api_key)
    judge_elapsed = time.perf_counter() - t1

    # Phase 3: report
    report(judged, extract_cost, judge_cost, extract_elapsed, judge_elapsed)

    # Save
    out_path = Path(__file__).parent / "eval_results.json"
    save_results(judged, out_path)


if __name__ == "__main__":
    main()
