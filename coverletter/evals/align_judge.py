"""Judge alignment script.

Runs the extraction judge against your gold standard labeled examples and
reports where it agrees and disagrees with your labels.

Run with:
  uv run python coverletter/evals/align_judge.py

The gold standard IS the source of truth for what good and bad claims look like
for this user's library. Categories and source_notes in rejected examples define
the patterns the judge should catch. When the judge gets something wrong:

  1. Run this script — see the disagreement and the judge's reasoning
  2. If it's a new pattern not in the gold standard:
       Add the failing example to gold_standard_claims.json with:
       - correct label (approved/rejected)
       - failure_categories that name the pattern
       - source_note explaining exactly why
  3. If the category exists but the judge is still missing it:
       The structural rule in _JUDGE_SYSTEM in extract.py needs sharpening
  4. Re-run to confirm improvement

DO NOT add specific claim texts from your library into _JUDGE_SYSTEM.
The gold standard is where user-specific examples live.
Concrete named examples in _JUDGE_SYSTEM are fine — they must just be generic
fictional examples that teach the structural rule, not your real work history.

Alignment targets:
  Recall  >= 0.89  (catch bad claims — false approvals corrupt the DB)
  Accuracy >= 0.80
  Precision: track, don't over-optimize (false rejects are recoverable in review app)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Allow running from project root or evals/ directory
_PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(override=True)

from coverletter.extract import _judge_claim, _JUDGE_SYSTEM


def load_gold_standard(path: Path | None = None) -> list[dict]:
    if path is None:
        path = Path(__file__).parent / "gold_standard_claims.json"
    if not path.exists():
        print(f"ERROR: Gold standard not found at {path}")
        sys.exit(1)
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("examples", [])


def run_judge_on_examples(examples: list[dict], api_key: str) -> list[dict]:
    """Run the judge on every gold standard example. Returns results list."""
    results = []
    for ex in examples:
        claim_text = ex["claim_text"]
        human_label = ex["label"]

        # Use the claim itself as the source paragraph for quality-level checks.
        # Grounding checks (does the claim appear in the paragraph?) are not what
        # we're testing here — we're testing whether the judge correctly evaluates
        # claim granularity, context type, and framing.
        judge_pass, judge_reason = _judge_claim(claim_text, claim_text, api_key)
        judge_label = "approved" if judge_pass else "rejected"

        results.append({
            "id": ex["id"],
            "claim_text": claim_text,
            "human_label": human_label,
            "judge_label": judge_label,
            "judge_reason": judge_reason,
            "correct": judge_label == human_label,
            "failure_categories": ex.get("failure_categories", []),
            "source_note": ex.get("source_note", ""),
        })

    return results


def compute_metrics(results: list[dict]) -> dict:
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    accuracy = correct / total if total else 0

    # Treating "approved" as positive class (what we want to keep)
    approved_total = sum(1 for r in results if r["human_label"] == "approved")
    rejected_total = sum(1 for r in results if r["human_label"] == "rejected")

    false_negatives = [r for r in results if r["human_label"] == "approved" and r["judge_label"] == "rejected"]
    false_positives = [r for r in results if r["human_label"] == "rejected" and r["judge_label"] == "approved"]
    true_positives = approved_total - len(false_negatives)

    precision = true_positives / (true_positives + len(false_positives)) if (true_positives + len(false_positives)) else 0
    recall = true_positives / approved_total if approved_total else 0

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "approved_total": approved_total,
        "rejected_total": rejected_total,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def print_report(results: list[dict], metrics: dict) -> None:
    acc = metrics["accuracy"]
    prec = metrics["precision"]
    rec = metrics["recall"]

    acc_sym  = "✅" if acc  >= 0.80 else "⚠️ " if acc  >= 0.65 else "❌"
    rec_sym  = "✅" if rec  >= 0.89 else "⚠️ " if rec  >= 0.70 else "❌"
    prec_sym = "✅" if prec >= 0.60 else "⚠️ "

    print("\n" + "="*60)
    print("JUDGE ALIGNMENT REPORT")
    print("="*60)
    print(f"  {acc_sym}  Accuracy:  {acc:.0%}  ({metrics['correct']}/{metrics['total']} correct)")
    print(f"  {rec_sym}  Recall:    {rec:.0%}  (catching bad claims — target ≥ 89%)")
    print(f"  {prec_sym}  Precision: {prec:.0%}  (false alarm rate — track, don't over-optimize)")
    print(f"\n  Gold standard: {metrics['approved_total']} approved, {metrics['rejected_total']} rejected")

    # False positives: judge approved what should be rejected
    fps = metrics["false_positives"]
    if fps:
        print(f"\n{'─'*60}")
        print(f"FALSE POSITIVES ({len(fps)}) — judge APPROVED but should be REJECTED")
        print("These are the most dangerous: bad claims getting through to the DB.")
        print("Fix: make the judge stricter for these patterns.\n")
        for r in fps:
            cats = ", ".join(r["failure_categories"]) if r["failure_categories"] else "unlabeled"
            print(f"  ❌ [{r['id']}] {r['claim_text'][:80]}")
            print(f"     Failure pattern: {cats}")
            print(f"     Note: {r['source_note'][:100]}")
            print()
    else:
        print(f"\n{'─'*60}")
        print("FALSE POSITIVES: none ✅")

    # False negatives: judge rejected what should be approved
    fns = metrics["false_negatives"]
    if fns:
        print(f"\n{'─'*60}")
        print(f"FALSE NEGATIVES ({len(fns)}) — judge REJECTED but should be APPROVED")
        print("These are recoverable: user can approve in Streamlit review app.")
        print("Fix: loosen the judge for these patterns (carefully).\n")
        for r in fns:
            print(f"  ⚠️  [{r['id']}] {r['claim_text'][:80]}")
            print(f"     Judge reason: {r['judge_reason']}")
            print(f"     Note: {r['source_note'][:100]}")
            print()
    else:
        print(f"\n{'─'*60}")
        print("FALSE NEGATIVES: none ✅")

    # All correct cases (for confirmation)
    print(f"\n{'─'*60}")
    print(f"CORRECT ({metrics['correct']}/{metrics['total']})\n")
    for r in results:
        if r["correct"]:
            sym = "✅" if r["human_label"] == "approved" else "🚫"
            print(f"  {sym} [{r['id']}] {r['claim_text'][:70]}")

    print(f"\n{'='*60}")

    # Guidance
    if acc < 0.80 or rec < 0.89:
        print("\n⚠️  ACTION NEEDED: Judge alignment is below target.")
        print()
        print("   For each false positive (judge approved, should reject):")
        print("   1. Is this failure pattern already in gold_standard_claims.json?")
        print("      If NO: add the claim as a rejected example with:")
        print("        - failure_categories: the pattern name (e.g. should_be_support_item)")
        print("        - source_note: exactly WHY this is rejected — the rule, not just the observation")
        print("      If YES: is the source_note clear enough? Does it explain the rule generically?")
        print("        Improve the source_note so the pattern is unambiguous.")
        print()
        print("   For each false negative (judge rejected, should approve):")
        print("   1. Add the claim as an approved example with a source_note explaining")
        print("      what makes it valid despite looking borderline.")
        print()
        print("   Only touch _JUDGE_SYSTEM in extract.py if the structural rule itself")
        print("   is wrong or missing entirely — not to add specific examples.")
        print()
        print("   Re-run this script after updating the gold standard.")
    else:
        print("\n✅ Judge is aligned. No changes needed.")
        print("   If you've added new paragraphs to the library, run `coverletter extract --dry-run`")
        print("   and review in the Streamlit app. Mark clear cases as gold standard examples.")

    print()


def save_results_csv(results: list[dict], path: Path) -> None:
    """Save results to CSV for deeper analysis."""
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "claim_text", "human_label", "judge_label",
            "correct", "judge_reason", "failure_categories", "source_note",
        ])
        writer.writeheader()
        for r in results:
            row = dict(r)
            row["failure_categories"] = ", ".join(r["failure_categories"])
            writer.writerow(row)
    print(f"Results saved to: {path}")


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in environment or .env file")
        sys.exit(1)

    print("Loading gold standard examples...")
    examples = load_gold_standard()
    print(f"Loaded {len(examples)} examples ({sum(1 for e in examples if e['label'] == 'approved')} approved, "
          f"{sum(1 for e in examples if e['label'] == 'rejected')} rejected)")

    print("\nRunning judge on all examples...")
    print("(Each call uses the actual _judge_claim function from extract.py)\n")

    results = []
    for i, ex in enumerate(examples, 1):
        print(f"  [{i}/{len(examples)}] {ex['id']} — {ex['claim_text'][:60]}...", end="", flush=True)
        judge_pass, judge_reason = _judge_claim(ex["claim_text"], ex["claim_text"], api_key)
        judge_label = "approved" if judge_pass else "rejected"
        correct = judge_label == ex["label"]
        mark = "✓" if correct else "✗"
        print(f" {mark}")
        results.append({
            "id": ex["id"],
            "claim_text": ex["claim_text"],
            "human_label": ex["label"],
            "judge_label": judge_label,
            "judge_reason": judge_reason,
            "correct": correct,
            "failure_categories": ex.get("failure_categories", []),
            "source_note": ex.get("source_note", ""),
        })

    metrics = compute_metrics(results)
    print_report(results, metrics)

    # Save CSV
    out_path = Path(__file__).parent / "align_judge_results.csv"
    save_results_csv(results, out_path)

    # Offer to draft a prompt update if there are disagreements
    fps = metrics["false_positives"]
    fns = metrics["false_negatives"]
    if (fps or fns) and api_key:
        print()
        answer = input("Draft a judge prompt patch for these disagreements? [y/N]: ").strip().lower()
        if answer in ("y", "yes"):
            draft_prompt_patch(fps, fns, api_key)


def draft_prompt_patch(false_positives: list[dict], false_negatives: list[dict], api_key: str) -> None:
    """Ask Haiku to draft targeted additions to _JUDGE_SYSTEM based on disagreements."""
    import anthropic

    fp_block = "\n".join(
        f"- APPROVED (should be REJECTED): {r['claim_text']}\n"
        f"  Failure pattern: {', '.join(r['failure_categories']) or 'unlabeled'}\n"
        f"  Why it should be rejected: {r['source_note']}"
        for r in false_positives
    )
    fn_block = "\n".join(
        f"- REJECTED (should be APPROVED): {r['claim_text']}\n"
        f"  Judge's reason for rejecting: {r['judge_reason']}\n"
        f"  Why it should be approved: {r['source_note']}"
        for r in false_negatives
    )

    system = """\
