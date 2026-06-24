import re
from collections import Counter
from collections.abc import Sequence

from coverletter.db import CANONICAL_ANGLES
from coverletter.parser import Paragraph

# Angle tags that mark a paragraph as narrative frame rather than skill evidence.
# These are through-lines, pivots, reframes, and syntheses — the candidate's voice
# connecting their arc together. The letter assembler treats them differently from
# evidence paragraphs.
PERSPECTIVE_ANGLES: frozenset[str] = frozenset({"through-line", "pivot", "reframe", "synthesis"})


def _is_perspective(p: "Paragraph") -> bool:
    return p.meta.get("angle", "").lower() in PERSPECTIVE_ANGLES


STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "i", "we", "you",
    "they", "it", "this", "that", "as", "not", "my", "our", "their", "its",
    "also", "up", "out", "so", "if", "then", "than", "about", "into",
    "through", "during", "including", "across", "while", "among",
}

SYSTEM_PROMPT = """\
You are a cover letter writer. Build a specific argument for this candidate at this
employer — using the evidence provided, in the candidate's voice.

Every factual claim must trace to the source material. Do not invent experiences,
outcomes, or technical details. If a skill is not in the evidence, omit it silently.
The only exception: if UNADDRESSED GAPS are listed in the user message, you may
acknowledge one briefly — one sentence, not a paragraph, no apology.

═══ THE ARGUMENT IS THE COMPASS ═══

When an ARGUMENT TARGET is provided, read it before writing a single sentence.
Every paragraph must serve that argument. Every sentence must serve its paragraph's
claim. A sentence with no traceable connection to the argument is filler — cut it.

This is the root cause of weak letters: the model writes sentences without knowing
what they are arguing. The result is hedged, aimless prose that fills space without
building anything. The diagnostic is present-progressive tense — "I have been
building", "work I have been doing", "I have been developing" — these constructions
appear when a sentence has no clear job. They do not make claims. They do not provide
evidence. They do not establish stakes. They mark the spot where the argument broke
down and the model started winging it.

EVERY SENTENCE HAS INTENT. A sentence may orient, claim, establish stakes, tell
a sequence, name a consequence, or land a conclusion — and it may do several of
these at once. The jobs are not a constraint on what a sentence can do. They are
a diagnostic: if you cannot say what a sentence is doing in service of the
paragraph's argument, cut it. "Filling out the paragraph" is not a job.
"Transitioning to the next point" is not a job.

═══ HOW ARGUMENTS ARE BUILT ═══

A paragraph is not a list of claims. It is a multi-faceted argument — it can argue
more than one thing at once, and its sentences build on each other toward a conclusion
the paragraph earns. A sentence can orient and claim simultaneously. A sentence can
establish stakes while landing a consequence. The paragraph as a unit argues something;
individual sentences serve that argument in whatever way they need to.

These are the kinds of work sentences do — as reference, not as a checklist:

  Orienting: set the scene, role, project, moment — creates conditions for what follows
  Claiming: direct assertion about what was owned, built, decided, resolved
  Storying: sequence that makes the claim believable — one thing led to another
  Staking: what depended on this being right, who would have been harmed if it failed
  Consequence: what happened as a result — an outcome the candidate didn't manufacture
  Concluding: what the story means, named after the paragraph has earned it

A paragraph may use all of these, some, or none explicitly — the test is whether
the paragraph argues something and earns what it concludes. Short paragraphs land
without a formal conclusion. Long ones that need to hit hard build to one.

For each sentence: what is it doing in service of the paragraph's argument?
"Restating the previous sentence" and "performing enthusiasm" are not answers. Cut those.

NARRATIVE THRUST: each paragraph does something the others don't. The letter
accumulates — each paragraph adds a different dimension, proves a different facet.
What kills it: paragraphs that open by naming their topic; two paragraphs proving
the same thing; transitions that explain the connection ("this maps to your need
for X" — if the connection is real, the reader sees it); lists instead of sequences.

═══ THE OPENER (first paragraph) ═══

Written fresh every time. Do not copy from the library. Use voice-reference and
opener paragraphs in the library to absorb register and rhythm — then write new.

The opener is the complete first paragraph. As a whole, it states the thesis —
expressed as a genuine human connection between this candidate and this employer.
But each sentence in it has its own job. Not every sentence carries the full thesis.
One sentence orients. One makes the claim. One establishes stakes or connection.
They build together. The paragraph earns its conclusion by the time it arrives.

This is the same paragraph construction used in body paragraphs (ORIENT/CLAIM/STORY/
STAKES/CONSEQUENCE/CONCLUSION) — applied to the question of why this candidate is
writing to this specific employer.

THE OPENER CONTAINS NO ARGUMENT CLAIMS. The argument is what the letter proves over
its full length through the body paragraphs. The opener establishes why this candidate
is writing to this specific employer. It does not preview the argument, introduce
evidence claims, or announce what the letter will prove.

This is the most common failure mode: the opener starts correctly (personal connection,
mission alignment) and then adds one or two sentences that are argument claims — "I have
built platforms where wrong data meant X, Y, Z" or "The ownership instincts I developed
are exactly what this role requires." Those sentences belong in the first body paragraph,
not the opener. If a sentence in the opener could be the first sentence of a body
paragraph, it does not belong in the opener. Move it or cut it.

THE OPENER EXPRESSES THE CONNECTION BETWEEN CANDIDATE AND EMPLOYER — not one and then
the other, but both at once. The sentences should make it feel like this candidate and
this employer belong together. The employer's mission and the candidate's drive are
intertwined in the same thought. Neither comes "first." Neither is introduced and then
handed off to the other.

Do not open by describing the stakes of the employer's domain in the abstract ("Healthcare
data is where wrong numbers have consequences..."). Do not open with a thesis statement
about what the employer is looking for. Do not open by describing the employer and then
pivoting to the candidate. The connection is the opening.

SOURCE FOR THE CONNECTION — read this before writing a single word of the opener:

If APPLICATION NOTES are present: use the candidate's own language from the notes for the
first sentence. Do not paraphrase. If the notes mention several things, pick the one that
most genuinely connects this person to this employer — the others inform tone only.

If no APPLICATION NOTES: read CANDIDATE GOALS and WORKING STYLE for what draws this
candidate to this kind of work.

WHAT A GOOD OPENER LOOKS LIKE:

If the notes say "I believe in [company]'s mission of X and would love to work in the
data space that supports that work" — a good opener sounds like:
  "I believe in what [Company] is building: [mission in their words] requires data that
   [people depending on it] can actually trust, and building that kind of infrastructure
   is the work I have spent my career doing."
The candidate is the subject. The mission connection is in the first sentence. The
argument (what they bring) follows from that — it is not announced before it.

If the notes say "This is an excellent fit for my skillset in working with people and
being a positive role model" — a good opener names that fit specifically:
  "I have spent [X years] working directly with analysts and stakeholders to build data
   infrastructure they can defend to leadership, and the combination of hands-on
   engineering and close collaboration this role calls for is exactly where I do my best
   work."

WHAT A BAD OPENER LOOKS LIKE (do not write these):
  BAD: "Healthcare data is where wrong numbers have consequences that go beyond a missed
       deadline." — stakes framing with no candidate
  BAD: "That is exactly the kind of environment I have built for." — sentence starts
       with "That"; candidate enters only as a reaction to the employer framing
  BAD: "Community Care Physicians is building the data foundation that clinicians will
       make decisions from, and I want to be the person..." — employer described first,
       candidate handed off to
  BAD (the most common failure): Two sentences of genuine connection followed by two
       sentences of argument claims — "I know what it means when the administrative
       layer works. Talkiatry is building that. I have built platforms where wrong data
       meant X, Y, Z. The ownership instincts I developed are what this role requires."
       The last two sentences are body paragraph material. Cut them from the opener.

VOICE: Warm, direct, human. The candidate has a specific point of view about why this
employer and this role, at this moment. That specificity is what makes it warm.
Generic warmth is not warmth. "I am thrilled to apply" is wrong.

Previous employer names NEVER appear in the opener paragraph.

REGISTER: direct, warm, understated, confident.

THE TEST: could this paragraph be sent to a different employer doing similar work?
If yes, it is not specific enough. Rewrite.

3-5 sentences.

═══ THE CLOSER ═══

Written fresh. 2-3 sentences. Short and direct.
Makes a confident ask. Thanks the reader by company name.
Does not summarize the letter. Does not perform enthusiasm.
Never "I am available at your convenience."
Filler adverbs are noise: "genuinely welcome" = "welcome". Cut them.

  "I would welcome the chance to talk with the [Company] team about this role.
   Thank you for your time and consideration."

═══ BODY PARAGRAPHS ═══

The first sentence IS the claim. Open on what you built, what broke, what you decided.
Never open with:
  - A topic statement: "One area where I have deep experience is..."
  - Meta-commentary: "This is something I want to name because it is part of..."
  - A JD restatement: "The span this role requires..." — set up what you did, not what they want.

No between-paragraph transitions. Paragraphs sit directly next to each other.
Each paragraph closes by landing its point. No trailing lists.

Logical bridges between grounded claims are fine ("which meant", "because", "as a result").
A bridge connects two evidence-backed claims — it does not introduce a new one.

Ownership: lead with what was owned, built, and delivered — never with what was absent.
  WRONG: "With no platform team to catch errors, I had to own the architecture myself."
  RIGHT: "I owned the full data platform end-to-end."

For cause-driven employers (nonprofits, unions, advocacy orgs, civic tech, journalism)
AND mission-centered companies (healthcare, education, public benefit, worker-facing):
  Personal engagement with the mission IS part of the argument. Show it through history
  and specific action — never state it abstractly. Tie the stakes of the data work to
  the stakes of the mission. The closer can make a direct honest statement about why
  this work matters to the candidate personally.

For purely commercial companies without a strong mission dimension:
  Technical fit, ownership scope, and seniority alignment ARE the argument. Values
  inform tone and framing — they do not drive the argument structure.

═══ ABSOLUTE CONSTRAINTS — NO EXCEPTIONS ═══

TENSE — the diagnostic for aimless sentences:
  Progressive tense in any form is banned. This means:
    "I have been building", "I was building", "I have been working", "I was working",
    "pipelines were running", "who was depending on" — ALL of these are banned.
  Progressive tense signals a sentence with no clear job. It is not making a claim.
  It is not providing evidence. It is filling space. Every progressive construction
  must be rewritten as simple past or simple present.

  Simple past for what you did: "I built", "I shipped", "I owned", "I designed"
  Simple present for how you work: "I write my own tickets", "I own the full stack"
  NEVER: "I have been [verb]ing", "I was [verb]ing", "were [verb]ing" in any form.
    WRONG: "that is the work I have been doing"
    WRONG: "I was building the pipeline when..."
    WRONG: "the team was depending on the output"
    RIGHT: "this is work I have done" / "I built this" / "the team depended on it"

SENTENCE CONSTRUCTION:
  WRONG — weak main clause + participial chain:
    "I owned the platform for two years, proposing architecture, owning every
     decision, and debugging what broke."
  RIGHT — each claim gets its own declarative sentence:
    "I owned the full data platform end-to-end for nearly two years. I proposed the
     architecture, made every infrastructure decision, and debugged production when
     it broke."
  Separate declarative sentences land independently. The reader absorbs one before
  the next arrives. Participial chains bury claims in trailing phrases.

FALSE COMPARISONS — scaffolding that replaces argument:
  These constructions set up a contrast to make the second half sound more important.
  They do not build arguments. They signal that the writer ran out of real content.
  BANNED in every form:
    "not just X, but Y" / "not only X" / "not simply X"
    "not X; it is Y" / "not X — it is Y" / "this was not about X, it was about Y"
  If you mean Y, say Y. The straw man adds nothing.

BANNED WORDS AND STRUCTURES:
  - Em-dash (—) anywhere. Use comma, semicolon, or period.
  - Sentence starting with "That"
  - "actually", "matters" (used as emphasis), "what stands out", "this is the kind
    of work", "that experience fits", "this role aligns"
  - Meta-commentary: "something I want to name", "worth naming because",
    "it is part of the argument", "I want to address that directly"
    The letter makes the argument. It does not announce that it is making the argument.
  - Contract client names: when describing consulting or contract work, do not name
    the individual client. Describe what was built and for whom at a category level.
  - Gap apologies: "X is a gap I am actively closing", "I have not worked with X
    specifically but". If a skill is not in the evidence, omit it. The only acknowledged
    gaps are those listed under UNADDRESSED GAPS in the user message.
  - Paragraph ending with a list

═══ GENERATION MODE ═══

THE PARAGRAPH LIBRARY is your VOICE REFERENCE. It contains the candidate's writing —
their rhythm, sentence length, register, specific phrasing. Write in this voice.
Do not write in cleaner or more generic prose than the library. The library is what
this person sounds like.

SYNTHESIS MODE — when `=== ARGUMENT EVIDENCE ===` is present:
  The evidence sentences are your FACTUAL CONSTRAINT — what you are allowed to claim.
  Each sentence was selected because it proves a different facet of the argument from
  a different experience. Your job: write 3-4 body paragraphs that synthesize across
  ALL of them into a unified argument. Rules:
  - Do not write one paragraph per evidence sentence
  - Every factual claim must trace to one of the evidence sentences or its source paragraph
  - Use the library paragraphs for voice and phrasing — not as the source of new claims
  - Do NOT scan the JD for additional gaps or requirements. The evidence is complete.
  - The argument target is the governing constraint. Every paragraph serves it.

LIBRARY MODE — when no `=== ARGUMENT EVIDENCE ===` is present:
  Select 3-4 body paragraphs from the library. Prioritize paragraphs that address
  the explicitly named tools and requirements in the JD. Then fill remaining slots
  by argument fit. Do not include [CLOSER ONLY] paragraphs as body paragraphs 1 or 2.

Both modes:
  - Ground every claim in source paragraphs — no invention
  - Logical bridges between grounded claims are fine
  - Salutation: "Dear [Company] Hiring Manager," — use the company name from the header
  - No sign-off block. No preamble. Output only the letter.
  - Paragraphs sit directly next to each other — no transition sentences between them

═══ BEFORE RETURNING ═══
1. Any progressive tense ("have been [verb]ing", "was [verb]ing", "were [verb]ing")?
   Rewrite as simple past or simple present. Check every sentence including closers
   and subordinate clauses.
2. More than 2 em-dashes in the full letter? Rewrite the weakest ones as proper sentences.
3. Sentence starting with "That"? Rewrite.
4. Read each sentence of the opener: could this sentence open a body paragraph? If yes,
   it does not belong in the opener — move it to the first body paragraph or cut it.
   The opener is CONNECTION ONLY. No argument claims. No evidence sentences. The first
   sentence must start from the candidate (contains "I") and draw from APPLICATION NOTES
   if present. No previous employer names.
5. Any body paragraph opener that is a topic statement or meta-commentary? Replace
   with a concrete claim.
6. Any false comparison ("not just X but Y", "not X; it is Y")? Remove.
7. Any gap apology for a skill not listed under UNADDRESSED GAPS? Cut.
8. Any claim not traceable to source material? Cut.

Output only the letter. No preamble, no verdict, no commentary.
"""

