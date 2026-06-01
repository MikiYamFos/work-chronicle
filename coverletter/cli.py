import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.spinner import Spinner
from rich.table import Table
from rich.live import Live

from coverletter.align import AlignmentResult, alignment_report, generate_argument, generate_thesis, has_library_coverage
from coverletter.profile import CandidateProfile, load_profile
from coverletter.costs import running_total
from coverletter.coach import WeakSentence, analyze_letter, get_context, rewrite_sentence
from coverletter.config import load_config
from coverletter.llm import stream_cover_letter, stream_revision
from coverletter.output import _flush_stdin, _prompt_choice, render_letter, save_letter, save_pdf
from coverletter.parser import Paragraph, available_roles, filter_by_role, load_paragraphs, library_stats
from coverletter.prompt import SHORT_RESPONSE_SYSTEM, SYSTEM_PROMPT, build_user_message, embed_classify, embed_prefilter, prefilter
from coverletter.resume import load_resume
from coverletter.verify import verbatim_check, verify_letter

console = Console()


def _read_from_clipboard() -> str:
    """Read text from the system clipboard. Returns empty string on failure."""
    import platform, subprocess
    try:
        if platform.system() == "Darwin":
            result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
            return result.stdout if result.returncode == 0 else ""
        # Linux: try xclip then xsel
        for cmd in [
            ["xclip", "-selection", "clipboard", "-o"],
            ["xsel", "--clipboard", "--output"],
        ]:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return result.stdout
            except FileNotFoundError:
                continue
    except Exception:
        pass
    return ""


def _display_jd(text: str) -> None:
    from rich.panel import Panel
    console.print(Panel(text, title="[bold]Job Description[/bold]", border_style="dim", padding=(1, 2)))


def _save_jd(text: str, jds_dir: "Path") -> None:
    import datetime
    jds_dir.mkdir(parents=True, exist_ok=True)
    default = datetime.date.today().isoformat()
    console.print(f"\nSave JD as [dim](press Enter for {default})[/dim]: ", end="")
    _flush_stdin()
    try:
        label = input().strip() or default
    except (KeyboardInterrupt, EOFError):
        return
    # Sanitize to safe filename
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in label).strip("-")
    if not safe:
        safe = default
    fname = jds_dir / f"{safe}.txt"
    counter = 1
    while fname.exists():
        fname = jds_dir / f"{safe}_{counter}.txt"
        counter += 1
    fname.write_text(text, encoding="utf-8")
    console.print(f"[dim]Saved → {fname}[/dim]")


def read_job_description(
    prompt: str | None = None,
    jds_dir: "Path | None" = None,
) -> str:
    from pathlib import Path

    # Non-interactive (piped) input: read stdin directly.
    if not sys.stdin.isatty():
        try:
            text = sys.stdin.read().strip()
        except KeyboardInterrupt:
            raise SystemExit("\nCancelled.")
        if not text:
            raise SystemExit("\nNo input provided. Exiting.")
        return text

    # Clipboard path.
    if prompt is not None:
        console.print(prompt)
    else:
        console.print(
            "\n[bold]Copy the full job description to your clipboard, then press Enter.[/bold]\n"
            "[dim]The text will be displayed for confirmation.[/dim]\n"
        )

    try:
        _flush_stdin()
        input()
    except (KeyboardInterrupt, EOFError):
        raise SystemExit("\nCancelled.")

    text = _read_from_clipboard().strip()
    if not text:
        raise SystemExit("\nClipboard was empty. Copy the job description and try again.")

    # Reconnect stdin so any pasted text that bled into Python's stdio buffer
    # doesn't contaminate subsequent prompts.
    try:
        sys.stdin = open("/dev/tty", "r")
    except OSError:
        _flush_stdin()

    _display_jd(text)
    console.print(f"[dim]{len(text):,} characters read from clipboard.[/dim]")

    if jds_dir is not None:
        _save_jd(text, Path(jds_dir))

    return text


def select_role(all_paragraphs: list[Paragraph]) -> str | None:
    roles = available_roles(all_paragraphs)
    non_general = [r for r in roles if r != "General"]

    if not non_general:
        return None  # only General — no selection needed

    if len(non_general) == 1:
        return non_general[0]  # only one role — no point asking

    console.print("\n[bold]Which role are you applying for?[/bold]")
    for i, role in enumerate(non_general, 1):
        console.print(f"  [cyan]{i}[/cyan]. {role}")
    console.print(f"  [cyan]{len(non_general) + 1}[/cyan]. General (no role filter)")

    _flush_stdin()
    raw = input("\nEnter number: ").strip()
    try:
        choice = int(raw)
    except ValueError:
        return None

    if 1 <= choice <= len(non_general):
        return non_general[choice - 1]
    return None  # chose General or out of range


def _find_template(output_dir: "Path", name: str) -> "Path | None":
    from pathlib import Path

    if not output_dir.exists():
        return None
    name_lower = name.lower()
    matches = [f for f in output_dir.glob("*.md") if name_lower in f.stem.lower()]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    console.print("\n[bold]Multiple template matches:[/bold]")
    for i, m in enumerate(matches, 1):
        console.print(f"  [cyan]{i}[/cyan]. {m.name}")
    _flush_stdin()
    raw = input("Choose number: ").strip()
    try:
        return matches[int(raw) - 1]
    except (ValueError, IndexError):
        return matches[0]



def _read_multiline(prompt: str = "> ") -> str:
    """Read multiline input. Uses prompt_toolkit (no line-length limit, paste-safe).

    Enter adds a newline. Ctrl-D or Meta-Enter submits. Ctrl-C cancels.
    Falls back to double-Enter if prompt_toolkit is unavailable.
    """
    console.print(
        f"[dim]{prompt}Press Enter for new lines. Enter twice or Ctrl-D to submit.[/dim]"
    )
    lines: list[str] = []
    try:
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                lines.pop()
                break
            lines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelled.[/dim]")
        raise
    return "\n".join(lines).strip()


def _show_alignment(report: "AlignmentResult") -> None:
    from rich.panel import Panel
    score_color = "green" if report.score_pct >= 80 else "yellow" if report.score_pct >= 50 else "red"
    lines = [f"[{score_color}]{report.score_line()}[/{score_color}]\n"]
    if report.covered:
        lines.append("[dim]Covered:[/dim]")
        for c in report.covered:
            lines.append(f"  [green]✓[/green] [dim]{c}[/dim]")
    if report.gaps:
        lines.append("\n[bold]JD Gaps:[/bold]")
        for i, g in enumerate(report.gaps, 1):
            lines.append(f"  [red]{i}.[/red] {g}")
    if report.seniority_gaps:
        lines.append("\n[bold]Seniority Signal Gaps:[/bold]")
        for i, g in enumerate(report.seniority_gaps, 1):
            lines.append(f"  [yellow]{i}.[/yellow] {g}")
    if report.goal_alignment:
        lines.append(f"\n[bold]Goal fit:[/bold] {report.goal_alignment}")
    if report.perspective_note:
        lines.append(f"\n[bold yellow]Narrative frame:[/bold yellow] {report.perspective_note}")
    console.print(Panel("\n".join(lines), title="JD Alignment", border_style="yellow"))


def _gap_loop(
    gaps: "list[str]",
    all_paragraphs: "list[Paragraph]",
    priority_file: "Path",
    cfg: "Config",
    job_description: str,
    seniority_gaps: "list[str] | None" = None,
    resume_text: str = "",
) -> int:
    """Show all gaps at once, let user pick which to address. Returns count of paragraphs saved."""
    import re
    saved = 0
    console.print()

    all_gaps = [(g, "JD") for g in gaps] + [(g, "Seniority") for g in (seniority_gaps or [])]
    if not all_gaps:
        return 0

    # Separate library-covered (already have material, just need regen) from truly missing
    actionable: list[tuple[int, str, str]] = []
    covered_by_library: list[int] = []

    console.print(f"[bold]{len(all_gaps)} gap(s):[/bold]\n")
    for i, (gap, kind) in enumerate(all_gaps, 1):
        if has_library_coverage(gap):
            console.print(f"  [dim]{i}. [in library] {gap}[/dim]")
            covered_by_library.append(i)
        elif kind == "Seniority":
            console.print(f"  [yellow]{i}.[/yellow] [Seniority] {gap}")
            actionable.append((i, gap, kind))
        else:
            console.print(f"  [red]{i}.[/red] {gap}")
            actionable.append((i, gap, kind))

    if covered_by_library:
        console.print(f"\n[dim]Gaps {', '.join(str(n) for n in covered_by_library)} already have library paragraphs — they'll be pulled in on regen.[/dim]")

    if not actionable:
        console.print("[dim]No actionable gaps — all have library coverage.[/dim]")
        return 0

    actionable_nums = ", ".join(str(i) for i, _, _ in actionable)
    console.print(f"\n[dim]Actionable: {actionable_nums}[/dim]")
    _flush_stdin()
    raw = input("Address which gaps? (e.g. 1,3 or 'all' or Enter to skip all): ").strip()

    if not raw:
        return 0

    if raw.lower() in ("all", "a"):
        selected = {i for i, _, _ in actionable}
    else:
        try:
            selected = {int(n.strip()) for n in raw.replace(" ", "").split(",") if n.strip().isdigit()}
        except ValueError:
            selected = set()

    for i, gap, kind in actionable:
        if i not in selected:
            continue
        if kind == "Seniority":
            console.print(f"\n[yellow]Seniority gap {i}: {gap}[/yellow]")
        else:
            console.print(f"\n[bold]Gap {i}:[/bold] {gap}")

        # Guard against duplicate saves: search the current library for this gap
        # before starting Q&A. If we find a strong match, show it and let the user
        # confirm it doesn't already cover the gap. This catches the common case of
        # a session restart after interruption where the paragraph was already saved.
        if all_paragraphs:
            from coverletter.build import _search_library
            match_text = _search_library(gap, all_paragraphs, voyage_api_key=cfg.voyage_api_key)
            if match_text and match_text != "No matching paragraphs found.":
                from rich.panel import Panel
                console.print("\n[yellow]Library match found — may already cover this gap:[/yellow]")
                console.print(Panel(match_text[:600] + ("…" if len(match_text) > 600 else ""), border_style="yellow"))
                _flush_stdin()
                confirm = input("[Y] yes, this covers it — skip   [Enter] no, build new paragraph → ").strip().lower()
                if confirm == "y":
                    console.print("[dim]Skipped.[/dim]")
                    continue

        try:
            result = _qa_session(
                gap, all_paragraphs, priority_file, cfg,
                job_description=job_description, gap_description=gap,
                voyage_api_key=cfg.voyage_api_key,
                resume_text=resume_text,
            )
        except KeyboardInterrupt:
            console.print("\n[dim]Stopped. Any paragraphs saved above are in the library.[/dim]")
            break
        if result:
            saved += 1

    return saved


def _coaching_pass(
    letter_text: str,
    api_key: str,
    model: str,
    all_paragraphs: "list[Paragraph] | None" = None,
    corrected_paragraphs: "list[Paragraph] | None" = None,
    corrections_file: "Path | None" = None,
) -> str:
    """Walk through weak sentences one at a time. Returns the updated letter."""
    from pathlib import Path
    from rich.panel import Panel
    from coverletter.corrections import find_source_paragraph, save_correction

    with Live(Spinner("dots", text="Analyzing sentences..."), refresh_per_second=10, console=console):
        issues = analyze_letter(letter_text, api_key, model)

    if not issues:
        console.print("[green]Coaching: no weak sentences found.[/green]")
        return letter_text

    console.print(f"\n[bold]{len(issues)} sentence(s) flagged.[/bold]\n")
    console.print("[dim]For each: type a direction, type your replacement, or mix both. Press Enter to keep.[/dim]\n")

    current = letter_text
    for i, item in enumerate(issues, 1):
        if item.sentence not in current:
            continue

        console.print(f"[bold cyan]{i}/{len(issues)}[/bold cyan]  [yellow]{item.issue}[/yellow]")
        console.print(Panel(item.sentence, border_style="dim"))

        _flush_stdin()
        user_input = input("> ").strip()

        if not user_input:
            console.print("[dim]→ Kept.[/dim]\n")
            continue

        with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
            context = get_context(current, item.sentence)
            rewritten = rewrite_sentence(item.sentence, context, item.issue, user_input, api_key, model)

        while True:
            console.print(f"[green]→ {rewritten}[/green]")
            confirm = _prompt_choice("[A]ccept  [K]eep original  [R]edirect: ", {"a", "k", "r"})
            if confirm == "a":
                current = current.replace(item.sentence, rewritten, 1)
                console.print("[dim]→ Applied.[/dim]\n")
                # Offer to persist if sentence came from source (search corrected text first, then originals)
                if all_paragraphs and corrections_file:
                    search_pool = (corrected_paragraphs or []) + (all_paragraphs or [])
                    source = find_source_paragraph(item.sentence, search_pool)
                    if source:
                        src_filename = "library_refined.md" if source.layer == 0 else "library.md"
                        _flush_stdin()
                        save_it = input("Save this fix for future letters? [Y/n]: ").strip().lower()
                        if save_it in ("", "y", "yes"):
                            save_correction(corrections_file, source, item.sentence, rewritten, src_filename)
                            console.print("[dim]→ Correction saved.[/dim]\n")
                break
            elif confirm == "k":
                console.print("[dim]→ Kept original.[/dim]\n")
                break
            else:
                _flush_stdin()
                new_direction = input("New direction: ").strip()
                if not new_direction:
                    console.print("[dim]→ Kept original.[/dim]\n")
                    break
                with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
                    context = get_context(current, item.sentence)
                    rewritten = rewrite_sentence(item.sentence, context, item.issue, new_direction, api_key, model)

    return current


_QUESTION_SIGNALS = [
    "before i revise", "i need to ask", "a few questions", "can you clarify",
    "could you clarify", "can you tell me", "could you tell me", "what was",
    "what were", "what is", "what are", "answer what you can",
]


def _is_question_response(text: str) -> bool:
    lower = text.lower()
    question_count = lower.count("?")
    if question_count >= 2:
        return True
    return any(signal in lower for signal in _QUESTION_SIGNALS)


MAX_VERIFY_ATTEMPTS = 4


def _outline_alignment_report(outline: dict, letter_text: str) -> None:
    """Print which outline blocks made it into the letter vs. were dropped."""
    letter_lower = letter_text.lower()
    covered: list[str] = []
    dropped: list[str] = []

    for para in outline.get("paragraphs", []):
        label = para.get("label", "unlabeled")
        claims = para.get("claims", [])
        # A block is considered present if at least one anchor phrase appears in the letter
        anchors = [a for c in claims for a in c.get("anchors", [])]
        if anchors:
            hit = any(a.lower() in letter_lower for a in anchors)
        else:
            # No anchors — fall back to checking claim text fragments
            hit = any(
                len(c.get("text", "")) > 20 and c["text"][:30].lower() in letter_lower
                for c in claims
            )
        (covered if hit else dropped).append(label)

    if covered:
        console.print("[bold]Outline coverage:[/bold]")
        for label in covered:
            console.print(f"  [green]✓[/green] {label}")
    if dropped:
        for label in dropped:
            console.print(f"  [yellow]–[/yellow] {label} [dim](not detected in letter)[/dim]")
    if not covered and not dropped:
        console.print("[dim]No outline blocks to check.[/dim]")
    console.print()


