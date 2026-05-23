# WorkerChronicle — an engineer's experience library and cover letter generator

Engineers ship constantly. Projects stack up. Two years later you remember you built something important but you've lost the nuance — what was actually at stake, what made it hard, what you had to figure out, what broke, what downstream decisions depended on your work. The resume bullet survives. The story doesn't.

The gap between "what I actually did" and "what I can articulate I did to an outsider" is enormous for most engineers. That gap costs you in interviews, in cover letters, in performance reviews, in any moment where you need someone who wasn't there to understand the value of your work.

I built this because I was writing a lot of cover letters and kept losing the pivotal details of my own work. Generic LLM is almost perfectly wrong for this task — it flattens the story, over-polishes the voice, loses the facts, and produces something that sounds like a cover letter while destroying the evidence that would make it good. This tool does the opposite.

**Letters are assembled from your own paragraphs, not generated from scratch.** The model writes a fresh opener and closer per application. Every body sentence traces back to your source library. Library quality drives letter quality.

This tool works for anyone — not just engineers. If you're working through a career transition or have a non-standard work history, I'd especially love to hear how it works for you.

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

Your paragraph library is where your career lives. Every letter is assembled from paragraphs you've written and approved. The library grows over time — each application makes it stronger.

**If you have existing material** (a cover letter, resume, LinkedIn bio, raw notes):

```bash
uv run coverletter seed                    # paste text, press Ctrl-D when done
uv run coverletter seed --file resume.txt  # or point it at a file
```

The tool reads your material and groups sentences into distinct experience paragraphs — using your exact words, no rewriting or paraphrasing. For each extracted paragraph you choose: **[A]ccept**, **[E]dit**, or **[S]kip**.

It also generates targeted follow-up questions for each paragraph ("What broke when this failed?", "Who depended on this and what couldn't they do without it?"). These questions are saved and automatically used the next time you run `build` on that experience.

**If you're starting from scratch** and want to write a paragraph for a specific experience:

```bash
uv run coverletter build --about "the time I rebuilt our deployment pipeline from scratch"
```

`--about` is a short plain-English description of the experience you want to capture. The tool asks you 2–3 targeted questions to surface the concrete evidence, then drafts a paragraph from your answers.

### 3. Build your candidate profile

```bash
uv run coverletter profile --model opus   # run once; use opus, it's worth it
```

When prompted, press **G** to have the tool read your library and draft all four profile sections for you:

- **goals** — what kind of work and scope you're looking for right now
- **differentiators** — what makes your background distinct
- **focus_areas** — specific skills or domains to emphasize
- **avoid** — roles, environments, or work types that are wrong fits

Review and edit each section before saving. This is a prerequisite for full letter quality — without it the thesis is generic, the alignment report has no goal-fit signal, and gap analysis can't tell you whether a role actually serves your goals.

Re-run when your goals shift. This is the argument you're making about yourself right now, not a permanent document.

### 4. Generate a letter

```bash
uv run coverletter
```

Paste the job description, enter the company name, and the tool runs the full flow: generates a letter, shows you what's covered and what's missing, offers to fill gaps through Q&A, then lets you revise before saving.

---

## Command reference

| Command | What it does |
|---|---|
| `uv run coverletter` | Generate a cover letter — the main flow |
| `uv run coverletter seed` | Extract paragraphs from existing material (cover letters, resume, notes) |
| `uv run coverletter build` | Write a paragraph for a specific experience through Q&A |
| `uv run coverletter profile` | Build or update your candidate profile |
| `uv run coverletter show-library` | Show library stats and experience coverage |
| `uv run coverletter resume` | Generate a tailored resume PDF alongside a letter |
| `uv run coverletter init` | First-time setup |

```bash
# Model flag works on all commands
uv run coverletter --model haiku             # cheaper, faster
uv run coverletter --model sonnet            # default
uv run coverletter profile --model opus      # worth it for one-time profile generation

# Useful shortcuts
uv run coverletter --role "Senior Data Engineer"                    # skip role selection
uv run coverletter build --about "rebuilt the deployment pipeline"  # skip the about prompt
uv run coverletter seed --file resume.txt                          # read from file
uv run coverletter resume --company Google                         # skip company prompt
```

Model aliases: `haiku` → `claude-haiku-4-5-20251001`, `sonnet` → `claude-sonnet-4-6`, `opus` → `claude-opus-4-7`.

---

## How the library works

Every paragraph in your library has a **tier** based on what process produced it. Tier affects which file it lives in and how much the tool trusts it at letter-generation time.

```
TIER 1 — Raw source                         goes into library.md
  Your own notes, bullets, stream-of-consciousness narrative.
  Dense with facts. Not polished prose. Not ready for a letter on its own.
  Valuable because it captures everything you know about an experience.

TIER 2 — Semi-raw                           goes into library.md
  Extracted verbatim from existing written material — cover letters,
  LinkedIn bios, resume bullets. Has your voice but may have filler,
  buried leads, or weak argument structure.

TIER 3 — Refined                            goes into library_refined.md
  Produced through a Q&A session (build or gap loop). Concrete claims,
  specific evidence, tight structure. Still your words — but drawn out
  and tested through targeted questions. This is what letters are built from.
```

**Two files, two tiers:**
- `library.md` — everything `seed` produces (tiers 1 and 2). Your raw material.
- `library_refined.md` — everything `build` produces (tier 3). Takes priority at generation time.

When both files have a paragraph covering the same experience, `library_refined.md` wins. The raw library is the foundation; the refined library is the layer that gets used.