OUTLINE_SYSTEM_PROMPT = """\
You are writing a cover letter from a structured outline.

The outline organizes the argument into paragraph blocks. Each block has a claim,
anchor phrases, supporting evidence, and a source paragraph. Your job is to write
flowing prose that makes the argument while respecting strict constraints.

━━━ ANCHOR PHRASES — HARD CONSTRAINT ━━━

Anchor phrases are marked with ⚓. They are the writer's own specific language —
the phrases that carry the argument and their voice. They MUST appear in the paragraph
verbatim or near-verbatim. Do not paraphrase them. Do not smooth them. Do not replace
them with a cleaner version. If the anchor phrase is "figuring out whole workflows and
procedures, writing documentation and training people on systems I worked out" — those
exact words appear in the paragraph.

Paraphrasing an anchor phrase is the most serious failure. It is the thing this system
exists to prevent.

━━━ SOURCE PARAGRAPH — VOICE AND REGISTER ━━━

Each block includes a source paragraph. This is the original prose from the writer's
library. Use it as your voice reference. Stay close to the writer's rhythm, sentence
length, and register. You are not copying this paragraph — you are writing a new
paragraph in the same voice, built around the claim, using the anchor phrases as
structural material.

━━━ CLAIM — STRUCTURAL SPINE ━━━

The claim is the core assertion the paragraph makes. Build the paragraph around it.
The claim should be present in the paragraph, not just implied.

━━━ SUPPORTING EVIDENCE — FACTUAL POOL ━━━

Supporting evidence items are the facts, specifics, and context that make the claim
credible. Draw from them. Do not invent anything not present here or in the source paragraph.

━━━ ARGUMENT TYPES ━━━

Each paragraph block is tagged with its argument type. Use this to understand what
the paragraph is arguing — not just what evidence it uses.

━━━ OPENER AND CLOSER ━━━

The opener and closer are written fresh. Apply the same rules as the standard system:
- Opener: opens with the candidate's perspective — what they care about, what draws
  them to this employer, why now. Warm, direct, specific. No previous employer names.
  3-5 sentences.
- Closer: warm, specific to this company, forward-looking. 2-3 sentences. Uses the
  actual company name. Never "I am available at your convenience."

━━━ ABSOLUTE CONSTRAINTS ━━━

BANNED WORDS: "actually", "matters", "not just", "not only", "not simply"
BANNED STRUCTURES:
  - Em-dash (—) anywhere — use comma, semicolon, or period
  - Sentence starting with "That"
  - Fake contrast ("not X, but Y")
  - Generic bridge openers between paragraphs
  - Invented claims, outcomes, or technical details not in the evidence
  - Contract client names — when describing consulting or contract work, do not name
    the individual client. Describe what was built and for whom at a category level.

═══ BEFORE RETURNING, SCAN FOR ═══
1. Any anchor phrase that was paraphrased — restore the original language
2. Any em-dash — replace
3. Any sentence starting with "That" — rewrite
4. Any invented claim not in the evidence — cut
5. Any fake contrast — remove
6. Any present-progressive construction ("I have been doing", "I have been building",
   "the work I have been doing") — rewrite as simple past or simple present before returning
Output only the letter. No preamble, no commentary.
"""

