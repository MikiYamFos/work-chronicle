import re
import sys
import termios
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

console = Console()


def _split_paragraphs(text: str) -> list[str]:
    normalized = re.sub(r"\n{3,}", "\n\n", text)
    return [p.strip() for p in normalized.split("\n\n") if p.strip()]


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in parts if s.strip()]


def _flush_stdin() -> None:
    try:
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        pass


def _prompt_choice(prompt: str, valid: set[str]) -> str:
    _flush_stdin()
    while True:
        try:
            raw = input(prompt).strip().lower()
        except EOFError:
            raw = ""
        if raw in valid:
            return raw
        print(f"Please enter one of: {', '.join(sorted(valid)).upper()}")


def sentence_diff_and_approve(old_text: str, new_text: str) -> str:
    """
    Show changed paragraphs as context. Within each changed paragraph,
    diff at sentence level — A/S/R per changed sentence.
    """
    old_paras = _split_paragraphs(old_text)
    new_paras = _split_paragraphs(new_text)

    if old_paras == new_paras:
        console.print("\n[dim]No changes detected.[/dim]")
        return new_text

    para_ops = SequenceMatcher(None, old_paras, new_paras, autojunk=False).get_opcodes()
    changed = sum(1 for tag, *_ in para_ops if tag != "equal")
    console.print(f"\n[bold]Reviewing changes across {changed} paragraph(s)[/bold]\n")

    result: list[str] = []

    for tag, i1, i2, j1, j2 in para_ops:
        if tag == "equal":
            result.extend(new_paras[j1:j2])
            continue

        old_block = old_paras[i1:i2]
        new_block = new_paras[j1:j2]

        # For added/removed whole paragraphs, keep it simple
        if tag == "delete":
            for p in old_block:
                console.rule("[red]paragraph removed[/red]")
                console.print(Text(p, style="red dim"))
                console.rule()
                if _prompt_choice("[K]eep  [D]iscard: ", {"k", "d"}) == "k":
                    result.append(p)
                    console.print("[dim]→ Kept.[/dim]")
                else:
                    console.print("[dim]→ Removed.[/dim]")
            console.print()
            continue

        if tag == "insert":
            for p in new_block:
                console.rule("[green]new paragraph[/green]")
                console.print(Text(p, style="green"))
                console.rule()
                if _prompt_choice("[A]ccept  [S]kip: ", {"a", "s"}) == "a":
                    result.append(p)
                    console.print("[dim]→ Accepted.[/dim]")
                else:
                    console.print("[dim]→ Skipped.[/dim]")
            console.print()
            continue

        # replace — diff at sentence level within paired paragraphs
        pairs = list(zip(old_block, new_block))
        # handle unequal lengths
        for old_extra in old_block[len(pairs):]:
            pairs.append((old_extra, ""))
        for new_extra in new_block[len(pairs):]:
            pairs.append(("", new_extra))

        for old_para, new_para in pairs:
            if old_para == new_para:
                result.append(new_para)
                continue

            old_sents = _split_sentences(old_para) if old_para else []
            new_sents = _split_sentences(new_para) if new_para else []

            sent_ops = SequenceMatcher(None, old_sents, new_sents, autojunk=False).get_opcodes()
            sent_changes = sum(1 for t, *_ in sent_ops if t != "equal")

            if sent_changes == 0:
                result.append(new_para)
                continue

            # Print paragraph context header
            console.rule(f"[bold]paragraph ({sent_changes} sentence change(s))[/bold]")
            assembled: list[str] = []

            for stag, si1, si2, sj1, sj2 in sent_ops:
                if stag == "equal":
                    assembled.extend(new_sents[sj1:sj2])
                    continue

                old_ss = old_sents[si1:si2]
                new_ss = new_sents[sj1:sj2]

                for os, ns in zip(old_ss, new_ss):
                    console.print()
                    console.print(Text(f"  old: {os}", style="red"))
                    console.print(Text(f"  new: {ns}", style="green"))
                    choice = _prompt_choice("  [A]ccept  [S]kip  [R]eword: ", {"a", "s", "r"})
                    if choice == "s":
                        console.print("[dim]  → Kept original.[/dim]")
                        assembled.append(os)
                    elif choice == "r":
                        _flush_stdin()
                        replacement = input("  Type your version: ").strip()
                        assembled.append(replacement if replacement else ns)
                        console.print("[dim]  → Applied.[/dim]")
                    else:
                        console.print("[dim]  → Accepted.[/dim]")
                        assembled.append(ns)

                # Handle unequal sentence counts
                for os in old_ss[len(new_ss):]:
                    console.print(Text(f"  removed: {os}", style="red"))
                    if _prompt_choice("  [K]eep  [D]iscard: ", {"k", "d"}) == "k":
                        assembled.append(os)
                for ns in new_ss[len(old_ss):]:
                    console.print(Text(f"  added: {ns}", style="green"))
                    if _prompt_choice("  [A]ccept  [S]kip: ", {"a", "s"}) == "a":
                        assembled.append(ns)

            result.append(" ".join(assembled))
            console.print()

    return "\n\n".join(result)


def render_letter(letter_text: str) -> None:
    console.print()
    console.print(Panel(Markdown(letter_text), title="Your Cover Letter", border_style="blue"))
    console.print()


def _append_signoff(text: str, author_name: str) -> str:
    signoff = f"Sincerely,\n\n{author_name}" if author_name else "Sincerely,"
    stripped = text.rstrip()
    # Don't double-add if it's already there
    if stripped.endswith(author_name) or stripped.endswith("Sincerely,"):
        return text
    return stripped + "\n\n" + signoff


def save_letter(letter_text: str, output_dir: Path, company: str, author_name: str = "") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = company.strip().replace(" ", "_") if company.strip() else "letter"
    filename = f"{date.today().isoformat()}_{slug}.md"
    path = output_dir / filename
    path.write_text(_append_signoff(letter_text, author_name), encoding="utf-8")
    return path


def _strip_markdown(text: str) -> str:
    """Convert markdown to plain text for PDF rendering."""
    # Replace unicode characters Helvetica can't encode
    text = text.replace("—", "-").replace("–", "-").replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    # Remove horizontal rules
    text = re.sub(r"^---+\s*$", "", text, flags=re.MULTILINE)
    # Remove heading markers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}(.+?)_{1,3}", r"\1", text)
    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def save_pdf(letter_text: str, output_dir: Path, company: str, author_name: str = "") -> Path:
    from fpdf import FPDF

    output_dir.mkdir(parents=True, exist_ok=True)
    slug = company.strip().replace(" ", "_") if company.strip() else "letter"
    filename = f"{date.today().isoformat()}_{slug}.pdf"
    path = output_dir / filename

    plain = _strip_markdown(_append_signoff(letter_text, author_name))

    LINE_H = 6.5
    pdf = FPDF()
    pdf.set_margins(25.4, 25.4, 25.4)  # 1-inch margins
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25.4)
    pdf.set_font("Helvetica", size=11)

    paragraphs = plain.split("\n\n")
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if not para:
            continue
        if i > 0:
            pdf.ln(4)
        pdf.multi_cell(0, LINE_H, para)

    pdf.output(str(path))
    return path
