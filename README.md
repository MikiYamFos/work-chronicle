# WorkerChronicle — a worker's experience library and cover letter generator

Engineers ship constantly. Projects stack up. Two years later you remember you built something important but you've lost the nuance — what was actually at stake, what made it hard, what you had to figure out, what broke, what downstream decisions depended on your work. The resume bullet survives. The story doesn't.

The gap between "what I actually did" and "what I can articulate I did to an outsider" is enormous for most engineers. That gap costs you in interviews, in cover letters, in performance reviews, in any moment where you need someone who wasn't there to understand the value of your work.

I built this tool because I was writing a lot of cover letters and kept losing the pivotal details of my own work. Generic LLM is almost perfectly wrong for the task of writing cover letters — it flattens your story, over-polishes your voice, loses the facts, and produces something that sounds like a cover letter while destroying the evidence that would actually make it compelling.

This tool does the opposite. Your paragraph library contains your specific experiences in your own words — the ownership claims, the technical decisions, the evidence that makes those claims credible. The letter is assembled from that material. The model writes sentences grounded in your library rather than inventing generic ones. Library quality directly determines letter quality — a thin library produces a thin letter, a specific library produces a specific letter.

**Letters are argument-driven, not assembled from paragraphs.** The tool extracts atomic claims from your library — what you owned, how you work, who you are as an engineer — and groups them into a logical argument against what the JD actually requires. Every claim in the letter has evidence behind it from your own writing.

This tool works for anyone — not just engineers. If you're working through a career transition or have a non-standard work history, I'd especially love to hear how it works for you!

---