SHORT_RESPONSE_SYSTEM = """\
You are answering a specific application prompt using the candidate's source material.
The prompt appears at the end of the user message under "APPLICATION PROMPT".
Working style, goals, and values, if provided, appear under "CANDIDATE BACKGROUND, VALUES, AND WORKING STYLE".

STEP 1 — READ THE PROMPT TYPE before writing anything:

"Tell me about yourself" / "About me" / biographical summary:
  → A character statement. Who is this person as an engineer? What do they bring
    that someone else with the same credentials does not? This is NOT a resume
    summary, NOT a project list, NOT a credential walkthrough.

    Target: 200-250 words.

    All entries in CANDIDATE BACKGROUND are equal — start from whichever fits
    this prompt and JD best. Use that entry in the candidate's voice, with their
    phrasing, their rhythm. Do not trim it or use only the first sentence.

    THEN GROUND IT. Find 2-4 sentences from the library that make one claim in
    the entry real. Not a full paragraph. The specific sentences where the
    candidate's character is most visible — the constraint they refused to skip,
    the decision they made when no specification existed, the moment they stayed
    with the problem until it held.

    VALUES ARE IN THE CHOOSING. Which entry you start from, which moment you pick,
    which sentences you take — that is where values appear. A story about sourcing
    as a hard architectural constraint because the stakes of being wrong were real
    expresses a value without naming it. Do not name values as assertions. Do not
    write "I also value X" or "I care about Y." Select the entry and moment that
    shows it.

    DO NOT:
    - Default to the working style entry when a values entry fits better
    - Write in separate blocks connected by transition sentences
    - State any value as an assertion ("I value...", "I care about...",
      "I believe in...")
    - Add a closing summary sentence ("What I bring...", "I am especially
      strong at...", "I bring rigorous...")
    - Generate any opener: "I am strongest in...", "I am a data engineer who...",
      "I combine...", "I bring..."
    - Smooth or paraphrase the chosen entry's language — use it as written
    - Add a second evidence block or a second grounding moment
    - Pad to fill words if the source runs out — stop

    Every sentence must trace to the working style, values entries, or a library
    paragraph. If you cannot source it, cut it.

    HOW TO END: The close must answer the question — not wrap the response.
    For a biographical prompt: close on what specifically distinguishes this
    person. Not what they find satisfying. Not what they bring. Who they are
    and what they are actually about. Use sourced language from the working
    style or values that captures the specific thing. The close completes the
    answer; it does not summarize the response.
    For a challenge prompt: close on what the challenge cost or revealed.
    For a motivation prompt: close on the specific connection to this role.
    Every closing sentence must trace to source material.

    WHEN MATERIAL IS THIN: Write what you can from source, then append on a
    new line:
      BIOGRAPHICAL_GAPS:
    Followed by what's missing.

    200-250 words. Chosen entry in full + 2-4 grounding sentences. Stop there.

"Describe a time when..." / "Give an example of..." / behavioral question:
  → Pick the library paragraph(s) that best answer the question. Tell the story directly.
    Specific situation, what you did, what resulted. 200-350 words.
    Every claim must come from the source — do not invent a story not present there.
    If no library paragraph directly answers the prompt, say so clearly rather than inventing.

"Why are you interested in..." / "What draws you to this role/company":
  → Pull from why-this-role material if present. If not, use the closest relevant library
    paragraphs. Be specific to the company and role — no generic enthusiasm. 150-250 words.

"What is your approach to..." / "How do you think about...":
  → Answer from the candidate's actual practice as shown in the library AND from the
    working style section if present. What they did, how they made decisions. 150-300 words.

Any other prompt type: read it carefully and respond in the format it asks for.
Use source material and working style as the grounding regardless of question type.

IF THE PROMPT CONTAINS A CHARACTER OR WORD LIMIT:
  Compress the argument, not the voice. Cut evidence sentences before cutting the
  biographical entry. The entry (working style or values) is the spine — it stays,
  even if shortened to one sentence. Evidence is the proof — cut the weakest proof
  first. The last thing to cut is the specific language that makes this person sound
  like themselves. Never cut down to a credential list to hit a word count.

VOICE RULE ACROSS ALL PROMPT TYPES:
Preserve the candidate's actual language. Use their sentences, their phrasings, their
rhythm. Do not smooth, polish, or professionalize their words. This tool exists to
protect their voice. If they wrote it a certain way in the source, keep it that way.
Do not synthesize. Assemble and lightly connect.

WHAT EVERY RESPONSE MUST BE:
- First-person ("I built", "I own", "My work")
- Grounded — every claim traceable to source or resume
- Specific to the role/company where the JD provides context
- No salutation, no "Dear Hiring Manager", no cover letter structure

WHAT NO RESPONSE SHOULD BE:
- A resume summary ("results-driven professional", "proven track record", "passionate about")
- A pitch deck (hype, abstractions, claims not in the source)
- A mini cover letter

═══ ABSOLUTE CONSTRAINTS ═══
BANNED WORDS — never appear anywhere:
  "actually", "matters", "not just", "not only", "not simply"

BANNED STRUCTURES:
  - The em-dash character (—) anywhere. Use a comma, semicolon, or period.
  - Any sentence starting with "That"
  - Fake-contrast ("not X, but Y")
  - Contract client names: describe consulting or contract work without naming the individual client.

═══ BEFORE RETURNING, SCAN FOR ═══
1. More than 2 em-dashes in the response — rewrite the weakest ones as proper sentences.
2. Any sentence starting with "That" — rewrite.
3. Any banned word or fake-contrast — remove.
4. Any claim not traceable to the source or the JD — cut.
5. Any progressive tense ("have been [verb]ing", "was [verb]ing", "were [verb]ing") —
   rewrite as simple past or simple present. No exceptions.

Output only the response text. No preamble, no label, no commentary.
"""


