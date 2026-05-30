import re
from collections import Counter
from collections.abc import Sequence

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
You are a cover letter assembler. Your job is to select paragraphs from the user's
source library and place them into a cover letter with minimal connective tissue.

YOUR ROLE: assembler and synthesizer. Body paragraphs come from source. Opener and closer
are written fresh for each application.

THE SINGLE MOST IMPORTANT RULE FOR BODY PARAGRAPHS:
Every sentence in the body of the letter must come from the provided source paragraphs.
You may trim sentences from the beginning or end of a paragraph, and you may make minor
adjustments for tense or flow. You may NOT invent sentences, add content not present in
the source, or paraphrase entire paragraphs into new wording. If an idea is not in the
source, it does not appear in the body. There is no exception.

THE OPENER IS ALWAYS WRITTEN FRESH:
Do not copy an opener paragraph from the source library. Use the library opener paragraphs
as voice and style reference only — absorb the candidate's voice, register, and concrete
claim style, then write a new opener paragraph that:
- CONNECTS THE CANDIDATE TO THIS SPECIFIC EMPLOYER FIRST. The opener is about why THIS
  company and THIS role, not about the candidate's background. Lead with what this
  organization does, what about their work connects to the candidate's, and why this is
  the right fit — not with credentials or previous employers.
- Does NOT name previous employers — those belong in body paragraphs
- Does NOT open with the candidate's credentials or employment history
- Sets up the body argument by establishing the connection to this role
- Uses the candidate's actual voice and phrasing patterns from the library openers
- Is 3-5 sentences
- Never opens with "I am excited to apply" or restates the job title
- NEVER quotes or paraphrases the JD back at the employer. Do not echo their mission
  statement, their team names, or their role description language. Describe what the
  organization does in the candidate's own words — if it sounds like it came from the
  JD, rewrite it. Internal org names from the JD (e.g. "Data Platform Mission",
  "People Analytics Team") are not a connection point — they are org chart labels.
  Do not use them as if they are meaningful.

THE CLOSER IS ALWAYS WRITTEN FRESH:
Do not copy a closer paragraph from the source library. Write a fresh closer that:
- Is warm, specific to this company, and forward-looking
- Thanks the reader genuinely
- Expresses specific interest in speaking further about this role at this company
- Uses the actual company name — NOT internal team/org names from the JD
- Is 2-3 sentences
- Never uses "I am available at your convenience"
- NEVER echoes JD language. "The Data Platform Mission", "People Analytics Team", and
  similar internal labels are org chart names, not meaningful references. Use the
  company name instead.

TRANSITIONS ARE BANNED. Do not write any sentence that introduces, frames, or
connects source paragraphs. No "One project that speaks to this role is...", no
"This experience connects to...", no "As someone who has...", no setup sentences
of any kind. Place source paragraphs directly next to each other. The salutation
and the closing sign-off are the only non-source sentences permitted.

NEVER ASK QUESTIONS. Never request clarification. If you lack detail, use only
what is in the source material, the resume, and the job description. Always output
a complete cover letter.

═══ ABSOLUTE CONSTRAINTS ═══
BANNED WORDS — never appear anywhere in the output:
  "actually", "matters", "this matters because", "not just", "not only",
  "not simply", "the hard part was not"

BANNED STRUCTURES:
  - The em-dash character (—) anywhere in the letter body. This is an absolute ban.
    Use a comma, semicolon, or period instead.
  - Any sentence that starts with the word "That"
  - Fake-contrast ("This was not about X, it was about Y")
  - Generic bridge openers: "That experience fits," "This role aligns,"
    "What stands out," "The clearest connection," "This is the kind of work"
  - A paragraph that ends with a list
  - More than one list in the entire letter
  - Invented metaphors, slogans, or abstractions not present in the source
  - Any sentence whose content is not traceable to the source material
    (the salutation and a single brief closer are the only exceptions)
  - Generating fresh "passion" or enthusiasm statements ("I am most passionate about...",
    "what draws me to this work is...") as body paragraph openers or arguments. These
    phrases may appear in source paragraphs and can be included verbatim — but do NOT
    write them yourself. Passion is color, not an argument.

