"""Generate book notes with all sections."""

from datetime import date
from pathlib import Path
from typing import Optional

from tsc.parsers.models import Highlight, BookMetadata, ParsedBook
from tsc.processors.concept_extractor import ExtractedConcept
from tsc.processors.action_extractor import ExtractedAction


def _format_quote(highlight: Highlight) -> str:
    """Format a highlight as a blockquote."""
    location = highlight.location_str()
    return f'> "{highlight.text}"\n> — *{location}*'


def _format_concept_link(concept: ExtractedConcept) -> str:
    """Format concept as Obsidian link with relevance."""
    return f"- [[{concept.name}]] (relevance: {concept.relevance_score:.0%})"


def _format_action_item(
    action: ExtractedAction,
    asana_url: Optional[str] = None,
) -> str:
    """Format action as task with optional Asana link."""
    link_part = f" — [Asana]({asana_url})" if asana_url else ""
    return f"- [ ] {action.title}{link_part}"


def generate_book_note(
    book: ParsedBook,
    concepts: list[ExtractedConcept],
    actions: list[ExtractedAction],
    asana_urls: Optional[dict[str, str]] = None,
) -> str:
    """Generate complete book note.

    Args:
        book: Parsed book with all highlights.
        concepts: Extracted concepts (from yellow highlights).
        actions: Extracted actions (from pink highlights).
        asana_urls: Optional mapping of action titles to Asana task URLs.

    Returns:
        Complete markdown content for the book note.
    """
    today = date.today().isoformat()
    metadata = book.metadata
    counts = book.highlight_counts()
    asana_urls = asana_urls or {}

    # Build key concepts section
    concepts_section = ""
    if concepts:
        concepts_list = "\n".join(_format_concept_link(c) for c in concepts)
        concepts_section = f"""## Key Concepts

{concepts_list}
"""

    # Build action items section
    actions_section = ""
    if actions:
        actions_list = "\n".join(
            _format_action_item(a, asana_urls.get(a.title))
            for a in actions
        )
        actions_section = f"""## Action Items

{actions_list}
"""

    # Build beautiful quotes section
    quotes_section = ""
    if book.blue_highlights:
        quotes = "\n\n".join(_format_quote(h) for h in book.blue_highlights)
        quotes_section = f"""## Beautiful Quotes

{quotes}
"""

    # Build disagreements section
    disagreements_section = ""
    if book.orange_highlights:
        disagreements = "\n\n".join(
            _format_quote(h) + "\n\n*My thoughts:* [Add your response here]"
            for h in book.orange_highlights
        )
        disagreements_section = f"""## Disagreements

{disagreements}
"""

    # Build complete note
    content = f"""---
title: "{metadata.title}"
author: "{metadata.author}"
processed: {today}
source_file: "{metadata.source_file.name}"
highlights:
  yellow: {counts['yellow']}
  pink: {counts['pink']}
  blue: {counts['blue']}
  orange: {counts['orange']}
tags:
  - book
  - processed
---

# {metadata.title}

**Author:** {metadata.author}
**Processed:** {today}
**Highlights:** {sum(counts.values())} total ({counts['yellow']} concepts, {counts['pink']} actions, {counts['blue']} quotes, {counts['orange']} disagreements)

---

{concepts_section}
{actions_section}
{quotes_section}
{disagreements_section}
---

## Reading Notes

*Add any additional thoughts, connections, or reflections here.*
"""
    return content


def write_book_note(
    book: ParsedBook,
    concepts: list[ExtractedConcept],
    actions: list[ExtractedAction],
    output_dir: Path,
    asana_urls: Optional[dict[str, str]] = None,
) -> Path:
    """Write book note to file.

    Args:
        book: Parsed book with all highlights.
        concepts: Extracted concepts.
        actions: Extracted actions.
        output_dir: Directory to write the note to.
        asana_urls: Optional mapping of action titles to Asana task URLs.

    Returns:
        Path to the created file.
    """
    content = generate_book_note(book, concepts, actions, asana_urls)

    # Sanitize filename
    safe_title = "".join(
        c if c.isalnum() or c in " -_" else "_"
        for c in book.metadata.title
    ).strip()
    filename = f"{safe_title}.md"

    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")

    return output_path