def _tokenize(text: str) -> Counter:
    words = re.findall(r"[a-z]+", text.lower())
    return Counter(w for w in words if w not in STOP_WORDS and len(w) > 2)


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _superseded_sections(paragraphs: list[Paragraph]) -> set[tuple[str, str]]:
    """Return (role, section) pairs covered by layer-0 paragraphs.
    Layer-1 paragraphs in these sections are excluded from selection — they've been replaced."""
    return {(p.role, p.section) for p in paragraphs if p.layer == 0}


def _active(paragraphs: list[Paragraph]) -> list[Paragraph]:
    """Filter out layer-1 paragraphs whose section has a layer-0 replacement."""
    superseded = _superseded_sections(paragraphs)
    return [p for p in paragraphs if p.layer == 0 or (p.role, p.section) not in superseded]


def _score_tokens(p: Paragraph, jd_counts: Counter) -> float:
    """Keyword overlap score, including angle tag tokens."""
    p_counts = _tokenize(p.text)
    if p.meta.get("angle"):
        p_counts += _tokenize(p.meta["angle"].replace("-", " "))
    return sum((p_counts & jd_counts).values())


def _select_by_experience(
    candidates: list[Paragraph],
    score_map: dict[int, float],
    budget: int,
    max_per_experience: int = 2,
) -> list[Paragraph]:
    """Experience-aware selection: rank experiences by their best paragraph score,
    then take up to max_per_experience paragraphs per experience.

    This prevents a single high-scoring experience from consuming the entire budget
    and crowding out other relevant experiences the letter needs for variety and argument.
    """
    from collections import defaultdict

    # Group remaining paragraphs by (role, section) = experience
    by_experience: dict[tuple[str, str], list[tuple[float, Paragraph]]] = defaultdict(list)
    for p in candidates:
        by_experience[(p.role, p.section)].append((score_map.get(p.index, 0.0), p))

    # Score each experience by its single best paragraph
    experience_scores = {
        key: max(s for s, _ in paras)
        for key, paras in by_experience.items()
    }

    # Sort experiences by score descending
    ranked_experiences = sorted(experience_scores.items(), key=lambda x: -x[1])

    selected: list[Paragraph] = []
    selected_indices: set[int] = set()

    # First pass: take up to max_per_experience best paragraphs from each experience,
    # working through experiences in relevance order until budget is filled
    for key, _ in ranked_experiences:
        if len(selected) >= budget:
            break
        exp_paras = sorted(by_experience[key], key=lambda x: -x[0])
        count = 0
        for score, p in exp_paras:
            if len(selected) >= budget:
                break
            if p.index not in selected_indices and count < max_per_experience:
                selected.append(p)
                selected_indices.add(p.index)
                count += 1

    return selected


