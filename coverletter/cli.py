import sys
from pathlib import Path

import click
from rich.console import Console
from rich.spinner import Spinner
from rich.table import Table
from rich.live import Live

from coverletter.align import AlignmentResult, alignment_report, generate_thesis
from coverletter.profile import CandidateProfile, load_profile
from coverletter.costs import running_total
from coverletter.coach import WeakSentence, analyze_letter, get_context, rewrite_sentence
from coverletter.config import load_config
from coverletter.llm import stream_cover_letter, stream_revision
from coverletter.output import _flush_stdin, _prompt_choice, render_letter, save_letter, save_pdf
from coverletter.parser import Paragraph, available_roles, filter_by_role, load_paragraphs, library_stats
from coverletter.prompt import SYSTEM_PROMPT, build_user_message, embed_prefilter, prefilter
from coverletter.resume import load_resume
from coverletter.verify import VerbatimViolation, verbatim_check, verify_letter

console = Console()


def read_job_description() -> str:
    console.print(
        "\nPaste the job description below. Press [bold]Ctrl-D[/bold] (or Ctrl-Z on Windows) when done:\n"
    )
    lines = []
    try:
        for line in sys.stdin:
            lines.append(line)
    except KeyboardInterrupt:
        raise SystemExit("\nCancelled.")
    text = "".join(lines).strip()
    if not text:
        raise SystemExit("\nNo job description provided. Exiting.")
    return text


def select_role(all_paragraphs: list[Paragraph]) -> str | None:
    roles = available_roles(all_paragraphs)
    non_general = [r for r in roles if r != "General"]

    if not non_general:
        return None  # only General — no selection needed

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
    """Read until a blank line. Single-line answers just need one extra Enter."""
    console.print(f"[dim]{prompt}(blank line to submit)[/dim]")
    lines: list[str] = []
    try:
        while True:
            line = input()
            if not line and lines:
                break
            lines.append(line)
    except EOFError:
        pass
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
    console.print(Panel("\n".join(lines), title="JD Alignment", border_style="yellow"))


def _gap_loop(
    gaps: "list[str]",
    all_paragraphs: "list[Paragraph]",
    priority_file: "Path",
    cfg: "Config",
    job_description: str,
    seniority_gaps: "list[str] | None" = None,
) -> int:
    """Walk through JD gaps then seniority signal gaps, offering Q&A for each.
    Returns count of paragraphs saved."""
    saved = 0
    console.print()

    all_gaps = [(g, "JD") for g in gaps] + [(g, "Seniority") for g in (seniority_gaps or [])]
    total = len(all_gaps)

    for i, (gap, kind) in enumerate(all_gaps, 1):
        if kind == "Seniority":
            label = f"[yellow]Seniority signal gap {i}/{total}:[/yellow] {gap}"
        else:
            label = f"[bold]JD gap {i}/{total}:[/bold] {gap}"
        console.print(label)
        _flush_stdin()
        choice = input("Address this? [Y/n/done]: ").strip().lower()
        if choice in ("done", "d"):
            break
        if choice in ("n", "no"):
            console.print()
            continue
        result = _qa_session(gap, all_paragraphs, priority_file, cfg, job_description=job_description, gap_description=gap, voyage_api_key=cfg.voyage_api_key)
        if result:
            saved += 1
        console.print()
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


def _run_verification(
    letter_text: str,
    messages: list[dict[str, str]],
    api_key: str,
    model: str,
) -> None:
    """Verify and auto-revise until PASS or MAX_VERIFY_ATTEMPTS."""
    for attempt in range(MAX_VERIFY_ATTEMPTS):
        current = messages[-1]["content"]
        with Live(Spinner("dots", text="Checking quality rules..."), refresh_per_second=10, console=console):
            result = verify_letter(current, api_key, model)

        if result.passed:
            console.print("[green]Quality check: PASS[/green]")
            return

        attempt_label = f"{attempt + 1}/{MAX_VERIFY_ATTEMPTS}"
        n = len(result.failures)
        console.print(f"[yellow]Quality check: fixing {n} issue(s)... ({attempt_label})[/yellow]")

        if attempt == MAX_VERIFY_ATTEMPTS - 1:
            console.print(f"[yellow]Still {n} issue(s) after {MAX_VERIFY_ATTEMPTS} attempts — continuing to revision loop.[/yellow]")
            console.print("[dim]Issues:[/dim]")
            for f in result.failures:
                console.print(f"  [dim]• {f}[/dim]")
            return

        console.print()
        failure_list = "\n".join(f"- {f}" for f in result.failures)
        feedback = (
            "QUALITY FIX REQUIRED. The following violations are hard failures. "
            "Fixing them takes absolute priority over source material preservation — "
            "rewrite or cut the specific violating sentence regardless of where it came from. "
            "Do not make partial fixes. Do not introduce new violations. "
            "Every item below must be resolved:\n\n"
            + failure_list
        )
        with Live(Spinner("dots", text=f"Auto-revising..."), refresh_per_second=10, console=console):
            parts: list[str] = []
            for chunk in stream_revision(SYSTEM_PROMPT, messages, feedback, api_key, model):
                parts.append(chunk)

        revised = "".join(parts)
        messages.append({"role": "user", "content": feedback})
        messages.append({"role": "assistant", "content": revised})
        render_letter(revised)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs MD file")