def _run_verification(
    letter_text: str,
    messages: list[dict[str, str]],
    api_key: str,
    model: str,
    source_paragraphs: list[Paragraph] | None = None,
    evidence_sentences: list[str] | None = None,
) -> None:
    """Verify and propose fixes for human review — no silent auto-revision.

    Runs two checks in one pass:
    - Quality check (LLM): list-pile endings, generic body openers, AI/template prose
    - Verbatim check (deterministic): body sentences not traceable to any source paragraph

    Both sets of failures are surfaced together and fixed in a single proposed revision.
    """
    from rich.rule import Rule
    current = messages[-1]["content"]

    with Live(Spinner("dots", text="Checking quality and evidence grounding..."), refresh_per_second=10, console=console):
        result = verify_letter(current, api_key, model)
        verbatim_violations = verbatim_check(
            current, source_paragraphs or [],
            evidence_sentences=evidence_sentences,
        ) if (source_paragraphs or evidence_sentences) else []

    quality_failures = result.failures
    total_issues = len(quality_failures) + len(verbatim_violations)

    if total_issues == 0:
        console.print("[green]Quality check: PASS[/green]")
        return

    # Display all issues
    if quality_failures:
        console.print(f"\n[yellow]Quality issues ({len(quality_failures)}):[/yellow]")
        for f in quality_failures:
            console.print(f"  [yellow]• {f}[/yellow]")

    if verbatim_violations:
        console.print(f"\n[bold red]Ungrounded sentences ({len(verbatim_violations)}) — no evidence basis found:[/bold red]")
        for v in verbatim_violations:
            console.print(f"  [red]• {v.sentence[:120]}[/red]")
            console.print(f"    [dim]closest source ({v.score:.0%}): {v.best_match[:100]}[/dim]")

    # Build unified feedback prompt
    feedback_parts = ["FIX REQUIRED. Address all violations below.\n"]

    if quality_failures:
        feedback_parts.append("QUALITY VIOLATIONS — fix each using the minimal change possible:")
        feedback_parts.append("- Stay as close to the existing language as you can")
        feedback_parts.append("- Do not add any claim or language not already present in the letter")
        feedback_parts.append("- Do not introduce new violations")
        feedback_parts.append("")
        for f in quality_failures:
            feedback_parts.append(f"  - {f}")
        feedback_parts.append("")

    if verbatim_violations:
        feedback_parts.append("INVENTED SENTENCES — these body sentences were not found in the source library.")
        feedback_parts.append("For each: replace it with a sentence already in the source that serves the same")
        feedback_parts.append("purpose, or cut it entirely. Do not paraphrase source language — lift it directly.")
        feedback_parts.append("")
        for v in verbatim_violations:
            feedback_parts.append(f"  - \"{v.sentence}\"")
        feedback_parts.append("")

    feedback_parts.append(
        "If a violation cannot be fixed without inventing new language, leave the sentence "
        "as-is and add a comment after the letter: 'COULD NOT FIX: [quote the sentence]'"
    )
    feedback = "\n".join(feedback_parts)

    console.print()
    with Live(Spinner("dots", text="Proposing fixes..."), refresh_per_second=10, console=console):
        parts: list[str] = []
        for chunk in stream_revision(SYSTEM_PROMPT, messages, feedback, api_key, model):
            parts.append(chunk)

    proposed = "".join(parts)

    # Surface any sentences the model flagged as unfixable
    unfixable = [
        line.replace("COULD NOT FIX:", "").strip()
        for line in proposed.splitlines()
        if line.strip().startswith("COULD NOT FIX:")
    ]
    proposed_clean = "\n".join(
        line for line in proposed.splitlines()
        if not line.strip().startswith("COULD NOT FIX:")
    ).strip()

    console.print()
    console.print(Rule("[bold]Proposed fix[/bold]", style="yellow"))
    render_letter(proposed_clean)

    if unfixable:
        console.print("\n[yellow]Model could not fix without inventing language:[/yellow]")
        for s in unfixable:
            console.print(f"  [dim]• {s}[/dim]")
        console.print("[dim]Use the revision loop to address these manually.[/dim]\n")

    console.print()
    _flush_stdin()
    choice = _prompt_choice(
        "[A]ccept fix  [E]nter revision loop (keep current, fix manually)  [S]kip (keep current, ignore): ",
        {"a", "e", "s"},
    )

    if choice == "a":
        messages.append({"role": "user", "content": feedback})
        messages.append({"role": "assistant", "content": proposed_clean})
        # Re-check both after accepting
        with Live(Spinner("dots", text="Re-checking..."), refresh_per_second=10, console=console):
            recheck = verify_letter(proposed_clean, api_key, model)
            recheck_verbatim = verbatim_check(
                proposed_clean, source_paragraphs or [],
                evidence_sentences=evidence_sentences,
            ) if (source_paragraphs or evidence_sentences) else []
        remaining = len(recheck.failures) + len(recheck_verbatim)
        if remaining == 0:
            console.print("[green]Quality check: PASS[/green]")
        else:
            console.print(f"[yellow]Still {remaining} issue(s) — use the revision loop to resolve.[/yellow]")
            for f in recheck.failures:
                console.print(f"  [dim]• {f}[/dim]")
            for v in recheck_verbatim:
                console.print(f"  [dim]• Invented: {v.sentence[:100]}[/dim]")
    elif choice == "e":
        # E = "I'll handle this myself" — do NOT accept proposed_clean.
        # Keep the current letter; user addresses issues in the revision loop.
        console.print("[dim]Current letter kept. Address issues in the revision loop below.[/dim]")
    else:
        console.print("[dim]Skipping fix. Current letter kept.[/dim]")


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs MD file")
@click.option("--output", "-o", default=None, help="Directory to save output")
@click.option("--model", "-m", default=None, help="Claude model to use")
@click.option("--role", "-r", default=None, help="Role to filter paragraphs by (skip prompt)")
@click.option("--template", "-t", default=None, help="Name (or substring) of a previous letter to use as template")
@click.option("--resume", "-R", default=None, help="Path to resume file (.pdf, .md, or .txt)")
@click.option("--no-save", is_flag=True, default=False, help="Skip saving to file")
@click.option("--fast", "-f", is_flag=True, default=False, help="Skip thesis and alignment — generate, review, and revise only")
def main(
    ctx: click.Context,
    paragraphs: str | None,
    output: str | None,
    model: str | None,
    role: str | None,
    template: str | None,
    resume: str | None,
    no_save: bool,
    fast: bool,
) -> None:
    """Cover letter generator — builds argument-driven letters from your evidence library."""
    if ctx.invoked_subcommand is not None:
        ctx.ensure_object(dict)
        ctx.obj["paragraphs"] = paragraphs
        return

    cfg = load_config(paragraphs, output, model, resume)
    profile = load_profile(cfg.profile_file)

    console.print(f"\n[bold blue]Cover Letter Generator[/bold blue]")

    all_paragraphs = load_paragraphs(cfg.paragraphs_files)
    stats = library_stats(all_paragraphs)
    total = sum(sum(s.values()) for s in stats.values())
    role_count = len(stats)

    prefilter_label = "semantic (Voyage)" if cfg.voyage_api_key else "keyword"
    files_label = " + ".join(f.name for f in cfg.paragraphs_files)
    console.print(
        f"Using: [dim]{files_label}[/dim] "
        f"([green]{total} paragraphs[/green] across {role_count} role(s)) "
        f"[dim]prefilter: {prefilter_label}[/dim]"
    )

    resume_text = load_resume(cfg.resume_file)
    if resume_text:
        console.print(f"Resume: [dim]{cfg.resume_file}[/dim]")
    else:
        console.print(f"[dim]No resume found at {cfg.resume_file} — use --resume to set path[/dim]")

    if profile.is_empty:
        console.print(f"[dim]No candidate profile — fill in candidate_profile.toml for goal-aware thesis and alignment[/dim]")
    else:
        sig_note = f", {len(profile.seniority_signals)} seniority signal(s)" if profile.seniority_signals else " [yellow]— no seniority signals set[/yellow]"
        console.print(f"Profile: [dim]{cfg.profile_file}[/dim] ([green]{len(profile.goals)} goal(s), {len(profile.differentiators)} differentiator(s){sig_note}[/green])")

    # Role selection
    if role is None:
        role = select_role(all_paragraphs)

    role_paragraphs = filter_by_role(all_paragraphs, role) if role else all_paragraphs
    if role:
        role_total = len(role_paragraphs)
        console.print(f"Role: [bold]{role}[/bold] + General → {role_total} paragraphs available")

    # Template resolution
    template_text: str | None = None
    if template:
        tpath = _find_template(cfg.output_dir, template)
        if tpath:
            template_text = tpath.read_text(encoding="utf-8")
            console.print(f"Template: [dim]{tpath.name}[/dim]")
        else:
            console.print(f"[yellow]No template found matching '{template}' — continuing without.[/yellow]")

    job_description = read_job_description(
        jds_dir=cfg.paragraphs_files[0].parent / "jds",
    )

    _flush_stdin()
    company = input("\nCompany name (for filename, optional): ").strip()

    notes: str | None = None
    if template_text:
        _flush_stdin()
        raw_notes = input(
            "\nApplication notes (paragraphs to include, phrasing to emphasize — optional, Enter to skip): "
        ).strip()
        notes = raw_notes or None

    from coverletter.provider import get_embed_provider as _get_ep, get_provider as _get_provider
    _provider = _get_provider(cfg.model, cfg.api_key)
    _embed_provider = _get_ep(cfg.embed_model) or _provider
    if cfg.voyage_api_key or _embed_provider.supports_embed() or _embed_provider.supports_hybrid():
        filtered = embed_prefilter(role_paragraphs, job_description, cfg.top_n, cfg.voyage_api_key or "", _embed_provider)
    else:
        filtered = prefilter(role_paragraphs, job_description, cfg.top_n)

    # Apply known corrections to paragraph text before sending to the LLM
    from coverletter.corrections import apply_corrections, load_corrections
    corrections_file = cfg.paragraphs_files[0].parent / "corrections.md"
    corrections = load_corrections(corrections_file)
    corrected = apply_corrections(filtered, corrections)
    if corrections:
        n_applied = sum(1 for a, b in zip(filtered, corrected) if a.text != b.text)
        if n_applied:
            console.print(f"[dim]Applied {n_applied} correction(s) from corrections.md[/dim]\n")

    # Generate provisional argument (beacon) from JD alone — before the letter exists.
    # This seeds sentence retrieval so the evidence is focused on what the letter must argue.
    provisional_argument: str | None = None
    if cfg.voyage_api_key and not fast:
        with Live(Spinner("dots", text="Deriving argument target..."), refresh_per_second=10, console=console):
            try:
                provisional_argument = generate_argument(
                    job_description, cfg.api_key, cfg.model, profile=profile
                )
            except Exception:
                provisional_argument = None
        if provisional_argument:
            console.print(f"[dim]Argument: {provisional_argument}[/dim]")

    # Re-rank corrected paragraphs by sentence-level relevance (for library ordering)
    # and build angle-organized argument evidence (for synthesis).
    # Auto-syncs any new paragraphs added since the last coverletter sync run.
    angle_evidence: list[dict] | None = None
    evidence_sentences: list[str] = []
    _conn = None  # DB connection — kept in scope for the post-gap-loop regeneration path
    if cfg.voyage_api_key:
        try:
            from coverletter.db import (
                open_db, db_path, paragraph_hash,
                sync_from_markdown, compute_embeddings,
                extract_and_store_sentences, compute_sentence_embeddings,
                assign_angles_canonical,
                rank_paragraphs_by_sentences, build_angle_evidence,
            )
            _db = db_path(cfg.paragraphs_files)
            if _db.exists():
                _conn = open_db(_db)

                # Detect paragraphs added since the last sync
                all_hashes = {paragraph_hash(p.text) for p in all_paragraphs}
                existing_hashes = {
                    row[0] for row in _conn.execute(
                        "SELECT text_hash FROM paragraphs WHERE active = 1"
                    )
                }
                new_count = len(all_hashes - existing_hashes)
                if new_count:
                    with Live(
                        Spinner("dots", text=f"Syncing {new_count} new paragraph(s) to DB..."),
                        refresh_per_second=10, console=console,
                    ):
                        sync_from_markdown(_conn, all_paragraphs, cfg.paragraphs_files)
                        compute_embeddings(_conn, cfg.voyage_api_key)
                        extract_and_store_sentences(_conn)
                        compute_sentence_embeddings(_conn, cfg.voyage_api_key)
                        assign_angles_canonical(_conn, cfg.voyage_api_key)
                    console.print(f"[dim]Synced {new_count} new paragraph(s).[/dim]")

                # Re-rank library paragraphs by sentence-level precision
                sentence_scores = rank_paragraphs_by_sentences(
                    _conn, job_description, cfg.voyage_api_key
                )
                if sentence_scores:
                    def _sent_score(p: Paragraph) -> float:
                        return sentence_scores.get(paragraph_hash(p.text), 0.0)
                    corrected = sorted(corrected, key=_sent_score, reverse=True)

                # Build argument evidence organized by angle.
                # thesis_text focuses retrieval on the argument target — not just JD vocabulary.
                angle_evidence = build_angle_evidence(
                    _conn, job_description, cfg.voyage_api_key,
                    top_angles=4, sentences_per_angle=3,
                    thesis_text=provisional_argument,
                )
                if angle_evidence:
                    n_sents = sum(len(a["sentences"]) for a in angle_evidence)
                    console.print(f"[dim]Argument evidence: {len(angle_evidence)} angles, {n_sents} sentences[/dim]")
                    # Extract the flat sentence list as evidence grounding for verification.
                    # Model was given exactly these sentences; any body sentence not
                    # matching them is genuinely invented.
                    for block in angle_evidence:
                        for entry in block["sentences"]:
                            if entry["context_before"]:
                                evidence_sentences.append(entry["context_before"])
                            evidence_sentences.append(entry["text"])
                            if entry["context_after"]:
                                evidence_sentences.append(entry["context_after"])
        except Exception:
            pass

    user_message = build_user_message(
        job_description, corrected, role=role, company=company,
        resume=resume_text or None,
        template=template_text, notes=notes,
        angle_evidence=angle_evidence,
        argument=provisional_argument,
    )

    # Build conversation history — enables revision loop
    # content is a list of blocks (structured) for the first user message to enable caching
    messages: list[dict] = [{"role": "user", "content": user_message}]

    console.print()
    with Live(Spinner("dots", text="Generating..."), refresh_per_second=10, console=console):
        parts: list[str] = []
        for chunk in stream_cover_letter(SYSTEM_PROMPT, user_message, cfg.api_key, cfg.model):
            parts.append(chunk)

    letter_text = "".join(parts)
    messages.append({"role": "assistant", "content": letter_text})
    console.print(f"[dim]{running_total()}[/dim]")
    render_letter(letter_text)

    _run_verification(
        letter_text, messages, cfg.api_key, cfg.model,
        source_paragraphs=filtered,
        evidence_sentences=evidence_sentences or None,
    )
    letter_text = messages[-1]["content"]

    if not fast:
        # Letter thesis — what argument is this letter actually making?
        console.print()
        with Live(Spinner("dots", text="Identifying letter thesis..."), refresh_per_second=10, console=console):
            thesis = generate_thesis(job_description, letter_text, cfg.api_key, cfg.model, profile=profile)
        console.print(f"[dim]{running_total()}[/dim]")
        from rich.panel import Panel
        console.print(Panel(f"[bold]Letter thesis:[/bold] {thesis}", border_style="cyan", title="Argument"))
        _flush_stdin()
        thesis_ok = input("Accept this argument? [Y / type a correction]: ").strip()
        while thesis_ok.lower() not in ("", "y", "yes"):
            correction = thesis_ok
            console.print(f"[dim]Regenerating...[/dim]")
            with Live(Spinner("dots", text="Revising thesis..."), refresh_per_second=10, console=console):
                thesis = generate_thesis(job_description, letter_text, cfg.api_key, cfg.model, profile=profile, correction=correction)
            console.print(f"[dim]{running_total()}[/dim]")
            console.print(Panel(f"[bold]Letter thesis:[/bold] {thesis}", border_style="cyan", title="Argument"))
            _flush_stdin()
            thesis_ok = input("Accept this argument? [Y / type another correction]: ").strip()

        # Alignment report + gap loop
        console.print()
        with Live(Spinner("dots", text="Analyzing JD alignment..."), refresh_per_second=10, console=console):
            report = alignment_report(job_description, letter_text, filtered, cfg.api_key, cfg.model, profile=profile)
        console.print(f"[dim]{running_total()}[/dim]")

        from rich.panel import Panel
        _show_alignment(report)

        new_paragraphs_saved = 0
        if report.gaps or report.seniority_gaps:
            gap_priority_file = cfg.paragraphs_files[-1].parent / "library_refined.md"
            new_paragraphs_saved = _gap_loop(
                report.gaps, all_paragraphs, gap_priority_file, cfg, job_description,
                seniority_gaps=report.seniority_gaps,
                resume_text=resume_text or "",
            )

        # Regenerate if new paragraphs were saved
        if new_paragraphs_saved:
            _flush_stdin()
            regen = input(f"\nSaved {new_paragraphs_saved} new paragraph(s). Regenerate letter with new material? [Y/n]: ").strip().lower()
            if regen in ("", "y", "yes"):
                all_paragraphs = load_paragraphs(cfg.paragraphs_files)
                role_paragraphs = filter_by_role(all_paragraphs, role) if role else all_paragraphs
                if cfg.voyage_api_key or _embed_provider.supports_embed() or _embed_provider.supports_hybrid():
                    filtered = embed_prefilter(role_paragraphs, job_description, cfg.top_n, cfg.voyage_api_key or "", _embed_provider)
                else:
                    filtered = prefilter(role_paragraphs, job_description, cfg.top_n)
                corrections = load_corrections(corrections_file)
                corrected = apply_corrections(filtered, corrections)

                # Re-sync newly saved paragraphs into the DB and rebuild angle evidence
                # so synthesis mode can use the gap paragraphs just written.
                regen_angle_evidence: list[dict] | None = angle_evidence
                regen_evidence_sentences: list[str] = evidence_sentences
                if cfg.voyage_api_key and _conn is not None:
                    try:
                        all_hashes_regen = {paragraph_hash(p.text) for p in all_paragraphs}
                        existing_hashes_regen = {
                            row[0] for row in _conn.execute(
                                "SELECT text_hash FROM paragraphs WHERE active = 1"
                            )
                        }
                        new_regen_count = len(all_hashes_regen - existing_hashes_regen)
                        if new_regen_count:
                            with Live(
                                Spinner("dots", text=f"Syncing {new_regen_count} new paragraph(s)..."),
                                refresh_per_second=10, console=console,
                            ):
                                sync_from_markdown(_conn, all_paragraphs, cfg.paragraphs_files)
                                compute_embeddings(_conn, cfg.voyage_api_key)
                                extract_and_store_sentences(_conn)
                                compute_sentence_embeddings(_conn, cfg.voyage_api_key)
                                assign_angles_canonical(_conn, cfg.voyage_api_key)
                        # Rebuild angle evidence with newly-added paragraphs
                        with Live(Spinner("dots", text="Rebuilding argument evidence..."), refresh_per_second=10, console=console):
                            regen_angle_evidence = build_angle_evidence(
                                _conn, job_description, cfg.voyage_api_key,
                                top_angles=4, sentences_per_angle=3,
                                thesis_text=provisional_argument,
                            )
                        regen_evidence_sentences = []
                        if regen_angle_evidence:
                            for block in regen_angle_evidence:
                                for entry in block["sentences"]:
                                    if entry["context_before"]:
                                        regen_evidence_sentences.append(entry["context_before"])
                                    regen_evidence_sentences.append(entry["text"])
                                    if entry["context_after"]:
                                        regen_evidence_sentences.append(entry["context_after"])
                            n_sents = sum(len(a["sentences"]) for a in regen_angle_evidence)
                            console.print(f"[dim]Argument evidence: {len(regen_angle_evidence)} angles, {n_sents} sentences[/dim]")
                    except Exception:
                        pass

                user_message = build_user_message(
                    job_description, corrected, role=role, company=company,
                    resume=resume_text or None, template=template_text, notes=notes,
                    angle_evidence=regen_angle_evidence,
                    argument=provisional_argument,
                )
                messages = [{"role": "user", "content": user_message}]
                console.print()
                with Live(Spinner("dots", text="Regenerating..."), refresh_per_second=10, console=console):
                    parts = []
                    for chunk in stream_cover_letter(SYSTEM_PROMPT, user_message, cfg.api_key, cfg.model):
                        parts.append(chunk)
                letter_text = "".join(parts)
                messages.append({"role": "assistant", "content": letter_text})
                render_letter(letter_text)
                _run_verification(
                    letter_text, messages, cfg.api_key, cfg.model,
                    source_paragraphs=filtered,
                    evidence_sentences=regen_evidence_sentences or None,
                )
                letter_text = messages[-1]["content"]
                console.print()
                with Live(Spinner("dots", text="Re-analyzing alignment..."), refresh_per_second=10, console=console):
                    new_report = alignment_report(job_description, letter_text, filtered, cfg.api_key, cfg.model, profile=profile)
                _show_alignment(new_report)

    # Optional coaching pass
    _flush_stdin()
    do_coach = input("\nRun coaching pass (sentence-level review)? [y/N]: ").strip().lower()
    if do_coach in ("y", "yes"):
        letter_text = _coaching_pass(
            letter_text, cfg.api_key, cfg.model,
            all_paragraphs=all_paragraphs,
            corrected_paragraphs=corrected,
            corrections_file=corrections_file,
        )
        render_letter(letter_text)
    messages[-1] = {"role": "assistant", "content": letter_text}

    # Revision loop — targeted paragraph editing or global feedback
    _rejection_note: str = ""
    while True:
        letter_paras = [p.strip() for p in letter_text.split("\n\n") if p.strip()]
        console.print()
        console.print("[dim]Paragraphs:[/dim]")
        for i, p in enumerate(letter_paras, 1):
            preview = p.replace("\n", " ")
            if len(preview) > 90:
                preview = preview[:87] + "..."
            console.print(f"  [cyan]{i}[/cyan]  [dim]{preview}[/dim]")
        console.print()
        if _rejection_note:
            console.print(f"[dim]Previous rejection: {_rejection_note}[/dim]")
        console.print("[dim]Enter a paragraph number to target it, free text for global feedback, or Enter to finish:[/dim]")
        _flush_stdin()
        feedback = input("> ").strip()

        if not feedback:
            break

        # Targeted paragraph editing
        rejection_prefix = (
            f"Previous revision was rejected ({_rejection_note}). " if _rejection_note else ""
        )
        _rejection_note = ""
        try:
            para_idx = int(feedback) - 1
            if 0 <= para_idx < len(letter_paras):
                target_para = letter_paras[para_idx]
                console.print()
                console.print(Panel(target_para, border_style="cyan", title=f"Paragraph {para_idx + 1}"))
                _flush_stdin()
                targeted = input("How to revise this paragraph (or Enter to cancel): ").strip()
                if not targeted:
                    continue
                feedback = targeted
                wrapped_feedback = (
                    f"{rejection_prefix}REVISE ONLY paragraph {para_idx + 1} of the letter. "
                    f"That paragraph currently reads:\n\n{target_para}\n\n"
                    f"Instruction: {targeted}\n\n"
                    "Leave every other paragraph completely unchanged. "
                    "Output only the complete revised cover letter — no questions, no commentary, no preamble."
                )
            else:
                raise ValueError
        except ValueError:
            wrapped_feedback = (
                f"{rejection_prefix}REVISE THE LETTER using the information below. "
                "Output only the complete revised cover letter — no questions, no commentary, no preamble.\n\n"
                + feedback
            )

        console.print()
        with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
            parts = []
            for chunk in stream_revision(SYSTEM_PROMPT, messages, wrapped_feedback, cfg.api_key, cfg.model):
                parts.append(chunk)

        revised_text = "".join(parts)

        if _is_question_response(revised_text):
            console.print("[yellow]Forcing revision — model tried to ask questions...[/yellow]")
            forced = (
                "You asked questions instead of revising. Output the complete revised cover letter now. "
                "Use only what is in the source material, resume, and this feedback:\n" + feedback
            )
            with Live(Spinner("dots", text="Re-revising..."), refresh_per_second=10, console=console):
                parts = []
                for chunk in stream_revision(SYSTEM_PROMPT, messages, forced, cfg.api_key, cfg.model):
                    parts.append(chunk)
            revised_text = "".join(parts)

        render_letter(revised_text)
        _flush_stdin()
        accept = input("[A]ccept / [R]eject: ").strip().lower()
        if accept in ("", "a", "accept", "y", "yes"):
            letter_text = revised_text
            messages.append({"role": "user", "content": wrapped_feedback})
            messages.append({"role": "assistant", "content": letter_text})
        else:
            # Keep the rejected attempt in message history so the model knows what it tried
            messages.append({"role": "user", "content": wrapped_feedback})
            messages.append({"role": "assistant", "content": revised_text})
            _flush_stdin()
            _rejection_note = input("Why didn't this work? (Enter to skip): ").strip()

    from coverletter.costs import session_summary
    summary = session_summary()
    if summary:
        console.print(f"[dim]Session cost: {summary}[/dim]\n")

    if not no_save:
        _flush_stdin()
        save_it = input(
            f"Save to {cfg.output_dir}? [Y/n]: "
        ).strip().lower()
        if save_it in ("", "y", "yes"):
            label = company or (role or "letter")
            saved_md = save_letter(letter_text, cfg.output_dir, label, cfg.author_name)
            console.print(f"[green]Saved (MD):[/green] {saved_md}")
            saved_pdf = save_pdf(letter_text, cfg.output_dir, label, cfg.author_name)
            console.print(f"[green]Saved (PDF):[/green] {saved_pdf}\n")

            # Offer resume generation for the same application.
            typ_path = cfg.resume_typ_file if hasattr(cfg, "resume_typ_file") else None
            if typ_path and Path(typ_path).exists():
                _flush_stdin()
                make_resume = input("Generate a tailored resume for this application? [y/N]: ").strip().lower()
                if make_resume in ("y", "yes"):
                    ctx.invoke(
                        main.commands["resume"],
                        paragraphs=cfg.paragraphs_files[0].as_posix() if cfg.paragraphs_files else None,
                        company=company or None,
                        base=None,
                        bullets_file=None,
                    )