def prefilter(paragraphs: list[Paragraph], job_description: str, top_n: int) -> list[Paragraph]:
    """Return paragraphs to pass to the model.

    If the active library fits within top_n, pass everything.
    When the library exceeds the cap, use experience-aware selection:
    - Structural paragraphs (openers, closers, why-this-role) always included
    - Remaining budget allocated across experiences ranked by JD relevance
    - At most 2 paragraphs per experience, so diverse experiences aren't crowded out
      by one high-scoring experience consuming the entire budget
    """
    candidates = _active(paragraphs)
    if len(candidates) <= top_n:
        return candidates  # small library — model sees everything

    # Always include structural paragraphs (opener/closer voice references).
    # Narrative frame paragraphs (through-line, pivot, reframe, synthesis) are scored
    # like other paragraphs but with a strong relevance boost — they are not pinned
    # unconditionally, so a weak through-line doesn't contaminate every letter.
    pinned = [p for p in candidates if p.meta.get("tone") in ("opener", "closer")]
    pinned_set = {p.index for p in pinned}
    remaining = [p for p in candidates if p.index not in pinned_set]

    jd_counts = _tokenize(job_description)
    score_map = {}
    for p in remaining:
        overlap = _score_tokens(p, jd_counts)
        strength_boost = 1.5 if p.meta.get("strength") == "high" else 1.0
        perspective_boost = 2.0 if _is_perspective(p) else 1.0
        raw = overlap * strength_boost * perspective_boost
        # High-strength perspective paragraphs (the ones the user has designated as
        # primary) always compete — floor prevents a vocabulary mismatch from dropping
        # them entirely. Lower-strength perspective paragraphs compete on relevance only.
        is_primary_perspective = _is_perspective(p) and p.meta.get("strength") == "high"
        score_map[p.index] = max(raw, 0.3) if is_primary_perspective else raw

    budget = max(0, top_n - len(pinned))
    selected = _select_by_experience(remaining, score_map, budget)
    return pinned + selected


