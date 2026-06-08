import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from coverletter.costs import resolve_model

load_dotenv(override=True)

DEFAULT_LIBRARY_FILE = Path.home() / "cover-letters" / "library.md"
DEFAULT_OUTPUT_DIR = Path.home() / "cover-letters" / "output"
DEFAULT_RESUME_FILE = Path.home() / "cover-letters" / "resume.pdf"
DEFAULT_RESUME_TYP_FILE = Path.home() / "Documents" / "resumes" / "typst" / "resume.typ"
DEFAULT_RESUME_BULLETS_FILE = Path("resume_bullets.md")
DEFAULT_CLOSER_FILE = Path.home() / "cover-letters" / "closer.txt"
DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_TOP_N = 100  # safety cap — libraries under this size pass everything through


@dataclass
class Config:
    api_key: str          # active provider key (Anthropic or Mistral)
    voyage_api_key: str   # empty string = fall back to keyword prefilter
    paragraphs_files: list[Path]  # ordered by priority — index 0 is layer 0 (highest)
    resume_file: Path
    resume_typ_file: Path       # base resume.typ for Typst compilation
    resume_bullets_file: Path   # resume_bullets.md with alternative bullet options
    output_dir: Path
    model: str
    top_n: int
    author_name: str
    embed_model: str = ""  # EMBED_MODEL env var; "bge-m3" → local hybrid embed, "" → use provider's embed
    profile_file: Path = Path("candidate_profile.toml")
    experiences_file: Path = Path("experiences.md")
    custom_angles_file: Path = Path("custom_angles.toml")
    custom_categories_file: Path = Path("custom_categories.toml")


def _resolve_paragraphs_files(override: str | None) -> list[Path]:
    """
    Return an ordered list of paragraph files (highest priority first).

    Layer 3 (approved): library_approved.md — manually line-edited and approved
    Layer 2 (refined):  library_refined.md  — LLM-fixed seed output + build drafts
    Layer 1 (raw):      library.md          — verbatim seed extractions
    """
    base = Path(override) if override else (
        Path(os.environ["LIBRARY_FILE"]) if os.environ.get("LIBRARY_FILE")
        else (Path.cwd() / "library.md" if (Path.cwd() / "library.md").exists()
              else DEFAULT_LIBRARY_FILE)
    )

    lib_dir = base.parent
    files: list[Path] = []

    _approved_env = os.environ.get("LIBRARY_APPROVED_FILE", "")
    approved = Path(_approved_env) if _approved_env else lib_dir / "library_approved.md"
    _refined_env = os.environ.get("LIBRARY_REFINED_FILE", "")
    refined = Path(_refined_env) if _refined_env else lib_dir / "library_refined.md"

    if approved.exists():
        files.append(approved)
    if refined.exists():
        files.append(refined)
    files.append(base)

    return files


def load_config(
    paragraphs_override: str | None = None,
    output_override: str | None = None,
    model_override: str | None = None,
    resume_override: str | None = None,
) -> Config:
    # Resolve model first so we know which provider key to require
    model = resolve_model(model_override or os.environ.get("COVERLETTER_MODEL", DEFAULT_MODEL))

    from coverletter.provider import parse_model
    provider_name, _ = parse_model(model)

    if provider_name == "mistral":
        api_key = os.environ.get("MISTRAL_API_KEY", "")
        if not api_key:
            raise SystemExit(
                "\nMISTRAL_API_KEY is not set.\n"
                "Add it to a .env file in the project directory:\n\n"
                "  MISTRAL_API_KEY=...\n\n"
                "Or export it in your shell before running coverletter.\n"
            )
    elif provider_name == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise SystemExit(
                "\nOPENAI_API_KEY is not set.\n"
                "Add it to a .env file in the project directory:\n\n"
                "  OPENAI_API_KEY=sk-...\n\n"
                "Or export it in your shell before running coverletter.\n"
            )
    elif provider_name == "cohere":
        api_key = os.environ.get("COHERE_API_KEY", "")
        if not api_key:
            raise SystemExit(
                "\nCOHERE_API_KEY is not set.\n"
                "Add it to a .env file in the project directory:\n\n"
                "  COHERE_API_KEY=...\n\n"
                "Or export it in your shell before running coverletter.\n"
            )
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise SystemExit(
                "\nANTHROPIC_API_KEY is not set.\n"
                "Add it to a .env file in the project directory:\n\n"
                "  ANTHROPIC_API_KEY=sk-ant-...\n\n"
                "Or export it in your shell before running coverletter.\n"
            )

    voyage_api_key = os.environ.get("VOYAGE_API_KEY", "")
    paragraphs_files = _resolve_paragraphs_files(paragraphs_override)
    resume_file = Path(resume_override) if resume_override else Path(os.environ.get("RESUME_FILE", str(DEFAULT_RESUME_FILE)))
    resume_typ_file = Path(os.environ.get("RESUME_TYP_FILE", str(DEFAULT_RESUME_TYP_FILE)))
    resume_bullets_file = Path(os.environ.get("RESUME_BULLETS_FILE", str(DEFAULT_RESUME_BULLETS_FILE)))
    # Resolve bullets file relative to the first paragraphs file if not absolute
    if not resume_bullets_file.is_absolute() and not resume_bullets_file.exists():
        candidate = paragraphs_files[0].parent / resume_bullets_file
        if candidate.exists():
            resume_bullets_file = candidate
    output_dir = Path(output_override) if output_override else Path(os.environ.get("OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)))
    top_n = int(os.environ.get("COVERLETTER_TOP_N", DEFAULT_TOP_N))
    author_name = os.environ.get("AUTHOR_NAME", "")
    embed_model = os.environ.get("EMBED_MODEL", "").strip().lower()

    profile_file = Path(
        os.environ.get("CANDIDATE_PROFILE_FILE", "candidate_profile.toml")
    )

    # experiences.md — auto-detected alongside the paragraphs file
    experiences_env = os.environ.get("EXPERIENCES_FILE", "")
    if experiences_env:
        experiences_file = Path(experiences_env)
    else:
        candidate_exp = paragraphs_files[0].parent / "experiences.md"
        experiences_file = candidate_exp if candidate_exp.exists() else Path("experiences.md")

    # custom angle/category overrides — auto-detected alongside paragraphs file, gitignored
    _lib_dir = paragraphs_files[0].parent
    custom_angles_file = _lib_dir / "custom_angles.toml"
    custom_categories_file = _lib_dir / "custom_categories.toml"

    return Config(
        api_key=api_key,
        voyage_api_key=voyage_api_key,
        paragraphs_files=paragraphs_files,
        resume_file=resume_file,
        resume_typ_file=resume_typ_file,
        resume_bullets_file=resume_bullets_file,
        output_dir=output_dir,
        model=model,
        top_n=top_n,
        author_name=author_name,
        embed_model=embed_model,
        profile_file=profile_file,
        experiences_file=experiences_file,
        custom_angles_file=custom_angles_file,
        custom_categories_file=custom_categories_file,
    )