def _qa_session(
    topic: str,
    all_paragraphs: "list[Paragraph]",
    priority_file: "Path",
    cfg: "Config",
    job_description: str | None = None,
    gap_description: str | None = None,
    voyage_api_key: str = "",
    resume_text: str = "",
) -> str | None:
    """Interactive Q&A session. Returns accepted paragraph text or None."""
    from rich.panel import Panel
    from coverletter.build import _build_initial_context, qa_turn, force_draft, append_to_library
    from coverletter.experiences import load_experiences, find_experience, coverage_context

    experiences = load_experiences(cfg.experiences_file)
    exp = find_experience(experiences, topic)
    framing_ctx = coverage_context(exp, all_paragraphs) if exp else ""

    if exp and framing_ctx:
        console.print(f"[dim]Experience matched: {exp.name}[/dim]")
        coverage = {}
        from coverletter.experiences import framing_coverage
        coverage = framing_coverage(exp, all_paragraphs)
        missing = [a for a, c in coverage.items() if not c]
        if missing:
            console.print(f"[dim]Missing angles: {', '.join(missing)}[/dim]")

    from coverletter.provider import parse_model
    _use_tools = parse_model(cfg.model)[0] == "anthropic"
    context = _build_initial_context(
        topic, job_description, gap_description,
        framing_context=framing_ctx,
        resume_context=resume_text,
        use_tools=_use_tools,
    )
    history: list[dict] = [{"role": "user", "content": context}]

    console.print(f"\n[bold blue]Building:[/bold blue] {topic}")
    console.print("[dim]Answer the questions. 'draft' to draft now. 'done' to exit.[/dim]\n")

    with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, console=console):
        pending_draft, question = qa_turn(history, cfg.api_key, cfg.model, all_paragraphs, voyage_api_key=voyage_api_key)
    console.print(f"[dim]{running_total()}[/dim]")

    if question:
        console.print(f"[cyan]{question}[/cyan]\n")
        history.append({"role": "assistant", "content": question})

    accepted: str | None = None
    exchange_count = 0
    MAX_EXCHANGES = 2

    while True:
        if pending_draft is not None:
            # Show draft — A/R/K, no user input needed first
            console.print(Panel(pending_draft, border_style="green", title="Draft"))
            choice = _prompt_choice("[A]ccept  [R]edirect  [K]eep talking: ", {"a", "r", "k"})

            if choice == "a":
                accepted = pending_draft
                break

            elif choice == "r":
                redirect = _read_multiline("Direction: ")
                if not redirect:
                    continue
                RULES_REMINDER = (
                    "Revise the draft per the direction above.\n\n"
                    "This is a CAPTURE revision — preserve everything, do not polish.\n"
                    "DO NOT INVENT: every claim must trace to this conversation, not library results.\n"
                    "USE THEIR WORDS: their language and level of abstraction, not resume speak.\n"
                    "INCLUDE ALL DETAIL: every specific technical detail, fact, and explanation "
                    "the person provided must appear in full — including everything in this redirect. "
                    "Do not compress, summarize, or cut any of it. Length is fine.\n"
                    "DO NOT EDITORIALIZE: do not add framing or conclusions the person did not provide."
                )
                history.append({"role": "assistant", "content": pending_draft})
                history.append({"role": "user", "content": f"Revise the draft: {redirect}\n\n{RULES_REMINDER}"})
                with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
                    # Use qa_turn directly — history already ends with the revision instruction.
                    # force_draft would append a second user message, causing the model to ignore the redirect.
                    _draft_r, _raw_r = qa_turn(history, cfg.api_key, cfg.model, all_paragraphs, voyage_api_key=voyage_api_key)
                    pending_draft = _draft_r or _raw_r or ""

            elif choice == "k":
                history.append({"role": "assistant", "content": pending_draft})
                history.append({"role": "user", "content": "Let's keep going — what else do you need?"})
                pending_draft = None
                with Live(Spinner("dots", text="Continuing..."), refresh_per_second=10, console=console):
                    _, question = qa_turn(history, cfg.api_key, cfg.model, all_paragraphs, voyage_api_key=voyage_api_key)
                if question:
                    console.print(f"\n[cyan]{question}[/cyan]\n")
                    history.append({"role": "assistant", "content": question})

        else:
            # Waiting for user answer — do NOT flush here; user may have typed while spinner ran
            user_input = _read_multiline()

            if not user_input or user_input.lower() == "done":
                break

            if user_input.lower() == "draft":
                with Live(Spinner("dots", text="Drafting..."), refresh_per_second=10, console=console):
                    pending_draft = force_draft(history, cfg.api_key, cfg.model, all_paragraphs, voyage_api_key=voyage_api_key)
            else:
                history.append({"role": "user", "content": user_input})
                exchange_count += 1
                if exchange_count >= MAX_EXCHANGES:
                    with Live(Spinner("dots", text="Drafting..."), refresh_per_second=10, console=console):
                        pending_draft = force_draft(history, cfg.api_key, cfg.model, all_paragraphs, voyage_api_key=voyage_api_key)
                else:
                    with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, console=console):
                        pending_draft, question = qa_turn(history, cfg.api_key, cfg.model, all_paragraphs, voyage_api_key=voyage_api_key)
                    if question:
                        console.print(f"\n[cyan]{question}[/cyan]\n")
                        history.append({"role": "assistant", "content": question})

    if not accepted:
        return None

    # Derive a short default section name from the topic
    short_topic = topic.split(" — ")[0].split(" - ")[0].strip()
    if len(short_topic) > 40:
        short_topic = short_topic[:40].rsplit(" ", 1)[0]
    short_topic = short_topic.rstrip(" ,;:")

    console.print()
    console.print("[bold]Where should this go?[/bold]")
    console.print("[dim]Press Enter to accept the default shown in brackets.[/dim]\n")

    _flush_stdin()
    save_role = input("Role [Data Engineer]: ").strip() or "Data Engineer"
    _flush_stdin()
    save_section = input(f"Section [{short_topic}]: ").strip() or short_topic
    _flush_stdin()
    angle = input("Angle tag (optional, e.g. compliance, ownership): ").strip()
    _flush_stdin()
    strength = input("Strength [high]: ").strip() or "high"

    meta: dict[str, str] = {"strength": strength, "via": "build"}
    if angle:
        meta["angle"] = angle

    append_to_library(priority_file, save_role, save_section, accepted, meta)
    console.print(f"\n[green]Saved to {priority_file.name}[/green] under {save_role} / {save_section}\n")

    # Save raw Q&A responses to DB — preserves the user's exact words before
    # they get compressed into the refined paragraph. Used by claim extraction.
    try:
        from coverletter.db import open_db, db_path, save_raw_response, paragraph_hash
        _raw_db = db_path(cfg.paragraphs_files)
        if _raw_db.exists():
            _raw_conn = open_db(_raw_db)
            save_raw_response(
                _raw_conn, history, topic,
                para_text_hash=paragraph_hash(accepted),
            )
    except Exception:
        pass  # raw response saving is best-effort — never block the save

    return accepted


@main.command("build")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs file")
@click.option("--about", "-a", default=None, help="What to build a paragraph about")
@click.option("--resume", "-R", default=None, help="Path to resume file (.pdf, .md, or .txt)")
@click.option("--jd", "jd_text", default=None, help="Job description text or path to a JD file — drives gap-first build mode")
@click.pass_context
def build_library(ctx: click.Context, paragraphs: str | None, about: str | None, resume: str | None, jd_text: str | None) -> None:
    """Grow your paragraph library through Q&A — add new experiences, projects, or angles.

    With --jd: analyzes the JD against your library, shows what's covered and what's missing,
    then walks you through filling gaps with targeted Q&A.

    Without --jd: prompts you for a topic and builds one paragraph at a time.
    """
    from pathlib import Path
    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs, resume_override=resume)
    all_paragraphs = load_paragraphs(cfg.paragraphs_files)
    # Build always saves to library_refined.md — the priority layer.
    # Seed saves raw extractions to library.md (base layer).
    # library_refined.md overrides library.md at generation time.
    # This is true even if library_refined.md doesn't exist yet — append_to_library creates it.
    base_file = cfg.paragraphs_files[-1]
    priority_file = base_file.parent / "library_refined.md"

    resume_text = load_resume(cfg.resume_file)
    if resume_text:
        console.print(f"Resume: [dim]{cfg.resume_file}[/dim]")

    console.print(f"\n[bold blue]Paragraph Builder[/bold blue]  [dim]→ {priority_file.name}[/dim]\n")

    # --- Gap-driven mode: JD provided ---
    if jd_text:
        # Accept either raw JD text or a file path
        jd_path = Path(jd_text)
        if jd_path.exists():
            job_description = jd_path.read_text(encoding="utf-8").strip()
        else:
            job_description = jd_text.strip()

        if not job_description:
            console.print("[yellow]JD is empty — exiting.[/yellow]")
            return

        from coverletter.align import library_gap_analysis
        from coverletter.db import open_db, db_path
        from coverletter.provider import get_embed_provider as _get_ep, get_provider as _get_provider
        _gen_provider = _get_provider(cfg.model, cfg.api_key)
        _embed_prov = _get_ep(cfg.embed_model) or _gen_provider
        _db = db_path(cfg.paragraphs_files)
        if not _db.exists():
            console.print(
                "[yellow]No claims DB found.[/yellow] Run [bold]coverletter sync[/bold] then "
                "[bold]coverletter extract[/bold] to build the DB before using --jd gap analysis."
            )
            return
        _conn = open_db(_db)
        console.print("[dim]Analyzing your library against the JD...[/dim]")
        with Live(Spinner("dots", text="Analyzing..."), refresh_per_second=10, console=console):
            result = library_gap_analysis(
                job_description, cfg.api_key, cfg.model,
                conn=_conn,
                voyage_api_key=cfg.voyage_api_key or "",
                embed_provider=_embed_prov,
            )
        _conn.close()

        if result.no_db:
            console.print(
                "[yellow]No embeddings found in DB.[/yellow] Run [bold]coverletter sync[/bold] "
                "to compute embeddings, then [bold]coverletter extract[/bold] to populate claims."
            )
            return

        # Show what's covered
        if result.covered:
            console.print(f"\n[bold green]Covered ({len(result.covered)}):[/bold green]")
            for item in result.covered:
                console.print(f"  [green]✓[/green] {item['requirement']}")
                if item.get("best_claim"):
                    console.print(f"    [dim]{item['best_claim'][:100]}[/dim]")
        else:
            console.print("\n[dim]Nothing in your library addresses this JD yet.[/dim]")

        # Show gaps
        if not result.gaps:
            console.print("\n[bold green]No gaps — your library covers this JD well.[/bold green]")
            return

        console.print(f"\n[bold red]Gaps ({len(result.gaps)}):[/bold red]")
        for i, gap in enumerate(result.gaps, 1):
            console.print(f"  [red]{i}.[/red] {gap['requirement']}")
            if gap.get("build_prompt"):
                console.print(f"    [dim]→ {gap['build_prompt']}[/dim]")

        # Let user pick which gaps to address
        _flush_stdin()
        raw = input(
            f"\nAddress which gaps? (e.g. 1,3 or 'all' or Enter to skip): "
        ).strip()
        if not raw:
            return
        if raw.lower() in ("all", "a"):
            selected_indices = set(range(1, len(result.gaps) + 1))
        else:
            try:
                selected_indices = {int(n.strip()) for n in raw.replace(" ", "").split(",") if n.strip().isdigit()}
            except ValueError:
                selected_indices = set()

        for i, gap in enumerate(result.gaps, 1):
            if i not in selected_indices:
                continue
            requirement = gap["requirement"]
            build_prompt = gap.get("build_prompt", "")
            # Seed the Q&A topic with the gap requirement; the build_prompt goes into the
            # initial context so the coach starts from a concrete angle rather than cold.
            seed_topic = requirement
            if build_prompt:
                seed_topic = f"{requirement}\n\nStarting angle: {build_prompt}"
            console.print(f"\n[bold]Gap {i}:[/bold] {requirement}")
            try:
                accepted = _qa_session(
                    seed_topic, all_paragraphs, priority_file, cfg,
                    job_description=job_description,
                    gap_description=requirement,
                    voyage_api_key=cfg.voyage_api_key,
                    resume_text=resume_text or "",
                )
            except KeyboardInterrupt:
                console.print("\n[dim]Stopped.[/dim]")
                break

            # Sync newly written paragraph into the DB so subsequent gap
            # sessions can see it in coverage scoring.
            if accepted:
                all_paragraphs = load_paragraphs(cfg.paragraphs_files)
                try:
                    from coverletter.db import (
                        open_db, db_path, sync_from_markdown, compute_embeddings,
                    )
                    _sync_db = db_path(cfg.paragraphs_files)
                    if _sync_db.exists():
                        _sync_conn = open_db(_sync_db)
                        sync_from_markdown(_sync_conn, all_paragraphs, cfg.paragraphs_files)
                        compute_embeddings(_sync_conn, cfg.voyage_api_key)
                        _sync_conn.close()
                        console.print("[dim]Synced new paragraph to DB.[/dim]")
                except Exception:
                    pass  # sync failure never blocks the build flow
        return

    # --- Manual mode: no JD ---
    topic = about
    if not topic:
        _flush_stdin()
        topic = input(
            "What do you want to build a paragraph about?\n"
            "(project name, experience, angle you haven't written yet, or gap to fill): "
        ).strip()

    if not topic:
        console.print("[yellow]Nothing to explore — exiting.[/yellow]")
        return

    while True:
        _qa_session(topic, all_paragraphs, priority_file, cfg, voyage_api_key=cfg.voyage_api_key, resume_text=resume_text or "")

        _flush_stdin()
        another = input("Build another paragraph? [Y/n]: ").strip().lower()
        if another in ("n", "no"):
            break

        _flush_stdin()
        topic = input("What next? (Enter to exit): ").strip()
        if not topic:
            break


@main.command("reflect")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs file")
@click.option("--about", "-a", default=None, help="What shift, through-line, or pivot to explore")
@click.option(
    "--angle",
    default=None,
    type=click.Choice(["through-line", "pivot", "reframe", "synthesis"], case_sensitive=False),
    help="Angle type (through-line, pivot, reframe, synthesis)",
)
@click.pass_context
def reflect(
    ctx: click.Context,
    paragraphs: str | None,
    about: str | None,
    angle: str | None,
) -> None:
    """Capture a career through-line, pivot, reframe, or synthesis through Q&A.

    These are perspective paragraphs — your voice connecting your arc together.
    They are the narrative frame the letter's argument depends on.

    Examples:
      coverletter reflect --about "shift from analyst to data engineer" --angle pivot
      coverletter reflect --about "through-line across all roles"
    """
    from coverletter.build import PERSPECTIVE_SYSTEM, qa_turn, force_draft, append_to_library
    from rich.panel import Panel
    from rich.rule import Rule

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)
    all_paragraphs = load_paragraphs(cfg.paragraphs_files)
    priority_file = cfg.paragraphs_files[-1].parent / "library_refined.md"

    console.print(f"\n[bold blue]Reflect[/bold blue]  [dim]→ {priority_file.name}[/dim]\n")
    console.print(
        "[dim]Capture the through-line, pivot, or synthesis that connects your experience.\n"
        "These paragraphs establish the argument. Evidence paragraphs substantiate it.[/dim]\n"
    )

    topic = about
    if not topic:
        _flush_stdin()
        topic = input(
            "What shift, through-line, or pivot do you want to capture?\n"
            "(e.g. 'analyst to engineer transition', 'what runs through all my work'): "
        ).strip()
    if not topic:
        console.print("[yellow]Nothing to explore — exiting.[/yellow]")
        return

    # Angle-specific context — what the agent is trying to surface differs per angle type
    _angle_context = {
        "through-line": (
            "I want to write a through-line paragraph — the thread that runs consistently "
            "across my whole career, regardless of what the job was called or what industry I was in. "
            "This is NOT a story about one job. It is what has been true about how I work and what "
            "I get called on to do across all of them."
        ),
        "pivot": (
            "I want to write a pivot paragraph — a specific career transition, what drove it, "
            "and what was happening right before I made the move."
        ),
        "reframe": (
            "I want to write a reframe paragraph — taking an experience that looked one way "
            "from the outside and showing what I was actually building or developing inside it."
        ),
        "synthesis": (
            "I want to write a synthesis paragraph — two paths from my background that combine "
            "into a specific capability that neither path would have produced on its own."
        ),
    }
    angle_description = _angle_context.get(angle or "", f"Angle type: {angle}." if angle else "")
    context = (
        f"Angle type: {angle or 'perspective'}\n\n"
        f"{angle_description}\n\n"
        f"Topic: {topic}"
    )
    history: list[dict] = [{"role": "user", "content": context}]

    console.print(f"[bold blue]Exploring:[/bold blue] {topic}")
    console.print("[dim]Answer the questions. 'draft' to draft now. 'done' to exit without saving.[/dim]\n")

    with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, console=console):
        pending_draft, question = qa_turn(
            history, cfg.api_key, cfg.model, all_paragraphs,
            voyage_api_key=cfg.voyage_api_key, system=PERSPECTIVE_SYSTEM,
        )
    console.print(f"[dim]{running_total()}[/dim]")

    if question:
        console.print(f"[cyan]{question}[/cyan]\n")
        history.append({"role": "assistant", "content": question})

    accepted: str | None = None
    exchange_count = 0

    while True:
        if pending_draft is not None:
            console.print(Panel(pending_draft, border_style="green", title="Draft"))
            choice = _prompt_choice("[A]ccept  [R]edirect  [K]eep talking: ", {"a", "r", "k"})

            if choice == "a":
                accepted = pending_draft
                break
            elif choice == "r":
                redirect = _read_multiline("Direction: ")
                if not redirect:
                    continue
                RULES_REMINDER = (
                    "Revise the draft per the direction above.\n\n"
                    "This is a CAPTURE revision — preserve everything, do not polish.\n"
                    "DO NOT INVENT: every claim must trace to this conversation, not library results.\n"
                    "USE THEIR WORDS: their language and level of abstraction, not resume speak.\n"
                    "INCLUDE ALL DETAIL: every specific technical detail, fact, and explanation "
                    "the person provided must appear in full — including everything in this redirect. "
                    "Do not compress, summarize, or cut any of it. Length is fine.\n"
                    "DO NOT EDITORIALIZE: do not add framing or conclusions the person did not provide."
                )
                history.append({"role": "assistant", "content": pending_draft})
                history.append({"role": "user", "content": f"Revise the draft: {redirect}\n\n{RULES_REMINDER}"})
                with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
                    # Use qa_turn directly — history already ends with the revision instruction.
                    # force_draft would append a second user message, causing the model to ignore the redirect.
                    _draft_r, _raw_r = qa_turn(history, cfg.api_key, cfg.model, all_paragraphs, voyage_api_key=cfg.voyage_api_key, system=PERSPECTIVE_SYSTEM)
                    pending_draft = _draft_r or _raw_r or ""
            elif choice == "k":
                history.append({"role": "assistant", "content": pending_draft})
                history.append({"role": "user", "content": "Keep going — what else do you need to know?"})
                pending_draft = None
                with Live(Spinner("dots", text="Continuing..."), refresh_per_second=10, console=console):
                    _, question = qa_turn(
                        history, cfg.api_key, cfg.model, all_paragraphs,
                        voyage_api_key=cfg.voyage_api_key, system=PERSPECTIVE_SYSTEM,
                    )
                if question:
                    console.print(f"\n[cyan]{question}[/cyan]\n")
                    history.append({"role": "assistant", "content": question})
        else:
            # Waiting for user answer — do NOT flush here; user may have typed while spinner ran
            user_input = _read_multiline()

            if not user_input or user_input.lower() == "done":
                break

            if user_input.lower() == "draft":
                with Live(Spinner("dots", text="Drafting..."), refresh_per_second=10, console=console):
                    pending_draft = force_draft(
                        history, cfg.api_key, cfg.model, all_paragraphs,
                        voyage_api_key=cfg.voyage_api_key, system=PERSPECTIVE_SYSTEM,
                    )
            else:
                history.append({"role": "user", "content": user_input})
                exchange_count += 1
                with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, console=console):
                    pending_draft, question = qa_turn(
                        history, cfg.api_key, cfg.model, all_paragraphs,
                        voyage_api_key=cfg.voyage_api_key, system=PERSPECTIVE_SYSTEM,
                    )
                if question and pending_draft is None:
                    console.print(f"\n[cyan]{question}[/cyan]\n")
                    history.append({"role": "assistant", "content": question})

    if not accepted:
        console.print("[dim]Nothing saved.[/dim]")
        return

    # Save — ask for role/section/angle
    console.print()
    console.print(Rule("[bold]Where should this go?[/bold]", style="cyan"))
    console.print("[dim]Press Enter to accept the default shown in brackets.[/dim]\n")

    _flush_stdin()
    save_role = input("Role [General]: ").strip() or "General"
    short_topic = topic.split(" — ")[0].split(" - ")[0].strip()
    if len(short_topic) > 40:
        short_topic = short_topic[:40].rsplit(" ", 1)[0]
    _flush_stdin()
    save_section = input(f"Section [{short_topic}]: ").strip() or short_topic

    # Angle — default to what was passed in, or prompt
    angle_choices = ["through-line", "pivot", "reframe", "synthesis"]
    if not angle:
        console.print(f"Angle type: {', '.join(angle_choices)}")
        _flush_stdin()
        angle_input = input("Angle [pivot]: ").strip().lower() or "pivot"
        angle = angle_input if angle_input in angle_choices else "pivot"

    meta: dict[str, str] = {"angle": angle, "via": "reflect"}
    append_to_library(priority_file, save_role, save_section, accepted, meta)
    console.print(f"\n[green]Saved to {priority_file.name}[/green] under {save_role} / {save_section}  [dim][angle={angle}][/dim]\n")