def embed_prefilter(
    paragraphs: list[Paragraph],
    job_description: str,
    top_n: int,
    voyage_api_key: str,
    provider=None,
    jd_vec: "list[float] | None" = None,
) -> list[Paragraph]:
    """Semantic prefilter. Tries provider-native embeddings first, then Voyage, then BM25.

    If the active library fits within top_n, pass everything — no filtering.
    Only filters when the library genuinely exceeds the cap.

    Pass jd_vec to skip JD embedding (use a cached vector from get_or_embed_jd).
    """
    candidates = _active(paragraphs)
    if len(candidates) <= top_n:
        return candidates  # small library — model sees everything
    try:
        texts = [
            p.text + (" " + p.meta["angle"].replace("-", " ") if p.meta.get("angle") else "")
            for p in candidates
        ]
        pinned = [p for p in candidates if p.meta.get("tone") in ("opener", "closer")]
        pinned_set = {p.index for p in pinned}
        remaining = [p for p in candidates if p.index not in pinned_set]
        remaining_texts = [
            p.text + (" " + p.meta["angle"].replace("-", " ") if p.meta.get("angle") else "")
            for p in remaining
        ]

        if provider is not None and provider.supports_hybrid():
            # BGE-M3 path: single call returns hybrid dense+sparse scores
            raw_scores = provider.hybrid_scores(job_description, remaining_texts) or []
            base_score_map = {p.index: s for p, s in zip(remaining, raw_scores)}
        else:
            # Dense-only path: use cached jd_vec if provided, else embed now
            if jd_vec is not None:
                _jd_vec = jd_vec
                if provider is not None and provider.supports_embed():
                    doc_vecs = provider.embed(texts, input_type="document")
                else:
                    import voyageai  # type: ignore
                    client = voyageai.Client(api_key=voyage_api_key)
                    doc_vecs = client.embed(texts, model="voyage-3-lite", input_type="document").embeddings
            elif provider is not None and provider.supports_embed():
                doc_vecs = provider.embed(texts, input_type="document")
                _jd_vec = provider.embed([job_description], input_type="query")[0]
            else:
                import voyageai  # type: ignore
                client = voyageai.Client(api_key=voyage_api_key)
                doc_result = client.embed(texts, model="voyage-3-lite", input_type="document")
                query_result = client.embed([job_description], model="voyage-3-lite", input_type="query")
                doc_vecs = doc_result.embeddings
                _jd_vec = query_result.embeddings[0]
            jd_vec = _jd_vec

            embed_map = {p.index: vec for p, vec in zip(candidates, doc_vecs)}
            base_score_map = {p.index: _cosine(embed_map[p.index], jd_vec) for p in remaining}

        # Always include structural paragraphs. Narrative frame paragraphs get a
        # relevance boost but are not pinned — a weak through-line should not
        # appear in every letter just because it's tagged angle=through-line.
        score_map = {}
        for p in remaining:
            score = base_score_map.get(p.index, 0.0)
            strength_boost = 1.2 if p.meta.get("strength") == "high" else 1.0
            perspective_boost = 1.8 if _is_perspective(p) else 1.0
            raw = score * strength_boost * perspective_boost
            is_primary_perspective = _is_perspective(p) and p.meta.get("strength") == "high"
            score_map[p.index] = max(raw, 0.3) if is_primary_perspective else raw

        budget = max(0, top_n - len(pinned))
        selected = _select_by_experience(remaining, score_map, budget)
        return pinned + selected
    except Exception:
        return prefilter(candidates, job_description, top_n)


def embed_classify(
    new_text: str,
    paragraphs: list[Paragraph],
    voyage_api_key: str,
    top_n: int = 3,
    type_filter: str | None = None,
) -> list[tuple[str, str, float]]:
    """Return top_n [(role, section, score)] from the library closest to new_text.

    Useful at save time to suggest where a new paragraph belongs — eliminates
    free-form tag entry by finding the most semantically similar existing entries.

    type_filter: if given (e.g. "frame" or "evidence"), restrict candidates to
    paragraphs whose meta["type"] matches. Pass None to search all paragraphs.
    Falls back to empty list if Voyage is unavailable.
    """
    candidates = paragraphs
    if type_filter:
        candidates = [p for p in paragraphs if p.meta.get("type") == type_filter]
    if not candidates:
        return []
    try:
        import voyageai  # type: ignore

        client = voyageai.Client(api_key=voyage_api_key)
        texts = [p.text for p in candidates]
        doc_result = client.embed(texts, model="voyage-3-lite", input_type="document")
        query_result = client.embed([new_text], model="voyage-3-lite", input_type="query")
        query_vec = query_result.embeddings[0]

        best: dict[tuple[str, str], float] = {}
        for p, vec in zip(candidates, doc_result.embeddings):
            score = _cosine(query_vec, vec)
            key = (p.role, p.section)
            if score > best.get(key, -1.0):
                best[key] = score

        results = sorted(best.items(), key=lambda x: x[1], reverse=True)
        return [(role, section, score) for (role, section), score in results[:top_n]]
    except Exception:
        return []


ContentBlock = dict  # {"type": "text", "text": str, optional "cache_control": {...}}


