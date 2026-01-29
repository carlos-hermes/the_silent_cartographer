"""Extract actionable tasks from pink highlights using LLM."""

import json
from typing import Optional

from pydantic import BaseModel, Field

from tsc.parsers.models import Highlight, BookMetadata
from tsc.integrations.llm_client import query_llm


class ExtractedAction(BaseModel):
    """An actionable task extracted from highlights."""

    title: str = Field(..., description="Short task title for Asana")
    description: str = Field(..., description="Detailed task description")
    source_highlight: int = Field(..., description="Index of the primary supporting highlight")
    priority: str = Field(..., description="Priority level: high, medium, low")
    category: str = Field(..., description="Category: work, personal, family, faith")


ACTION_EXTRACTION_PROMPT = """You are analyzing book highlights to extract actionable tasks.

Book: "{title}" by {author}

User Profile Context:
{profile}

Highlights marked for action (pink):
{highlights}

Task: Identify the TOP 5 most impactful, actionable tasks from these highlights. Prioritize actions that:
1. Are specific and achievable (not vague aspirations)
2. Align with the user's current goals and responsibilities
3. Have clear outcomes that can be verified
4. Can realistically be acted upon within 1-4 weeks

For each action, provide:
- title: A clear, action-oriented task title (start with verb, max 60 chars)
- description: Detailed description including context and suggested approach
- source_highlight: Index (0-based) of the highlight that inspired this action
- priority: "high", "medium", or "low" based on potential impact and urgency
- category: "work" (Hermes AI/Serranova), "personal" (growth/hobbies), "family", or "faith"

Return EXACTLY 5 actions (or fewer if highlights don't support meaningful actions).

Respond with valid JSON in this exact format:
{{
    "actions": [
        {{
            "title": "Action Title Starting with Verb",
            "description": "Detailed description...",
            "source_highlight": 0,
            "priority": "high",
            "category": "work"
        }}
    ]
}}
"""


async def extract_actions(
    highlights: list[Highlight],
    metadata: BookMetadata,
    profile_content: str,
    max_actions: int = 5,
) -> list[ExtractedAction]:
    """Extract actionable tasks from pink highlights.

    Args:
        highlights: List of pink (action) highlights.
        metadata: Book metadata for context.
        profile_content: User profile content for relevance.
        max_actions: Maximum number of actions to extract.

    Returns:
        List of extracted actions, sorted by priority.
    """
    if not highlights:
        return []

    # Format highlights for the prompt
    highlights_text = "\n".join(
        f"[{i}] {h.text}"
        + (f" (Chapter: {h.chapter})" if h.chapter else "")
        for i, h in enumerate(highlights)
    )

    prompt = ACTION_EXTRACTION_PROMPT.format(
        title=metadata.title,
        author=metadata.author,
        profile=profile_content,
        highlights=highlights_text,
    )

    response_text = await query_llm(prompt, max_tokens=2048)

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
    actions = [ExtractedAction(**a) for a in data["actions"][:max_actions]]

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda a: priority_order.get(a.priority, 1))

    return actions