@main.command("intake")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs file")
@click.option("--mission", "mode", flag_value="mission", help="Capture a mission alignment paragraph")
@click.option("--evidence", "mode", flag_value="evidence", help="Capture a career evidence paragraph")
@click.pass_context
def intake(
    ctx: click.Context,
    paragraphs: str | None,
    mode: str | None,
) -> None:
    """Build your paragraph library through guided Q&A.

    Two modes:

    --mission   Capture why a specific company's purpose or product resonates
                with you. Produces a reusable mission-alignment paragraph.

    --evidence  Capture what you built or owned at a specific role.
                Produces an evidence paragraph for the cover letter body.

    Without a flag, you will be prompted to choose.

    Examples:
      coverletter intake --mission
      coverletter intake --evidence
    """
    from coverletter.build import MISSION_SYSTEM, BUILD_SYSTEM, qa_turn, force_draft, append_to_library
    from rich.panel import Panel
    from rich.rule import Rule

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)
    all_paragraphs = load_paragraphs(cfg.paragraphs_files)
    priority_file = cfg.paragraphs_files[-1].parent / "library_refined.md"

    console.print(f"\n[bold blue]Intake[/bold blue]  [dim]→ {priority_file.name}[/dim]\n")

    if not mode:
        console.print("What are you capturing?\n")
        console.print("  [bold]1.[/bold] Mission frame  [dim]— why a company's purpose or product resonates with you[/dim]")
        console.print("  [bold]2.[/bold] Evidence       [dim]— what you built or owned at a specific role[/dim]")
        _flush_stdin()
        choice = input("\nEnter 1 or 2: ").strip()
        mode = "mission" if choice == "1" else "evidence"

    if mode == "mission":
        _intake_mission(cfg, all_paragraphs, priority_file)
    else:
        _intake_evidence(cfg, all_paragraphs, priority_file)


def _pick_location(
    new_text: str,
    all_paragraphs: list["Paragraph"],
    voyage_api_key: str,
    *,
    type_filter: str | None,
    default_role: str,
    default_section: str,
    paragraphs_files: "list[Path] | None" = None,
) -> tuple[str, str]:
    """Use embeddings to suggest where a new paragraph belongs in the library.

    Prefers cached DB embeddings (fast). Falls back to re-embedding on the fly.
    Shows up to 3 closest (role, section) pairs. User picks a number or 'n' for manual.
    """
    from rich.rule import Rule

    console.print()
    console.print(Rule("[bold]Where should this go?[/bold]", style="cyan"))

    suggestions: list[tuple[str, str, float]] = []

    # Try DB first (cached embeddings — much faster)
    if paragraphs_files and voyage_api_key:
        try:
            from coverletter.db import open_db, db_path, query_similar
            db = db_path(paragraphs_files)
            if db.exists():
                conn = open_db(db)
                suggestions = query_similar(conn, new_text, voyage_api_key, top_n=3, type_filter=type_filter)
        except Exception:
            pass

    # Fall back to re-embedding the full library
    if not suggestions:
        suggestions = embed_classify(
            new_text, all_paragraphs, voyage_api_key, top_n=3, type_filter=type_filter
        )

    if suggestions:
        console.print("[dim]Closest existing locations by semantic similarity:[/dim]\n")
        for i, (role, section, score) in enumerate(suggestions, 1):
            console.print(f"  [bold]{i}[/bold]  {role} / {section}  [dim]({score:.2f})[/dim]")
        console.print(f"  [bold]n[/bold]  Enter new location manually")
        console.print()
        _flush_stdin()
        choice = input("Pick [1/2/3/n]: ").strip().lower()
        if choice in ("1", "2", "3"):
            idx = int(choice) - 1
            if idx < len(suggestions):
                return suggestions[idx][0], suggestions[idx][1]
    else:
        console.print("[dim]No similar paragraphs found — enter location manually.[/dim]\n")

    _flush_stdin()
    save_role = input(f"Role [{default_role}]: ").strip() or default_role
    _flush_stdin()
    save_section = input(f"Section [{default_section}]: ").strip() or default_section
    return save_role, save_section


def _intake_mission(cfg: "Config", all_paragraphs: list["Paragraph"], priority_file: "Path") -> None:
    """Q&A session to capture a mission alignment paragraph."""
    from coverletter.build import MISSION_SYSTEM, qa_turn, force_draft, append_to_library
    from rich.panel import Panel

    console.print("[bold]Mission frame[/bold]  [dim]— why a specific purpose or product resonates with you[/dim]\n")
    console.print(
        "[dim]Name the company or describe the purpose. Answer the questions.\n"
        "'draft' to draft now. 'done' to exit without saving.[/dim]\n"
    )

    _flush_stdin()
    company = input("What company or purpose prompted this? (e.g. 'Alt', 'NYT', 'a civic data org'): ").strip()
    if not company:
        console.print("[yellow]Nothing to capture — exiting.[/yellow]")
        return
    _flush_stdin()
    what_resonates = input("What specifically resonates? (your words, as much detail as you want): ").strip()

    topic = company
    theme = company

    context = (
        f"I want to write a mission alignment paragraph. The company that prompted this is: {company}\n\n"
        + (f"What resonates about it: {what_resonates}\n\n" if what_resonates else "")
        + "This paragraph should capture why this KIND of purpose genuinely resonates with me personally — "
        f"written broadly enough to apply to similar organizations, not tied to {company} specifically "
        f"unless I explicitly say I want it company-specific. "
        "Search the library first to understand what I have already said about my values and what I care about."
    )
    history: list[dict] = [{"role": "user", "content": context}]

    console.print(f"\n[bold blue]Capturing:[/bold blue] {theme}")
    console.print("[dim]Answer the questions. 'draft' to draft now. 'done' to exit without saving.[/dim]\n")

    with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, console=console):
        pending_draft, question = qa_turn(
            history, cfg.api_key, cfg.model, all_paragraphs,
            voyage_api_key=cfg.voyage_api_key, system=MISSION_SYSTEM,
        )
    console.print(f"[dim]{running_total()}[/dim]")

    if question:
        console.print(f"[cyan]{question}[/cyan]\n")
        history.append({"role": "assistant", "content": question})

    accepted: str | None = None

    while True:
        if pending_draft is not None:
            console.print(Panel(pending_draft, border_style="green", title="Draft"))
            choice = _prompt_choice("[A]ccept  [R]edirect  [K]eep talking: ", {"a", "r", "k"})
            if choice == "a":
                accepted = pending_draft
                break
            elif choice == "r":
                redirect = _read_multiline("Direction: ")
                if not redirect:
                    continue
                history.append({"role": "assistant", "content": pending_draft})
                history.append({"role": "user", "content": f"Revise the draft: {redirect}"})
                with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
                    pending_draft = force_draft(
                        history, cfg.api_key, cfg.model, all_paragraphs,
                        voyage_api_key=cfg.voyage_api_key, system=MISSION_SYSTEM,
                    )
            elif choice == "k":
                history.append({"role": "assistant", "content": pending_draft})
                history.append({"role": "user", "content": "Keep going — what else do you need to know?"})
                pending_draft = None
                with Live(Spinner("dots", text="Continuing..."), refresh_per_second=10, console=console):
                    _, question = qa_turn(
                        history, cfg.api_key, cfg.model, all_paragraphs,
                        voyage_api_key=cfg.voyage_api_key, system=MISSION_SYSTEM,
                    )
                if question:
                    console.print(f"\n[cyan]{question}[/cyan]\n")
                    history.append({"role": "assistant", "content": question})
        else:
            user_input = _read_multiline()
            if not user_input or user_input.lower() == "done":
                break
            if user_input.lower() == "draft":
                with Live(Spinner("dots", text="Drafting..."), refresh_per_second=10, console=console):
                    pending_draft = force_draft(
                        history, cfg.api_key, cfg.model, all_paragraphs,
                        voyage_api_key=cfg.voyage_api_key, system=MISSION_SYSTEM,
                    )
            else:
                history.append({"role": "user", "content": user_input})
                with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, console=console):
                    pending_draft, question = qa_turn(
                        history, cfg.api_key, cfg.model, all_paragraphs,
                        voyage_api_key=cfg.voyage_api_key, system=MISSION_SYSTEM,
                    )
                if question and pending_draft is None:
                    console.print(f"\n[cyan]{question}[/cyan]\n")
                    history.append({"role": "assistant", "content": question})

    if not accepted:
        console.print("[dim]Nothing saved.[/dim]")
        return

    save_role, save_section = _pick_location(
        accepted, all_paragraphs, cfg.voyage_api_key,
        type_filter="frame", default_role="General", default_section=company,
        paragraphs_files=cfg.paragraphs_files,
    )

    meta: dict[str, str] = {"type": "frame", "frame": "mission", "strength": "high"}
    append_to_library(priority_file, save_role, save_section, accepted, meta)
    console.print(f"\n[green]Saved to {priority_file.name}[/green] under {save_role} / {save_section}  [dim][type=frame, frame=mission][/dim]\n")


def _intake_evidence(cfg: "Config", all_paragraphs: list["Paragraph"], priority_file: "Path") -> None:
    """Q&A session to capture an evidence paragraph."""
    from coverletter.build import BUILD_SYSTEM, qa_turn, force_draft, append_to_library
    from rich.panel import Panel

    console.print("[bold]Evidence[/bold]  [dim]— what you built or owned at a specific role[/dim]\n")
    console.print(
        "[dim]Name the project, role, or topic. Answer the questions.\n"
        "'draft' to draft now. 'done' to exit without saving.[/dim]\n"
    )

    _flush_stdin()
    topic = input("What to capture (e.g. 'subscriber reporting pipeline', 'voter file ingestion'): ").strip()
    if not topic:
        console.print("[yellow]Nothing to capture — exiting.[/yellow]")
        return

    context = (
        f"Topic to explore: {topic}\n\n"
        "Use the search_library tool now to check what is already written about this topic before asking any questions."
    )
    history: list[dict] = [{"role": "user", "content": context}]

    console.print(f"\n[bold blue]Capturing:[/bold blue] {topic}")
    console.print("[dim]Answer the questions. 'draft' to draft now. 'done' to exit without saving.[/dim]\n")

    with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, console=console):
        pending_draft, question = qa_turn(
            history, cfg.api_key, cfg.model, all_paragraphs,
            voyage_api_key=cfg.voyage_api_key, system=BUILD_SYSTEM,
        )
    console.print(f"[dim]{running_total()}[/dim]")

    if question:
        console.print(f"[cyan]{question}[/cyan]\n")
        history.append({"role": "assistant", "content": question})

    accepted: str | None = None

    while True:
        if pending_draft is not None:
            console.print(Panel(pending_draft, border_style="green", title="Draft"))
            choice = _prompt_choice("[A]ccept  [R]edirect  [K]eep talking: ", {"a", "r", "k"})
            if choice == "a":
                accepted = pending_draft
                break
            elif choice == "r":
                redirect = _read_multiline("Direction: ")
                if not redirect:
                    continue
                RULES_REMINDER = (
                    "Revise the draft per the direction above.\n\n"
                    "This is a CAPTURE revision — preserve everything, do not polish.\n"
                    "DO NOT INVENT: every claim must trace to this conversation, not library results.\n"
                    "USE THEIR WORDS: their language and level of abstraction, not resume speak.\n"
                    "INCLUDE ALL DETAIL: every specific technical detail, fact, and explanation "
                    "the person provided must appear in full — including everything in this redirect. "
                    "Do not compress, summarize, or cut any of it. Length is fine.\n"
                    "DO NOT EDITORIALIZE: do not add framing or conclusions the person did not provide."
                )
                history.append({"role": "assistant", "content": pending_draft})
                history.append({"role": "user", "content": f"Revise the draft: {redirect}\n\n{RULES_REMINDER}"})
                with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
                    # Use qa_turn directly — history already ends with the revision instruction.
                    # force_draft would append a second user message, causing the model to ignore the redirect.
                    _draft_r, _raw_r = qa_turn(history, cfg.api_key, cfg.model, all_paragraphs, voyage_api_key=cfg.voyage_api_key, system=BUILD_SYSTEM)
                    pending_draft = _draft_r or _raw_r or ""
            elif choice == "k":
                history.append({"role": "assistant", "content": pending_draft})
                history.append({"role": "user", "content": "Keep going — what else do you need to know?"})
                pending_draft = None
                with Live(Spinner("dots", text="Continuing..."), refresh_per_second=10, console=console):
                    _, question = qa_turn(
                        history, cfg.api_key, cfg.model, all_paragraphs,
                        voyage_api_key=cfg.voyage_api_key, system=BUILD_SYSTEM,
                    )
                if question:
                    console.print(f"\n[cyan]{question}[/cyan]\n")
                    history.append({"role": "assistant", "content": question})
        else:
            user_input = _read_multiline()
            if not user_input or user_input.lower() == "done":
                break
            if user_input.lower() == "draft":
                with Live(Spinner("dots", text="Drafting..."), refresh_per_second=10, console=console):
                    pending_draft = force_draft(
                        history, cfg.api_key, cfg.model, all_paragraphs,
                        voyage_api_key=cfg.voyage_api_key, system=BUILD_SYSTEM,
                    )
            else:
                history.append({"role": "user", "content": user_input})
                with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, console=console):
                    pending_draft, question = qa_turn(
                        history, cfg.api_key, cfg.model, all_paragraphs,
                        voyage_api_key=cfg.voyage_api_key, system=BUILD_SYSTEM,
                    )
                if question and pending_draft is None:
                    console.print(f"\n[cyan]{question}[/cyan]\n")
                    history.append({"role": "assistant", "content": question})

    if not accepted:
        console.print("[dim]Nothing saved.[/dim]")
        return

    default_section = topic.split("—")[0].strip()[:40]
    save_role, save_section = _pick_location(
        accepted, all_paragraphs, cfg.voyage_api_key,
        type_filter="evidence", default_role="General", default_section=default_section,
        paragraphs_files=cfg.paragraphs_files,
    )

    meta: dict[str, str] = {"type": "evidence", "strength": "high"}
    append_to_library(priority_file, save_role, save_section, accepted, meta)
    console.print(f"\n[green]Saved to {priority_file.name}[/green] under {save_role} / {save_section}  [dim][type=evidence][/dim]\n")