The library compounds. Each gap session during a letter run produces a new tier 3 paragraph. Each tier 3 paragraph makes the next letter stronger.

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

### 5. Quality checks

**Hard check:** the letter fails immediately if it contains an em-dash.

**LLM check:** scans for banned words, fake-contrast structures, weak opener, closer that doesn't name the company. Auto-revises up to 4 times on failure.

**Source check:** flags any body sentence where less than 72% of the words appear in your source paragraphs. These are warnings, not blockers — use them to catch drift.

### 6. Letter thesis

```
Letter thesis: "This letter argues that [you] is the right fit because [X]..."
Is this the right argument? [Y/n/adjust]:
```

The tool reads the letter and names the central argument it's making about you. If your profile is loaded, it also evaluates whether the role fits your stated goals and flags tensions. Confirm it, adjust it, or reject it — the thesis shapes everything downstream.

### 7. Alignment report

```
75% aligned (6 covered, 2 gap(s), 1 seniority signal gap(s))

Covered:
  ✓ Python/SQL data pipelines — covered by the streaming pipeline paragraph

JD Gaps:
  1. BigQuery at scale — critical for this team's warehouse stack

Seniority Signal Gaps:
  1. Business impact — letter describes what was built but not what it enabled

Goal fit: Partially — role offers platform scope but sits in a central DE team.
```

**JD Gaps** are things the job description explicitly requires that the letter doesn't address.

**Seniority Signal Gaps** track five dimensions — business impact, production ownership, system design judgment, data modeling depth, cross-functional effectiveness — and flag only the ones that are genuinely absent, not just underemphasized.

**Goal fit** only appears if you have a candidate profile loaded.

### 8. Gap loop

```
Gap 1/2: BigQuery experience
Address this? [Y/n/done]:
```

For each gap: **Y** starts a Q&A session, **n** skips it, **done** stops and moves to regeneration.

Inside a Q&A session:
- The tool searches your library first so it doesn't ask about things you've already written
- If you've documented this experience in `experiences.md`, the tool sees what angles are already covered and asks about the gaps specifically
- Questions are validated internally before you see them — bad questions get regenerated
- Hard cap of 3 questions, then the tool forces a draft
- Type **"draft"** to force a draft early; **"done"** to exit without saving
- Multi-line answers: press **Enter twice** to submit

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
| `library.md` | Base paragraph library — tiers 1 and 2, produced by `seed` |
| `library_refined.md` | Priority layer — tier 3, produced by `build` and gap sessions |
| `experiences.md` | Experience register — raw facts, angle inventory, Q&A targets per experience |
| `candidate_profile.toml` | Your goals and differentiators — drives thesis and alignment report |
| `.env` | API keys, author name, and path overrides |
| `output/` | Saved letters and tailored resumes |
| `resume_bullets.md` | Alternative resume bullets for the `resume` command |
| `corrections.md` | Sentence-level fixes applied automatically before generation |

`library_refined.md` takes priority over `library.md` — the tool merges them automatically. You don't need to manage this manually.

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
- `angle`: matches angle names in `experiences.md` for coverage tracking

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

## Writing rules (enforced)

The tool checks every generated letter against these rules and auto-revises on failure:

- No em-dash (`—`) anywhere
- No sentence starting with "That"
- No banned words: `actually`, `matters`, `not just`, `not only`, `not simply`
- No fake-contrast: "This was not about X, it was about Y"
- No generic bridge openers: "That experience fits,", "This role aligns,"
- No paragraph ending with a list
- No more than one list in the entire letter
- Every body sentence must trace to source paragraphs
- Opener must be role/company-specific
- Closer must name the actual company

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
ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...                 # optional — strongly recommended
AUTHOR_NAME=Your Name
RESUME_FILE=/path/to/resume.pdf
RESUME_TYP_FILE=/path/to/resume.typ
RESUME_BULLETS_FILE=/path/to/resume_bullets.md
EXPERIENCES_FILE=/path/to/experiences.md
CANDIDATE_PROFILE_FILE=/path/to/candidate_profile.toml
OUTPUT_DIR=/path/to/output
LIBRARY_FILE=/path/to/library.md
LIBRARY_REFINED_FILE=/path/to/library_refined.md
COVERLETTER_MODEL=claude-sonnet-4-6
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

Prompt caching is active on all calls. The library is cached after the first call in a session — subsequent generation, revision, and alignment calls read from cache at ~10% of input cost.

| Model | Input /1M | Output /1M | Cache read /1M |
|---|---|---|---|
| Haiku | $0.80 | $4.00 | $0.08 |
| Sonnet | $3.00 | $15.00 | $0.30 |
| Opus | $15.00 | $75.00 | $1.50 |

---

## Provider support

**Currently Anthropic-only.** All API calls use the Anthropic SDK directly. This is a known limitation and the top roadmap priority — see [`ROADMAP.md`](ROADMAP.md) for the planned approach and target providers (Mistral, Cohere, Ollama).

---

## Known issues

**Closer quality depends on your voice reference paragraphs.** Weak source closer paragraphs produce weak synthesized closers. If your closers feel generic, improve the `### Closing` paragraph in `library.md`.

**Q&A can still ask about things you've already documented.** Voyage search reduces this but isn't perfect. If the agent asks about something already written, paste the paragraph and say "this is already documented."

**Experience name matching is exact.** Coverage tracking matches experience names in `experiences.md` against section names in the library files. Keep naming consistent across both — if you call it "Event Ingestion Pipeline" in one place, use the same name in the other.