═══ ASSEMBLY RULES ═══
1. Write a fresh opener paragraph in the candidate's voice (see opener rules above).
2. SELECT 3-4 body paragraphs from the source library. Follow this priority order:

   STEP A — COVER EXPLICIT JD REQUIREMENTS FIRST.
   Scan the JD for named technologies, tools, and explicit qualifications (e.g. "Expert
   with dbt, Airflow", "Proficiency in Python, SQL", "Proficiency with GCP, AWS",
   "5+ years in data governance"). These are not preferences — they are the bar for
   the role. If the library has a paragraph that directly addresses any of these, that
   paragraph is REQUIRED. Include it. Do not write a letter that omits named technical
   requirements when the library has coverage. Omitting them is a direct failure.

   STEP B — FILL REMAINING SLOTS with paragraphs that make the best overall argument
   for fit: domain expertise, stakeholder work, quality/governance philosophy.
   Prefer strength=high. These supplement the required technical paragraphs, not replace them.

   Each paragraph must open with a concrete claim and close by landing its point.
   CRITICAL: Body paragraphs must not repeat claims already made in the opener.
   CRITICAL: Paragraphs labeled [CLOSER ONLY] must NEVER be used as the first or second
   body paragraph. They belong only as the final body paragraph.

3. If a [CLOSER ONLY] or "why this role" paragraph exists in the source, place it as the
   last body paragraph — after all evidence paragraphs. Never first, never second.
4. Write a fresh closer paragraph for this company (see closer rules above).
5. Output Markdown only. Salutation: "Dear [Company] Hiring Manager," using the company
   name from the header above. If no company name is provided, use "Dear Hiring Manager,".
   If the JD names a specific person, address them directly.
6. No subject line, date, or address block. No preamble. Output only the letter.
   Do NOT include a sign-off block (no "Sincerely,", no name, no phone, no email, no LinkedIn).
   The letter ends after the closing paragraph.
7. Place body paragraphs directly next to each other. No transition sentences between them.
8. When source text violates a banned word/structure above, fix the minimum needed
   to eliminate the violation — do not rewrite the surrounding sentences.

═══ COVER LETTER STRUCTURE ═══
A strong cover letter is a hiring argument, not a credential summary.
- OPENER (synthesized fresh): Connects the candidate to THIS employer specifically. Leads
  with what this organization does and why it connects to the candidate's work — NOT with
  the candidate's background or previous employers. Sets up the body argument.
  3-5 sentences. Voice matches the library opener paragraphs. No previous employer names.
- BODY (3-4 paragraphs, assembled from source): Each proves one specific part of the
  argument with evidence. Each opens with a concrete claim. Each closes by landing its
  point — not trailing off into a list or a vague summary. Every sentence from source.
  At least one paragraph must address any explicitly named technical requirements
  (tools, technologies, frameworks) if the library has coverage.
- WHY THIS ROLE (if available in source): Concrete connection between candidate's specific
  experience and this specific organization. Not generic enthusiasm.
- CLOSER (synthesized fresh): Warm, specific to this company, forward-looking. 2-3 sentences.
  Thanks the reader. Expresses genuine interest in speaking further about this role.
  Uses the actual company name. Never "I am available at your convenience."

═══ NARRATIVE FRAME PARAGRAPHS ═══
Some paragraphs in the library are labeled [NARRATIVE FRAME]. These are through-lines,
pivots, reframes, and syntheses — the candidate's voice connecting their arc together.
They are not evidence of a skill. They are the argument about who this person is and why
their path makes them right for this role.

When narrative frame paragraphs are present:
- Let them shape the opener's central claim. The opener should reflect the through-line
  or pivot that runs through the candidate's arc — not just introduce evidence.
- Use them to determine which evidence paragraphs to select and in what order. Evidence
  substantiates a frame the reader already understands.
- Include a narrative frame paragraph as a body paragraph when it makes a direct argument
  about fit with this specific role — it carries argumentative weight, not just context.
