# clio Cheatsheet

## First-time setup
```bash
uv run clio init          # interactive setup: API keys, seed, profile
```

---

## Building your library

| What | Command |
|---|---|
| Seed from a file (resume, cover letter, bio) | `uv run clio seed --file resume.pdf` |
| Seed by pasting from clipboard | `uv run clio seed` |
| Q&A to write a paragraph from scratch | `uv run clio build` |
| Q&A for a specific experience | `uv run clio build --about "BritBox watch pipeline"` |
| Line-edit and approve paragraphs (Layer 3) | `uv run clio edit` |
| View library by role and section | `uv run clio show-library` |

**Library layers (priority order for generation):**
1. `library_approved.md` — manually line-edited and approved (highest)
2. `library_refined.md` — gap Q&A drafts, `clio build` output (high)
3. `library.md` — verbatim seed extractions, raw paragraphs (base)

---

## Profile and sync

```bash
uv run clio profile       # build/edit candidate profile (goals, values, working style)
uv run clio sync          # load library into DB, compute embeddings
uv run clio extract       # extract claims from library (needed for outline + interview)
```

---

## Generating a letter

```bash
uv run clio                                              # paste JD interactively (main path)
uv run clio generate jds/job.txt --company X             # file-based (JD already saved)
uv run clio outline jds/job.txt --company X              # build an argument outline first
uv run clio generate --from-outline output/outline.md jds/job.txt
```

**Inside the letter session:**
- Gap numbers → Q&A to fill a missing argument
- `s` → save letter to `output/`
- `r` → revision loop (targeted paragraph edits)

---

## Interview prep

```bash
uv run clio interview jds/job.txt --company X
uv run clio interview jds/job.txt --company X --summary   # shorter version
```

---

## JD management

```bash
uv run clio jd list
uv run clio jd replace <name>     # paste updated JD, version is logged
```

---

## Tracking

```bash
uv run clio log                   # all API calls with token counts and cost
uv run clio log --tail 50
uv run clio outcome "Company" interview   # record application outcome
uv run clio analytics             # outcome summary
```

---

## Evaluation

```bash
uv run streamlit run coverletter/label_evals.py    # label claims (approve/reject)
uv run python coverletter/evals/retrieval_eval.py  # BM25 vs semantic retrieval eval
```

---

## Typical flow

```
init → seed (repeat with different sources) → profile → sync → extract → generate
```

```
generate → [quality check? y/N] → gap Q&A → accept paragraph → regen → save letter → outcome
```

**Evidence retrieval — what the model sees:**
- Angles scored against JD: ★ REQUIRED (≥ 0.45 cosine) must appear as claims; SUPPORTING woven in
- Paragraphs written in a previous gap session for this JD are guaranteed in evidence (by JD hash)
- Quality check is opt-in; fix proposal is opt-in — skip both to keep costs down
