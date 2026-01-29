"""Fill concept note template sections using LLM."""

import json
from typing import Optional

from pydantic import BaseModel, Field

from tsc.parsers.models import Highlight, BookMetadata
from tsc.processors.concept_extractor import ExtractedConcept
from tsc.integrations.llm_client import query_llm


class FilledTemplate(BaseModel):
    """A fully filled concept template."""

    trivium_grammar: str = Field(..., description="Core idea in own words")
    trivium_logic: str = Field(..., description="How it works (cause-effect)")
    trivium_rhetoric: str = Field(..., description="How to explain/persuade")

    dialectic_thesis: str = Field(..., description="Core idea (from grammar)")
    dialectic_antithesis: str = Field(..., description="Strongest opposing view")
    dialectic_synthesis: str = Field(..., description="New perspective from tension")

    polarity_tension: str = Field(..., description="Ongoing tension this sits inside")
    polarity_balance: str = Field(..., description="How to balance both sides")

    socratic_falsification: str = Field(..., description="What would prove this wrong")

    scientific_hypothesis: str = Field(..., description="Expected result if applied")
    scientific_experiment: str = Field(..., description="Small way to test")
    scientific_measure: str = Field(..., description="How to know if it worked")
    scientific_learn: str = Field(..., description="What to refine")

    kairos_relevant: str = Field(..., description="When most relevant")
    kairos_irrelevant: str = Field(..., description="When it loses relevance")

    connections_supportive: list[str] = Field(default_factory=list, description="Related supportive concepts")
    connections_contrasting: list[str] = Field(default_factory=list, description="Contrasting ideas")
    connections_sources: str = Field(..., description="Key sources with quotes")

    applications_work: str = Field(..., description="Application to Hermes AI/work")
    applications_family: str = Field(..., description="Application to family/homestead")
    applications_personal: str = Field(..., description="Application to personal growth/faith")

    open_questions: list[str] = Field(default_factory=list, description="Questions for further exploration")


TEMPLATE_FILL_PROMPT = """You are a philosophical thinker helping to deeply analyze a concept from a book.

Concept: {concept_name}
Description: {concept_description}

Source: "{book_title}" by {book_author}

Supporting Highlights:
{supporting_highlights}

User Profile (for personalizing applications):
{profile}

Existing Notes in Knowledge Base (for connections):
{existing_notes}

Fill out each section of this concept analysis framework thoughtfully and concisely.
Be specific and practical. Use the user's profile to make applications relevant.
For connections, only link to notes that actually exist in the provided list.

Respond with valid JSON matching this structure:
{{
    "trivium_grammar": "Core idea explained simply, as if to a child",
    "trivium_logic": "Cause-effect mechanism or principle behind it",
    "trivium_rhetoric": "Analogy, metaphor, or pitch line for explaining to others",

    "dialectic_thesis": "The core idea restated",
    "dialectic_antithesis": "Strongest opposing view or limitation",
    "dialectic_synthesis": "New perspective from holding both together",

    "polarity_tension": "The ongoing tension this idea sits inside (e.g., freedom vs discipline)",
    "polarity_balance": "How both sides can be balanced rather than solved",

    "socratic_falsification": "What would prove this idea wrong or incomplete",

    "scientific_hypothesis": "If I apply this, what result do I expect?",
    "scientific_experiment": "One small way to test it",
    "scientific_measure": "How to know if it worked",
    "scientific_learn": "What to refine or change based on results",

    "kairos_relevant": "When and under what conditions this is most relevant",
    "kairos_irrelevant": "Conditions under which it loses relevance",

    "connections_supportive": ["Existing Note 1", "Existing Note 2"],
    "connections_contrasting": ["Contrasting Note"],
    "connections_sources": "Book citation with strongest supporting quote",

    "applications_work": "Specific application to Hermes AI or Serranova",
    "applications_family": "Application to family, marriage, or parenting",
    "applications_personal": "Application to personal growth, faith, or development",

    "open_questions": ["Question 1 for further exploration", "Question 2"]
}}

Be concise but insightful. Each field should be 1-3 sentences max.
"""


async def fill_template(
    concept: ExtractedConcept,
    highlights: list[Highlight],
    metadata: BookMetadata,
    profile_content: str,
    existing_notes: list[str],
) -> FilledTemplate:
    """Fill all template sections for a concept using LLM.

    Args:
        concept: The extracted concept to analyze.
        highlights: All yellow highlights from the book.
        metadata: Book metadata for citation.
        profile_content: User profile for personalizing applications.
        existing_notes: List of existing note titles for connections.

    Returns:
        FilledTemplate with all sections populated.
    """
    # Get supporting highlights
    supporting = [
        highlights[i] for i in concept.supporting_highlights
        if i < len(highlights)
    ]
    supporting_text = "\n".join(
        f"- \"{h.text}\" ({h.location_str()})"
        for h in supporting
    )

    # Format existing notes
    notes_text = "\n".join(f"- [[{note}]]" for note in existing_notes[:50]) if existing_notes else "No existing notes yet."

    prompt = TEMPLATE_FILL_PROMPT.format(
        concept_name=concept.name,
        concept_description=concept.description,
        book_title=metadata.title,
        book_author=metadata.author,
        supporting_highlights=supporting_text,
        profile=profile_content,
        existing_notes=notes_text,
    )

    response_text = await query_llm(prompt, max_tokens=4096)

    # Extract JSON from response
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()

    data = json.loads(response_text)
    return FilledTemplate(**data)
