---
name: handoff-2026-06-09
description: "Session handoff — three-layer library, seed multi-round, clio edit, build paste fix, label_evals criteria rewrite"
metadata: 
  node_type: memory
  type: project
  updated: 2026-06-09
  branch: flow_bugs
---

# Session Handoff — 2026-06-09

All work uncommitted. User does their own commits.

---

## What was built this session

### 1. Three-layer library architecture (config.py)

`_resolve_paragraphs_files` now returns up to three files in priority order:

- Layer 3 (approved): `library_approved.md` — manually line-edited via `clio edit`
- Layer 2 (refined): `library_refined.md` — LLM-validated seed output + build drafts
- Layer 1 (raw): `library.md` — verbatim seed extractions

Critical bug fixed: `os.environ.get("LIBRARY_APPROVED_FILE", "")` returns `""`, `Path("")` is `Path('.')` which is a directory → `IsADirectoryError`. Fixed with `if _approved_env` guard before constructing Path.

### 2. Seed multi-round loop (cli.py)

`clio seed` now loops: after each accept/reject round, asks "Add more material?" and continues until user declines. `_confirm_role` is defined BEFORE the `while True` loop (4-space indent). `all_session_accepted` accumulates across rounds.

### 3. Dual-file save in seed (cli.py, seed.py)

Each seed round saves to BOTH:
- `library.md` — raw verbatim extraction (`text` field)
- `library_refined.md` — LLM-validated/fixed extraction (`text_fixed` field)

`extract_from_material` in seed.py returns both `text` (raw) and `text_fixed` (LLM-fixed) per paragraph.

### 4. clio edit command (cli.py)

New `clio edit` command. Opens each paragraph in `library_refined.md` (or `library.md` if no refined exists) for line-editing in the terminal. Saves edited result to `library_approved.md` (Layer 3).

### 5. Build paste interleaving fix (cli.py)

"What next?" in build changed to clipboard-based input. Avoids stdin paste interleaving with spinner:

```python
console.print("[dim]Copy your next topic or material to your clipboard, then press Enter. Just press Enter to exit.[/dim]")
_flush_stdin()
sentinel = input()
topic = _read_from_clipboard().strip()
if not topic:
    topic = sentinel.strip()
if not topic:
    break
try:
    sys.stdin = open("/dev/tty", "r")
except OSError:
    _flush_stdin()
```

### 6. Profile generation moved to clio init (cli.py)

Profile generation prompt removed from end of `clio seed`. Added as a deliberate step in `clio init` onboarding flow after seed/build completes. Seed now shows a reminder: "Run `clio init` to generate your candidate profile."

### 7. label_evals.py: API keys removed (label_evals.py)

Anthropic and Voyage API key text_input fields removed from sidebar. Keys load silently from `.env`. No UI clutter.

### 8. label_evals.py: approve/reject criteria rewritten (label_evals.py)

Previous copy said "approve if it names something specific the person did, built, or owned" — only described ownership claims (1 of 5 types). Rewrote to show all five valid claim types:

1. Ownership/Decision — named employer + deliverable
2. Approach/Method — how they consistently work
3. Disposition/Character — who they are as an engineer (broad is fine if paragraph backs it up)
4. Motivation/Orientation — what kind of work they find meaningful
5. Personal project

Reject criteria made explicit: skill/capability statement, system-did-it, resume-speak, too generic.

### 9. label_evals.py: gold standard criteria rewritten (label_evals.py)

Gold standard copy updated to match actual claim taxonomy. Disposition/character claims now explicitly called out as valid gold standard approved examples. "Only add if zero hesitation" rule made explicit.

### 10. CHEATSHEET.md (CHEATSHEET.md)

New quick-reference doc: all commands, library layers, typical flows.

### 11. library.md cleaned (work-chronicle)

Removed placeholder template block, bad BritBox/Watch Duration paragraph (wrong facts), hallucinated Universe paragraph. File now starts directly with `## Senior Data Engineer`.

### 12. .gitignore: library_approved.md added

---

## Bugs found and fixed this session

- **`Path("")` → IsADirectoryError**: fixed with `if _approved_env` guard in config.py
- **`_confirm_role` unreachable code**: multiple times during seed refactor — fixed by ensuring `_confirm_role` is defined at 4-space indent BEFORE the `while True` loop
- **Seed not looping**: `while True` multi-round loop added
- **Raw text not saved**: seed was only saving refined text; now saves both to separate files
- **Build paste interleaving**: clipboard-based input at "What next?"
- **Profile generated at end of every seed**: moved to init onboarding
- **API keys showing in Streamlit**: removed, load silently from .env
- **Gold standard UI text incomprehensible**: rewritten based on actual extract.py taxonomy

---

## Files changed this session

```
coverletter/config.py         — three-layer _resolve_paragraphs_files, Path("") guard
coverletter/seed.py           — extract_from_material returns text + text_fixed
coverletter/cli.py            — seed loop, dual save, clio edit, build clipboard input, profile in init
coverletter/label_evals.py    — API keys removed, criteria rewritten, gold standard rewritten
CHEATSHEET.md                 — new quick reference
.gitignore                    — library_approved.md added
```

Work-chronicle clone:
```
library.md                    — placeholder + bad paragraphs removed
```

---

## State of the two repos

