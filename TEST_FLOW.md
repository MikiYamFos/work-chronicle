# End-to-End Test Flow

Run all commands from the repo root. Use `TEST_CONTENT.md` for source material if you don't have your own.

---

## 0. Setup

```bash
git clone <repo-url>
cd work-chronicle
uv sync
cp .env.example .env   # then add your ANTHROPIC_API_KEY
```

---

## 1. Init

```bash
uv run clio init
```

- Prompts for ANTHROPIC_API_KEY → paste it
- Prompts for AUTHOR_NAME → type your name
- Prompts for RESUME_FILE → paste path to a PDF or hit Enter to skip
- Offers to seed or build → choose S (skip) for now

**Verify:**
- `.env` exists and contains your key and name
- `library.md` exists (empty template)

---

## 2. Seed your library

Paste one or more paragraphs from `TEST_CONTENT.md` (or your own resume/cover letter).

```bash
uv run clio seed
```

- Choose **P** (paste) when prompted for source type
- Paste a paragraph or two from `TEST_CONTENT.md`
- Review each extracted paragraph: **[A]ccept / [E]dit / [S]kip**
- Accept at least 3

Repeat with more paragraphs if you want more coverage:

```bash
uv run clio seed
```

**Verify:**
- `library.md` has paragraphs appended
- `library_refined.md` exists with LLM-fixed versions

---

## 3. Sync to DB

```bash
uv run clio sync
```

**Verify:** runs without errors, reports paragraph count > 0

---

## 4. Extract claims — dry run

```bash
uv run clio extract --dry-run
```

**Verify:** `extractions_review.json` written, no DB writes

---

## 5. Label claims

```bash
uv run streamlit run coverletter/label_evals.py
```

- Approve good claims, reject bad ones with a failure category
- Mark "Save as gold standard" on at least 5 approved and 5 rejected — **required before live extraction**

**Verify:** claim count updates as you approve

---

## 6. Extract claims — live

```bash
uv run clio extract
```

**Verify:** claims inserted, no errors

---

## 7. Check claims

```bash
uv run clio claims
```

**Verify:** claims listed by source, count > 0

---

## 8. Build your profile

```bash
uv run clio profile
```

- Press **G** to generate suggestions from your library
- Review and save

**Verify:** `candidate_profile.toml` has content in goals, working_style, values

---

## 9. Generate a letter — main flow

This is the primary flow. Copy the sample JD from `TEST_CONTENT.md` to your clipboard, then:

```bash
uv run clio
```

- Paste the JD when prompted (or paste from clipboard)
- Enter company name: `Greenfield Analytics`

**Inside generate — what to test:**

1. **Gap list appears** — numbered list of JD requirements not covered by your library
2. **Enter a gap number** (e.g. `2`) → Q&A session starts
3. **Answer the questions** — give specific answers, not abstract ones
4. **`draft`** — force a draft paragraph at any point
5. **Accept the paragraph** → it appends to `library_refined.md` and fills the gap
6. **Repeat** for 1-2 more gaps
7. **`s`** → save the letter to `output/`

**Verify:**
- Letter streams without errors
- Gap list shows covered items dimmed and uncovered items in red/yellow
- Q&A follow-up question fires after first answer
- Accepted paragraph appears in `library_refined.md`
- Saved letter appears in `output/`
- Alignment report prints at end showing covered/gap breakdown

---

## 10. Revision loop

Run again on the same JD:

```bash
uv run clio
```

After the letter streams:
- Enter **`r`** → revision loop
- Enter a paragraph number to revise
- Give revision feedback
- Accept the revised paragraph

**Verify:** revised paragraph replaces the original in the letter

---

## 11. Add a manual claim

```bash
uv run clio claim-add
```

- Enter claim text in your own words
- Choose context type (g = general, e = employer, p = project)
- Confirm

```bash
uv run clio claims --source manual
```

**Verify:** your claim appears

---

## 12. Build a paragraph from scratch

```bash
uv run clio build --about "a specific project or experience"
```

- Answer the Q&A questions
- Type `draft` to force a draft
- Accept it

**Verify:** paragraph appears in `library_refined.md`

---

## 13. File-based path (optional — if you have a saved JD file)

```bash
uv run clio generate jds/test_jd.txt --company "Greenfield Analytics"
```

**Verify:** letter streams, gap analysis runs, `s` saves it

---

## 14. Argument-driven path (optional, requires claims in DB)

```bash
uv run clio outline jds/test_jd.txt --company "Greenfield Analytics"
```

- Edit the outline file it produces

```bash
uv run clio generate --from-outline output/<outline-file>.md jds/test_jd.txt
```

**Verify:** letter references anchor phrases from the outline

---

## 15. Interview prep

```bash
uv run clio interview jds/test_jd.txt --company "Greenfield Analytics"
```

**Verify:**
- Briefing streams without errors
- Coverage tags appear: `[RESUME]`, `[LIBRARY]`, `[GAP]`
- Output file written to `output/`

---

## 16. Monitoring

```bash
uv run clio log --tail 20
```

**Verify:** every API call appears with token counts and estimated cost

---

## 17. Outcome tracking

```bash
uv run clio outcome "Greenfield Analytics" interview
uv run clio analytics
```

**Verify:** outcome recorded, analytics runs without error

---

## 18. Tests

```bash
uv run pytest tests/ -v
```

**Verify:** all pass, no API calls made
