import re
from pathlib import Path

_SIGN_OFF_RE = re.compile(
    r"\n\s*Sincerely[,.].*$",
    re.IGNORECASE | re.DOTALL,
)


def load_resume(path: Path) -> str:
    """Load resume text from a .pdf, .md, or .txt file."""
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n\n".join(p.strip() for p in pages if p.strip())
        except Exception as e:
            raise SystemExit(f"\nCould not read resume PDF: {e}\n")
    else:
        text = path.read_text(encoding="utf-8")
    return _SIGN_OFF_RE.sub("", text).strip()