@main.command("blurb")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs file")
@click.option("--output", "-o", default=None, help="Directory to save output")
@click.option("--model", "-m", default=None, help="Claude model to use")
@click.option("--role", "-r", default=None, help="Role to filter paragraphs by (skip prompt)")
@click.option("--resume", "-R", default=None, help="Path to resume file (.pdf, .md, or .txt)")
@click.option("--no-save", is_flag=True, default=False, help="Skip saving to file")
@click.pass_context
def blurb(
    ctx: click.Context,
    paragraphs: str | None,
    output: str | None,
    model: str | None,
    role: str | None,
    resume: str | None,
    no_save: bool,
) -> None:
    """Answer a short application prompt using your paragraph library.

    Handles any short-form application question: biographical "about me" sections,
    behavioral questions ("describe a time when..."), motivation questions
    ("why this role"), approach questions ("how do you think about..."), etc.

    The JD provides context for which paragraphs to select. The application
    prompt determines the response format and length.

    Example:
      coverletter blurb
      coverletter blurb --role "Data Engineering" --no-save
    """
    from rich.panel import Panel
    from rich.markdown import Markdown

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs, output, model, resume)
    profile = load_profile(cfg.profile_file)

    console.print(f"\n[bold blue]Short Response Generator[/bold blue]")

    all_paragraphs = load_paragraphs(cfg.paragraphs_files)
    total = sum(sum(s.values()) for s in library_stats(all_paragraphs).values())
    console.print(
        f"Using: [dim]{' + '.join(f.name for f in cfg.paragraphs_files)}[/dim] "
        f"([green]{total} paragraphs[/green])"
    )

    resume_text = load_resume(cfg.resume_file)

    if role is None:
        role = select_role(all_paragraphs)

    role_paragraphs = filter_by_role(all_paragraphs, role) if role else all_paragraphs
    if role:
        console.print(f"Role: [bold]{role}[/bold] + General → {len(role_paragraphs)} paragraphs available")

    # JD — used for paragraph prefiltering; clipboard avoids PTY buffer truncation.
    job_description = read_job_description(
        prompt=(
            "\n[bold]Copy the job description to your clipboard, then press Enter[/bold] "
            "[dim](used to select relevant paragraphs)[/dim]\n"
        ),
        jds_dir=cfg.paragraphs_files[0].parent / "jds",
    )

    # Application prompt — copy the question from the application form to clipboard, press Enter.
    console.print(
        "\n[bold]Copy the application question to your clipboard, then press Enter.[/bold]\n"
        "[dim]The question will be displayed for confirmation.[/dim]\n"
    )
    try:
        _flush_stdin()
        input()
    except (KeyboardInterrupt, EOFError):
        raise SystemExit("\nCancelled.")
    application_prompt = _read_from_clipboard().strip()
    try:
        sys.stdin = open("/dev/tty", "r")
    except OSError:
        _flush_stdin()
    if not application_prompt:
        raise SystemExit("\nClipboard was empty. Copy the application question and try again.")
    from rich.panel import Panel as _Panel
    console.print(_Panel(application_prompt, title="[bold]Application Question[/bold]", border_style="dim", padding=(1, 2)))
    console.print(f"[dim]{len(application_prompt):,} characters read from clipboard.[/dim]")

    _flush_stdin()
    company = input("\nCompany name (for filename, optional): ").strip()

    from coverletter.provider import get_embed_provider as _get_ep, get_provider as _get_provider
    _provider = _get_provider(cfg.model, cfg.api_key)
    _embed_provider = _get_ep(cfg.embed_model) or _provider
    if cfg.voyage_api_key or _embed_provider.supports_embed() or _embed_provider.supports_hybrid():
        filtered = embed_prefilter(role_paragraphs, job_description, cfg.top_n, cfg.voyage_api_key or "", _embed_provider)
    else:
        filtered = prefilter(role_paragraphs, job_description, cfg.top_n)

    from coverletter.corrections import apply_corrections, load_corrections
    corrections_file = cfg.paragraphs_files[0].parent / "corrections.md"
    corrections = load_corrections(corrections_file)
    corrected = apply_corrections(filtered, corrections)

    # Biographical framing from profile.
    working_style = profile.working_style if profile and profile.working_style else None
    values = profile.values if profile and profile.values else None
    goals = profile.goals if profile and profile.goals else None
    avoid = profile.avoid if profile and profile.avoid else None
    bio_count = len(working_style or []) + len(values or []) + len(avoid or [])
    if bio_count:
        console.print(f"[dim]Biographical context: {bio_count} entries (working_style + values + avoid)[/dim]")

    # Warn before generation if biographical material is too thin for a biographical prompt.
    # The model will surface BIOGRAPHICAL_GAPS after the fact, but this saves an API call
    # when the profile is clearly empty going in.
    _BIO_MIN = 2
    if bio_count < _BIO_MIN:
        console.print(
            f"\n[yellow]Thin biographical profile ({bio_count} entries).[/yellow]\n"
            f"[dim]For biographical prompts ('tell me about yourself', 'about me'), the response\n"
            f"quality depends on working_style + values entries in your profile.\n"
            f"Consider running [bold]coverletter profile[/bold] to add entries before continuing.[/dim]"
        )
        _flush_stdin()
        proceed = input("Continue anyway? [Y/n]: ").strip().lower()
        if proceed in ("n", "no"):
            return

    # Application prompt is appended to the JD block — it's the last thing the model
    # reads before writing. The JD drove paragraph prefiltering; the application
    # prompt drives what the model actually writes. Keeping it here (not in the
    # library/notes block) ensures recency: bio block comes right before it,
    # application prompt comes after the JD.
    combined_jd = f"{job_description.strip()}\n\n=== APPLICATION PROMPT ===\n{application_prompt.strip()}"

    user_message = build_user_message(
        combined_jd, corrected, role=role, company=company or None,
        resume=resume_text or None,
        working_style=working_style,
        values=values,
        goals=goals,
        avoid=avoid,
    )

    console.print()
    with Live(Spinner("dots", text="Generating..."), refresh_per_second=10, console=console):
        parts: list[str] = []
        for chunk in stream_cover_letter(SHORT_RESPONSE_SYSTEM, user_message, cfg.api_key, cfg.model):
            parts.append(chunk)

    response_text = "".join(parts)
    console.print(f"[dim]{running_total()}[/dim]")

    # Split off any BIOGRAPHICAL_GAPS section before displaying
    bio_gaps: str | None = None
    if "BIOGRAPHICAL_GAPS:" in response_text:
        parts_split = response_text.split("BIOGRAPHICAL_GAPS:", 1)
        response_text = parts_split[0].strip()
        bio_gaps = parts_split[1].strip()

    console.print(Panel(Markdown(response_text), title="Response", border_style="cyan", padding=(1, 2)))
    word_count = len(response_text.split())
    color = "green" if word_count <= 350 else "yellow"
    console.print(f"[{color}]{word_count} words[/{color}]")
    console.print("[dim]── plain text ──[/dim]")
    print(response_text)
    console.print("[dim]────────────────[/dim]")

    # Surface biographical gaps and offer to add working_style entries
    if bio_gaps:
        from rich.rule import Rule
        console.print()
        console.print(Rule("[yellow]Biographical material gaps[/yellow]"))
        console.print(f"[yellow]{bio_gaps}[/yellow]")
        console.print()
        console.print("[dim]Your biographical profile is thin for this prompt type.[/dim]")
        console.print("[dim]You can add to: [bold]working_style[/bold] (how you think/work) or [bold]values[/bold] (what you believe — open-source, mentorship, how you show up on a team)[/dim]")
        _flush_stdin()
        add_bio = input("Add biographical entries now? [y/N]: ").strip().lower()
        if add_bio in ("y", "yes"):
            console.print("\nWhich section?")
            console.print("  [cyan]1[/cyan]. working_style — how you think, how you work, what shaped you")
            console.print("  [cyan]2[/cyan]. values — what you believe as a programmer and teammate")
            _flush_stdin()
            section_choice = input("Section [1]: ").strip() or "1"
            section_map = {"1": "working_style", "2": "values"}
            target_section = section_map.get(section_choice, "working_style")
            console.print(
                f"\nWrite {target_section} entries — one per line. Blank line when done.\n"
            )
            new_entries: list[str] = []
            while True:
                _flush_stdin()
                entry = input("> ").strip()
                if not entry:
                    break
                new_entries.append(entry)
            if new_entries:
                getattr(profile, target_section).extend(new_entries)
                from coverletter.profile import write_profile
                write_profile(
                    cfg.profile_file,
                    {k: getattr(profile, k) for k in [
                        "goals", "differentiators", "focus_areas",
                        "avoid", "seniority_signals", "working_style", "values"
                    ]},
                )
                console.print(f"[green]Added {len(new_entries)} entries to {target_section} in {cfg.profile_file.name}[/green]")

    # Revision loop
    messages: list[dict] = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response_text},
    ]

    while True:
        console.print()
        _flush_stdin()
        feedback = input("Revise (free text), or Enter to finish: ").strip()
        if not feedback:
            break

        wrapped = (
            "REVISE THE RESPONSE using the following feedback. "
            "Output only the revised response — no preamble, no commentary.\n\n"
            + feedback
        )
        with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
            parts = []
            for chunk in stream_revision(SHORT_RESPONSE_SYSTEM, messages, wrapped, cfg.api_key, cfg.model):
                parts.append(chunk)

        revised = "".join(parts)
        console.print(Panel(Markdown(revised), title="Revised", border_style="cyan", padding=(1, 2)))
        word_count = len(revised.split())
        color = "green" if word_count <= 350 else "yellow"
        console.print(f"[{color}]{word_count} words[/{color}]")
        console.print("[dim]── plain text ──[/dim]")
        print(revised)
        console.print("[dim]────────────────[/dim]")
        console.print(f"[{color}]{word_count} words[/{color}]")

        _flush_stdin()
        accept = input("[A]ccept / [R]eject: ").strip().lower()
        # Always append to history so the model retains context of what was tried.
        messages.append({"role": "user", "content": wrapped})
        messages.append({"role": "assistant", "content": revised})
        if accept in ("", "a", "accept", "y", "yes"):
            response_text = revised

    from coverletter.costs import session_summary
    summary = session_summary()
    if summary:
        console.print(f"[dim]Session cost: {summary}[/dim]\n")

    if not no_save:
        _flush_stdin()
        save_it = input(f"Save to {cfg.output_dir}? [Y/n]: ").strip().lower()
        if save_it in ("", "y", "yes"):
            label = (company or role or "response") + "-response"
            saved_md = save_letter(response_text, cfg.output_dir, label, cfg.author_name)
            console.print(f"[green]Saved:[/green] {saved_md}\n")


@main.command("init")
def init() -> None:
    """Scaffold .env, library.md, and experiences.md in the current directory."""
    from pathlib import Path

    env_path = Path(".env")
    paragraphs_path = Path("library.md")
    experiences_path = Path("experiences.md")
    created: list[str] = []
    skipped: list[str] = []

    if env_path.exists():
        skipped.append(".env")
    else:
        env_path.write_text(
            "# Cover Letter Generator — configuration\n"
            "# ─────────────────────────────────────────\n"
            "# Generation provider — pick one:\n"
            "ANTHROPIC_API_KEY=sk-ant-...        # https://console.anthropic.com\n"
            "# MISTRAL_API_KEY=...               # https://console.mistral.ai\n"
            "# OPENAI_API_KEY=sk-...             # https://platform.openai.com\n"
            "# COHERE_API_KEY=...                # https://dashboard.cohere.com\n\n"
            "# Switch provider by setting the model (prefix selects provider):\n"
            "# COVERLETTER_MODEL=claude-sonnet-4-6   (default, Anthropic)\n"
            "# COVERLETTER_MODEL=mistral/mistral-large-latest\n"
            "# COVERLETTER_MODEL=openai/gpt-4o\n"
            "# COVERLETTER_MODEL=cohere/command-r-plus\n\n"
            "# Embeddings (for paragraph + claim retrieval):\n"
            "# VOYAGE_API_KEY=pa-...             # https://www.voyageai.com — best retrieval quality\n"
            "# OPENAI_EMBED_MODEL=text-embedding-3-small  # if using OpenAI-compat host\n"
            "# EMBED_MODEL=bge-m3                # local hybrid dense+sparse (uv add FlagEmbedding)\n\n"
            "# Your name as it appears on the sign-off\n"
            "AUTHOR_NAME=Your Name\n\n"
            "# Absolute path to your resume PDF (or .md / .txt)\n"
            "# RESUME_FILE=/path/to/your/resume.pdf\n\n"
            "# Where to save generated letters (defaults to ./output)\n"
            "# OUTPUT_DIR=/path/to/output\n\n"
            "# How many paragraphs to pass to the model (default 100)\n"
            "# COVERLETTER_TOP_N=100\n",
            encoding="utf-8",
        )
        created.append(".env")

    if paragraphs_path.exists():
        skipped.append("library.md")
    else:
        paragraphs_path.write_text(
            "<!--\n"
            "  HOW TO USE THIS FILE\n"
            "  -----------------------------------------------------------------------\n"
            "  STRUCTURE\n"
            "  * ## Role Name    -> groups paragraphs for a specific role type\n"
            "  * ## General      -> included in every generation regardless of role\n"
            "  * ### Section     -> paragraph type (Opening, Technical, Why This Role...)\n"
            "  * Paragraphs separated by blank lines within each section\n"
            "  * Optional meta comment above each paragraph:\n"
            "      <!-- meta: tone=opener, strength=high -->\n"
            "      <!-- meta: tech=python,spark, strength=high -->\n"
            "  * Valid meta keys: tone (opener|closer), strength (high|medium|low),\n"
            "                     tech (comma-separated list)\n"
            "\n"
            "  WORKFLOW\n"
            "  1. Add your source paragraphs below -- written in your own voice\n"
            "  2. Run: coverletter\n"
            "  3. Select a role, paste a job description, get a letter\n"
            "  4. After every application, add what worked\n"
            "  -----------------------------------------------------------------------\n"
            "-->\n"
            "\n"
            "# My Cover Letter Paragraphs\n"
            "\n"
            "## General\n"
            "\n"
            "### Opening\n"
            "\n"
            "<!-- meta: tone=opener, strength=high -->\n"
            "Write an opening paragraph here that describes who you are and what kind of\n"
            "work you do. Make a concrete claim. Do not start with \"I am excited to apply.\"\n"
            "\n"
            "### Strengths\n"
            "\n"
            "<!-- meta: strength=high -->\n"
            "Write a paragraph about a specific strength here, with an example or evidence.\n"
            "\n"
            "### Closing\n"
            "\n"
            "<!-- meta: tone=closer, strength=high -->\n"
            "Write a closing paragraph here. Thank the reader and express genuine interest\n"
            "in speaking further. Be specific, not generic.\n"
            "\n"
            "## Your Role Type\n"
            "\n"
            "### Opening\n"
            "\n"
            "<!-- meta: tone=opener, strength=high -->\n"
            "Write a role-specific opening paragraph here.\n"
            "\n"
            "### Technical\n"
            "\n"
            "<!-- meta: tech=your,tools,here, strength=high -->\n"
            "Write a technical paragraph here about a specific project or system you built.\n"
            "Concrete situation, specific problem, what you did, why it was hard, what changed.\n"
            "\n"
            "### Why This Role\n"
            "\n"
            "<!-- meta: tone=closer, strength=high -->\n"
            "Write a paragraph about why this type of role or organization appeals to you.\n"
            "Specific connection, not generic enthusiasm.\n",
            encoding="utf-8",
        )
        created.append("library.md")

    if experiences_path.exists():
        skipped.append("experiences.md")
    else:
        experiences_path.write_text(
            "# Experience Register\n"
            "#\n"
            "# Stores raw facts and desired angle framings per experience.\n"
            "# Used to inject targeted context into Q&A sessions so the agent\n"
            "# asks about gaps instead of re-asking what's already written.\n"
            "#\n"
            "# Format:\n"
            "#\n"
            "# ## Experience Name\n"
            "# company: Company Name\n"
            "# years: 2021–2023\n"
            "# angles: production-ownership, system-design, business-impact\n"
            "#\n"
            "# Raw facts about this experience (things the Q&A agent already knows).\n"
            "# Write these as bullet points or short sentences.\n"
            "#\n"
            "# qa_targets:\n"
            "# - What downstream decisions depended directly on the output?\n"
            "# - What broke or became unreliable when it failed?\n"
            "#\n"
            "# Angles to use:\n"
            "#   production-ownership, system-design, business-impact, data-model,\n"
            "#   cross-functional, scope-opener, domain-expertise, reliability,\n"
            "#   leverage, through-line, ownership, architecture, strategic-vision,\n"
            "#   financial-complexity\n",
            encoding="utf-8",
        )
        created.append("experiences.md")

    console.print()
    if created:
        console.print("[bold green]Created:[/bold green]")
        for f in created:
            console.print(f"  [green]{f}[/green]")
    if skipped:
        console.print("[dim]Already exists (skipped):[/dim]")
        for f in skipped:
            console.print(f"  [dim]{f}[/dim]")

    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Add your API key and [bold]AUTHOR_NAME[/bold] to .env")
    console.print("  2. Set [bold]RESUME_FILE[/bold] in .env (used by build and generate)")
    console.print()
    console.print("  [bold]If you have existing material[/bold] (resume, old cover letters, LinkedIn):")
    console.print("    uv run coverletter seed                     # paste material, extract paragraphs")
    console.print()
    console.print("  [bold]If you have a job description and want to see what's missing:[/bold]")
    console.print("    uv run coverletter build --jd jd.txt        # gap analysis + targeted Q&A")
    console.print("    uv run coverletter build --about \"project\"  # build one paragraph manually")
    console.print()
    console.print("  [bold]Build your profile[/bold] (do once before generating letters):")
    console.print("    uv run coverletter profile --model opus")
    console.print()
    console.print("  [bold]Generate your first letter:[/bold]")
    console.print("    uv run coverletter\n")