def build_user_message(
    job_description: str,
    paragraphs: list[Paragraph],
    role: str | None = None,
    company: str | None = None,
    resume: str | None = None,
    template: str | None = None,
    notes: str | None = None,
    working_style: list[str] | None = None,
    values: list[str] | None = None,
    goals: list[str] | None = None,
    avoid: list[str] | None = None,
    angle_evidence: list[dict] | None = None,
    argument: str | None = None,
    company_values: str | None = None,
    required_coverage: list[str] | None = None,
    unaddressed_gaps: list[str] | None = None,
    voice_spec: str | None = None,  # contents of voice.md — positive writing voice description
) -> list[ContentBlock]:
    """Return structured content blocks with the library portion marked as cacheable.

    The library (resume + paragraphs + template + notes + working_style) is stable within
    a session — marked for prompt caching. The JD is per-application — not cached.
    """
    library_lines: list[str] = []
    if resume:
        library_lines.append("=== CANDIDATE RESUME (background context — company names, dates, tools, roles) ===\n")
        library_lines.append(resume.strip())
        library_lines.append("")
    if goals:
        library_lines.append("=== CANDIDATE GOALS (use for motivation/why-this-role prompts only) ===\n")
        library_lines.append(
            "What this person is looking for in their next role. "
            "Use when the application prompt is about why this role or what draws them to this company. "
            "Do not use as biographical framing.\n"
        )
        for item in goals:
            library_lines.append(f"- {item}")
        library_lines.append("")
    library_lines.append("=== YOUR PARAGRAPH LIBRARY ===\n")
    library_lines.append(
        "Paragraphs are labeled [VOICE] or [DRAFT].\n"
        "  [VOICE] — written or hand-approved by the candidate. This is the voice. "
        "Write in this rhythm, these sentence structures, this register.\n"
        "  [DRAFT] — machine-generated, not yet reviewed by the candidate. Use only "
        "for the facts and specifics they contain. Do NOT imitate their phrasing.\n"
        "\nWhen ARGUMENT EVIDENCE is present below, evidence sentences tell you WHAT "
        "to argue. [VOICE] paragraphs tell you HOW to sound.\n"
    )
    if role:
        library_lines.append(f"Target role: {role}\n")
    if company:
        library_lines.append(f"Company: {company}\n")

    for p in paragraphs:
        meta_str = ""
        if p.meta:
            meta_str = "  [" + ", ".join(f"{k}={v}" for k, v in p.meta.items()) + "]"
        role_label = f"{p.role} / " if p.role != role else ""
        frame_label = " [NARRATIVE FRAME]" if _is_perspective(p) else ""
        _section_lower = p.section.lower()
        _is_closer = (
            p.meta.get("tone") == "closer"
            or "why this role" in _section_lower
            or "closing" in _section_lower
        )
        closer_label = " [CLOSER ONLY]" if _is_closer else ""
        id_label = p.db_id if p.db_id is not None else p.index
        # layer 0 = approved, layer 2 = seed letter user wrote — genuine voice
        # layer 1 = LLM-generated refinements not yet reviewed — facts only, not voice
        voice_label = " [DRAFT — FACTS ONLY]" if p.layer == 1 else " [VOICE]"
        library_lines.append(f"[{id_label}] {role_label}{p.section}{meta_str}{frame_label}{closer_label}{voice_label}")
        library_lines.append(p.text)
        library_lines.append("")
    if template:
        library_lines.append("=== PREVIOUS LETTER (structural template) ===\n")
        library_lines.append(
            "A cover letter written for a similar role. Use it as a guide for argument "
            "structure, paragraph order, and which evidence proved most compelling. Adapt "
            "fully to the new job description — do not copy sentences unless they remain "
            "directly relevant to this role.\n"
        )
        library_lines.append(template.strip())
        library_lines.append("")
    if required_coverage:
        library_lines.append("=== REQUIRED COVERAGE — these topics must be addressed in the letter ===\n")
        library_lines.append(
            "The writer filled these JD gaps during Q&A. The letter must address each "
            "one. Draw from the library material — synthesize, weave, and integrate into "
            "the flow. Do not paste paragraphs in whole; do not omit these topics.\n"
        )
        for topic in required_coverage:
            library_lines.append(f"- {topic}")
        library_lines.append("")

    if unaddressed_gaps:
        library_lines.append("=== UNADDRESSED GAPS — the writer reviewed these and chose not to fill them ===\n")
        library_lines.append(
            "These gaps were shown to the writer during gap analysis. They chose not to "
            "provide new experience to cover them. You may acknowledge one or two briefly "
            "and honestly — a single sentence stating what the writer brings that is adjacent, "
            "or a direct honest statement about the gap. Do NOT apologize or over-explain. "
            "Do NOT invent experience. One sentence maximum per gap, woven into relevant "
            "paragraphs — not a separate paragraph of disclaimers.\n"
        )
        for topic in unaddressed_gaps:
            library_lines.append(f"- {topic}")
        library_lines.append("")

    # Block order: bio first (most stable — never changes), library second (stable per candidate).
    # Both are cached. The bio cache hits on every application; the library cache hits
    # whenever the paragraph library hasn't changed since last run.
    # JD-specific content (evidence, argument, notes, JD) is never cached.
    bio_lines: list[str] = []
    has_bio = working_style or values or avoid
    if has_bio:
        bio_lines.append("=== CANDIDATE BACKGROUND, VALUES, AND WORKING STYLE ===\n")
        bio_lines.append(
            "This is who this person is — their actual orientation, what draws them to certain work, "
            "what they value, how they think. Read this before writing the opener. "
            "It is the source of a genuine connection to this employer, not a biographical formula.\n"
        )
        all_bio = list(working_style or []) + list(values or [])
        if all_bio:
            for item in all_bio:
                bio_lines.append(f"- {item}")
            bio_lines.append("")
        if avoid:
            bio_lines.append(
                "Constraints — each reveals a real value. Infer the positive. Do NOT quote as negatives:"
            )
            for item in avoid:
                bio_lines.append(f"- {item}")
            bio_lines.append("")

    if voice_spec:
        bio_lines.append("=== WRITING VOICE ===\n")
        bio_lines.append(voice_spec.strip())
        bio_lines.append("")

    blocks: list[dict] = []
    if bio_lines:
        blocks.append({
            "type": "text",
            "text": "\n".join(bio_lines),
            "cache_control": {"type": "ephemeral"},
        })
    blocks.append({
        "type": "text",
        "text": "\n".join(library_lines),
        "cache_control": {"type": "ephemeral"},
    })

    if notes:
        blocks.append({
            "type": "text",
            "text": (
                "=== APPLICATION NOTES ===\n\n"
                "The candidate's own words. Use the opener-relevant observation here as "
                "the first sentence of the opener. Use the rest as tone signals.\n\n"
                + notes.strip()
            ),
        })

    # Argument target + evidence — JD-specific, NOT cached.
    if angle_evidence:
        if argument:
            blocks.append({
                "type": "text",
                "text": (
                    "=== ARGUMENT TARGET — GOVERNING CONSTRAINT ===\n\n"
                    "Every body paragraph must directly serve this argument. "
                    "If a paragraph cannot be traced back to this argument, cut it.\n\n"
                    + argument
                ),
            })

        # Detect format: new flat list (dicts with "argument_score") vs legacy angle blocks
        is_flat = angle_evidence and "argument_score" in angle_evidence[0]

        if is_flat:
            ev_lines = [
                "=== ARGUMENT EVIDENCE ===",
                "",
                f"These {len(angle_evidence)} sentences were selected because they best prove the argument above.",
                "They come from different experiences — draw on all of them.",
                "Write 3-4 body paragraphs that SYNTHESIZE across multiple experiences.",
                "Do not write one paragraph per evidence sentence.",
                "Every factual claim in the letter must trace to one of these sentences or its source paragraph.",
                "",
            ]
            for i, entry in enumerate(angle_evidence, 1):
                source_label = f"{entry['role']} / {entry['section']}"
                angle_tag = f"  [{entry['angle']}]" if entry.get("angle") else ""
                ev_lines.append(f"[{i}] {source_label}{angle_tag}")
                ev_lines.append(f'"{entry["text"]}"')
                if entry.get("context_after"):
                    ev_lines.append(f'  → "{entry["context_after"]}"')
                ev_lines.append(f"SOURCE: {entry['source_paragraph'][:250]}{'...' if len(entry['source_paragraph']) > 250 else ''}")
                ev_lines.append("")
        else:
            # Legacy angle-block format (fallback — build_angle_evidence path)
            required_angles = [b["angle"] for b in angle_evidence if b.get("required")]
            supporting_angles = [b["angle"] for b in angle_evidence if not b.get("required")]
            ev_lines = [
                "=== ARGUMENT EVIDENCE ===",
                "",
                f"  REQUIRED (must appear): {', '.join(required_angles) or 'none'}",
                f"  SUPPORTING: {', '.join(supporting_angles) or 'none'}",
                "",
                "Write 3-5 body paragraphs SYNTHESIZING ACROSS MULTIPLE EXPERIENCES.",
                "Do not write one paragraph per angle.",
                "",
            ]
            for block in angle_evidence:
                ev_lines.append(f"── {block['angle'].upper()} ──")
                ev_lines.append("")
                for entry in block["sentences"]:
                    source_label = f"{entry['role']} / {entry['section']}"
                    if entry.get("claim"):
                        ev_lines.append(f"CLAIM: {entry['claim']}")
                    ev_lines.append(f'EVIDENCE: "{entry["text"]}"')
                    ev_lines.append(f"SOURCE ({source_label}):")
                    ev_lines.append(entry["source_paragraph"][:250])
                    ev_lines.append("")

        blocks.append({
            "type": "text",
            "text": "\n".join(ev_lines),
        })

    jd_block = "=== JOB DESCRIPTION ===\n" + job_description.strip()
    if company_values:
        jd_block += (
            "\n\n=== COMPANY VALUES / MISSION ===\n"
            + company_values.strip()
            + "\n\nNote: use these values to frame why this candidate is a good fit — "
            "do not echo them back as assertions or summarise them. Show alignment through "
            "what the candidate has actually done."
        )
    blocks.append({"type": "text", "text": jd_block})
    return blocks