@click.option("--output", "-o", default=None, help="Directory to save output")
@click.option("--model", "-m", default=None, help="Claude model to use")
@click.option("--role", "-r", default=None, help="Role to filter paragraphs by (skip prompt)")
@click.option("--template", "-t", default=None, help="Name (or substring) of a previous letter to use as template")
@click.option("--resume", "-R", default=None, help="Path to resume file (.pdf, .md, or .txt)")
@click.option("--no-save", is_flag=True, default=False, help="Skip saving to file")
def main(
    ctx: click.Context,
    paragraphs: str | None,
    output: str | None,
    model: str | None,
    role: str | None,
    template: str | None,
    resume: str | None,
    no_save: bool,
) -> None:
    """Cover letter generator — assembles your voice from your own source paragraphs."""
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
        console.print(f"Profile: [dim]{cfg.profile_file}[/dim] ([green]{len(profile.goals)} goal(s), {len(profile.differentiators)} differentiator(s)[/green])")

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

    job_description = read_job_description()

    _flush_stdin()
    company = input("\nCompany name (for filename, optional): ").strip()

    notes: str | None = None
    if template_text:
        _flush_stdin()
        raw_notes = input(
            "\nApplication notes (paragraphs to include, phrasing to emphasize — optional, Enter to skip): "
        ).strip()
        notes = raw_notes or None

    if cfg.voyage_api_key:
        filtered = embed_prefilter(role_paragraphs, job_description, cfg.top_n, cfg.voyage_api_key)
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

    user_message = build_user_message(
        job_description, corrected, role=role, company=company,
        resume=resume_text or None,
        template=template_text, notes=notes,
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

    _run_verification(letter_text, messages, cfg.api_key, cfg.model)
    letter_text = messages[-1]["content"]

    # Verbatim source check — flag sentences not traceable to source paragraphs
    violations = verbatim_check(letter_text, filtered)
    if violations:
        from rich.panel import Panel
        from rich.text import Text
        console.print(f"\n[bold red]{len(violations)} sentence(s) not found verbatim in source:[/bold red]")
        for v in violations:
            console.print()
            console.print(Text(f"  LETTER:  {v.sentence}", style="red"))
            console.print(Text(f"  CLOSEST: {v.best_match}", style="dim"))
            console.print(f"  [dim]similarity: {v.score:.0%}[/dim]")
        console.print()
        console.print("[dim]These sentences may be LLM-paraphrased or invented. Use the revision loop to fix them.[/dim]")
        console.print()
    else:
        console.print("[green]Verbatim check: all body sentences trace to source.[/green]")

    # Letter thesis — what argument is this letter actually making?
    console.print()
    with Live(Spinner("dots", text="Identifying letter thesis..."), refresh_per_second=10, console=console):
        thesis = generate_thesis(job_description, letter_text, cfg.api_key, cfg.model, profile=profile)
    console.print(f"[dim]{running_total()}[/dim]")
    from rich.panel import Panel
    console.print(Panel(f"[bold]Letter thesis:[/bold] {thesis}", border_style="cyan", title="Argument"))
    _flush_stdin()
    thesis_ok = input("Is this the right argument? [Y/n/adjust]: ").strip().lower()
    if thesis_ok not in ("", "y", "yes"):
        if thesis_ok == "n":
            console.print("[dim]Noted. The gap loop and revision loop are where you can redirect the argument.[/dim]")
        else:
            # They typed an adjustment
            console.print(f"[dim]Thesis direction noted: {thesis_ok}[/dim]")
            console.print("[dim]Use the revision loop to push the letter toward this argument.[/dim]")

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
        )

    # Regenerate if new paragraphs were saved
    if new_paragraphs_saved:
        _flush_stdin()
        regen = input(f"\nSaved {new_paragraphs_saved} new paragraph(s). Regenerate letter with new material? [Y/n]: ").strip().lower()
        if regen in ("", "y", "yes"):
            all_paragraphs = load_paragraphs(cfg.paragraphs_files)
            role_paragraphs = filter_by_role(all_paragraphs, role) if role else all_paragraphs
            if cfg.voyage_api_key:
                filtered = embed_prefilter(role_paragraphs, job_description, cfg.top_n, cfg.voyage_api_key)
            else:
                filtered = prefilter(role_paragraphs, job_description, cfg.top_n)
            corrections = load_corrections(corrections_file)
            corrected = apply_corrections(filtered, corrections)
            user_message = build_user_message(
                job_description, corrected, role=role, company=company,
                resume=resume_text or None, template=template_text, notes=notes,
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
            _run_verification(letter_text, messages, cfg.api_key, cfg.model)
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


def _qa_session(
    topic: str,
    all_paragraphs: "list[Paragraph]",
    priority_file: "Path",
    cfg: "Config",
    job_description: str | None = None,
    gap_description: str | None = None,
    voyage_api_key: str = "",
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

    context = _build_initial_context(topic, job_description, gap_description, framing_context=framing_ctx)
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
    MAX_EXCHANGES = 3

    while True:
        if pending_draft is not None:
            # Show draft — A/R/K, no user input needed first
            console.print(Panel(pending_draft, border_style="green", title="Draft"))
            choice = _prompt_choice("[A]ccept  [R]edirect  [K]eep talking: ", {"a", "r", "k"})

            if choice == "a":
                accepted = pending_draft
                break

            elif choice == "r":
                _flush_stdin()
                redirect = _read_multiline("Direction: ")
                if not redirect:
                    continue
                RULES_REMINDER = (
                    "Hard rules: no sentence starts with 'That', no em-dashes, "
                    "no 'actually'/'not just'/'not only'/'not simply', no fake contrast. "
                    "Scan every sentence before writing."
                )
                history.append({"role": "assistant", "content": pending_draft})
                history.append({"role": "user", "content": f"Revise the draft: {redirect}\n\n{RULES_REMINDER}"})
                with Live(Spinner("dots", text="Revising..."), refresh_per_second=10, console=console):
                    pending_draft = force_draft(history, cfg.api_key, cfg.model, all_paragraphs, voyage_api_key=voyage_api_key)

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
            # Waiting for user answer
            _flush_stdin()
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
    save_role = input("Role [Data Engineering]: ").strip() or "Data Engineering"
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
    return accepted


@main.command("build")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs file")
@click.option("--about", "-a", default=None, help="What to build a paragraph about")
@click.pass_context
def build_library(ctx: click.Context, paragraphs: str | None, about: str | None) -> None:
    """Grow your paragraph library through Q&A — add new experiences, projects, or angles."""
    from pathlib import Path
    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)
    all_paragraphs = load_paragraphs(cfg.paragraphs_files)
    # Build always saves to library_refined.md — the priority layer.
    # Seed saves verbatim extractions to library.md (base).
    # library_refined.md overrides library.md at generation time.
    # This is true even if library_refined.md doesn't exist yet — append_to_library creates it.
    base_file = cfg.paragraphs_files[-1]
    priority_file = base_file.parent / "library_refined.md"

    console.print(f"\n[bold blue]Paragraph Builder[/bold blue]  [dim]→ {priority_file.name}[/dim]\n")

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
        _qa_session(topic, all_paragraphs, priority_file, cfg, voyage_api_key=cfg.voyage_api_key)

        _flush_stdin()
        another = input("Build another paragraph? [Y/n]: ").strip().lower()
        if another in ("n", "no"):
            break

        _flush_stdin()
        topic = input("What next? (Enter to exit): ").strip()
        if not topic:
            break


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
            "# Get your key at https://console.anthropic.com\n"
            "ANTHROPIC_API_KEY=sk-ant-...\n\n"
            "# Optional: Voyage AI for semantic paragraph matching (better than keyword)\n"
            "# Get your key at https://www.voyageai.com\n"
            "# VOYAGE_API_KEY=pa-...\n\n"
            "# Your name as it appears on the sign-off\n"
            "AUTHOR_NAME=Your Name\n\n"
            "# Absolute path to your resume PDF (or .md / .txt)\n"
            "# RESUME_FILE=/path/to/your/resume.pdf\n\n"
            "# Where to save generated letters (defaults to ./output)\n"
            "# OUTPUT_DIR=/path/to/output\n\n"
            "# Override the model (defaults to claude-sonnet-4-6)\n"
            "# COVERLETTER_MODEL=claude-opus-4-7\n\n"
            "# How many paragraphs to pass to the model (default 20)\n"
            "# COVERLETTER_TOP_N=20\n",
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
    console.print("  1. Add your [bold]ANTHROPIC_API_KEY[/bold] to .env")
    console.print("  2. Set [bold]AUTHOR_NAME[/bold] in .env")
    console.print()
    console.print("  [bold]If you have existing material[/bold] (cover letter, resume, LinkedIn bio):")
    console.print("    uv run coverletter seed              # paste material, extract paragraphs")
    console.print()
    console.print("  [bold]If you're starting from scratch:[/bold]")
    console.print("    uv run coverletter build --about \"your experience\"")
    console.print()
    console.print("  Then build your profile (do this once before generating letters):")
    console.print("    uv run coverletter profile --model opus")
    console.print()
    console.print("  Then generate your first letter:")
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
    suggestions: dict[str, list[str]] = {"goals": [], "differentiators": [], "focus_areas": [], "avoid": []}
    if choice in ("g", "generate"):
        all_paragraphs = load_paragraphs(cfg.paragraphs_files)
        console.print()
        with Live(Spinner("dots", text="Reading your library and generating suggestions..."), refresh_per_second=10, console=console):
            try:
                suggestions = suggest_from_library(all_paragraphs, cfg.api_key, cfg.model)
            except RuntimeError as e:
                console.print(f"\n[red]Failed to parse suggestions:[/red]\n{e}\n")
                suggestions = {"goals": [], "differentiators": [], "focus_areas": [], "avoid": []}
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
        if current_items:
            console.print("[bold]Entries:[/bold]")
            for i, item in enumerate(current_items, 1):
                console.print(f"  [cyan]{i}.[/cyan] {item}")
            console.print()
            console.print("[dim]→ Press Enter to accept these as-is.[/dim]")
            console.print("[dim]→ Or type replacements line by line (your input replaces the whole list). Blank line when done.[/dim]\n")
        else:
            console.print("[dim]No entries yet. Type one item per line. Blank line when done.[/dim]\n")

        _flush_stdin()
        lines: list[str] = []
        try:
            while True:
                line = input("> ").strip()
                if not line:
                    break
                lines.append(line)
        except EOFError:
            pass

        if not lines and current_items:
            console.print("[dim]→ Keeping current entries.[/dim]\n")
            return current_items
        return lines

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

    # Preview
    console.print(Rule("[bold]Preview[/bold]", style="green"))
    final = {"goals": goals, "differentiators": differentiators, "focus_areas": focus_areas, "avoid": avoid}
    for section, items in final.items():
        if items:
            console.print(f"\n[cyan]{section}:[/cyan]")
            for item in items:
                console.print(f"  • {item}")

    console.print()
    _flush_stdin()
    confirm = input(f"Save to {cfg.profile_file}? [Y/n]: ").strip().lower()
    if confirm not in ("n", "no"):
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
        console.print("[dim]Paste your material below. Press Ctrl-D when done.[/dim]\n")
        _flush_stdin()
        lines = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            pass
        material = "\n".join(lines).strip()

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
    # Seed always writes to the base layer — verbatim extractions, not strengthened.
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


@main.command("show-library")
@click.option("--paragraphs", "-p", default=None, help="Path to paragraphs MD file")
@click.pass_context
def show_library(ctx: click.Context, paragraphs: str | None) -> None:
    """Show a summary of your paragraph library by role."""
    paragraphs = paragraphs or (ctx.obj or {}).get("paragraphs")
    cfg = load_config(paragraphs)
    all_paragraphs = load_paragraphs(cfg.paragraphs_files)
    stats = library_stats(all_paragraphs)

    console.print(f"\n[bold blue]Paragraph Library[/bold blue]")
    for i, f in enumerate(cfg.paragraphs_files):
        label = f"[cyan]layer {i}[/cyan]" if len(cfg.paragraphs_files) > 1 else ""
        console.print(f"[dim]{f}[/dim] {label}")
    console.print()

    total = 0
    for role, sections in stats.items():
        role_total = sum(sections.values())
        total += role_total
        console.print(f"[bold]{role}[/bold] — {role_total} paragraph(s)")
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Section")
        table.add_column("Count", justify="right")
        for section, count in sections.items():
            table.add_row(f"[dim]{section}[/dim]", str(count))
        console.print(table)
        console.print()

    console.print(f"[bold]Total:[/bold] {total} paragraphs\n")

    # Framing inventory — show per-experience angle coverage if experiences.md exists
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