@main.command("profile")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs file")
@click.option("--model", "-m", default=None, help="Claude model to use (e.g. opus for higher quality suggestions)")
@click.pass_context
def build_profile(ctx: click.Context, paragraphs: str | None, model: str | None) -> None:
    """Build or rebuild your candidate profile through guided questions."""
    from rich.panel import Panel
    from rich.rule import Rule
    from coverletter.profile import load_profile, write_profile, suggest_from_library

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs, model_override=model)
    current = load_profile(cfg.profile_file)

    console.print(f"\n[bold blue]Candidate Profile Builder[/bold blue]  [dim]→ {cfg.profile_file}[/dim]\n")
    console.print(
        "[dim]This profile drives the letter thesis, alignment report, and goal-fit evaluation.\n"
        "The more specific and honest, the more useful it is.[/dim]\n"
    )

    if not current.is_empty:
        console.print("[bold]Current profile:[/bold]")
        if current.goals:
            console.print("  [cyan]Goals:[/cyan]")
            for g in current.goals:
                console.print(f"    • {g}")
        if current.differentiators:
            console.print("  [cyan]Differentiators:[/cyan]")
            for d in current.differentiators:
                console.print(f"    • {d}")
        if current.focus_areas:
            console.print("  [cyan]Focus areas:[/cyan]")
            for f in current.focus_areas:
                console.print(f"    • {f}")
        if current.avoid:
            console.print("  [cyan]Avoid:[/cyan]")
            for a in current.avoid:
                console.print(f"    • {a}")
        console.print()
        _flush_stdin()
        choice = input("Start from scratch [S], edit existing [E], or generate suggestions from library [G]? ").strip().lower()
    else:
        console.print("[dim]Profile is empty — let's fill it in.[/dim]\n")
        _flush_stdin()
        choice = input("Type your own answers [T] or generate suggestions from library first [G]? ").strip().lower()

    # Generate LLM suggestions from the paragraph library
    suggestions: dict[str, list[str]] = {"goals": [], "differentiators": [], "focus_areas": [], "avoid": [], "seniority_signals": [], "working_style": [], "values": []}
    if choice in ("g", "generate"):
        all_paragraphs = load_paragraphs(cfg.paragraphs_files)
        console.print()
        with Live(Spinner("dots", text="Reading your library and generating suggestions..."), refresh_per_second=10, console=console):
            try:
                suggestions = suggest_from_library(all_paragraphs, cfg.api_key, cfg.model)
            except RuntimeError as e:
                console.print(f"\n[red]Failed to parse suggestions:[/red]\n{e}\n")
                suggestions = {"goals": [], "differentiators": [], "focus_areas": [], "avoid": [], "seniority_signals": [], "working_style": [], "values": []}
        console.print(f"[dim]{running_total()}[/dim]\n")
        console.print("[bold]Suggestions based on your paragraph library:[/bold]\n")
        for section, items in suggestions.items():
            if items:
                console.print(f"  [cyan]{section}:[/cyan]")
                for item in items:
                    console.print(f"    • {item}")
        console.print()
        console.print("[dim]You'll review and edit each section below.[/dim]\n")

    # Starting values — use current if editing, suggestions if generating, empty otherwise
    if choice in ("e", "edit") and not current.is_empty:
        start = {
            "goals": list(current.goals),
            "differentiators": list(current.differentiators),
            "focus_areas": list(current.focus_areas),
            "avoid": list(current.avoid),
            "seniority_signals": list(current.seniority_signals),
            "working_style": list(current.working_style),
            "values": list(current.values),
        }
    else:
        start = suggestions

    def _edit_section(
        section: str,
        heading: str,
        guidance: str,
        current_items: list[str],
    ) -> list[str]:
        console.print(Rule(f"[bold]{heading}[/bold]", style="cyan"))
        console.print(f"[dim]{guidance}[/dim]\n")

        items = list(current_items)

        if items:
            console.print("[bold]Current entries:[/bold]")
            for i, item in enumerate(items, 1):
                console.print(f"  [cyan]{i}.[/cyan] {item}")
            console.print()

        # Add new entries
        console.print("[dim]Add entries — one per line, blank line when done (or Enter to skip):[/dim]")
        _flush_stdin()
        try:
            while True:
                line = input("  + ").strip()
                if not line:
                    break
                items.append(line)
                console.print(f"  [green]✓[/green] {line}")
        except EOFError:
            pass

        # Remove entries if any exist
        if items:
            console.print()
            console.print("[dim]Remove any? Enter numbers to delete (e.g. 1,3) or Enter to skip:[/dim]")
            if len(items) != len(current_items):  # re-show if list changed
                for i, item in enumerate(items, 1):
                    console.print(f"  [cyan]{i}.[/cyan] {item}")
            _flush_stdin()
            try:
                raw = input("  - ").strip()
            except EOFError:
                raw = ""
            if raw:
                to_delete = set()
                for part in raw.split(","):
                    part = part.strip()
                    if part.isdigit():
                        idx = int(part) - 1
                        if 0 <= idx < len(items):
                            to_delete.add(idx)
                items = [item for i, item in enumerate(items) if i not in to_delete]
                if to_delete:
                    console.print(f"[dim]Removed {len(to_delete)} entry/entries.[/dim]")

        console.print()
        return items

    # Walk through each section
    console.print()
    goals = _edit_section(
        "goals",
        "What you want from the next role",
        "Think about: scope (IC vs. staff vs. lead), team structure (embedded in product vs. "
        "central platform), planning culture, what 'data is taken seriously' looks like.\n"
        "Be specific — 'move toward staff scope' is better than 'grow as an engineer'.",
        start.get("goals", []),
    )

    differentiators = _edit_section(
        "differentiators",
        "Your actual technical edge",
        "Name specific technologies, scale, and ownership level.\n"
        "'Strong communicator' and 'fast learner' belong nowhere near this list.\n"
        "Concrete: 'Sole DE at Acme Corp — owned 1B+ events/day pipeline end-to-end for 2 years'\n"
        "          'Built schema governance and data contracts from scratch, no prior process existed'",
        start.get("differentiators", []),
    )

    focus_areas = _edit_section(
        "focus_areas",
        "Where you want to go deeper",
        "DE areas you want to develop further in this next role — not just what you already know.",
        start.get("focus_areas", []),
    )

    avoid = _edit_section(
        "avoid",
        "Poor fit environments",
        "What would waste your strengths or put you in a bad dynamic? Be honest.\n"
        "E.g. 'pure ETL shops with no platform ambition', 'teams where scope is always pre-defined'",
        start.get("avoid", []),
    )

    seniority_signals = _edit_section(
        "seniority_signals",
        "Seniority signals for your role type",
        "These describe YOUR expertise level and domain — not the job title on any specific posting.\n"
        "A senior DE applying to roles called 'AI Engineer' or 'Staff Analytics Engineer' uses the\n"
        "same signals. They reflect what you actually do at your level, not what a JD calls itself.\n"
        "Only revisit if your career direction genuinely shifts.\n"
        "Each entry: short label + what evidence looks like.\n"
        "Example (senior data engineering background):\n"
        "  'Business impact: quantified outcomes, not just \"built X\" — what did it enable?'\n"
        "  'Production ownership: SLAs, incidents, reliability decisions — not greenfield only'\n"
        "  'System design judgment: trade-offs made and articulated, not just tool choices'\n"
        "  'Data modeling depth: schema decisions, SCD handling, warehouse design'\n"
        "  'Cross-functional effectiveness: translating infra to business context'",
        start.get("seniority_signals", []),
    )

    working_style = _edit_section(
        "working_style",
        "Working style",
        "How you work, how you think, what shaped you as an engineer.\n"
        "Not skill claims. Not what you've built. How you operate day-to-day.\n"
        "Write in your own voice. Used to frame biographical 'about me' responses.\n"
        "Example entries:\n"
        "  'I'm the person people think through a problem with to figure out how to build it'\n"
        "  'I move naturally between technical and non-technical audiences — I translate, not present'\n"
        "  'I think creatively about data problems; my background gives me angles that pure\n"
        "   backend engineers don't have'",
        start.get("working_style", []),
    )

    values = _edit_section(
        "values",
        "Values",
        "What you believe and care about as a programmer, teammate, and person.\n"
        "Open-source, mentorship, test-forward development, how you show up on a team.\n"
        "What kind of engineer are you at a deeper level? How do you orient with others?\n"
        "Write affirmatively in your own voice.\n"
        "Example entries:\n"
        "  'I believe in open-source development and contribute to the commons where I can'\n"
        "  'I care about mentorship — I have benefited from people who made time for me\n"
        "   and I pay that forward'\n"
        "  'I write tests not because I am told to but because I have been burned by not doing it'\n"
        "  'I am direct and honest with teammates even when it is uncomfortable'",
        start.get("values", []),
    )

    # Preview
    console.print(Rule("[bold]Preview[/bold]", style="green"))
    final = {"goals": goals, "differentiators": differentiators, "focus_areas": focus_areas, "avoid": avoid, "seniority_signals": seniority_signals, "working_style": working_style, "values": values}
    for section, items in final.items():
        if items:
            console.print(f"\n[cyan]{section}:[/cyan]")
            for item in items:
                console.print(f"  • {item}")

    console.print()
    _flush_stdin()
    confirm = input(f"Save to {cfg.profile_file}? [Y/n]: ").strip().lower()
    if confirm not in ("n", "no"):
        # If an existing profile is being replaced, offer to capture the shift
        if cfg.profile_file.exists() and not current.is_empty:
            old_goals = set(current.goals)
            new_goals = set(final.get("goals", []))
            if old_goals != new_goals:
                console.print()
                console.print("[bold yellow]Your goals have changed from the previous profile.[/bold yellow]")
                if current.goals:
                    console.print("[dim]Previous goals:[/dim]")
                    for g in current.goals:
                        console.print(f"  [dim]• {g}[/dim]")
                console.print()
                _flush_stdin()
                capture = input("Capture this shift through a Q&A session before saving? [Y/n]: ").strip().lower()
                if capture not in ("n", "no"):
                    from coverletter.build import PERSPECTIVE_SYSTEM, qa_turn, force_draft, append_to_library
                    all_paragraphs = load_paragraphs(cfg.paragraphs_files)
                    priority_file = cfg.paragraphs_files[-1].parent / "library_refined.md"
                    voyage_api_key = cfg.voyage_api_key if hasattr(cfg, "voyage_api_key") else ""

                    old_goals_text = "\n".join(f"- {g}" for g in current.goals)
                    new_goals_text = "\n".join(f"- {g}" for g in final.get("goals", []))
                    context = (
                        f"I'm capturing a shift in career direction.\n\n"
                        f"Previous goals:\n{old_goals_text}\n\n"
                        f"New goals:\n{new_goals_text}\n\n"
                        f"Help me articulate what drove this shift — what the decision was and what informed it."
                    )
                    history: list[dict] = [{"role": "user", "content": context}]

                    console.print()
                    console.print("[bold blue]Shift capture — Q&A[/bold blue]")
                    console.print("[dim]Answer the questions. 'draft' to draft now. 'done' to exit without saving.[/dim]\n")

                    with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, console=console):
                        pending_draft, question = qa_turn(
                            history, cfg.api_key, cfg.model, all_paragraphs,
                            voyage_api_key=voyage_api_key, system=PERSPECTIVE_SYSTEM,
                        )

                    if question:
                        console.print(f"[cyan]{question}[/cyan]\n")
                        history.append({"role": "assistant", "content": question})

                    accepted_shift: str | None = None
                    exchange_count = 0
                    MAX_EXCHANGES = 2

                    while True:
                        if pending_draft is not None:
                            console.print(Panel(pending_draft, border_style="green", title="Draft"))
                            choice = _prompt_choice("[A]ccept  [R]edirect  [K]eep talking: ", {"a", "r", "k"})
                            if choice == "a":
                                accepted_shift = pending_draft
                                break
                            elif choice == "r":
                                redirect = _read_multiline("Direction: ")
                                if redirect:
                                    history.append({"role": "assistant", "content": pending_draft})
                                    history.append({"role": "user", "content": f"Revise: {redirect}"})
                                    with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
                                        pending_draft = force_draft(
                                            history, cfg.api_key, cfg.model, all_paragraphs,
                                            voyage_api_key=voyage_api_key, system=PERSPECTIVE_SYSTEM,
                                        )
                            elif choice == "k":
                                history.append({"role": "assistant", "content": pending_draft})
                                history.append({"role": "user", "content": "Let's keep going."})
                                pending_draft = None
                                with Live(Spinner("dots", text="Continuing..."), refresh_per_second=10, console=console):
                                    _, question = qa_turn(
                                        history, cfg.api_key, cfg.model, all_paragraphs,
                                        voyage_api_key=voyage_api_key, system=PERSPECTIVE_SYSTEM,
                                    )
                                if question:
                                    console.print(f"\n[cyan]{question}[/cyan]\n")
                                    history.append({"role": "assistant", "content": question})
                        else:
                            user_input = _read_multiline()
                            if not user_input or user_input.lower() == "done":
                                break
                            if user_input.lower() == "draft":
                                with Live(Spinner("dots", text="Drafting..."), refresh_per_second=10, console=console):
                                    pending_draft = force_draft(
                                        history, cfg.api_key, cfg.model, all_paragraphs,
                                        voyage_api_key=voyage_api_key, system=PERSPECTIVE_SYSTEM,
                                    )
                            else:
                                history.append({"role": "user", "content": user_input})
                                exchange_count += 1
                                if exchange_count >= MAX_EXCHANGES:
                                    with Live(Spinner("dots", text="Drafting..."), refresh_per_second=10, console=console):
                                        pending_draft = force_draft(
                                            history, cfg.api_key, cfg.model, all_paragraphs,
                                            voyage_api_key=voyage_api_key, system=PERSPECTIVE_SYSTEM,
                                        )
                                else:
                                    with Live(Spinner("dots", text="Thinking..."), refresh_per_second=10, console=console):
                                        pending_draft, question = qa_turn(
                                            history, cfg.api_key, cfg.model, all_paragraphs,
                                            voyage_api_key=voyage_api_key, system=PERSPECTIVE_SYSTEM,
                                        )
                                    if question:
                                        console.print(f"\n[cyan]{question}[/cyan]\n")
                                        history.append({"role": "assistant", "content": question})

                    if accepted_shift:
                        _flush_stdin()
                        save_role = input("Role for this paragraph [General]: ").strip() or "General"
                        save_section = input("Section name [Career shift]: ").strip() or "Career shift"
                        append_to_library(
                            priority_file, save_role, save_section, accepted_shift,
                            {"strength": "high", "via": "build", "angle": "pivot"},
                        )
                        console.print(f"\n[green]Shift paragraph saved to {priority_file.name}[/green]\n")

        from datetime import date
        if cfg.profile_file.exists():
            archive_name = cfg.profile_file.with_name(
                f"{cfg.profile_file.stem}_{date.today().isoformat()}.toml"
            )
            cfg.profile_file.rename(archive_name)
            console.print(f"[dim]Previous profile archived to {archive_name.name}[/dim]")
        write_profile(cfg.profile_file, final)
        console.print(f"\n[green]Saved:[/green] {cfg.profile_file}\n")
        console.print("[dim]Run `coverletter` to generate a letter — the thesis and alignment report will now use your profile.[/dim]\n")
    else:
        console.print("[dim]Not saved.[/dim]\n")


@main.command("seed")
@click.option("--file", "-f", "input_file", default=None, help="Path to source material file (txt or pdf)")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs file to write into")
@click.option("--model", "-m", default=None, help="Claude model to use")
@click.pass_context
def seed_library(ctx: click.Context, input_file: str | None, paragraphs: str | None, model: str | None) -> None:
    """Extract and strengthen paragraphs from existing career material.

    Paste a cover letter, resume, LinkedIn bio, or bullets — the tool structures
    it into library paragraphs, strengthens the argument without inventing anything,
    and flags what Q&A would make each paragraph stronger.
    """
    from rich.rule import Rule
    from rich.live import Live
    from rich.spinner import Spinner
    from coverletter.seed import extract_from_material

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs, model_override=model)

    console.print("\n[bold blue]Paragraph Library Seeder[/bold blue]\n")
    console.print(
        "[dim]Paste your existing career material — cover letter, resume bullets, LinkedIn bio,\n"
        "or any mix. The tool extracts your paragraphs into the library using your own language,\n"
        "tags them by role and angle, and flags what Q&A would make each stronger.[/dim]\n"
    )

    # --- Read input ---
    material = ""
    if input_file:
        path = Path(input_file)
        if not path.exists():
            console.print(f"[red]File not found:[/red] {input_file}")
            return
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                material = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as e:
                console.print(f"[red]Could not read PDF:[/red] {e}")
                return
        elif suffix == ".odt":
            try:
                from odf.opendocument import load as odf_load
                from odf.text import P
                doc = odf_load(str(path))
                paragraphs_odt = doc.contentxml().decode("utf-8", errors="ignore")
                # Extract plain text from all <text:p> elements
                import re as _re
                material = "\n".join(
                    _re.sub(r"<[^>]+>", "", p)
                    for p in _re.findall(r"<text:p[^>]*>(.*?)</text:p>", paragraphs_odt, _re.DOTALL)
                ).strip()
            except Exception as e:
                console.print(f"[red]Could not read ODT:[/red] {e}")
                return
        else:
            material = path.read_text(encoding="utf-8")
        console.print(f"[dim]Read {len(material):,} chars from {path.name}[/dim]\n")
    else:
        console.print("[dim]Copy your material to your clipboard, then press Enter.[/dim]\n")
        _flush_stdin()
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            return
        material = _read_from_clipboard().strip()
        try:
            sys.stdin = open("/dev/tty", "r")
        except OSError:
            _flush_stdin()

    if not material:
        console.print("[red]No material provided.[/red]")
        return

    # --- Extract ---
    console.print()
    with Live(Spinner("dots", text="Extracting paragraphs..."), refresh_per_second=10, console=console):
        try:
            extracted = extract_from_material(material, cfg.api_key, cfg.model)
        except RuntimeError as e:
            console.print(f"\n[red]Extraction failed:[/red]\n{e}\n")
            return

    console.print(f"[dim]{running_total()}[/dim]\n")
    console.print(f"[bold]{len(extracted)} paragraph(s) extracted.[/bold] Review each below.\n")

    # --- Review loop ---
    # Load existing role types from library so user can file into them
    try:
        existing_roles = [r for r in available_roles(load_paragraphs(cfg.paragraphs_files)) if r != "General"]
    except Exception:
        existing_roles = []

    def _confirm_role(extracted_role: str) -> str:
        """Let user confirm or override the role the model inferred. Press Enter to accept."""
        raw = input(f"Role [{extracted_role}]: ").strip()
        return raw if raw else extracted_role

    accepted: list[dict] = []
    for i, p in enumerate(extracted, 1):
        strength_color = {"high": "green", "medium": "yellow", "low": "red"}.get(p["strength"], "white")
        console.print(Rule(
            f"[bold][{i}/{len(extracted)}] {p['role']} / {p['section']}[/bold]  "
            f"[{strength_color}]{p['angle']} · {p['strength']}[/{strength_color}]",
            style="cyan"
        ))
        console.print()
        console.print(p["text"])
        console.print()
        has_warnings = bool(p.get("_warnings"))
        if has_warnings:
            for w in p["_warnings"]:
                console.print(f"[yellow]⚠ {w}[/yellow]")
            console.print("[yellow]This paragraph has issues the auto-fix could not resolve. Edit before accepting.[/yellow]\n")
        if p["augmentations"]:
            console.print("[dim]Strengthen later with[/dim] [bold]uv run coverletter build[/bold][dim]:[/dim]")
            for aug in p["augmentations"]:
                console.print(f"  [dim]→ {aug}[/dim]")
            console.print()

        _flush_stdin()
        if has_warnings:
            prompt_str = "[E]dit  [S]kip: "
            valid_choices = {"e", "edit", "s", "skip"}
        else:
            prompt_str = "[A]ccept  [E]dit  [S]kip: "
            valid_choices = {"a", "accept", "", "e", "edit", "s", "skip"}

        while True:
            choice = input(prompt_str).strip().lower()
            if choice not in valid_choices and has_warnings:
                console.print("[dim]This paragraph must be edited or skipped — it has unfixed issues.[/dim]")
                continue
            if choice in ("a", "accept", ""):
                role_type = _confirm_role(p["role"])
                p = dict(p, role=role_type)
                accepted.append(p)
                console.print(f"[green]→ Accepted under[/green] [bold]{role_type}[/bold]\n")
                break
            elif choice in ("e", "edit"):
                console.print("[dim]Type replacement paragraph. Blank line when done.[/dim]\n")
                edit_lines = []
                try:
                    while True:
                        line = input("> ")
                        if not line.strip():
                            break
                        edit_lines.append(line)
                except EOFError:
                    pass
                if not edit_lines:
                    console.print("[dim]No edit entered — skipping.[/dim]\n")
                    break
                edited_text = " ".join(edit_lines)
                console.print()
                console.print("[bold]Edited paragraph:[/bold]")
                console.print(edited_text)
                console.print()
                confirm = input("[A]ccept edit  [R]edo  [S]kip: ").strip().lower()
                if confirm in ("s", "skip"):
                    console.print("[dim]→ Skipped.[/dim]\n")
                    break
                elif confirm in ("r", "redo"):
                    continue
                else:
                    p = dict(p, text=edited_text)
                    role_type = _confirm_role(p["role"])
                    p = dict(p, role=role_type)
                    console.print(f"[green]→ Accepted (edited) under[/green] [bold]{role_type}[/bold]\n")
                    accepted.append(p)
                    break
            elif choice in ("s", "skip"):
                console.print("[dim]→ Skipped.[/dim]\n")
                break

    if not accepted:
        console.print("[yellow]No paragraphs accepted. Nothing saved.[/yellow]\n")
        return

    # --- Save ---
    from coverletter.seed import append_paragraphs_to_file, upsert_experience_targets
    # Seed always writes to the base layer — raw extractions, not strengthened.
    # Build writes to library_refined.md (priority layer) after Q&A strengthening.
    target = cfg.paragraphs_files[-1]
    console.print(Rule(style="green"))
    console.print(f"\n[bold]{len(accepted)} paragraph(s) accepted.[/bold] Saving to [cyan]{target}[/cyan]...\n")
    append_paragraphs_to_file(target, accepted)
    console.print("[green]Saved.[/green]\n")

    # Write augmentation questions into experiences.md so coverletter build picks them up
    augs_written = 0
    for p in accepted:
        if p.get("augmentations"):
            upsert_experience_targets(
                cfg.experiences_file,
                name=p["section"],
                company=p.get("company", p["role"]),
                angle=p.get("angle", ""),
                augmentations=p["augmentations"],
            )
            augs_written += 1

    # Summarise augmentations across all accepted paragraphs
    all_augs = [(p.get("company", p["role"]), p["section"], aug) for p in accepted for aug in p.get("augmentations", [])]
    if all_augs:
        console.print("[bold]Q&A agenda saved to experiences.md — run[/bold] [cyan]uv run coverletter build --about \"[experience]\"[/cyan] [bold]to fill these gaps:[/bold]")
        for company, section, aug in all_augs:
            console.print(f"  [dim]{company} / {section}:[/dim] {aug}")
        console.print()

    # Offer profile generation
    if not cfg.profile_file.exists():
        console.print("[dim]No candidate profile found.[/dim]")
        _flush_stdin()
        run_profile = input("Generate profile from this library now? [Y/n]: ").strip().lower()
        if run_profile not in ("n", "no"):
            from coverletter.profile import load_profile, write_profile, suggest_from_library
            all_paragraphs = load_paragraphs(cfg.paragraphs_files)
            console.print()
            with Live(Spinner("dots", text="Generating profile suggestions..."), refresh_per_second=10, console=console):
                try:
                    suggestions = suggest_from_library(all_paragraphs, cfg.api_key, cfg.model)
                except RuntimeError as e:
                    console.print(f"\n[red]Profile generation failed:[/red] {e}\n")
                    return
            console.print(f"[dim]{running_total()}[/dim]\n")
            console.print("[bold]Profile suggestions:[/bold]\n")
            for section, items in suggestions.items():
                if items:
                    console.print(f"  [cyan]{section}:[/cyan]")
                    for item in items:
                        console.print(f"    • {item}")
            console.print()
            console.print(f"[dim]Run [bold]uv run coverletter profile[/bold] to review and save.[/dim]\n")


