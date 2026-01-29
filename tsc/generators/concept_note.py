"""Generate concept notes from extracted concepts and filled templates."""

from datetime import date
from pathlib import Path
from typing import Optional

from tsc.parsers.models import BookMetadata, Highlight
from tsc.processors.concept_extractor import ExtractedConcept
from tsc.generators.template_filler import FilledTemplate


def _format_wikilinks(items: list[str]) -> str:
    """Format a list of items as Obsidian wikilinks."""
    return ", ".join(f"[[{item}]]" for item in items) if items else "None yet"


def _format_questions(questions: list[str]) -> str:
    """Format questions as a bulleted list."""
    return "\n".join(f"- {q}" for q in questions) if questions else "- None yet"


def _format_highlights(highlights: list[Highlight]) -> str:
    """Format supporting highlights as blockquotes."""
    if not highlights:
        return "> No highlights captured"

    formatted = []
    for h in highlights:
        location = h.location_str() if hasattr(h, 'location_str') else ""
        formatted.append(f"> \"{h.text}\"\n> — {location}")

    return "\n\n".join(formatted)


def generate_concept_note(
    concept: ExtractedConcept,
    filled: FilledTemplate,
    metadata: BookMetadata,
    supporting_highlights: Optional[list[Highlight]] = None,
) -> str:
    """Generate a complete concept note from template.

    Args:
        concept: The extracted concept.
        filled: The filled template sections.
        metadata: Source book metadata.
        supporting_highlights: Original highlights that support this concept.

    Returns:
        Complete markdown content for the concept note.
    """
    today = date.today().isoformat()
    highlights_section = _format_highlights(supporting_highlights or [])

    content = f"""---
title: "{concept.name}"
source: "[[{metadata.title}]]"
author: "{metadata.author}"
created: {today}
relevance: {concept.relevance_score:.2f}
tags:
  - concept
  - from-reading
---

# {concept.name}

> {concept.description}

---

## 📖 Original Highlights
*(The source passages that inspired this concept.)*

{highlights_section}

---

## 📚 Trivium (Grammar / Logic / Rhetoric)
*(Classical education model: understand → reason → explain.)*

- **Core Idea (Grammar):** {filled.trivium_grammar}
- **Logic:** {filled.trivium_logic}
- **Rhetoric:** {filled.trivium_rhetoric}

---

## 🗣 Dialectic (Thesis → Antithesis → Synthesis)
*(Progress comes from tension between opposing ideas.)*

- **Thesis:** {filled.dialectic_thesis}
- **Antithesis:** {filled.dialectic_antithesis}
- **Synthesis:** {filled.dialectic_synthesis}

---

## ⚖️ Polarity Thinking
*(Tensions that can't be "solved" but must be balanced.)*

- **Tension:** {filled.polarity_tension}
- **Balance:** {filled.polarity_balance}

---

## ❓ Socratic Method
*(Truth-seeking by questioning assumptions.)*

- **What would prove this wrong?** {filled.socratic_falsification}

---

## 🧪 Scientific Method (Application & Testing)
*(Make the idea practical — test in real life.)*

- **Hypothesis:** {filled.scientific_hypothesis}
- **Experiment:** {filled.scientific_experiment}
- **Measure:** {filled.scientific_measure}
- **Learn:** {filled.scientific_learn}

---

## ⏳ Kairos (Timing)
*(Finding the right moment to act.)*

- **Most relevant:** {filled.kairos_relevant}
- **Loses relevance:** {filled.kairos_irrelevant}

---

## 🔗 Connections
*(Situate this idea in your graph.)*

- **Related Concepts:** {_format_wikilinks(filled.connections_supportive)}
- **Contrasting Ideas:** {_format_wikilinks(filled.connections_contrasting)}
- **Source:** {filled.connections_sources}

---

## ⚙️ Practical Applications
*(Anchor the idea in your real context.)*

- **Hermes AI / Work:** {filled.applications_work}
- **Family / Homestead:** {filled.applications_family}
- **Personal Growth / Faith:** {filled.applications_personal}

---

## ❓ Open Questions
*(Hooks for future learning.)*

{_format_questions(filled.open_questions)}
"""
    return content


def write_concept_note(
    concept: ExtractedConcept,
    filled: FilledTemplate,
    metadata: BookMetadata,
    output_dir: Path,
    supporting_highlights: Optional[list[Highlight]] = None,
) -> Path:
    """Write concept note to file.

    Args:
        concept: The extracted concept.
        filled: The filled template sections.
        metadata: Source book metadata.
        output_dir: Directory to write the note to.
        supporting_highlights: Original highlights that support this concept.

    Returns:
        Path to the created file.
    """
    content = generate_concept_note(concept, filled, metadata, supporting_highlights)

    # Sanitize filename
    safe_name = "".join(
        c if c.isalnum() or c in " -_" else "_"
        for c in concept.name
    ).strip()
    filename = f"{safe_name}.md"

    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")

    return output_path