You are editing a judge prompt for a cover letter claim quality system.
The judge evaluates whether a claim is specific enough to be useful in a cover letter.

You will be given:
1. The current judge system prompt
2. Cases where the judge got it wrong

Your job: draft ONLY the new or modified rules needed to fix the errors.
- Write in the same style and format as the existing prompt
- Do NOT rewrite the whole prompt — draft additions or replacements for specific rules only
- Keep it short — one rule per disagreement pattern
- Do not add user-specific claim texts as examples. Use generic structural descriptions.
- Output format:
  ### Changes to _JUDGE_SYSTEM
  [your additions/modifications here]
  ### Reasoning
  [one line per change: what error it fixes and why this wording works]
"""

    content = (
        f"=== CURRENT JUDGE PROMPT ===\n{_JUDGE_SYSTEM}\n\n"
        + (f"=== FALSE POSITIVES (judge too lenient) ===\n{fp_block}\n\n" if fp_block else "")
        + (f"=== FALSE NEGATIVES (judge too strict) ===\n{fn_block}\n\n" if fn_block else "")
    )

    client = anthropic.Anthropic(api_key=api_key)
    print("\nDrafting prompt patch...\n")
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": content}],
        temperature=0,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")
    print("─" * 60)
    print("Review the above, then manually edit _JUDGE_SYSTEM in coverletter/extract.py.")
    print("Re-run this script to confirm improvement.")


if __name__ == "__main__":
    main()