@main.command("sync")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs MD file")
@click.option("--embed/--no-embed", default=True, show_default=True, help="Compute missing embeddings via Voyage")
@click.option("--angles/--no-angles", default=True, show_default=True, help="Auto-assign missing angles via embedding centroids")
@click.pass_context
def sync_library(ctx: click.Context, paragraphs: str | None, embed: bool, angles: bool) -> None:
    """Sync markdown library to SQLite database.

    Markdown is the source of truth. This command reads all library .md files,
    upserts paragraphs into the DB, computes missing Voyage embeddings, and
    auto-assigns angle tags to paragraphs that lack one using centroid matching.

    Run after editing any library .md file.

    Example:
      coverletter sync
      coverletter sync --no-embed
    """
    from coverletter.db import (
        open_db, db_path, sync_from_markdown, compute_embeddings,
        extract_and_store_sentences, compute_sentence_embeddings,
        assign_angles_canonical, stats,
    )
    from rich.table import Table

    cfg = load_config(paragraphs)
    all_paragraphs = load_paragraphs(cfg.paragraphs_files)

    path = db_path(cfg.paragraphs_files)
    conn = open_db(path)

    with Live(Spinner("dots", text="Syncing paragraphs..."), refresh_per_second=10, console=console):
        counts = sync_from_markdown(conn, all_paragraphs, cfg.paragraphs_files)
    console.print(
        f"Paragraphs: [green]{counts['inserted']} inserted[/green]  "
        f"[yellow]{counts['updated']} updated[/yellow]  "
        f"[red]{counts['retired']} retired[/red]  "
        f"[dim]{counts['unchanged']} unchanged[/dim]"
    )

    if embed and cfg.voyage_api_key:
        with Live(Spinner("dots", text="Embedding paragraphs..."), refresh_per_second=10, console=console):
            n_embedded = compute_embeddings(conn, cfg.voyage_api_key)
        console.print(f"Paragraph embeddings: [green]{n_embedded} computed[/green]")

        with Live(Spinner("dots", text="Extracting sentences..."), refresh_per_second=10, console=console):
            n_sentences = extract_and_store_sentences(conn)
        console.print(f"Sentences extracted: [green]{n_sentences}[/green]")

        with Live(Spinner("dots", text="Embedding sentences..."), refresh_per_second=10, console=console):
            n_sent_embedded = compute_sentence_embeddings(conn, cfg.voyage_api_key)
        console.print(f"Sentence embeddings: [green]{n_sent_embedded} computed[/green]")
    elif embed and not cfg.voyage_api_key:
        console.print("[dim]Skipping embeddings — VOYAGE_API_KEY not set.[/dim]")

    if angles and cfg.voyage_api_key:
        with Live(Spinner("dots", text="Classifying angles..."), refresh_per_second=10, console=console):
            assigned = assign_angles_canonical(conn, cfg.voyage_api_key)
        if assigned:
            console.print(f"Angles assigned: [green]{sum(assigned.values())} primary[/green]")
            for angle, count in sorted(assigned.items(), key=lambda x: -x[1]):
                console.print(f"  [dim]{angle}[/dim]: {count}")
        else:
            console.print("[dim]Angles: nothing new to assign.[/dim]")
    elif angles and not cfg.voyage_api_key:
        console.print("[dim]Skipping angle assignment — VOYAGE_API_KEY not set.[/dim]")

    s = stats(conn)
    console.print()
    table = Table.grid(padding=(0, 2))
    table.add_row("[dim]Paragraphs[/dim]",        str(s["total"]))
    table.add_row("[dim]Embedded[/dim]",           str(s["embedded"]))
    table.add_row("[dim]Sentences[/dim]",          f"{s['sentences']}  ({s['sentences_embedded']} embedded)")
    table.add_row("[dim]With angles[/dim]",        f"{s['paragraphs_with_angle']}  ({s['angle_assignments']} total assignments)")
    table.add_row("[dim]Missing angle[/dim]",      str(s["missing_angle"]))
    table.add_row("[dim]DB[/dim]",                 str(path))
    console.print(table)


@main.command("extract")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs MD file")
@click.option("--model", "-m", default=None, help="Claude model (default: Haiku)")
@click.option("--force", is_flag=True, default=False, help="Re-extract paragraphs already in claims table")
@click.option("--dry-run", is_flag=True, default=False, help="Write review files for Streamlit app — insert nothing")
@click.pass_context
def extract_library(
    ctx: click.Context,
    paragraphs: str | None,
    model: str | None,
    force: bool,
    dry_run: bool,
) -> None:
    """Extract claims, evidence, and conclusions from the paragraph library.

    Judge runs on every claim automatically. Judge alignment is checked against the
    gold standard at the start of every run — warns if accuracy drops below threshold.

    Normal run extracts and inserts directly.
    Dry-run extracts to review files so you can label in the Streamlit app first,
    which handles insertion directly without any additional command.

    Example:
      coverletter extract
      coverletter extract --dry-run
      coverletter extract --force
    """
    from coverletter.db import open_db, db_path
    from coverletter.extract import (
        extract_claims_and_evidence, extract_to_review,
        _write_review_markdown, _EXTRACT_MODEL,
    )

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)
    use_model = model or _EXTRACT_MODEL

    if not cfg.api_key:
        console.print("[red]API key required for extraction.[/red]")
        return

    path = db_path(cfg.paragraphs_files)
    lib_dir = cfg.paragraphs_files[0].parent

    if not path.exists():
        console.print("[red]No database found. Run `coverletter sync` first.[/red]")
        return
    conn = open_db(path)

    already = conn.execute(
        "SELECT COUNT(DISTINCT source_para_hash) FROM claims"
    ).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM paragraphs WHERE active = 1").fetchone()[0]
    pending = total if force else total - already

    if pending == 0:
        console.print(f"[green]All {total} paragraphs already extracted.[/green] Use --force to re-run.")
        return

    if dry_run:
        console.print(
            f"Extracting from {pending} paragraph(s)  [dim]({already} already done)[/dim]"
        )
        console.print("[dim]Judge + alignment check run automatically. Writing review files.[/dim]\n")
        with Live(Spinner("dots", text="Extracting + judging..."), refresh_per_second=10, console=console):
            review_data = extract_to_review(conn, cfg.api_key, use_model, force=force)
        json_path = lib_dir / "extractions_review.json"
        md_path = lib_dir / "extractions_review.md"
        json_path.write_text(json.dumps(review_data, indent=2), encoding="utf-8")
        _write_review_markdown(review_data, md_path)
        n = review_data["paragraph_count"]
        n_claims = sum(len(p["claims"]) for p in review_data["paragraphs"])
        n_rejected = sum(
            1 for p in review_data["paragraphs"]
            for c in p["claims"] if c.get("status") == "rejected"
        )
        console.print(f"[green]Extracted from {n} paragraph(s)[/green] — {n_claims} claim(s)")
        if n_rejected:
            console.print(f"[yellow]Judge pre-rejected {n_rejected} claim(s) — visible in app[/yellow]")
        console.print(f"\n  [dim]{md_path}[/dim]  ← scan this")
        console.print(f"  [dim]{json_path}[/dim]")
        console.print(f"\n  [cyan]uv run streamlit run coverletter/label_evals.py[/cyan]  ← review and insert")
        if review_data.get("judge_accuracy"):
            console.print(f"\n  [dim]Judge alignment: {review_data['judge_accuracy']}[/dim]")
        return

    console.print(
        f"Extracting from {pending} paragraph(s)  [dim]({already} already done)[/dim]"
    )
    console.print("[dim]Judge + alignment check run automatically.[/dim]\n")

    try:
        with Live(Spinner("dots", text="Extracting + judging..."), refresh_per_second=10, console=console):
            n, alignment = extract_claims_and_evidence(
                conn, cfg.api_key, use_model,
                voyage_api_key=cfg.voyage_api_key or "",
                force=force,
            )
    except RuntimeError as e:
        console.print(f"\n[yellow]Not ready for full extraction:[/yellow]\n")
        for line in str(e).splitlines():
            console.print(f"  {line}")
        console.print(f"\n[dim]Run `coverletter onboard` to see the full setup checklist.[/dim]")
        return

    n_claims = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    n_contexts = conn.execute("SELECT COUNT(*) FROM claim_contexts").fetchone()[0]
    n_support = conn.execute("SELECT COUNT(*) FROM support_items").fetchone()[0]
    n_conclusions = conn.execute("SELECT COUNT(*) FROM conclusions").fetchone()[0]
    console.print(f"[green]Extracted from {n} paragraph(s)[/green]")
    console.print(f"  Claims:      {n_claims}")
    console.print(f"  Contexts:    {n_contexts}")
    console.print(f"  Support:     {n_support}")
    console.print(f"  Conclusions: {n_conclusions}")
    if alignment:
        acc = alignment["accuracy"]
        color = "green" if acc >= 0.80 else "yellow" if acc >= 0.65 else "red"
        console.print(f"\n  Judge alignment: [{color}]{acc:.0%}[/{color}]  "
                      f"precision {alignment['precision']:.0%}  recall {alignment['recall']:.0%}")


@main.command("onboard")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs MD file")
@click.pass_context
def onboard_command(ctx: click.Context, paragraphs: str | None) -> None:
    """Check setup readiness and print the steps to get started.

    Run this first as a new user, or any time you want to see what's missing
    before running extract, outline, or generate.

    Example:
      coverletter onboard
    """
    from coverletter.db import open_db, db_path
    from coverletter.extract import _check_gold_standard_readiness, _GS_MIN_APPROVED, _GS_MIN_REJECTED

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)
    path = db_path(cfg.paragraphs_files)
    lib_dir = cfg.paragraphs_files[0].parent
    gs_path = Path(__file__).parent / "evals" / "gold_standard_claims.json"

    steps = []

    # Step 1: library synced?
    db_ok = path.exists()
    para_count = 0
    if db_ok:
        conn = open_db(path)
        para_count = conn.execute("SELECT COUNT(*) FROM paragraphs WHERE active = 1").fetchone()[0]
    steps.append((
        para_count > 0,
        f"Library synced ({para_count} paragraphs)" if para_count > 0 else "Library not synced",
        "coverletter sync",
    ))

    # Step 2: extraction dry-run done?
    review_file = lib_dir / "extractions_review.json"
    review_exists = review_file.exists()
    steps.append((
        review_exists,
        "Extraction review file exists" if review_exists else "No extraction review file yet",
        "coverletter extract --dry-run",
    ))

    # Step 3: gold standard ready?
    gs_ready, gs_msg = _check_gold_standard_readiness()
    if gs_path.exists():
        gs = json.loads(gs_path.read_text(encoding="utf-8"))
        gs_approved = sum(1 for e in gs.get("examples", []) if e["label"] == "approved")
        gs_rejected = sum(1 for e in gs.get("examples", []) if e["label"] == "rejected")
        gs_label = f"Gold standard: {gs_approved} approved, {gs_rejected} rejected"
    else:
        gs_approved, gs_rejected = 0, 0
        gs_label = "No gold standard yet"
    steps.append((
        gs_ready,
        gs_label,
        "uv run streamlit run coverletter/label_evals.py  ← label claims, check 'Save as gold standard'",
    ))

    # Step 4: claims in DB?
    claims_count = 0
    if db_ok:
        conn = open_db(path)
        claims_count = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    steps.append((
        claims_count > 0,
        f"Claims extracted ({claims_count} in DB)" if claims_count > 0 else "No claims in DB yet",
        "coverletter extract",
    ))

    console.print("\n[bold]Setup checklist[/bold]\n")
    all_done = True
    next_step_shown = False
    for done, label, cmd in steps:
        icon = "[green]✅[/green]" if done else "[yellow]⬜[/yellow]"
        console.print(f"  {icon}  {label}")
        if not done and not next_step_shown:
            console.print(f"       [cyan]→ {cmd}[/cyan]")
            next_step_shown = True
            all_done = False

    if all_done:
        console.print(f"\n[green]Ready.[/green] Next steps:")
        console.print(f"  [cyan]coverletter outline <jd_file>[/cyan]  — build claim-driven outline")
        console.print(f"  [cyan]coverletter outline <jd_file>[/cyan]  — build claim-driven outline (generation from outline coming)")
    else:
        console.print(f"\n[dim]Re-run `coverletter onboard` after each step to track progress.[/dim]")

    console.print()


@main.command("outline")
@click.argument("jd_file", type=click.Path(exists=True, path_type=Path))
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs MD file")
@click.option("--model", "-m", default=None, help="Claude model")
@click.option("--company", "-c", default=None, help="Company name (used in output filename)")
@click.option("--output", "-o", default=None, help="Output path for outline markdown")
@click.pass_context
def build_outline_command(
    ctx: click.Context,
    jd_file: Path,
    paragraphs: str | None,
    model: str | None,
    company: str | None,
    output: str | None,
) -> None:
    """Build an editable claim-evidence outline from the library for a given JD.

    Pulls relevant claims from the DB, groups them into argument-driven paragraph
    blocks, and writes a markdown outline you edit before generating the letter.

    Requires `coverletter extract` to have been run first to populate claims.

    Example:
      coverletter outline jobs/acme_jd.md --company Acme
      coverletter outline jobs/acme_jd.md -c Acme -o outlines/acme_outline.md
    """
    from coverletter.db import open_db, db_path
    from coverletter.align import generate_argument
    from coverletter.outline import build_outline
    from coverletter.profile import load_profile

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)
    use_model = model or cfg.model

    if not cfg.api_key:
        console.print("[red]API key required.[/red]")
        return

    path = db_path(cfg.paragraphs_files)
    if not path.exists():
        console.print("[red]No database found. Run `coverletter sync` first.[/red]")
        return

    conn = open_db(path)
    n_claims = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    if n_claims == 0:
        console.print("[red]No claims in DB. Run `coverletter extract` first.[/red]")
        return

    jd = jd_file.read_text(encoding="utf-8")
    company_name = company or jd_file.stem.replace("_", " ").title()

    # Generate thesis from JD
    profile = load_profile(cfg.paragraphs_files)
    console.print(f"Building outline for [cyan]{company_name}[/cyan] — {n_claims} claims in DB\n")

    with Live(Spinner("dots", text="Generating thesis..."), refresh_per_second=10, console=console):
        thesis = generate_argument(jd, cfg.api_key, use_model, profile)

    console.print(f"[dim]Thesis:[/dim] {thesis}")
    _flush_stdin()
    thesis_edit = input("Edit thesis (Enter to keep): ").strip()
    if thesis_edit:
        thesis = thesis_edit
    console.print()

    with Live(Spinner("dots", text="Assembling outline..."), refresh_per_second=10, console=console):
        outline_md, relevant_claims, category_scores, gaps = build_outline(
            conn, jd, thesis,
            api_key=cfg.api_key,
            model=use_model,
            company=company_name,
            voyage_api_key=cfg.voyage_api_key or "",
            embed_model=cfg.embed_model,
        )

    # Write output
    if output:
        out_path = Path(output)
    else:
        safe = re.sub(r"[^a-z0-9]+", "_", company_name.lower()).strip("_")
        out_path = jd_file.parent / f"{safe}_outline.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(outline_md, encoding="utf-8")

    # Record application and capture category/claim scores for analytics
    from coverletter.db import record_application, record_category_scores, record_claim_scores, record_gaps
    application_id = record_application(conn, company_name, "", jd)
    if category_scores:
        record_category_scores(conn, application_id, category_scores)
    if relevant_claims:
        scored_claims = [
            {
                "claim_id": c["id"],
                "argument_category": (c.get("argument_categories") or ["unknown"])[0],
                "similarity_score": c.get("_similarity_score", 0.0),
                "in_outline": True,
                "in_letter": False,
            }
            for c in relevant_claims
        ]
        record_claim_scores(conn, application_id, scored_claims)
    if gaps:
        record_gaps(conn, application_id, gaps)

    console.print(f"[green]Outline written:[/green] {out_path}")
    console.print(f"[dim]Application recorded (id={application_id}) — update outcome later with `coverletter outcome`[/dim]")

    if gaps:
        console.print(f"\n[yellow]JD gaps ({len(gaps)} uncovered requirements):[/yellow]")
        for g in gaps:
            cat = g.get("inferred_category", "")
            console.print(f"  [dim]·[/dim] {g['requirement_text']}" + (f" [dim][{cat}][/dim]" if cat else ""))
        console.print("[dim]These will appear in `coverletter analytics` after multiple applications.[/dim]")

    console.print(f"\nEdit the outline, then:")
    console.print(f"  [cyan]coverletter generate --from-outline {out_path} {jd_file}[/cyan]")


@main.command("generate")
@click.option("--from-outline", "outline_file", default=None, type=click.Path(exists=True, path_type=Path),
              help="Path to an edited outline markdown file (from coverletter outline)")
@click.argument("jd_file", type=click.Path(exists=True, path_type=Path))
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs file")
@click.option("--model", "-m", default=None, help="Claude model")
@click.option("--no-save", is_flag=True, default=False, help="Skip saving to file")
@click.pass_context
def generate_from_outline_command(
    ctx: click.Context,
    outline_file: Path | None,
    jd_file: Path,
    paragraphs: str | None,
    model: str | None,
    no_save: bool,
) -> None:
    """Generate a cover letter from an edited outline.

    The outline is produced by `coverletter outline`, edited by you, then
    passed here. Anchor phrases from the outline appear in the letter verbatim.
    Source paragraphs provide voice and register.

    Example:
      coverletter generate --from-outline acme_outline.md acme_jd.md
    """
    from coverletter.outline import parse_outline, build_outline_user_message
    from coverletter.prompt import OUTLINE_SYSTEM_PROMPT
    from coverletter.db import open_db, db_path
    from rich.panel import Panel
    from rich.markdown import Markdown

    if not outline_file:
        console.print("[red]--from-outline is required.[/red]")
        console.print("[dim]Run `coverletter outline <jd>` first to produce an outline.[/dim]")
        return

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs, model_override=model)
    use_model = model or cfg.model
    profile = load_profile(cfg.profile_file)

    if not cfg.api_key:
        console.print("[red]API key required.[/red]")
        return

    jd = jd_file.read_text(encoding="utf-8")

    # Parse the outline
    outline = parse_outline(outline_file)
    company = outline.get("company", "")

    if not outline["paragraphs"]:
        console.print("[red]No paragraph blocks found in outline. Check the file format.[/red]")
        return

    console.print(f"\n[bold blue]Generate from Outline[/bold blue]")
    console.print(f"Outline:  [dim]{outline_file.name}[/dim]")
    console.print(f"Company:  [bold]{company}[/bold]")
    console.print(f"Thesis:   [dim]{outline['thesis'][:80]}...[/dim]" if len(outline['thesis']) > 80 else f"Thesis:   [dim]{outline['thesis']}[/dim]")
    console.print(f"Blocks:   {len(outline['paragraphs'])} paragraph(s)\n")

    # Open DB for source paragraph lookups and analytics capture
    db = db_path(cfg.paragraphs_files)
    if not db.exists():
        console.print("[yellow]Warning: DB not found — source paragraph voice references unavailable.[/yellow]")
        conn = None
        application_id = None
    else:
        conn = open_db(db)
        from coverletter.db import record_application, ensure_category_embeddings
        from coverletter.provider import get_provider as _get_provider
        ensure_category_embeddings(conn, cfg.voyage_api_key or "", _get_provider(cfg.model, cfg.api_key))
        # Record this application
        application_id = record_application(conn, company, "", jd)
        console.print(f"[dim]Application recorded (id={application_id})[/dim]")

    # Build profile text for the prompt
    profile_text = ""
    if profile and not profile.is_empty:
        profile_text = profile.as_goals_text()

    # Build user message
    user_message = build_outline_user_message(
        outline,
        conn,
        jd,
        company,
        profile_text=profile_text,
    )

    if conn:
        conn.close()
        conn = None

    # Stream the letter
    anchor_count = sum(
        len(claim["anchors"])
        for para in outline["paragraphs"]
        for claim in para["claims"]
    )
    console.print(f"[dim]{anchor_count} anchor phrase(s) enforced[/dim]\n")

    letter_parts: list[str] = []
    with Live(Spinner("dots", text="Generating..."), refresh_per_second=10, console=console):
        for chunk in stream_cover_letter(OUTLINE_SYSTEM_PROMPT, user_message, cfg.api_key, use_model):
            letter_parts.append(chunk)

    letter_text = "".join(letter_parts)
    console.print(f"[dim]{running_total()}[/dim]\n")
    console.print(Panel(Markdown(letter_text), title=f"[bold]{company or 'Letter'}[/bold]",
                         border_style="cyan", padding=(1, 2)))

    # Build message history for verification and revision
    messages: list[dict] = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": letter_text},
    ]

    # Verification
    console.print()
    _run_verification(letter_text, messages, cfg.api_key, use_model)

    # Alignment report
    _outline_alignment_report(outline, letter_text)

    # Revision loop
    while True:
        console.print()
        _flush_stdin()
        feedback = input("Revise (free text), or Enter to finish: ").strip()
        if not feedback:
            break

        with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
            parts: list[str] = []
            for chunk in stream_revision(OUTLINE_SYSTEM_PROMPT, messages, feedback, cfg.api_key, use_model):
                parts.append(chunk)

        revised = "".join(parts)
        console.print(Panel(Markdown(revised), title="Revised", border_style="cyan", padding=(1, 2)))
        console.print(f"[dim]{running_total()}[/dim]")

        _flush_stdin()
        accept = input("[A]ccept / [R]eject: ").strip().lower()
        messages.append({"role": "user", "content": feedback})
        messages.append({"role": "assistant", "content": revised})
        if accept in ("", "a", "accept", "y", "yes"):
            letter_text = revised

    from coverletter.costs import session_summary
    summary = session_summary()
    if summary:
        console.print(f"[dim]Session cost: {summary}[/dim]\n")

    if not no_save:
        _flush_stdin()
        save_it = input(f"Save to {cfg.output_dir}? [Y/n]: ").strip().lower()
        if save_it in ("", "y", "yes"):
            label = company or "letter"
            saved_md = save_letter(letter_text, cfg.output_dir, label, cfg.author_name)
            console.print(f"[green]Saved (MD):[/green] {saved_md}")
            saved_pdf = save_pdf(letter_text, cfg.output_dir, label, cfg.author_name)
            console.print(f"[green]Saved (PDF):[/green] {saved_pdf}\n")

            # Mark claims that appeared in the letter and update outcome to 'applied'
            if application_id is not None:
                _conn = open_db(db_path(cfg.paragraphs_files))
                from coverletter.db import mark_claims_in_letter, update_application_outcome, infer_paragraph_provenance
                # Collect claim ids from the outline blocks that were used
                used_claim_texts = {
                    claim["text"]
                    for para in outline["paragraphs"]
                    for claim in para["claims"]
                }
                used_ids = [
                    row["id"] for row in _conn.execute("SELECT id, text FROM claims").fetchall()
                    if row["text"] in used_claim_texts
                ]
                mark_claims_in_letter(_conn, application_id, used_ids)
                update_application_outcome(_conn, application_id, "applied")
                infer_paragraph_provenance(_conn)
                _conn.close()
                console.print(f"[dim]Analytics updated — {len(used_ids)} claim(s) marked in letter[/dim]")

            typ_path = cfg.resume_typ_file if hasattr(cfg, "resume_typ_file") else None
            if typ_path and Path(typ_path).exists():
                _flush_stdin()
                make_resume = input("Generate a tailored resume for this application? [y/N]: ").strip().lower()
                if make_resume in ("y", "yes"):
                    ctx.invoke(
                        main.commands["resume"],
                        paragraphs=cfg.paragraphs_files[0].as_posix() if cfg.paragraphs_files else None,
                        company=company or None,
                        base=None,
                        bullets_file=None,
                    )