## Prerequisites

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com) (required)
- **Voyage AI key** — [voyageai.com](https://www.voyageai.com) (optional but strongly recommended — enables semantic paragraph matching; falls back to keyword search without it)

No other install needed. `uv run coverletter` handles all dependencies on first run.

---

## Getting started

### 1. Initialize

```bash
uv run coverletter init
```

Creates a `.env` file and an empty `library.md`. Open `.env` and add your `ANTHROPIC_API_KEY`.

### 2. Build your paragraph library

Your paragraph library is where your career documentation lives. Every letter is assembled from paragraphs you've written and approved. The library grows over time — each application makes it stronger.

**If you have existing material** (a cover letter, resume, LinkedIn bio, raw notes):

```bash
uv run coverletter seed                    # paste text, press Ctrl-D when done
uv run coverletter seed --file resume.txt  # or point it at a file
```

The tool reads your material and groups sentences into distinct experience paragraphs — using your exact words, no rewriting or paraphrasing. For each extracted paragraph you choose: **[A]ccept**, **[E]dit**, or **[S]kip**.

It also generates targeted follow-up questions for each paragraph ("What broke when this failed?", "Who depended on this and what couldn't they do without it?"). These questions are saved and automatically used the next time you run `build` on that experience.

**If you're starting from scratch** and want to write a paragraph for a specific experience:

```bash
uv run coverletter build
```

The tool asks what you want to write about, searches your library to see what's already there, and runs a focused conversation to draw out the specific details — what you owned, what you decided, what made it hard, who depended on it. It drafts a paragraph from your answers when the material is there. The draft uses your actual words and phrasing from the conversation, not polished rewrites of them.

### 3. Build your candidate profile

```bash
uv run coverletter profile --model opus   # run once; use opus or another more robust LLM, it's worth it
```

When prompted, press **G** to have the tool read your library and draft profile sections for you, or **E** to edit what's already there.

The profile has seven sections:

- **goals** — what kind of work and scope you're looking for right now
- **differentiators** — what makes your background distinct (specific technologies, scale, ownership — not generic claims)
- **focus_areas** — skills or domains you want to go deeper in
- **avoid** — roles, environments, or work types that are wrong fits. Also used in biographical responses: each avoid entry reveals a real value — the tool infers the positive claim, it doesn't quote the constraint
- **seniority_signals** — what separates senior candidates from mid-level ones in your domain
- **working_style** — how you work and think day-to-day. Not skill claims. Not project evidence. How you operate. Used as thesis material in biographical responses alongside `values`
- **values** — what you believe and care about as a programmer, teammate, and person. Open-source development, mentorship, test discipline, how you show up on a team, what kind of engineer you are at a deeper level. Write affirmatively in your own voice. Used as thesis material in biographical responses alongside `working_style`

**On seniority signals:** these describe your expertise level, not the job title on the posting. If you have a senior data engineering background, your signals stay the same whether the role is called "Senior Data Engineer," "Staff Analytics Engineer," or "AI/ML Engineer with a DE focus." They travel with you across applications. You'd only revisit them if your direction genuinely shifts — crossing into a new discipline, moving from IC to staff, that kind of change.

Example signals for a senior data engineering background:
- `Business impact: quantified outcomes, not just "built X" — what did it enable?`
- `Production ownership: SLAs, incidents, reliability decisions — not greenfield only`
- `System design judgment: trade-offs made and articulated, not just tool choices`
- `Data modeling depth: schema decisions, SCD handling, warehouse design`
- `Cross-functional effectiveness: translating infra needs to business context`

**On working_style and values:** these two sections are the biographical argument — the thesis about who you are. They are not decorative framing. For biographical prompts, the tool reads them as the argument it needs to make, then selects library paragraphs that prove specific claims within that argument. Strong claims without evidence are just assertions. Evidence without the argument is just a resume. The two work together: biographical content organizes what gets said, library paragraphs prove it.

`working_style` example entries:
- `I'm the person people think through a problem with to figure out how to build it`
- `I move naturally between technical and non-technical audiences — I translate, not present`
- `I think creatively about data problems; my background gives me angles that pure backend engineers don't have`

`values` example entries:
- `I believe in open-source development — the community is how consequential engineering gets built outside commercial walled gardens`
- `I care about mentorship and pay forward what I've received from people who made time for me`
- `I write tests because I've been burned by not writing them, not because a process requires it`
- `I am direct and honest with teammates even when it's uncomfortable — I learned early that clarity builds trust and cuts through wasted effort`

A PM, a solutions engineer, a frontend lead — they'd write completely different entries. The tool does not infer them; you define them. Update them when your direction genuinely shifts.

Review and edit each section before saving. Without a profile the thesis is generic, the alignment report has no goal-fit signal, and biographical prompts produce resume summaries instead of an argument about who you are.

Re-run when your goals or direction shift. When you save a new profile, the previous one is automatically archived with a date stamp in the same directory — your goal history is preserved, not overwritten.

### 4. Build your claim-evidence library

Before generating argument-driven letters, extract claims from your library. Claims are atomic ownership and decision assertions — "At BritBox, I owned the VideoViewEvents pipeline end-to-end" — that map to JD requirements and are supported by hierarchical evidence from your paragraphs.

```bash
uv run coverletter onboard          # shows your setup checklist and next step
coverletter extract --dry-run       # extract claims, write review file
uv run streamlit run coverletter/label_evals.py  # review claims, build your gold standard
coverletter extract                 # insert approved claims into DB
```

**First run:** `coverletter onboard` checks your readiness and tells you exactly what to do next. During the Streamlit labeling session, check "Save as gold standard example" on clear cases — this builds the personal baseline used to validate the judge that filters bad claims before they enter your library. You need at least 5 approved and 5 rejected examples before full extraction runs.

**The labeling app** shows the source paragraph, extracted claim, judge verdict, and full evidence hierarchy for each claim. Approve it (inserts to DB immediately), reject it with a failure category, or mark it as a gold standard reference example.

### 5. Generate a letter

**Argument-driven flow (recommended once claims are extracted):**

```bash
uv run coverletter outline <jd_file> --company Acme         # build editable outline
# edit the outline — reorder paragraphs, drop irrelevant claims, add notes
uv run coverletter generate --from-outline acme_outline.md <jd_file>
```

`coverletter outline` uses two-stage retrieval: it scores argument categories against the JD first, then ranks claims within relevant categories by embedding similarity. After thesis generation, you can edit the thesis before grouping runs to steer the argument. The outline shows uncovered JD requirements (gaps) immediately after writing.

`coverletter generate --from-outline` reads the edited outline, generates a letter grounded in the claim/evidence structure, then shows an alignment report of which outline blocks made it into the letter. Records the application in the analytics DB automatically.

**Classic flow (still works):**

```bash
uv run coverletter
```

Paste the job description, enter the company name, and the tool runs the full flow: generates a letter, shows you what's covered and what's missing, offers to fill gaps through Q&A, then lets you revise before saving.

---

## Command reference

### Setup and library building

| Command | What it does |
|---|---|
| `uv run coverletter init` | First-time setup — creates `.env` and empty `library.md` |
| `uv run coverletter onboard` | Setup checklist — shows readiness status and next command at each step |
| `uv run coverletter seed` | Use this to extract paragraphs from existing material you've written already (cover letters, resume, notes) |
| `uv run coverletter build` | Focused conversation to draw out and document a specific experience — drafts a paragraph from what you say |
| `uv run coverletter reflect` | Capture perspective material — through-lines, pivots, reframes, syntheses — through conversation |
| `uv run coverletter sync` | Sync library markdown to SQLite DB, compute embeddings |
| `uv run coverletter profile` | Build or update your candidate profile |

### Claim-evidence pipeline

| Command | What it does |
|---|---|
| `uv run coverletter extract --dry-run` | Extract claims from library, write review files — always runs, even without gold standard |
| `uv run coverletter extract` | Extract, judge, and insert claims into DB (requires gold standard) |
| `uv run streamlit run coverletter/label_evals.py` | Review extracted claims — approve/reject, build gold standard, insert to DB |
| `uv run coverletter claims` | Show claim count, anchor count, and argument categories per paragraph — zero cost |
| `uv run coverletter outline <jd>` | Build editable outline from DB — two-stage category retrieval, thesis editable before grouping, gaps shown immediately |
| `uv run coverletter generate --from-outline <outline> <jd>` | Generate letter from edited outline — alignment report shown after generation |

### Letter generation

| Command | What it does |
|---|---|
| `uv run coverletter` | Generate a cover letter — classic paragraph-assembly flow |
| `uv run coverletter blurb` | Answer a short application prompt — "about me", behavioral, motivation |
| `uv run coverletter show-library` | Show library stats and experience coverage |
| `uv run coverletter resume` | Generate a tailored resume PDF alongside a letter |

### Analytics and tracking

| Command | What it does |
|---|---|
| `uv run coverletter outcome <company> <result>` | Record application result after the fact (interview / rejected / offer / ghosted) |
| `uv run coverletter analytics` | Cross-application patterns — coverage rates, recurring gaps, claim usage, JD similarity |

### Evaluation (development tools)

| Command | What it does |
|---|---|
| `uv run python coverletter/evals/align_judge.py` | Check judge accuracy against gold standard — offers to draft a prompt patch if misaligned |
| `uv run python coverletter/evals/run_evals.py` | Measure pipeline quality as % of claims approved — run to compare prompt changes |

Most commands work without flags — they'll ask you what they need. Flags are shortcuts for when you already know the answer and want to skip the prompt.

```bash
# Model override — works on any command when you want to change cost/quality
uv run coverletter --model haiku             # cheaper, faster
uv run coverletter profile --model opus      # worth it for one-time profile generation

# --fast / -f skips thesis and alignment — generate, review, and revise only
uv run coverletter --fast

# Shortcuts that skip a prompt you already know the answer to
uv run coverletter --role "Senior Data Engineer"   # skip role selection
uv run coverletter seed --file resume.txt          # read from file instead of paste
uv run coverletter resume --company Google         # skip company prompt
```

Model aliases: `haiku` → `claude-haiku-4-5-20251001`, `sonnet` → `claude-sonnet-4-6`, `opus` → `claude-opus-4-7`.

---

## How the claim-evidence architecture works

The classic generation flow assembles letter paragraphs from your library paragraphs. It works, but it has a ceiling: claims inside one paragraph can't be combined with evidence from other paragraphs, and the model can't explicitly map your experience to specific JD requirements.

The claim-evidence layer solves this. It extracts **claims** from your paragraphs — atomic, portable ownership assertions — and stores them with hierarchical evidence. When you run `coverletter outline`, the tool scores argument categories against the JD, retrieves the most relevant claims within each category, groups them into argument-driven paragraph blocks, and writes an editable outline. Uncovered JD requirements are flagged immediately. You edit the outline — reorder blocks, drop weak claims, adjust notes — then run `coverletter generate --from-outline` to produce the letter. Every application is recorded in the analytics DB automatically.

**Claims** are ownership or decision assertions at the right level of specificity: "At Acme, I owned the VideoViewEvents pipeline end-to-end." Matchable to a JD requirement. Provable by the evidence beneath it.

**Support items** are the specific facts that prove a claim: "processed play/pause/seek/heartbeat events into coherent viewing sessions." Sub-details preserve technical specifics verbatim — the how, the why, the edge cases.

**Conclusions** are synthesized insights that emerge from a group of claims: "This is data where instrumentation is imperfect — getting to trustworthy output requires understanding what the source is actually recording before you model anything."

**The judge** validates every extracted claim before it enters your DB. It asks one question: can this claim be proven by specific evidence? Pure capability statements ("I have experience with X") are rejected. Broad substantiatable claims ("I built production Python while staying deeply thoughtful about non-technical users") are valid — they describe a way of working that evidence can prove.

**The gold standard** is built by you during your first labeling session. As you approve and reject claims in the Streamlit app, you mark clear examples as gold standard reference cases. Once you have 5 approved and 5 rejected, the judge is validated against your personal baseline before any extraction runs.

---

## How the library works

The library is split across several markdown files with distinct roles. You do not need to manage which file is active — the tool reads all configured files and merges them, with higher-priority files winning when the same experience is covered in multiple places.

| File | What goes here | Priority |
|---|---|---|
| `library.md` | Your raw paragraphs — written directly, Q&A answers, anything you typed. Source of truth. Never rewritten by the tool. | Base |
| `library_refined.md` | Paragraphs that have been through a refinement process and approved. Takes priority over `library.md` for the same section. | High |
| `library_salvaged.md` | Paragraphs corrected via the diff tool — reviewed against raw source and approved. | High |
| `library_rebuilt.md` | Paragraphs built through the correct workflow from scratch — raw → coaching → your edits → approved. | High |
| `story_notes.md` | Raw material from conversations that hasn't been turned into paragraphs yet. Surfaced in the diff tool but not used in generation. | — |

**Write path for new paragraphs:**
Write raw text → `library.md`. Run the diff tool to draft, coach, and approve → `library_salvaged.md` or `library_rebuilt.md`.

**The library compounds.** Each gap session during a letter run produces a new paragraph. Each new paragraph makes the next letter stronger. The more specific your paragraphs, the more specific your letters.

---

## Full letter flow (what `uv run coverletter` does, step by step)

> Requires a candidate profile — run `uv run coverletter profile` first.

### 1. Startup

Shows library stats (how many paragraphs, by tier), experience register status, and profile status.

### 2. Role selection

Choose a target role to filter which paragraphs are eligible, or pick General to use everything. Skip this prompt with `--role "Senior Data Engineer"`.

### 3. Job description

Paste the full job description. Press **Ctrl-D** when done. Enter a company name.

### 4. Letter generation

The tool selects the most relevant paragraphs from your library (ranked by overlap with the JD, capped at 2 paragraphs per experience so no single experience dominates) and assembles a letter. The opener and closer are written fresh for this specific role and company. Every body sentence traces back to your source paragraphs.

**Opener rule:** the opener connects you to the target employer first — what the organization does, what about their work connects to yours, why this is the right fit. It does not name previous employers (those belong in body paragraphs) and does not open with credentials or employment history.

### 5. Quality checks

**Hard check:** the letter fails immediately if it contains an em-dash.

**LLM check:** scans for banned words, fake-contrast structures, weak opener, closer that doesn't name the company. On failure, the tool proposes a minimal fix and shows it to you:

```
[A]ccept fix  [E]dit manually (revision loop)  [S]kip (keep current):
```

The model stays as close to your source language as possible — it prefers cutting or restructuring over rewriting. If it can't fix something without inventing new language, it flags the sentence explicitly: `COULD NOT FIX: [sentence]`. Use the revision loop to resolve those manually.

**Source check:** flags any body sentence where less than 72% of the words appear in your source paragraphs. These are warnings, not blockers — use them to catch drift.

### 6. Letter thesis *(skipped with `--fast`)*

```
Letter thesis: "This letter argues that [you] is the right fit because [X]..."
Is this the right argument? [Y/n/adjust]:
```

The tool reads the letter and names the central argument it's making about you. If your profile is loaded, it also evaluates whether the role fits your stated goals and flags tensions. Confirm it, adjust it, or reject it — the thesis shapes everything downstream.

### 7. Alignment report *(skipped with `--fast`)*

```
75% aligned (6 covered, 2 gap(s), 1 seniority signal gap(s))

Covered:
  ✓ Python/SQL data pipelines — covered by the streaming pipeline paragraph

JD Gaps:
  1. BigQuery at scale — critical for this team's warehouse stack

Seniority Signal Gaps:
  1. Business impact — letter describes what was built but not what it enabled

Goal fit: Partially — role offers platform scope but sits in a central DE team.

Narrative frame: No through-line, pivot, reframe, or synthesis paragraph in library.
The letter has evidence but no narrative frame. Run: uv run coverletter reflect
```

**JD Gaps** are things the job description explicitly requires that the letter doesn't address. Keep in mind the letter is a supplment to your resume so it really has to cover the extra mile between what your resume says and what *you* want to highlight.

**Seniority Signal Gaps** check the dimensions you defined in `seniority_signals` and flag only the ones that are genuinely absent from the letter — not just underemphasized. Only appears if you have seniority signals set in your profile.

**Goal fit** only appears if you have a candidate profile loaded.

**Narrative frame** flags when your library has no perspective paragraphs — no through-line, pivot, reframe, or synthesis. The letter has evidence but no narrative argument about who you are and why your arc makes you right for this role. Fix it with `coverletter reflect`.

### 8. Gap loop *(skipped with `--fast`)*

All gaps are shown at once, numbered:

```
3 gap(s):

  1. BigQuery experience — critical for this team's warehouse stack
  2. [in library] dbt modeling — paragraph exists in library (library: [4])
  3. [Seniority] Business impact — letter describes what was built but not what it enabled

  Gaps 2 already have library paragraphs — they'll be pulled in on regen.
  Actionable: 1, 3

Address which gaps? (e.g. 1,3 or 'all' or Enter to skip all):
```

Gaps already covered by a library paragraph are dimmed and labeled `[in library]` — they'll be included automatically on regeneration, no Q&A needed. Library coverage is detected via BM25 keyword matching against the full paragraph library — it runs in Python, not as an extra LLM call, so it catches matches the model misses.

Enter individual gap numbers (`1,3`), type `all` or `a` to address every actionable gap in sequence, or press Enter to skip all and go straight to regeneration.

Press **Ctrl-C** at any time during the gap loop to stop and return to the regeneration prompt. Any paragraphs saved before you stopped are kept.

Inside a Q&A session for each selected gap:
- The tool searches your library first so it doesn't ask about things you've already written
- If you've documented this experience in `experiences.md`, the tool sees what angles are already covered and asks about the gaps specifically — the matcher filters stop words and requires at least two meaningful overlapping words to match, so it won't send you to the wrong experience
- Questions are validated internally before you see them — bad questions get regenerated
- Hard cap of 2 exchanges, then the tool forces a draft
- Type **"draft"** to force a draft early; **"done"** to exit without saving
- Multi-line answers: press **Enter** to add a new line, **Ctrl-D** or **Alt-Enter** to submit. Paste works at any length — prompt_toolkit reads input in raw mode, bypassing the terminal's per-line length limit

After Q&A, the tool drafts a paragraph:

```
[A]ccept  [R]edirect  [K]eep talking:
```

**A** → prompts for role, section name, angle tag, and strength rating → saves to `library_refined.md`

### 9. Regeneration

```
Saved 2 new paragraph(s). Regenerate letter with new material? [Y/n]:
```

### 10. Coaching pass (optional)

```
Run coaching pass (sentence-level review)? [y/N]:
```

Sentence-level weakness analysis with directed rewrites. Off by default — use it when you want a close read.

### 11. Revision loop

```
Enter a paragraph number, free text for global feedback, or Enter to finish:
```

Give a paragraph number to revise a specific section, or type free text for a global note. After each revision: **[A]ccept** keeps it, **[R]eject** restores the previous version.

### 12. Save

```
Session cost: 45,231 in / 3,102 out tokens  ~$0.18
Save to output/? [Y/n]:
```

Saves `YYYY-MM-DD_CompanyName.md` and `YYYY-MM-DD_CompanyName.pdf` to your output directory.

---

## Files

| File | Purpose |
|---|---|
| `library.md` | Raw paragraphs — your words, never rewritten by the tool |
| `library_refined.md` | Refined paragraphs — high priority at generation time |
| `library_salvaged.md` | Paragraphs corrected via the diff tool and approved |
| `library_rebuilt.md` | Paragraphs built through the clean workflow from scratch |
| `story_notes.md` | Raw conversation material not yet turned into paragraphs |
| `experiences.md` | Experience register — raw facts, angle inventory, Q&A targets per experience |
| `candidate_profile.toml` | Your goals and differentiators — drives thesis and alignment report |
| `.env` | API keys, author name, and path overrides |
| `output/` | Saved letters and tailored resumes |
| `resume_bullets.md` | Alternative resume bullets for the `resume` command |
| `corrections.md` | Sentence-level fixes applied automatically before generation |

The tool reads all configured library files and merges them. Higher-priority files win when the same section exists in multiple places. You don't manage this manually.

All file paths are configurable in `.env` — see the [.env reference](#env-reference) below.

---

## Paragraph library format

The library files are plain Markdown. The tool reads them at generation time — you can edit them directly if needed.

```markdown
## Senior Data Engineer

### Acme Corp / Event Ingestion Pipeline

<!-- meta: strength=high, via=build, angle=production-ownership -->
Your paragraph text here. Written in your voice. Concrete claims, specific evidence.

## General

### Opening

<!-- meta: tone=opener, strength=high -->
Voice reference for opener synthesis. Not copied verbatim — the model uses this
to match your tone when writing a fresh opener for each application.

### Closing

<!-- meta: tone=closer, strength=high -->
Voice reference for closer synthesis. Same deal.
```

**Structure:**
- `## Role` — top-level header is a job title ("Senior Data Engineer", "General"). Controls which paragraphs appear for a given application.
- `### Section` — the experience or project name, including company context ("Acme Corp / Event Ingestion Pipeline").
- `<!-- meta: ... -->` — paragraph metadata (see below).

**Meta keys:**
- `strength`: `high` | `medium` | `low` — how ready this paragraph is for a letter
- `via`: how this paragraph was produced
  - `seed-notes` — extracted from raw notes or bullets (tier 1)
  - `seed-letter` — extracted from existing written prose (tier 2)
  - `build` — produced through a Q&A session (tier 3)
  - `build+seed` — seed extracted, then build refined (tier 3, full lifecycle)
- `tone`: `opener` | `closer` — marks voice-reference paragraphs
- `angle`: two uses:
  - Evidence angles (`production-ownership`, `system-design`, `business-impact`, etc.) — matches angle names in `experiences.md` for coverage tracking
  - Perspective angles (`through-line`, `pivot`, `reframe`, `synthesis`) — marks narrative frame paragraphs produced by `coverletter reflect`. These are pinned in prefilter (never filtered out) and labeled `[NARRATIVE FRAME]` for the assembler

---

## Experience register (`experiences.md`)

The experience register stores raw facts and desired angle framings per experience. It's separate from the paragraph library — it's not prose, it's a structured fact sheet that the tool uses to ask better questions.

```markdown
## Acme Corp / Event Ingestion Pipeline
company: Acme Corp
years: 2021–2023
angles: scope-opener, production-ownership, system-design, business-impact

Sole DE on a two-person data team. Vendor pipeline failed regularly.
Built replacement in 4 months. 1B+ events/day. 100% stable since go-live.

qa_targets:
- What downstream decisions depended directly on these numbers?
- What broke or became unreliable when the vendor pipeline failed?
```

`qa_targets` are written automatically by `coverletter seed`. The next time you run `coverletter build` for this experience, those questions drive the Q&A instead of generic ones.

---

## Capturing perspective paragraphs (`coverletter reflect`)

Evidence paragraphs prove specific claims. Perspective paragraphs make the argument about who you are and why your arc makes you right for this role. They are the narrative frame — through-lines, pivots, reframes, syntheses. Without them, a letter has facts but no argument.

```bash
uv run coverletter reflect
```

The tool asks what you want to capture and what angle fits. You can also describe it directly when it asks — it will read what you say and pick the angle with you. The conversation goes after specific moments and decisions, not after meaning or reflection directly. Meaning emerges from the specifics.

The angle types:

| Angle | What it captures |
|---|---|
| `through-line` | The consistent thread across your whole arc — what has always been true about how you work or what you care about |
| `pivot` | A deliberate change in direction with a reason — not just "I moved from X to Y" but why, and what made it coherent |
| `reframe` | Same experience, different lens — "when I was doing X it looked like Y, but what I was actually building was Z" |
| `synthesis` | Two seemingly unrelated experiences that combine into something specific that neither path produces alone |

The Q&A follows the same discipline as `build` — goes after decisions, moments, and specifics, not after meaning or reflection directly. Saved to `library_refined.md` with `via=reflect`.

Once perspective paragraphs are in your library, the letter assembler sees them labeled `[NARRATIVE FRAME]` and uses them to shape the opener's central claim and inform which evidence paragraphs to select. They are woven through the letter, not placed in a separate block.

---

## Short application prompts (`coverletter blurb`)

For application prompts that aren't a full cover letter:

```bash
uv run coverletter blurb
```

Two inputs: paste the job description first (used to select relevant library paragraphs), then paste the specific prompt you're answering. These are separate reads — Ctrl-D ends each one.

The tool reads the prompt type and responds accordingly:

| Prompt type | What the tool does |
|---|---|
| "Tell me about yourself" / biographical | Reads `working_style` and `values` as the argument — the thesis about who you are. Then selects library paragraphs that prove specific claims within that argument. Narrative drives; evidence substantiates. The `avoid` section informs values inference (each constraint reveals a positive value). |
| "Describe a time when..." / behavioral | Picks the library paragraph(s) that best answer the question and tells the story with specific evidence. Does not invent a story not in the library. |
| "Why are you interested in..." / motivation | Draws from your `goals` profile section and relevant library material. |
| "What is your approach to..." | Answers from actual practice in the library, not philosophy. |

Up to 400 words depending on prompt type. After the response, a plain-text version is printed for clean copying.

**Revision loop:** type feedback and hit Enter to revise. Rejected drafts stay in conversation history — the model knows what was tried. Accept/Reject after each revision. Enter with no text to finish.

**If biographical material is thin:** the tool outputs a `BIOGRAPHICAL_GAPS` section naming what's missing. You'll be offered the option to add `working_style` or `values` entries on the spot.

**For biographical prompts to work well, your profile needs `working_style` and `values` entries.** Fill these in with `uv run coverletter profile` → Edit, or edit `candidate_profile.toml` directly. Write in your own voice. Not skill claims. Not project evidence. Who you are, how you work, what you believe.

---

## Writing rules (enforced)

The tool checks every generated letter against these rules and auto-revises on failure:

- No em-dash (`—`) anywhere
- No sentence starting with "That"
- No banned phrases: `actually`, `not just`, `not only`, `not simply`, `this matters because`, `the hard part was not`, `what stands out`, `the clearest connection`, `this is the kind of work`, `i am strongest in`, `i combine`
- No generic bridge openers: `that experience fits`, `this role aligns`
- No paragraph ending with a list of 3+ items
- No generic body paragraph opener (must lead with a concrete fact, not a topic statement like "I combine..." or "My approach to X is...")
- No body paragraph that reads like AI-generated template prose (abstract values as assertions, no evidence)
- Every body sentence must trace to source paragraphs
- Opener connects to the target employer first — no previous employer names, no credential lead
- Body paragraphs must not restate claims already made in the opener
- `[CLOSER ONLY]` paragraphs (Why This Role / Closing sections) must not appear as the first or second body paragraph

---

## Resume builder

```bash
uv run coverletter resume --company Google
```

For each company in your `resume.typ` that has alternative bullets in `resume_bullets.md`, the tool shows your options and lets you pick per experience.

Output: `output/YYYY-MM-DD_CompanyName.typ` and `.pdf`

Requires `typst`: `brew install typst`

---

## .env reference

```bash
# Generation provider — set the key matching your chosen model
ANTHROPIC_API_KEY=sk-ant-...         # required for Anthropic (default)
MISTRAL_API_KEY=...                  # required for Mistral
OPENAI_API_KEY=sk-...                # required for OpenAI
COHERE_API_KEY=...                   # required for Cohere

# Embeddings — provider-native used automatically; Voyage is the explicit fallback
VOYAGE_API_KEY=pa-...                # optional — highest retrieval quality

AUTHOR_NAME=Your Name
RESUME_FILE=/path/to/resume.pdf      # used by build and generate
RESUME_TYP_FILE=/path/to/resume.typ
RESUME_BULLETS_FILE=/path/to/resume_bullets.md
EXPERIENCES_FILE=/path/to/experiences.md
CANDIDATE_PROFILE_FILE=/path/to/candidate_profile.toml
OUTPUT_DIR=/path/to/output
LIBRARY_FILE=/path/to/library.md
LIBRARY_REFINED_FILE=/path/to/library_refined.md

# Model selection — bare names default to Anthropic; prefix selects provider
COVERLETTER_MODEL=claude-sonnet-4-6              # Anthropic (default)
# COVERLETTER_MODEL=mistral/mistral-large-latest # Mistral (EU sovereign, green energy)
# COVERLETTER_MODEL=mistral/mistral-small-latest # Mistral Small
# COVERLETTER_MODEL=openai/gpt-4o               # OpenAI GPT-4o
# COVERLETTER_MODEL=openai/gpt-4o-mini          # OpenAI GPT-4o Mini
# COVERLETTER_MODEL=cohere/command-r-plus        # Cohere (Canadian, embed + rerank on one key)

# Embedding model override (independent of generation provider)
# EMBED_MODEL=bge-m3                # local BGE-M3 hybrid dense+sparse (uv add FlagEmbedding)
# OPENAI_EMBED_MODEL=text-embedding-3-small  # embedding model for OpenAI-compat hosts

# For OpenAI-compatible providers (Regolo.ai, Hugging Face Inference, local servers)
# OPENAI_BASE_URL=https://api.regolo.ai/v1       # Regolo.ai (Italian, green, zero retention)
# OPENAI_BASE_URL=https://router.huggingface.co  # Hugging Face Inference

COVERLETTER_TOP_N=100               # paragraphs passed to the model per generation
```

---

## Cost reference

| Operation | Haiku | Sonnet | Opus |
|---|---|---|---|
| Full letter run | ~$0.02–0.05 | ~$0.10–0.25 | ~$0.50–1.25 |
| `seed` (per paste) | ~$0.01 | ~$0.03 | — |
| `profile` (G option) | ~$0.01 | ~$0.05 | ~$0.10–0.25 |
| `build` (Q&A session) | ~$0.01 | ~$0.03–0.05 | — |

Prompt caching is active on Anthropic (90% discount via cache_control) and Mistral (90% via cache_key parameter). OpenAI automatic prefix caching gives ~50% discount when prompts are structured correctly. Cohere caching behavior is unknown — not explicitly configured.

### Anthropic

| Model | Input /1M | Output /1M | Cache read /1M |
|---|---|---|---|
| Haiku | $0.80 | $4.00 | $0.08 |
| Sonnet | $3.00 | $15.00 | $0.30 |
| Opus | $15.00 | $75.00 | $1.50 |

### Mistral (EU sovereign — recommended for GDPR/ethics-first users)

French company, data centers in the EU, €1.2B green energy facility in Sweden. **One `MISTRAL_API_KEY` covers generation + embeddings + caching** — no Voyage key needed.

| Model alias | Full name | Input /1M | Output /1M | Cached input /1M |
|---|---|---|---|---|
| `mistral-large` | `mistral-large-latest` | $2.00 | $6.00 | $0.20 |
| `mistral-medium` | `mistral-medium-latest` | $0.40 | $2.00 | $0.04 |
| `mistral-small` | `mistral-small-latest` | $0.10 | $0.30 | $0.01 |
| embeddings | `mistral-embed` | $0.10 | — | — |

Caching: 90% discount via `cache_key`. Session economics comparable to Anthropic.

### OpenAI

**One `OPENAI_API_KEY` covers generation + embeddings.** Caching is automatic (50% discount, no configuration).

| Model alias | Full name | Input /1M | Output /1M | Cached input /1M |
|---|---|---|---|---|
| `gpt-4o` | `gpt-4o` | $2.50 | $10.00 | $1.25 |
| `gpt-4o-mini` | `gpt-4o-mini` | $0.15 | $0.60 | $0.075 |
| embeddings | `text-embedding-3-small` | $0.02 | — | — |

### OpenAI-compatible providers (via `OPENAI_BASE_URL`)

Any OpenAI-compatible host works without code changes. Two worth knowing:

**[Regolo.ai](https://regolo.ai)** — Italian, 100% green energy, zero data retention, GDPR by design, open-source models only, transparent token pricing. Set `OPENAI_BASE_URL=https://api.regolo.ai/v1`.

**[Hugging Face Inference](https://huggingface.co/inference)** — Open-source community, free tier, runs open weights models. Set `OPENAI_BASE_URL=https://router.huggingface.co`.

---

## Provider support

**Anthropic, Mistral, and OpenAI are supported.** Any OpenAI-compatible provider works via `OPENAI_BASE_URL`. See [`ROADMAP.md`](ROADMAP.md) for planned additions (Cohere, Ollama).

**On embeddings**: Mistral and OpenAI users do not need a Voyage key — provider-native embeddings are used automatically for the claim/outline pipeline. Anthropic users still need Voyage (or can switch to Mistral/OpenAI for a single-key setup). Track 1 paragraph filtering still uses Voyage regardless of provider — this is a known gap documented in the roadmap.

---

## Known issues

**Closer quality depends on your voice reference paragraphs.** Weak source closer paragraphs produce weak synthesized closers. If your closers feel generic, improve the `### Closing` paragraph in `library.md`.

**Q&A can still ask about things you've already documented.** Voyage search reduces this but isn't perfect. If the agent asks about something already written, paste the paragraph and say "this is already documented."

**Experience name matching is exact.** Coverage tracking matches experience names in `experiences.md` against section names in the library files. Keep naming consistent across both — if you call it "Event Ingestion Pipeline" in one place, use the same name in the other.

---

## Development

```bash
uv run pytest tests/
```

All tests run without API keys and without touching your real library or profile. The test suite uses a synthetic fixture library in `tests/fixtures/` — fake company names, fake paragraphs, no personal data.

**Test isolation:** any test that needs a `Config` object should use the `test_cfg` fixture defined in `tests/conftest.py`. It points all reads at `tests/fixtures/` and all writes at pytest's `tmp_path`. Never call `load_config()` directly in tests — that resolves real environment paths and could touch your actual data directory.

```python
def test_save_output(test_cfg):
    from coverletter.output import save_letter
    path = save_letter("Letter text.", test_cfg.output_dir, "TestCo", test_cfg.author_name)
    assert path.exists()
```