**cover-letter-generator** (dev) — branch `flow_bugs`
All changes above. Uncommitted. This is the source of truth for code.

**work-chronicle** (user's working clone) — branch `flow_bugs`
Needs a `git pull origin flow_bugs` after dev is committed and pushed to get the code changes.
`library.md` was cleaned directly in the clone.

---

## Session 2 additions (continued from context overflow)

### Extraction prompt quality fixes (extract.py)
- Added `━━━ ANCHOR RULE ━━━`: claims must anchor on sharpest specific fact (deadline, scale, failure replaced, consequence to others)
- Added `━━━ CLAIM TEXT FORMATTING ━━━`: no em-dashes, no "not just/only/simply/merely", no topic lists
- All em-dashes inside GOOD/STRONG/RIGHT quoted examples replaced with semicolons/commas
- Removed "work backwards" phrasing from both locations (was being hallucinated verbatim by model)
- Added multiple-claims-per-paragraph rule
- WRONG/RIGHT example uses Meridian Health (fictional, not user's real employer)

### Mixed paragraph handling (seed.py)
- Skip rule stays narrow: RESUME SUMMARIES only (thesis-only openers/closers excluded from skip)
- Mixed paragraphs instruction: "select and quote only the specific sentences. Drop the thesis wrapper."

### Stable paragraph DB ids (parser.py, cli.py, prompt.py)
- `Paragraph.db_id: int | None = None` added to dataclass
- **Universal db_id attachment** in `generate` command: opens DB unconditionally (not gated on Voyage key), stamps every paragraph with its stable DB id from `text_hash` lookup
- Regen path also re-stamps db_ids after loading new paragraphs
- Prompt labels now use `db_id` when set, fall back to `index` only if not in DB
- `clio para` command: `uv run clio para` lists all paragraphs with DB ids; `uv run clio para <id>` shows full text

### Library stripping fix (prompt.py)
- Body paragraphs were being stripped when Voyage key set (only openers/closers/frames kept)
- Fixed to hybrid: openers/closers/frames + top 8 body paragraphs pre-sorted by relevance

### Question judge fix (build.py)
- `judge_context` was only first 300 chars of initial topic — never saw user's answers
- Fixed: `_build_judge_context(messages)` passes full conversation history (last 1200 chars) to `validate_question`

### Other fixes
- `clio claim-add` Rich markup crash: `[dim]` tag split across two print calls — merged
- `clio claims` command: restored as proper DB-querying command
- label_evals.py judge queue approve/reject: items now removed from queue on action
- TEST_CONTENT.md: fictional candidate (Alex Rivera) for peer graders to test full app
- TEST_FLOW.md rewritten: main flow is `uv run clio` (paste), not `clio generate` (file)
- WORKFLOW.md + CHEATSHEET.md + README.md: `uv run clio generate` → `uv run clio` for interactive path

### Rename `generate` → `gen-letter` (PENDING — user approved, not done yet)
User wants `uv run clio gen-letter jds/file.txt` for the file-based path. Hold until stable.

---

## Files changed in session 2

```
coverletter/extract.py        — anchor rule, formatting rules, em-dash cleanup, WRONG/RIGHT example
coverletter/seed.py           — mixed paragraph handling, skip rule scope
coverletter/parser.py         — Paragraph.db_id field
coverletter/cli.py            — universal db_id attachment, clio para, clio claims, claim-add fix, regen db_ids
coverletter/prompt.py         — library hybrid (top 8 body), db_id labels, system prompt note
coverletter/build.py          — _build_judge_context, full conversation history to judge
coverletter/label_evals.py    — judge queue button fix
TEST_CONTENT.md               — new (fictional candidate)
TEST_FLOW.md                  — rewritten (main flow = uv run clio)
WORKFLOW.md, CHEATSHEET.md    — generate → interactive path corrections
README.md                     — same
```

---

## Pending tasks

### Immediate
1. **Commit cover-letter-generator** (all changes from this session) and push to `flow_bugs`
2. **Pull work-chronicle**: `git pull origin flow_bugs` after push
3. **Run full test suite**: `uv run pytest` — verify nothing broken

### Extraction flow (content work)
4. **Run `clio seed`** with more sources to build up library
5. **Run `clio edit`** — line-edit refined paragraphs → library_approved.md
6. **Run `clio extract --dry-run`** — generate extractions_review.json
7. **Label claims** in label_evals.py — now with correct criteria
8. **Run `clio extract`** — write approved claims to DB

### Engineering backlog
- GitHub Actions CI (+2 points toward scoring) — not built
- Streamlit monitoring dashboard (+1 point) — not built
- Continue TEST_FLOW.md end-to-end validation

---

## Key file map

- `coverletter/config.py` — `_resolve_paragraphs_files`, three-layer priority
- `coverletter/seed.py` — `extract_from_material` returns `text` + `text_fixed`
- `coverletter/cli.py` — ~3700 lines; grep before reading
  - `seed` command — multi-round while loop, dual-file save
  - `edit` command — Layer 3 approval flow
  - `_qa_session` — central Q&A hub
  - `build_library` — `clio build` command
- `coverletter/extract.py` — claim taxonomy (5 types), judge prompt, gold standard logic
- `coverletter/label_evals.py` — Streamlit labeling app
- `CHEATSHEET.md` — user-facing quick reference