@main.command("pdf")
@click.argument("letter_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", default=None, help="Output directory (default: same as letter)")
@click.option("--company", "-c", default=None, help="Company name for filename (inferred from filename if omitted)")
@click.option("--paragraphs", "-p", default=None)
@click.pass_context
def render_pdf(
    ctx: click.Context,
    letter_file: "Path",
    output: str | None,
    company: str | None,
    paragraphs: str | None,
) -> None:
    """Render a letter markdown file to PDF.

    Useful after editing a saved letter .md file — regenerates the PDF without
    re-running the full generation pipeline.

    Example:
      coverletter pdf ~/cover-letters/output/2026-05-29_Acme.md
      coverletter pdf letter.md --output ~/Desktop --company "Acme Corp"
    """
    cfg = load_config(paragraphs)
    text = letter_file.read_text(encoding="utf-8")

    if not company:
        stem = letter_file.stem
        parts = stem.split("_", 1)
        company = parts[1].replace("_", " ") if len(parts) > 1 else stem

    output_dir = Path(output) if output else letter_file.parent
    out_path = save_pdf(text, output_dir, company, cfg.author_name)
    console.print(f"[green]PDF saved:[/green] {out_path}")


@main.command("outcome")
@click.argument("company")
@click.argument("result", type=click.Choice(["response", "interview", "offer", "rejected", "withdrew"]))
@click.option("--notes", "-n", default=None, help="Optional notes on this outcome")
@click.option("--paragraphs", "-p", default=None)
@click.pass_context
def record_outcome(ctx: click.Context, company: str, result: str, notes: str | None, paragraphs: str | None) -> None:
    """Update the outcome for a recent application.

    Example:
      coverletter outcome "New York Times" interview
      coverletter outcome Acme rejected --notes "no Spark experience"
    """
    from coverletter.db import open_db, db_path, update_application_outcome
    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)
    path = db_path(cfg.paragraphs_files)
    if not path.exists():
        console.print("[red]No DB found. Run `coverletter sync` first.[/red]")
        return
    conn = open_db(path)
    # Find most recent application for this company
    row = conn.execute(
        "SELECT id, company, role, applied_at FROM applications "
        "WHERE company LIKE ? ORDER BY applied_at DESC LIMIT 1",
        (f"%{company}%",),
    ).fetchone()
    if not row:
        console.print(f"[red]No application found for '{company}'.[/red]")
        conn.close()
        return
    update_application_outcome(conn, row["id"], result, notes)
    conn.close()
    console.print(f"[green]Updated:[/green] {row['company']} ({row['applied_at'][:10]}) → {result}")


@main.command("claims")
@click.pass_context
def show_claims(ctx: click.Context) -> None:
    """Show extraction status per paragraph — how many claims and anchors each has."""
    from coverletter.db import open_db, db_path
    cfg = load_config(ctx.obj.get("paragraphs") if ctx.obj else None)
    conn = open_db(db_path(cfg.paragraphs_files))

    rows = conn.execute(
        """
        SELECT
            p.hash,
            p.role,
            p.angle,
            COUNT(DISTINCT c.id) AS claim_count,
            COUNT(DISTINCT CASE WHEN si.is_anchor = 1 THEN si.id END) AS anchor_count,
            GROUP_CONCAT(c.argument_categories, ', ') AS categories
        FROM paragraphs p
        LEFT JOIN claims c ON c.source_para_hash = p.hash
        LEFT JOIN support_items si ON si.claim_id = c.id AND si.parent_id IS NULL
        GROUP BY p.hash
        ORDER BY p.role, p.angle
        """
    ).fetchall()
    conn.close()

    from rich.table import Table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Role", style="cyan")
    table.add_column("Angle")
    table.add_column("Claims", justify="right")
    table.add_column("Anchors", justify="right")
    table.add_column("Categories")

    for r in rows:
        claim_style = "green" if r["claim_count"] > 0 else "dim"
        table.add_row(
            r["role"] or "",
            r["angle"] or "",
            f"[{claim_style}]{r['claim_count']}[/{claim_style}]",
            str(r["anchor_count"]),
            r["categories"] or "—",
        )

    console.print(table)
    total_claims = sum(r["claim_count"] for r in rows)
    total_anchors = sum(r["anchor_count"] for r in rows)
    no_claims = sum(1 for r in rows if r["claim_count"] == 0)
    console.print(f"\n[dim]{total_claims} claims · {total_anchors} anchors · {no_claims} paragraphs with no claims[/dim]")


@main.command("analytics")
@click.option("--paragraphs", "-p", default=None)
@click.option("--min-gap-count", default=2, help="Minimum applications a gap must appear in to be shown")
@click.pass_context
def show_analytics(ctx: click.Context, paragraphs: str | None, min_gap_count: int) -> None:
    """Cross-application analysis — coverage patterns, recurring gaps, claim usage, JD similarity."""
    from coverletter.db import (
        open_db, db_path, application_summary, recurring_gaps,
        claim_usage_stats, category_coverage_trend, jd_similarity_matrix,
    )
    from rich.table import Table

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)
    path = db_path(cfg.paragraphs_files)
    if not path.exists():
        console.print("[red]No DB found.[/red]")
        return
    conn = open_db(path)

    # --- Applications summary ---
    apps = application_summary(conn)
    if not apps:
        console.print("[dim]No applications recorded yet. Applications are captured when you run `coverletter outline`.[/dim]")
        conn.close()
        return

    console.print(f"\n[bold blue]Application Analytics[/bold blue]  ({len(apps)} application(s))\n")

    t = Table(show_header=True, header_style="bold cyan")
    t.add_column("Company", style="bold")
    t.add_column("Date", style="dim")
    t.add_column("Outcome")
    t.add_column("Claims used", justify="right")
    t.add_column("Gaps", justify="right")
    for a in apps:
        outcome = a["outcome"] or "—"
        outcome_style = {
            "interview": "green", "offer": "bold green",
            "response": "cyan", "rejected": "red", "withdrew": "dim",
        }.get(outcome, "dim")
        t.add_row(
            a["company"],
            (a["applied_at"] or "")[:10],
            f"[{outcome_style}]{outcome}[/{outcome_style}]",
            str(a["claims_in_letter"] or 0),
            str(a["gap_count"] or 0),
        )
    console.print(t)

    # --- Category coverage ---
    cat_trend = category_coverage_trend(conn)
    if cat_trend:
        console.print("\n[bold]Argument category coverage[/bold]")
        console.print("[dim]How often each category is matching and reaching letters[/dim]\n")
        t2 = Table(show_header=True, header_style="bold cyan")
        t2.add_column("Category")
        t2.add_column("Avg score", justify="right")
        t2.add_column("Times in outline", justify="right")
        t2.add_column("Times in letter", justify="right")
        for c in cat_trend:
            t2.add_row(
                c["argument_category"],
                f"{c['avg_score']:.2f}" if c["avg_score"] else "—",
                str(c["times_in_outline"] or 0),
                str(c["times_in_letter"] or 0),
            )
        console.print(t2)

    # --- Recurring gaps ---
    gaps = recurring_gaps(conn, min_count=min_gap_count)
    if gaps:
        console.print(f"\n[bold]Recurring gaps[/bold]  (appearing in ≥{min_gap_count} applications)\n")
        for g in gaps:
            console.print(f"  [yellow]• {g['requirement_text']}[/yellow]")
            console.print(f"    [dim]{g['app_count']} application(s) — {g['companies']}[/dim]")
            if g["inferred_category"]:
                console.print(f"    [dim]category: {g['inferred_category']}[/dim]")
            console.print()

    # --- Claim usage ---
    usage = claim_usage_stats(conn)
    never_used = [c for c in usage if (c["times_in_letter"] or 0) == 0 and (c["times_in_outline"] or 0) == 0]
    high_use = [c for c in usage if (c["times_in_letter"] or 0) >= 2]

    if high_use:
        console.print("[bold]Claims doing the most work[/bold]\n")
        for c in high_use[:5]:
            cats = c["argument_categories"] or ""
            console.print(f"  [green]•[/green] {c['text'][:90]}")
            console.print(f"    [dim]in letter {c['times_in_letter']}x — category: {cats}[/dim]")
        console.print()

    if never_used and len(apps) >= 3:
        console.print(f"[bold]{len(never_used)} claim(s) never reached a letter[/bold]")
        console.print("[dim]These may not be relevant to the roles you're targeting, or may not be strong enough to surface.[/dim]\n")

    # --- JD similarity ---
    sim = jd_similarity_matrix(conn)
    if sim:
        high_sim = [p for p in sim if p["similarity"] >= 0.85]
        low_sim = [p for p in sim if p["similarity"] < 0.60]
        if high_sim:
            console.print("[bold]Very similar JDs[/bold]  (≥0.85 similarity)\n")
            for p in high_sim[:3]:
                console.print(f"  {p['company_a']} ↔ {p['company_b']}  [dim]{p['similarity']}[/dim]")
            console.print()
        if low_sim and len(apps) >= 4:
            console.print("[bold]Most different JDs[/bold]  (<0.60 similarity)\n")
            for p in low_sim[-3:]:
                console.print(f"  {p['company_a']} ↔ {p['company_b']}  [dim]{p['similarity']}[/dim]")
            console.print()

    conn.close()


@main.command("show-library")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs MD file")
@click.pass_context
def show_library(ctx: click.Context, paragraphs: str | None) -> None:
    """Show your paragraph library organized by type."""
    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)
    all_paragraphs = load_paragraphs(cfg.paragraphs_files)

    console.print(f"\n[bold blue]Paragraph Library[/bold blue]")
    for i, f in enumerate(cfg.paragraphs_files):
        label = f"[cyan]layer {i}[/cyan]" if len(cfg.paragraphs_files) > 1 else ""
        console.print(f"[dim]{f}[/dim] {label}")
    console.print()

    def _preview(text: str, width: int = 90) -> str:
        flat = text.replace("\n", " ").strip()
        return flat[:width] + "…" if len(flat) > width else flat

    # --- FRAMES ---
    person_frames = [p for p in all_paragraphs if
        p.meta.get("type") == "frame" and p.meta.get("frame") == "person"
        or (p.meta.get("type") != "frame" and p.meta.get("angle", "").lower() in ("through-line", "pivot", "reframe", "synthesis"))]
    mission_frames = [p for p in all_paragraphs if
        p.meta.get("type") == "frame" and p.meta.get("frame") == "mission"]

    console.print("[bold cyan]FRAMES — PERSON[/bold cyan]  [dim]who you are, how you work, your arc[/dim]")
    if person_frames:
        for p in person_frames:
            angle = p.meta.get("angle", "")
            strength = "[yellow]high[/yellow]" if p.meta.get("strength") == "high" else ""
            console.print(f"  [{p.index}] {strength} [dim]{p.role} / {p.section}[/dim]" + (f" [dim]angle={angle}[/dim]" if angle else ""))
            console.print(f"      [dim]{_preview(p.text, 80)}[/dim]")
    else:
        console.print("  [dim](none)[/dim]")
    console.print()

    console.print("[bold cyan]FRAMES — MISSION[/bold cyan]  [dim]why a specific purpose or kind of org resonates[/dim]")
    if mission_frames:
        for p in mission_frames:
            strength = "[yellow]high[/yellow]" if p.meta.get("strength") == "high" else ""
            console.print(f"  [{p.index}] {strength} [dim]{p.role} / {p.section}[/dim]")
            console.print(f"      [dim]{_preview(p.text, 80)}[/dim]")
    else:
        console.print("  [dim](none — use: coverletter intake --mission)[/dim]")
    console.print()

    # --- BRIDGE ---
    bridge = [p for p in all_paragraphs if
        p.meta.get("type") == "bridge"
        or p.meta.get("angle", "").lower() in ("interpreter", "domain-synthesis")]
    console.print("[bold cyan]BRIDGE[/bold cyan]  [dim]connects technical work to business value[/dim]")
    if bridge:
        for p in bridge:
            strength = "[yellow]high[/yellow]" if p.meta.get("strength") == "high" else ""
            console.print(f"  [{p.index}] {strength} [dim]{p.role} / {p.section}[/dim]")
            console.print(f"      [dim]{_preview(p.text, 80)}[/dim]")
    else:
        console.print("  [dim](none)[/dim]")
    console.print()

    # --- EVIDENCE ---
    evidence_angles = {"through-line", "pivot", "reframe", "synthesis", "interpreter", "domain-synthesis"}
    evidence = [p for p in all_paragraphs if
        p.meta.get("type") == "evidence"
        or (p.meta.get("type") not in ("frame", "bridge")
            and p.meta.get("tone") not in ("opener", "closer")
            and p.meta.get("angle", "").lower() not in evidence_angles
            and p.meta.get("frame") not in ("person", "mission"))]

    by_role: dict[str, list] = {}
    for p in evidence:
        by_role.setdefault(p.role, []).append(p)

    console.print("[bold cyan]EVIDENCE[/bold cyan]  [dim]what you built and owned[/dim]")
    for role, paras in by_role.items():
        console.print(f"  [bold]{role}[/bold] — {len(paras)} paragraph(s)")
        by_section: dict[str, list] = {}
        for p in paras:
            by_section.setdefault(p.section, []).append(p)
        for section, sps in by_section.items():
            console.print(f"    [dim]{section}[/dim] ({len(sps)})")
            for p in sps:
                angle = p.meta.get("angle", "")
                console.print(f"      [{p.index}] [dim]{angle or '—'}[/dim]  {_preview(p.text, 60)}")
    if not by_role:
        console.print("  [dim](none)[/dim]")
    console.print()

    console.print(f"[dim]Total: {len(all_paragraphs)} paragraphs[/dim]\n")

    # Framing inventory
    from coverletter.experiences import load_experiences, inventory_lines
    experiences = load_experiences(cfg.experiences_file)
    if experiences:
        console.print("[bold]Framing Inventory[/bold]")
        console.print(f"[dim]{cfg.experiences_file}[/dim]\n")
        for exp in experiences:
            header = f"[bold]{exp.name}[/bold]"
            if exp.company or exp.years:
                meta = " / ".join(filter(None, [exp.company, exp.years]))
                header += f"  [dim]{meta}[/dim]"
            console.print(header)
            lines = inventory_lines(exp, all_paragraphs)
            if lines:
                for angle, covered in lines:
                    mark = "[green]✓[/green]" if covered else "[red]✗[/red]"
                    console.print(f"  {mark} {angle}")
            else:
                console.print("  [dim](no angles defined)[/dim]")
            console.print()


@main.command("resume")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs file")
@click.option("--company", "-c", default=None, help="Company name for output filename")
@click.option("--base", default=None, help="Path to base resume.typ (overrides config)")
@click.option("--bullets-file", default=None, help="Path to resume_bullets.md (overrides config)")
@click.pass_context
def build_resume(
    ctx: click.Context,
    paragraphs: str | None,
    company: str | None,
    base: str | None,
    bullets_file: str | None,
) -> None:
    """Generate a tailored resume PDF by selecting bullet options per application."""
    from pathlib import Path
    from datetime import date
    from rich.panel import Panel
    from coverletter.resume_parser import load_resume_bullets, find_role_for_company
    from coverletter.typst_builder import (
        compile_typst,
        extract_companies_from_typ,
        replace_company_bullets,
    )

    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)

    typ_path = Path(base) if base else cfg.resume_typ_file
    bullets_path = Path(bullets_file) if bullets_file else cfg.resume_bullets_file

    if not typ_path.exists():
        console.print(f"[red]Base resume not found:[/red] {typ_path}")
        console.print("[dim]Set RESUME_TYP_FILE in .env or use --base[/dim]")
        return

    console.print(f"\n[bold blue]Resume Builder[/bold blue]")
    console.print(f"Base:    [dim]{typ_path}[/dim]")
    console.print(f"Bullets: [dim]{bullets_path}[/dim]\n")

    typ_content = typ_path.read_text(encoding="utf-8")
    companies_in_typ = extract_companies_from_typ(typ_content)
    bullet_roles = load_resume_bullets(bullets_path)

    if not bullet_roles:
        console.print("[yellow]No entries found in resume_bullets.md — nothing to tailor.[/yellow]")
        console.print(f"[dim]Add bullet options to: {bullets_path}[/dim]")
        return

    # For each company in the .typ file that has alternatives, offer selection
    modified = typ_content
    any_changed = False

    for typ_company in companies_in_typ:
        role = find_role_for_company(bullet_roles, typ_company)
        if role is None:
            continue

        all_options: list = []
        for section in role.sections:
            all_options.extend(section.options)

        if not all_options:
            continue

        console.print(f"[bold]{typ_company}[/bold] — {len(all_options)} alternative bullet option(s)\n")

        for i, opt in enumerate(all_options, 1):
            preview = opt.text[:120] + ("..." if len(opt.text) > 120 else "")
            console.print(f"  [cyan]{i}[/cyan]. [dim]{opt.label}[/dim]")
            console.print(f"     {preview}\n")

        console.print(f"  [cyan]K[/cyan]. Keep current resume bullets")
        _flush_stdin()
        raw = input(f"Select [1–{len(all_options)}/K]: ").strip().lower()

        if raw in ("k", ""):
            console.print("[dim]→ Keeping current bullets.[/dim]\n")
            continue

        try:
            choice = int(raw) - 1
            if 0 <= choice < len(all_options):
                selected = [all_options[choice]]
                modified = replace_company_bullets(modified, typ_company, selected)
                console.print(f"[green]→ Using: {all_options[choice].label}[/green]\n")
                any_changed = True
            else:
                console.print("[yellow]Invalid choice — keeping current.[/yellow]\n")
        except ValueError:
            console.print("[yellow]Invalid input — keeping current.[/yellow]\n")

    if not any_changed:
        console.print("[dim]No bullets changed — compiling base resume as-is.[/dim]\n")

    # Write generated .typ and compile
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    slug = company.strip().replace(" ", "_") if company else "resume"
    stem = f"{date.today().isoformat()}_{slug}"
    out_typ = cfg.output_dir / f"{stem}.typ"
    out_pdf = cfg.output_dir / f"{stem}.pdf"

    out_typ.write_text(modified, encoding="utf-8")
    console.print(f"[dim]Compiling {out_typ.name}...[/dim]")

    if compile_typst(out_typ, out_pdf):
        console.print(f"[green]Resume PDF:[/green] {out_pdf}")
    else:
        console.print(f"[yellow]Typst source saved:[/yellow] {out_typ}")
        console.print("[dim]Fix the errors above and run: typst compile <file.typ>[/dim]")
