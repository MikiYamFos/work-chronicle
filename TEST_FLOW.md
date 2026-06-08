# End-to-End Test Flow

Run all commands from the repo root. Complete each step before moving to the next.

---

## 0. Fresh clone

```bash
git clone <repo-url>
cd work-chronicle
uv sync
```

---

## 1. Init

```bash
uv run clio init
```

- Prompts for ANTHROPIC_API_KEY → paste it
- Prompts for AUTHOR_NAME → type your name
- Prompts for RESUME_FILE → paste path to resume PDF
- Offers to seed or build → choose A (seed) or B (build) or S (skip)

**Verify:**
- `.env` exists and contains your key and name
- `library.md` exists with just the comment block, no placeholder paragraphs
- `experiences.md` exists
- `custom_angles.toml` and `custom_categories.toml` exist

---

## 2. Seed from existing material

```bash
uv run clio seed --file /path/to/resume.pdf
```

- Reviews each extracted paragraph: **[A]ccept / [E]dit / [S]kip**
- Accept at least 3 paragraphs

**Verify:**
- `library.md` has new paragraphs appended (no hard line breaks — prose is one continuous line)
- `experiences.md` has Q&A agenda items written under each accepted paragraph
- No em-dash violation errors on paragraphs you wrote yourself

---

## 3. Build a paragraph from scratch

```bash
uv run clio build
```

- Enter a topic when prompted (e.g. a project or experience)
- Answer the follow-up question
- Type `draft` to force a draft, or wait for the auto-draft after 2 exchanges
- At the draft: **[A]ccept / [R]edirect / [K]eep talking**
- Accept it

**Verify:**
- `library_refined.md` has the new paragraph appended (no hard line breaks)
- `experiences.md` updated with any new Q&A targets

---

## 4. Build your profile

```bash
uv run clio profile
```

- Press **G** to generate suggestions from your library
- Review and edit each section
- Save

**Verify:**
- `candidate_profile.toml` exists and has content in goals, working_style, values

---

## 5. Sync to DB

```bash
uv run clio sync
```

**Verify:**
- Runs without errors
- Reports paragraph count > 0

---

## 6. Check library

```bash
uv run clio show-library
```

**Verify:** paragraphs listed by role and section

---

## 7. Extract claims — dry run

```bash
uv run clio extract --dry-run
```

**Verify:**
- `extractions_review.json` written
- Claims look like real assertions, not summaries

---

## 8. Label claims

```bash
uv run streamlit run coverletter/label_evals.py
```

- Approve good claims
- Reject bad ones with a failure category
- Check "Save as gold standard" on clear unambiguous cases
- Need: 5 approved gold standard + 5 rejected gold standard minimum

**Verify:** claim count updates as you approve

---

## 9. Extract claims — live

```bash
uv run clio extract
```

**Verify:** claims inserted, no errors

---

## 10. Check claims

```bash
uv run clio claims
```

**Verify:** claim counts per paragraph > 0

---

## 11. Generate a letter — classic path

```bash
uv run clio generate
```

- Paste a JD when prompted
- Enter company name

**Verify:**
- Letter streams without errors
- `Indexing resume... N claims indexed (v1)` prints on first run (resume auto-extraction)
- Verification pass runs after the letter
- Alignment report prints with covered/gap breakdown
- Thesis prints
- Revision loop works: enter a gap number, do Q&A, accept a paragraph
- `s` saves the letter to `output/`

---

## 12. Generate a letter — argument-driven path

```bash
uv run clio outline jds/<saved-jd>.txt --company "Company Name"
```

- Edit the outline file it produces (reorder, drop weak claims)

```bash
uv run clio generate --from-outline output/<outline-file>.md jds/<saved-jd>.txt
```

**Verify:** letter references anchor phrases from the outline

---

## 13. Resume re-extraction

```bash
uv run clio resume-extract --force
```

**Verify:** version number increments (v2), claim count printed

---

## 14. Interview prep

```bash
uv run clio interview jds/<saved-jd>.txt --company "Company Name"
```

- Paste an optional recruiter note or hit Enter to skip

**Verify:**
- Briefing streams without errors
- Coverage tags appear: `[RESUME]`, `[LIBRARY]`, `[GAP]`
- Output file written to `output/`

```bash
uv run clio interview jds/<saved-jd>.txt --company "Company Name" --summary
```

**Verify:** shorter version produced

---

## 15. JD management

```bash
uv run clio jd list
uv run clio jd replace <name>    # paste updated JD
```

**Verify:** version change logged, list shows updated JD

---

## 16. Paragraph editor

```bash
uv run streamlit run coverletter/library_diff.py
```

**Verify:**
- Loads without error
- Three columns render when `library_refined.md` exists
- Level 1 coach button works (costs API call)
- Level 2 coach button works (costs API call)
- Save writes to `library_salvaged.md`

---

## 17. Monitoring

```bash
uv run clio log
uv run clio log --tail 50
uv run clio log --sessions 5
```

**Verify:** every command that made API calls appears with token counts and cost

---

## 18. Outcome tracking

```bash
uv run clio outcome "Company Name" interview
uv run clio analytics
```

**Verify:** outcome recorded, analytics runs without error

---

## 19. Tests

```bash
uv run pytest tests/ -v
```

**Verify:** all tests pass, no API calls made