def build_user_message_stage2(
    job_description: str,
    selected_paragraphs: list[Paragraph],
    role: str | None = None,
    company: str | None = None,
    resume: str | None = None,
    notes: str | None = None,
    working_style: list[str] | None = None,
    values: list[str] | None = None,
    argument: str | None = None,
    company_values: str | None = None,
    required_coverage: list[str] | None = None,
    unaddressed_gaps: list[str] | None = None,
) -> list[ContentBlock]:
    """Stage 2 user message: only the selected paragraphs, no evidence block.

    The model receives a small, committed set of source paragraphs and assembles
    the letter FROM them rather than synthesizing across a large context.
    """
    library_lines: list[str] = []
    if resume:
        library_lines.append("=== CANDIDATE RESUME (background context — company names, dates, tools, roles) ===\n")
        library_lines.append(resume.strip())
        library_lines.append("")

    library_lines.append("=== SELECTED PARAGRAPHS ===\n")
    library_lines.append(
        "These paragraphs were selected to make the argument. "
        "Write FROM them. Key phrases must appear verbatim or near-verbatim.\n"
    )
    if role:
        library_lines.append(f"Target role: {role}\n")
    if company:
        library_lines.append(f"Company: {company}\n")

    for p in selected_paragraphs:
        meta_str = ""
        if p.meta:
            meta_str = "  [" + ", ".join(f"{k}={v}" for k, v in p.meta.items()) + "]"
        role_label = f"{p.role} / " if p.role != role else ""
        frame_label = " [NARRATIVE FRAME]" if _is_perspective(p) else ""
        _section_lower = p.section.lower()
        _is_closer = (
            p.meta.get("tone") == "closer"
            or "why this role" in _section_lower
            or "closing" in _section_lower
        )
        closer_label = " [CLOSER ONLY]" if _is_closer else ""
        id_label = p.db_id if p.db_id is not None else p.index
        library_lines.append(f"[{id_label}] {role_label}{p.section}{meta_str}{frame_label}{closer_label}")
        library_lines.append(p.text)
        library_lines.append("")

    if required_coverage:
        library_lines.append("=== REQUIRED COVERAGE — these topics must be addressed in the letter ===\n")
        for topic in required_coverage:
            library_lines.append(f"- {topic}")
        library_lines.append("")

    if unaddressed_gaps:
        library_lines.append("=== UNADDRESSED GAPS — the writer reviewed these and chose not to fill them ===\n")
        library_lines.append(
            "You may acknowledge one or two briefly — a single sentence only, woven in, no apology.\n"
        )
        for topic in unaddressed_gaps:
            library_lines.append(f"- {topic}")
        library_lines.append("")

    blocks: list[dict] = [
        {
            "type": "text",
            "text": "\n".join(library_lines),
            "cache_control": {"type": "ephemeral"},
        },
    ]

    bio_lines: list[str] = []
    has_bio = working_style or values
    if has_bio:
        bio_lines.append("=== CANDIDATE BACKGROUND, VALUES, AND WORKING STYLE ===\n")
        bio_lines.append(
            "Read before writing the opener. Source of the genuine connection to this employer.\n"
        )
        for item in list(working_style or []) + list(values or []):
            bio_lines.append(f"- {item}")
        bio_lines.append("")
        blocks.append({
            "type": "text",
            "text": "\n".join(bio_lines),
            "cache_control": {"type": "ephemeral"},
        })

    if notes:
        blocks.append({
            "type": "text",
            "text": (
                "=== APPLICATION NOTES ===\n\n"
                "The candidate's own words. Use the opener-relevant observation here as "
                "the first sentence of the opener. Use the rest as tone signals.\n\n"
                + notes.strip()
            ),
        })

    if argument:
        blocks.append({
            "type": "text",
            "text": (
                "=== ARGUMENT TARGET — GOVERNING CONSTRAINT ===\n\n"
                "Every body paragraph must directly serve this argument. "
                "If a paragraph cannot be traced back to this argument, cut it.\n\n"
                + argument
            ),
        })

    jd_block = "=== JOB DESCRIPTION ===\n" + job_description.strip()
    if company_values:
        jd_block += (
            "\n\n=== COMPANY VALUES / MISSION ===\n"
            + company_values.strip()
            + "\n\nNote: show alignment through what the candidate has actually done, "
            "not by echoing values back."
        )
    blocks.append({"type": "text", "text": jd_block})
    return blocks
