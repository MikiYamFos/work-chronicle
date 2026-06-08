# WorkerChronicle — a worker's experience library and cover letter generator

Engineers ship constantly. Projects stack up. Two years later you remember you built something important but you've lost the nuance — what was actually at stake, what made it hard, what you had to figure out, what broke, what downstream decisions depended on your work. The resume bullet survives. The story doesn't.

The gap between "what I actually did" and "what I can articulate I did to an outsider" is enormous for most engineers. That gap costs you in interviews, in cover letters, in performance reviews, in any moment where you need someone who wasn't there to understand the value of your work.

I built this tool because I was writing cover letters and preparing for interviews and felt like I kept losing the small yet pivotal details of my own work. Generic LLM is almost perfectly wrong for the task of writing cover letters — it flattens your story, over-polishes your voice, loses the facts, and produces something that sounds like a cover letter while destroying the evidence that would actually make it compelling.

This tool does the opposite. Your paragraph library contains your specific experiences in your own words — the ownership claims, the technical decisions, the evidence that makes those claims credible. The letter is assembled from that material. The model writes sentences grounded in your library rather than inventing generic ones. Library quality directly determines letter quality — a thin library produces a thin letter, a specific library produces a specific letter.

**Letters are argument-driven, not assembled from paragraphs.** The tool extracts atomic claims from your library — what you owned, how you work, who you are as an engineer — and groups them into a logical argument against what the JD actually requires. Every claim in the letter has evidence behind it from your own writing.

This tool works for anyone — not just engineers. If you're working through a career transition or have a non-standard work history, I'd especially love to hear how it works for you!

---

