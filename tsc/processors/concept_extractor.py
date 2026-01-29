"""Extract key concepts from yellow highlights using LLM."""

import json
from typing import Optional

from pydantic import BaseModel, Field

from tsc.parsers.models import Highlight, BookMetadata
from tsc.integrations.llm_client import query_llm


class ExtractedConcept(BaseModel):
    """A concept extracted from highlights."""

    name: str = Field(..., description="Short, memorable concept name")
    description: str = Field(..., description="One-sentence summary of the concept")
    supporting_highlights: list[int] = Field(
        ...,
        description="Indices of highlights that support this concept",
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How relevant this concept is to the user's profile",
    )


CONCEPT_EXTRACTION_PROMPT = """You are analyzing book highlights to extract the most important concepts.

Book: "{title}" by {author}

User Profile Context:
{profile}

Highlights to analyze:
{highlights}

Task: Identify the TOP 10 most important concepts from these highlights. Prioritize concepts that:
1. Are most relevant to the user's profile and goals
2. Represent unique, actionable ideas from the book
3. Have strong supporting evidence in the highlights
4. Would be valuable as standalone knowledge notes

For each concept, provide:
- name: A short, memorable title (2-5 words)
- description: A one-sentence summary
- supporting_highlights: List of highlight indices (0-based) that support this concept
- relevance_score: 0.0-1.0 indicating relevance to user's profile

Return EXACTLY 10 concepts (or fewer if the highlights don't support that many).

Respond with valid JSON in this exact format:
{{
    "concepts": [
        {{
            "name": "Concept Name",
            "description": "One sentence description",
            "supporting_highlights": [0, 2, 5],
            "relevance_score": 0.85
        }}
    ]
}}
"""


async def extract_concepts(
    highlights: list[Highlight],
    metadata: BookMetadata,
    profile_content: str,
    max_concepts: int = 10,
) -> list[ExtractedConcept]:
    """Extract key concepts from yellow highlights.

    Args:
        highlights: List of yellow (key concept) highlights.
        metadata: Book metadata for context.
        profile_content: User profile content for relevance scoring.
        max_concepts: Maximum number of concepts to extract.

    Returns:
        List of extracted concepts, sorted by relevance.
    """
    if not highlights:
        return []

    # Format highlights for the prompt
    highlights_text = "\n".join(
        f"[{i}] {h.text}"
        + (f" (Chapter: {h.chapter})" if h.chapter else "")
        for i, h in enumerate(highlights)
    )

    prompt = CONCEPT_EXTRACTION_PROMPT.format(
        title=metadata.title,
        author=metadata.author,
        profile=profile_content,
        highlights=highlights_text,
    )

    response_text = await query_llm(prompt, max_tokens=4096)

    # Extract JSON from response (handle markdown code blocks)
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()

    data = json.loads(response_text)
    concepts = [ExtractedConcept(**c) for c in data["concepts"][:max_concepts]]

    # Sort by relevance score
    concepts.sort(key=lambda c: c.relevance_score, reverse=True)

    return concepts