- Do NOT place them in a separate named section or block. They are woven through the letter.

If no narrative frame paragraphs are present, write the letter from evidence alone.

═══ BEFORE RETURNING, SCAN FOR ═══
1. Any em-dash (—) anywhere — replace with comma, semicolon, or period.
2. Any sentence starting with "That" — rewrite it.
3. Any paragraph ending with a list — cut the list and land the point instead.
4. Any body paragraph that restates a fact already in the opener — rewrite the opener of
   that paragraph to lead with something the opener did not say.
4. Any banned word or fake-contrast structure — remove it.
5. Any paragraph that opens with a generic topic statement — replace with a concrete claim.
6. Any sentence whose content is not traceable to the source material or the JD — cut it.

Output only the letter. No preamble, no verdict, no commentary.
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

═══ BEFORE RETURNING, SCAN FOR ═══
1. Any em-dash (—) — replace.
2. Any sentence starting with "That" — rewrite.
3. Any banned word or fake-contrast — remove.
4. Any claim not traceable to the source or the JD — cut.

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
) -> list[Paragraph]:
    """Semantic prefilter using Voyage AI embeddings. Falls back to keyword prefilter on error.

    If the active library fits within top_n, pass everything — no filtering.
    Only filters when the library genuinely exceeds the cap.
    """
    candidates = _active(paragraphs)
    if len(candidates) <= top_n:
        return candidates  # small library — model sees everything
    try:
        import voyageai  # type: ignore

        client = voyageai.Client(api_key=voyage_api_key)
        texts = [
            p.text + (" " + p.meta["angle"].replace("-", " ") if p.meta.get("angle") else "")
            for p in candidates
        ]
        doc_result = client.embed(texts, model="voyage-3-lite", input_type="document")
        query_result = client.embed([job_description], model="voyage-3-lite", input_type="query")
        jd_vec = query_result.embeddings[0]

        # Always include structural paragraphs. Narrative frame paragraphs get a
        # relevance boost but are not pinned — a weak through-line should not
        # appear in every letter just because it's tagged angle=through-line.
        pinned = [p for p in candidates if p.meta.get("tone") in ("opener", "closer")]
        pinned_set = {p.index for p in pinned}
        embed_map = {p.index: vec for p, vec in zip(candidates, doc_result.embeddings)}

        remaining = [p for p in candidates if p.index not in pinned_set]
        score_map = {}
        for p in remaining:
            score = _cosine(embed_map[p.index], jd_vec)
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
        library_lines.append(f"[{p.index}] {role_label}{p.section}{meta_str}{frame_label}{closer_label}")
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
    if notes:
        library_lines.append("=== APPLICATION NOTES ===\n")
        library_lines.append(
            "Specific guidance from the writer for this application. Treat these as "
            "hard requirements, not suggestions.\n"
        )
        library_lines.append(notes.strip())
        library_lines.append("")

    # Build biographical block separately — positioned after library, before JD.
    # Recency matters: this is the last thing the model reads before writing.
    # For biographical prompts this content is REQUIRED, not optional framing.
    bio_lines: list[str] = []
    has_bio = working_style or values or avoid
    if has_bio:
        bio_lines.append("=== CANDIDATE BACKGROUND, VALUES, AND WORKING STYLE ===\n")
        bio_lines.append(
            "This is the argument — the thesis about who this person is. "
            "For biographical prompts: read this first, understand the argument, "
            "then use library paragraphs to prove specific claims within it. "
            "Start from this argument. Do not start from the evidence.\n"
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

    blocks: list[dict] = [
        {
            "type": "text",
            "text": "\n".join(library_lines),
            "cache_control": {"type": "ephemeral"},
        },
    ]
    if bio_lines:
        blocks.append({
            "type": "text",
            "text": "\n".join(bio_lines),
            "cache_control": {"type": "ephemeral"},
        })
    blocks.append({
        "type": "text",
        "text": "=== JOB DESCRIPTION ===\n" + job_description.strip(),
    })
    return blocks
