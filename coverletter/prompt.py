import re
from collections import Counter
from collections.abc import Sequence

from coverletter.parser import Paragraph

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
- Leads with a concrete claim about who this person is and what their work points toward
- Is tailored to this specific role and company — the claim should set up the body argument
- Uses the candidate's actual voice and phrasing patterns from the library openers
- Is 3-5 sentences
- Never opens with "I am excited to apply" or restates the job title

THE CLOSER IS ALWAYS WRITTEN FRESH:
Do not copy a closer paragraph from the source library. Write a fresh closer that:
- Is warm, specific to this company, and forward-looking
- Thanks the reader genuinely
- Expresses specific interest in speaking further about this role at this company
- Uses the actual company name
- Is 2-3 sentences
- Never uses "I am available at your convenience"

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

═══ ASSEMBLY RULES ═══
1. Write a fresh opener paragraph in the candidate's voice (see opener rules above).
2. SELECT 2-3 body paragraphs from the source library that best match the job description.
   Prefer strength=high. Each must open with a concrete claim and close by landing its point.
3. If a "why this role" paragraph exists in the source, include it as the final body paragraph.
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
- OPENER (synthesized fresh): Concrete claim about who this person is and what their work
  points toward. Tailored to the specific role and company. Sets up the body argument.
  3-5 sentences. Voice matches the library opener paragraphs.
- BODY (2-3 paragraphs, assembled from source): Each proves one specific part of the
  argument with evidence. Each opens with a concrete claim. Each closes by landing its
  point — not trailing off into a list or a vague summary. Every sentence from source.
- WHY THIS ROLE (if available in source): Concrete connection between candidate's specific
  experience and this specific organization. Not generic enthusiasm.
- CLOSER (synthesized fresh): Warm, specific to this company, forward-looking. 2-3 sentences.
  Thanks the reader. Expresses genuine interest in speaking further about this role.
  Uses the actual company name. Never "I am available at your convenience."

═══ BEFORE RETURNING, SCAN FOR ═══
1. Any em-dash (—) anywhere — replace with comma, semicolon, or period.
2. Any sentence starting with "That" — rewrite it.
3. Any paragraph ending with a list — cut the list and land the point instead.
4. Any banned word or fake-contrast structure — remove it.
5. Any paragraph that opens with a generic topic statement — replace with a concrete claim.
6. Any sentence whose content is not traceable to the source material or the JD — cut it.

Output only the letter. No preamble, no verdict, no commentary.
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

    # Always include structural paragraphs
    pinned = [p for p in candidates if p.meta.get("tone") in ("opener", "closer")]
    pinned_set = {p.index for p in pinned}
    remaining = [p for p in candidates if p.index not in pinned_set]

    jd_counts = _tokenize(job_description)
    score_map = {}
    for p in remaining:
        overlap = _score_tokens(p, jd_counts)
        boost = 1.5 if p.meta.get("strength") == "high" else 1.0
        score_map[p.index] = overlap * boost

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

        # Always include structural paragraphs
        pinned = [p for p in candidates if p.meta.get("tone") in ("opener", "closer")]
        pinned_set = {p.index for p in pinned}
        embed_map = {p.index: vec for p, vec in zip(candidates, doc_result.embeddings)}

        remaining = [p for p in candidates if p.index not in pinned_set]
        score_map = {}
        for p in remaining:
            score = _cosine(embed_map[p.index], jd_vec)
            boost = 1.2 if p.meta.get("strength") == "high" else 1.0
            score_map[p.index] = score * boost

        budget = max(0, top_n - len(pinned))
        selected = _select_by_experience(remaining, score_map, budget)
        return pinned + selected
    except Exception:
        return prefilter(candidates, job_description, top_n)


ContentBlock = dict  # {"type": "text", "text": str, optional "cache_control": {...}}


def build_user_message(
    job_description: str,
    paragraphs: list[Paragraph],
    role: str | None = None,
    company: str | None = None,
    resume: str | None = None,
    template: str | None = None,
    notes: str | None = None,
) -> list[ContentBlock]:
    """Return structured content blocks with the library portion marked as cacheable.

    The library (resume + paragraphs + template + notes) is stable within a session —
    marked for prompt caching. The JD is per-application — not cached.
    """
    library_lines: list[str] = []
    if resume:
        library_lines.append("=== CANDIDATE RESUME (background context — company names, dates, tools, roles) ===\n")
        library_lines.append(resume.strip())
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
        library_lines.append(f"[{p.index}] {role_label}{p.section}{meta_str}")
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

    return [
        {
            "type": "text",
            "text": "\n".join(library_lines),
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": "=== JOB DESCRIPTION ===\n" + job_description.strip(),
        },
    ]