## Prerequisites

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **An API key** — Anthropic is the default; Mistral, OpenAI, and Cohere also supported. See [.env reference](#env-reference).

No other install needed. `uv run clio` handles all dependencies on first run.

---

## How the claim-evidence architecture works

Before the getting started steps, this is worth understanding — it's the core of what the tool does.

The **classic generation flow** assembles letter paragraphs from your library paragraphs. It works, but it has a ceiling: claims inside one paragraph can't be combined with evidence from other paragraphs, and the model can't explicitly map your experience to specific JD requirements.

The **claim-evidence layer** solves this. It extracts atomic assertions from your paragraphs and stores them with hierarchical evidence:

**Claims** are ownership or decision assertions at the right level of specificity: "At Acme, I owned the VideoViewEvents pipeline end-to-end." Matchable to a JD requirement. Provable by the evidence beneath it.

**Support items** are the specific facts that prove a claim: "processed play/pause/seek/heartbeat events into coherent viewing sessions." Sub-details preserve technical specifics verbatim.

**Conclusions** are synthesized insights that emerge from a group of claims.

When you run `clio outline`, the tool scores argument categories against the JD, retrieves the most relevant claims for each category, groups them into argument-driven paragraph blocks, and writes an editable outline. You edit the outline — reorder blocks, drop weak claims, adjust notes — then generate a letter grounded in that structure.

### The gold standard

The extraction pipeline uses a **judge** to validate every claim before it enters your DB. The judge asks one question: can this claim be proven by specific evidence? Pure capability statements ("I have experience with X") are rejected. Substantiatable claims ("I built production Python while staying deeply thoughtful about non-technical users") are valid — they describe a way of working that evidence can prove.

**The gold standard is your personal calibration set** — a set of claims you've labeled as correct approvals and correct rejections. As you review extracted claims in the Streamlit app, you mark clear, unambiguous cases as gold standard examples. Once you have at least 5 approved and 5 rejected examples, the judge is validated against your baseline before any extraction run. This prevents prompt drift and catches regressions when the judge prompt is updated.

You build the gold standard during your first labeling session. You don't need it for `--dry-run` — you only need it before the first real extraction run.

---

## Getting started

### 1. Initialize

```bash
uv run clio init
```

Creates a `.env` file with comments explaining every option, and an empty `library.md`. Open `.env` and add your API key. Shows a "what to do next" guide after creating files.

### 2. Build your paragraph library

Your paragraph library is where your career documentation lives. Every letter is assembled from paragraphs you've written and approved. The library grows over time — each application makes it stronger.

**If you have existing material** (a cover letter, resume, LinkedIn bio, raw notes):

```bash
uv run clio seed                    # paste text
uv run clio seed --file resume.txt  # or point it at a file
```

The tool reads your material and groups sentences into distinct experience paragraphs — using your exact words, no rewriting or paraphrasing. For each extracted paragraph you choose: **[A]ccept**, **[E]dit**, or **[S]kip**.

**If you have a job description and want to know what's missing from your library:**

```bash
uv run clio build --jd /path/to/jd.txt
```

Analyzes the JD against your claims DB, shows what's covered and what's missing, then walks you through filling each gap with targeted Q&A. Requires the DB to be populated first (`clio sync` + `clio extract`). Pass `--resume` to give the coach your resume as context — it won't re-ask what the resume already says, it asks about what's behind the bullets.

**If you're starting from scratch** and want to write a paragraph for a specific experience:

```bash
uv run clio build
```

The tool asks what you want to write about, searches your library to see what's already there, and runs a focused conversation to draw out the specific details — what you owned, what you decided, what made it hard, who depended on it. It drafts a paragraph from your answers using your actual words and phrasing, not polished rewrites of them.

### 3. Build your candidate profile

```bash
uv run clio profile --model opus   # run once; opus is worth it for this
```

When prompted, press **G** to have the tool read your library and draft profile sections for you, or **E** to edit what's already there.

The profile has seven sections:

- **goals** — what kind of work and scope you're looking for right now
- **differentiators** — what makes your background distinct (specific technologies, scale, ownership — not generic claims)
- **focus_areas** — skills or domains you want to go deeper in
- **avoid** — roles, environments, or work types that are wrong fits. Also used in biographical responses: each avoid entry reveals a real value — the tool infers the positive claim, it doesn't quote the constraint
- **seniority_signals** — what separates senior candidates from mid-level ones in your domain
- **working_style** — how you work and think day-to-day. Not skill claims. Not project evidence. How you operate
- **values** — what you believe and care about as a programmer, teammate, and person

`working_style` and `values` are the biographical argument — the thesis about who you are. For biographical prompts, the tool reads them as the argument it needs to make, then selects library paragraphs that prove specific claims within that argument.

Review and edit each section before saving. Without a profile the thesis is generic, the alignment report has no goal-fit signal, and biographical prompts produce resume summaries instead of an argument.

Re-running `profile` archives the previous version automatically — your goal history is preserved.

### 4. Build your claim-evidence library

```bash
uv run clio onboard            # shows your setup checklist and next step
uv run clio sync               # sync library to DB, compute embeddings
uv run clio extract --dry-run  # extract claims, write review file
uv run streamlit run coverletter/label_evals.py  # review claims, build gold standard
uv run clio extract            # insert approved claims into DB
```

`clio onboard` checks your readiness at each step and tells you exactly what to do next.

During the Streamlit labeling session: the app shows you the source paragraph, the extracted claim, the judge's verdict with reasoning, and the full evidence hierarchy. **Approve** (inserts to DB immediately), **Reject** with a failure category, or check **Save as gold standard example** on clear unambiguous cases. You need at least 5 approved and 5 rejected gold standard examples before full extraction runs. Session position saves on every action — reopen and it picks up where you left off.

### 5. Generate a letter

**Argument-driven flow (recommended once claims are extracted):**

```bash
uv run clio outline <jd_file> --company Acme   # build editable outline
# edit the outline — reorder paragraphs, drop irrelevant claims, add notes
uv run clio generate --from-outline acme_outline.md <jd_file>
```

**Classic flow (works without claims):**

```bash
uv run clio
```

Paste the job description, enter the company name, and the tool runs the full flow: generates a letter, shows what's covered and what's missing, offers to fill gaps through Q&A, then lets you revise before saving.

---

## Command reference

### Setup and library building

| Command | What it does |
|---|---|
| `uv run clio init` | First-time setup — creates `.env` and empty `library.md` |
| `uv run clio onboard` | Setup checklist — shows readiness status and next command at each step |
| `uv run clio seed` | Extract paragraphs from existing material (cover letters, resume, notes) |
| `uv run clio build` | Focused Q&A to draw out and document a specific experience |
| `uv run clio build --jd <file>` | Gap-driven mode — analyzes JD against library, Q&A targets gaps |
| `uv run clio reflect` | Capture perspective material — through-lines, pivots, reframes, syntheses |
| `uv run clio sync` | Sync library markdown to SQLite DB, compute embeddings |
| `uv run clio profile` | Build or update your candidate profile |

### Job description management

| Command | What it does |
|---|---|
| `uv run clio jd list` | List saved JDs with date, size, and preview |
| `uv run clio jd rename <old> <new>` | Rename a saved JD |
| `uv run clio jd replace <name>` | Replace a saved JD from clipboard; clears DB cache |

JDs are saved automatically when you paste one during `generate` or `blurb`. They are saved after cleaning — EEO/disability disclosure boilerplate is stripped before storage and before the JD is embedded. The JD embedding is cached so the same JD is not re-embedded across `generate`, `outline`, `blurb`, and `build --jd` runs.

### Claim-evidence pipeline

| Command | What it does |
|---|---|
| `uv run clio extract --dry-run` | Extract claims from library, write review files |
| `uv run clio extract` | Extract, judge, and insert claims into DB (requires gold standard) |
| `uv run streamlit run coverletter/label_evals.py` | Review extracted claims — approve/reject, build gold standard |
| `uv run clio claims` | Show claim count, anchor count, and argument categories per paragraph |
| `uv run clio outline <jd>` | Build editable outline from DB — three-stage retrieval, gaps shown after |
| `uv run clio generate --from-outline <outline> <jd>` | Generate letter from edited outline |

### Interview prep

| Command | What it does |
|---|---|
| `uv run clio interview <jd_file>` | Full interview prep briefing — role snapshot, themes, coverage analysis, likely questions |
| `uv run clio interview <jd_file> --summary` | Short one-page version — fast to read before a call |
| `uv run clio resume-extract` | Manually re-extract resume claims (runs automatically on hash change) |

The interview command prompts for an optional recruiter or HR note (paste and double-Enter to submit). The briefing is saved to `output/YYYY-MM-DD_Company_interview.md`.

Each coverage item is marked `[RESUME]` (on paper and visible to the interviewer), `[LIBRARY]` (in your library but not on resume — needs to come out verbally), or `[GAP]` (thin or no material). The `[LIBRARY]` distinction is the grounding layer: what you need to proactively say because the interviewer can't see it yet.

The agent uses three tools to gather your material per theme: `search_library` (paragraph library), `get_claims` (claims DB — resume and library sources), and `get_experience_facts` (experience register).

### Letter generation

| Command | What it does |
|---|---|
| `uv run clio` | Generate a cover letter — classic paragraph-assembly flow |
| `uv run clio blurb` | Answer a short application prompt — "about me", behavioral, motivation |
| `uv run clio show-library` | Show library stats and experience coverage |
| `uv run clio resume` | Generate a tailored resume PDF alongside a letter |

### Analytics and tracking

| Command | What it does |
|---|---|
| `uv run clio outcome <company> <result>` | Record application result (interview / rejected / offer / ghosted) |
| `uv run clio analytics` | Cross-application patterns — coverage rates, recurring gaps, claim usage |
| `uv run clio log` | Show LLM call log — token counts, cost per call, and cost per session |

The log is stored at `~/.coverletter/runs.jsonl` — one JSON line per API call, with timestamp, caller label, model, token counts, and estimated cost. Survives crashes and accumulates across sessions. Use `--tail N` to show the last N calls and `--sessions N` to show session summaries.

### Evaluation (development tools)

| Command | What it does |
|---|---|
| `uv run python coverletter/evals/align_judge.py` | Check judge accuracy against gold standard — offers patch if misaligned |
| `uv run python coverletter/evals/run_evals.py` | Measure pipeline quality as % of claims approved |
| `uv run python coverletter/evals/retrieval_eval.py` | Compare BM25 vs semantic retrieval — MRR and Hit@3 across 8 query types |

See [`RETRIEVAL_EVAL.md`](RETRIEVAL_EVAL.md) for methodology, example results, and how to extend the evaluation.

Most commands work without flags — they'll ask you what they need. Flags are shortcuts for when you already know the answer.

```bash
uv run clio --model haiku              # cheaper, faster
uv run clio profile --model opus       # worth it for one-time profile generation
uv run clio --fast                     # skip thesis and alignment
uv run clio --role "Senior Data Engineer"
uv run clio seed --file resume.txt
```

Model aliases: `haiku` → `claude-haiku-4-5-20251001`, `sonnet` → `claude-sonnet-4-6`, `opus` → `claude-opus-4-7`.

---

## Full letter flow (what `uv run clio` does, step by step)

> Requires a candidate profile — run `uv run clio profile` first.

### 1. Startup

Shows library stats (how many paragraphs, by tier), experience register status, and profile status.

### 2. Role selection

Choose a target role to filter which paragraphs are eligible, or pick General to use everything.

### 3. Job description

Copy the job description to your clipboard and press Enter. Enter a company name.

EEO/disability disclosure boilerplate is stripped automatically before the JD is processed. If the JD includes company values or a mission statement, those are extracted separately and used to inform the argument framing — the tool uses them to show alignment through what you've done, not by echoing them back.

The JD embedding is cached after the first run. If you run `generate`, then `blurb`, then `outline` on the same JD, the embedding is computed once and reused.

### 4. Letter generation

The tool selects the most relevant paragraphs from your library (ranked by semantic similarity to the JD, capped at 2 paragraphs per experience) and assembles a letter. The opener and closer are written fresh for this specific role and company.

**Opener rule:** the opener connects you to the target employer first — what the organization does, what about their work connects to yours, why this is the right fit. It does not name previous employers and does not open with credentials or employment history.

### 5. Quality checks

**Hard check:** the letter fails immediately if it contains an em-dash.

**LLM check:** scans for banned words, fake-contrast structures, weak opener, closer that doesn't name the company. On failure, the tool proposes a minimal fix:

```
[A]ccept fix  [E]dit manually (revision loop)  [S]kip (keep current):
```

The model stays as close to your source language as possible — it prefers cutting or restructuring over rewriting. If it can't fix something without inventing new language, it flags the sentence: `COULD NOT FIX: [sentence]`.

**Source check:** flags any body sentence where less than 72% of the words appear in your source paragraphs. Warnings, not blockers.

### 6. Letter thesis *(skipped with `--fast`)*

The tool reads the letter and names the central argument it's making about you. If your profile is loaded, it also evaluates goal fit. Confirm it, adjust it, or reject it.

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

Narrative frame: No through-line in library. Run: uv run clio reflect
```

**JD Gaps** are requirements the letter doesn't address. Keep in mind the letter supplements your resume — it covers what your resume doesn't highlight.

**Seniority Signal Gaps** check the dimensions you defined in `seniority_signals` and flag ones genuinely absent from the letter.

**Goal fit** and **Narrative frame** only appear if you have a candidate profile loaded.

### 8. Gap loop *(skipped with `--fast`)*

All gaps are shown at once, numbered. Gaps where your claims DB already has matching material are dimmed — they'll pull in automatically on regeneration without needing new writing. The coverage check is semantic (embedding cosine against your extracted claims), not keyword matching.

```
3 gap(s):

  1. BigQuery experience — critical for this team's warehouse stack
  2. [in library] dbt modeling — material exists in your claims DB
  3. [Seniority] Business impact — letter describes what was built not what it enabled

  Actionable: 1, 3

Address which gaps? (e.g. 1,3 or 'all' or Enter to skip):
```

Enter individual numbers (`1,3`), `all`, or Enter to skip. Press **Ctrl-C** during a Q&A session to stop and return to the regeneration prompt — any paragraphs already saved are kept.

Inside each Q&A session:
- The tool searches your library first so it doesn't re-ask about things already written
- Your resume (if configured) is passed as established context — the coach asks about what's behind the bullets, not what they say
- Questions are validated internally before you see them
- Type **"draft"** to force a draft early; **"done"** to exit without saving
- Hard cap: 2 exchanges, then a draft is forced regardless

After Q&A:
```
[A]ccept  [R]edirect  [K]eep talking:
```
**A** → prompts for role, section name, angle tag, and strength rating → saves to `library_refined.md`

### 9. Regeneration

```
Saved 2 new paragraph(s). Regenerate letter with new material? [Y/n]:
```

### 10. Revision loop

```
Enter a paragraph number, free text for global feedback, or Enter to finish:
```

Give a paragraph number to revise a specific section, or type free text for a global note. After each revision: **[A]ccept** keeps it, **[R]eject** restores the previous version.

### 11. Save

```
Session cost: 45,231 in / 3,102 out tokens  ~$0.18
Save to output/? [Y/n]:
```

Saves `YYYY-MM-DD_CompanyName.md` and `YYYY-MM-DD_CompanyName.pdf` to your output directory.

---

## How the library works

The library is split across several markdown files with distinct roles. The tool reads all configured files and merges them — higher-priority files win when the same experience is covered in multiple places. You don't manage this manually.

| File | What goes here | Priority |
|---|---|---|
| `library.md` | Your raw paragraphs — written directly, Q&A answers, anything you typed. Never rewritten by the tool. | Base |
| `library_refined.md` | Paragraphs built through `clio build` and approved. Takes priority over `library.md` for the same section. | High |
| `library_salvaged.md` | Paragraphs corrected via the diff tool — reviewed against raw source and approved. | High |
| `library_rebuilt.md` | Paragraphs built from scratch through the correct workflow. | High |
| `story_notes.md` | Raw material from conversations that hasn't been turned into paragraphs yet. Surfaced in the diff tool but not used in generation. | — |

**The library compounds.** Each gap session during a letter run produces a new paragraph. Each new paragraph makes the next letter stronger.

---

## Paragraph library format

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

**Meta keys:**
- `strength`: `high` | `medium` | `low`
- `via`: how this paragraph was produced — `seed-notes`, `seed-letter`, `build`, `build+seed`, `reflect`
- `tone`: `opener` | `closer` — marks voice-reference paragraphs
- `angle`: evidence angles (`production-ownership`, `system-design`, `business-impact`) or perspective angles (`through-line`, `pivot`, `reframe`, `synthesis`)

---

## Experience register (`experiences.md`)

Stores raw facts and desired angle framings per experience. Not prose — a structured fact sheet the tool uses to ask better questions.

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

`qa_targets` are written automatically by `clio seed`. The next time you run `clio build` for this experience, those questions drive the Q&A.

---

## Capturing perspective paragraphs (`clio reflect`)

Evidence paragraphs prove specific claims. Perspective paragraphs make the argument about who you are and why your arc makes you right for this role.

```bash
uv run clio reflect
```

| Angle | What it captures |
|---|---|
| `through-line` | The consistent thread across your whole arc |
| `pivot` | A deliberate change in direction with a reason |
| `reframe` | Same experience, different lens |
| `synthesis` | Two experiences that combine into something specific |

Once perspective paragraphs are in your library, they're pinned in prefilter (never filtered out) and labeled `[NARRATIVE FRAME]` for the assembler.

---

## Short application prompts (`clio blurb`)

```bash
uv run clio blurb
```

Two inputs: job description first (used to select paragraphs), then the specific prompt. JD boilerplate is cleaned automatically. Company values from the JD inform the framing.

| Prompt type | What the tool does |
|---|---|
| Biographical / "tell me about yourself" | Reads `working_style` and `values` as the argument spine; selects library paragraphs that prove specific claims within it |
| Behavioral / "describe a time when..." | Picks the best matching library paragraph(s) and tells the story |
| Motivation / "why are you interested in..." | Draws from `goals` profile section and relevant library material |
| Approach / "what is your approach to..." | Answers from actual practice in the library, not philosophy |

Up to 400 words depending on prompt type. Revision loop retains rejected drafts in conversation history.

---

## Writing rules (enforced)

- No em-dash (`—`) anywhere
- No sentence starting with "That"
- No banned phrases: `actually`, `not just`, `not only`, `not simply`, `this matters because`, `the hard part was not`, `what stands out`, `the clearest connection`, `this is the kind of work`, `i am strongest in`, `i combine`
- No generic bridge openers: `that experience fits`, `this role aligns`
- No paragraph ending with a list of 3+ items
- No generic body paragraph opener (must lead with a concrete fact)
- Every body sentence must trace to source paragraphs
- Opener connects to the target employer first — no previous employer names, no credential lead
- Body paragraphs must not restate claims already made in the opener
- `[CLOSER ONLY]` paragraphs must not appear as the first or second body paragraph

---

## Resume builder

```bash
uv run clio resume --company Google
```

For each company in your `resume.typ` that has alternative bullets in `resume_bullets.md`, the tool shows your options and lets you pick per experience.

Output: `output/YYYY-MM-DD_CompanyName.typ` and `.pdf`

Requires Typst: `brew install typst`

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
| `library.db` | SQLite DB — paragraphs, claims, evidence, embeddings, application analytics |
| `.env` | API keys, author name, and path overrides |
| `jds/` | Saved job descriptions — cleaned on save, cached embeddings and company values |
| `output/` | Saved letters and tailored resumes |
| `corrections.md` | Sentence-level fixes applied automatically before generation |

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

## Provider support

| Provider | Generation | Caching | Embeddings | Hybrid | Rerank |
|---|---|---|---|---|---|
| Anthropic | ✓ | 90% cache_control | via Voyage | — | — |
| Mistral | ✓ | 90% cache_key | mistral-embed ✓ | — | — |
| OpenAI | ✓ | 50% auto | text-embedding-3-small ✓ | — | — |
| Cohere | ✓ | unknown | embed-v4.0 ✓ | — | rerank-v3.5 ✓ |
| BGE-M3 | embed-only | local | dense ✓ | hybrid ✓ | — |

`EMBED_MODEL=bge-m3` uses BGE-M3 for all embeddings regardless of generation provider. BGE-M3 requires `uv add FlagEmbedding` and downloads BAAI/bge-m3 (~2GB) on first use.

`OPENAI_EMBED_MODEL` lets OpenAI-compatible hosts specify their embedding model. Defaults to `text-embedding-3-small` for OpenAI proper.

Cohere's reranker runs as Stage 3 in the outline claim pipeline — cross-encoder scoring over the pre-filtered claim set.

See [`ROADMAP.md`](ROADMAP.md) for Ollama and what's planned.

---

## Cost reference

| Operation | Haiku | Sonnet | Opus |
|---|---|---|---|
| Full letter run | ~$0.02–0.05 | ~$0.10–0.25 | ~$0.50–1.25 |
| `seed` (per paste) | ~$0.01 | ~$0.03 | — |
| `profile` (G option) | ~$0.01 | ~$0.05 | ~$0.10–0.25 |
| `build` (Q&A session) | ~$0.01 | ~$0.03–0.05 | — |

Prompt caching is active on Anthropic (90% discount via cache_control) and Mistral (90% via cache_key). OpenAI automatic prefix caching gives ~50% discount. Cohere caching behavior is unknown.

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

### OpenAI

**One `OPENAI_API_KEY` covers generation + embeddings.** Caching is automatic (50% discount).

| Model alias | Full name | Input /1M | Output /1M | Cached input /1M |
|---|---|---|---|---|
| `gpt-4o` | `gpt-4o` | $2.50 | $10.00 | $1.25 |
| `gpt-4o-mini` | `gpt-4o-mini` | $0.15 | $0.60 | $0.075 |
| embeddings | `text-embedding-3-small` | $0.02 | — | — |

### OpenAI-compatible providers (via `OPENAI_BASE_URL`)

**[Regolo.ai](https://regolo.ai)** — Italian, 100% green energy, zero data retention, GDPR by design, open-source models only. Set `OPENAI_BASE_URL=https://api.regolo.ai/v1`.

**[Hugging Face Inference](https://huggingface.co/inference)** — Open-source community, free tier. Set `OPENAI_BASE_URL=https://router.huggingface.co`.

---

## Known issues

**Closer quality depends on your voice reference paragraphs.** Weak source closer paragraphs produce weak synthesized closers. If your closers feel generic, improve the `### Closing` paragraph in `library.md`.

**Q&A can still ask about things you've already documented.** Semantic search reduces this but isn't perfect. If the agent asks about something already written, paste the paragraph and say "this is already documented."

**Experience name matching is exact.** Coverage tracking matches experience names in `experiences.md` against section names in the library files. Keep naming consistent across both.

---

## Monitoring and evaluation pipeline

### How monitoring works

Every API call is logged automatically to `~/.coverletter/runs.jsonl` — one JSON line
per call with timestamp, caller label, model, input/output tokens, cache hit/miss, and
estimated cost. The log persists across sessions and survives crashes.

```bash
uv run clio log              # last 20 calls + last 10 session summaries
uv run clio log --tail 50    # last N calls
uv run clio log --sessions 5 # session summaries only
```

Each line in the log looks like:

```json
{
  "ts": "2026-06-08T14:23:01",
  "label": "extract",
  "model": "claude-haiku-4-5-20251001",
  "input_tokens": 4821,
  "output_tokens": 312,
  "cache_read_tokens": 3200,
  "cost_usd": 0.0041
}
```

The `label` field identifies which code path made the call: `extract`, `judge`,
`build`, `seed`, `generate`, `interview`, `align_judge`, `profile`, etc. This lets
you see exactly what each command cost and compare costs across runs as you tune
prompts or switch models.

### Ground truth pipeline

The monitoring log connects to evaluation through the extraction pipeline. The full
loop:

**Step 1 — Extract**
```bash
uv run clio extract --dry-run    # extract claims, log the API call
```
Writes `extractions_review.json`. The extraction call is logged with label `extract`.

**Step 2 — Label (manual ground truth)**
```bash
uv run streamlit run coverletter/label_evals.py
```
Hand-label every extracted claim: approve or reject, with a failure category on
rejects. Check "Save as gold standard" on clear unambiguous cases — both correct
approvals and correct rejections. This is your hand-crafted ground truth dataset.
Session position saves on every action so you can label across multiple sessions.

**Step 3 — Run extraction live**
```bash
uv run clio extract    # requires 5 approved + 5 rejected gold standard examples
```
Approved claims insert to DB. The judge call is logged with label `judge`.

**Step 4 — Calibrate the judge**
```bash
uv run python coverletter/evals/align_judge.py
```
Runs the judge against your gold standard. Reports accuracy, precision, and recall.
If alignment is below target (recall ≥ 89%, accuracy ≥ 80%), offers to draft a
targeted patch to the judge prompt. The calibration call is logged with label
`align_judge`.

**Step 5 — Measure pipeline quality**
```bash
uv run python coverletter/evals/run_evals.py
```
Measures overall pipeline quality as the percentage of claims the judge approves.
Run this before and after a prompt change to measure the effect. Logged with label
`run_evals`.

**Step 6 — Compare across runs**
```bash
uv run clio log --tail 50
```
Every extraction and evaluation run is in the log. Compare token costs and session
costs before and after prompt changes to understand the quality/cost tradeoff.

### The feedback loop

```
extract --dry-run
    ↓
hand-label in Streamlit  ← this is your ground truth
    ↓
extract (live)
    ↓
align_judge.py  ←  if below target: patch judge prompt → repeat
    ↓
run_evals.py    ←  compare % approved before/after changes
    ↓
clio log        ←  cost and token tracking across all runs
```

As your gold standard grows (more labeled examples), `align_judge.py` becomes a
more reliable signal. As your library grows, `run_evals.py` measures whether the
judge stays calibrated across new material.

### Retrieval evaluation

```bash
uv run python coverletter/evals/retrieval_eval.py
```

Compares BM25 vs semantic retrieval across 8 query types. Reports MRR and Hit@3 for
each method. See [`RETRIEVAL_EVAL.md`](RETRIEVAL_EVAL.md) for full methodology.

---

## Development

```bash
uv run pytest tests/
```

All tests run without API keys and without touching your real library or profile. The test suite uses a synthetic fixture library in `tests/fixtures/` — fake company names, fake paragraphs, no personal data.

**Test isolation:** any test that needs a `Config` object should use the `test_cfg` fixture defined in `tests/conftest.py`. It points all reads at `tests/fixtures/` and all writes at pytest's `tmp_path`. Never call `load_config()` directly in tests.
