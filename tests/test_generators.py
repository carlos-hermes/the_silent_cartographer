"""Tests for note generators."""

from datetime import date
from pathlib import Path

import pytest

from tsc.parsers.models import BookMetadata, Highlight, HighlightColor, ParsedBook
from tsc.processors.concept_extractor import ExtractedConcept
from tsc.processors.action_extractor import ExtractedAction
from tsc.generators.book_note import generate_book_note
from tsc.generators.concept_note import generate_concept_note
from tsc.generators.template_filler import FilledTemplate


@pytest.fixture
def sample_metadata():
    """Create sample book metadata."""
    return BookMetadata(
        title="Test Book",
        author="Test Author",
        source_file=Path("test.html"),
    )


@pytest.fixture
def sample_book(sample_metadata):
    """Create sample parsed book."""
    return ParsedBook(
        metadata=sample_metadata,
        highlights=[
            Highlight(text="Yellow highlight", color=HighlightColor.YELLOW, page=1),
            Highlight(text="Pink highlight", color=HighlightColor.PINK, page=2),
            Highlight(text="Blue quote", color=HighlightColor.BLUE, page=3),
            Highlight(text="Orange disagreement", color=HighlightColor.ORANGE, page=4),
        ],
    )


@pytest.fixture
def sample_concept():
    """Create sample extracted concept."""
    return ExtractedConcept(
        name="Test Concept",
        description="A test concept for unit testing",
        supporting_highlights=[0],
        relevance_score=0.85,
    )


@pytest.fixture
def sample_filled_template():
    """Create sample filled template."""
    return FilledTemplate(
        trivium_grammar="Core idea explanation",
        trivium_logic="How it works",
        trivium_rhetoric="How to explain it",
        dialectic_thesis="The thesis",
        dialectic_antithesis="The antithesis",
        dialectic_synthesis="The synthesis",
        polarity_tension="The tension",
        polarity_balance="The balance",
        socratic_falsification="What proves it wrong",
        scientific_hypothesis="Expected result",
        scientific_experiment="How to test",
        scientific_measure="How to measure",
        scientific_learn="What to learn",
        kairos_relevant="When relevant",
        kairos_irrelevant="When not relevant",
        connections_supportive=["Related Note 1"],
        connections_contrasting=["Opposing Note"],
        connections_sources="Book citation",
        applications_work="Work application",
        applications_family="Family application",
        applications_personal="Personal application",
        open_questions=["Question 1", "Question 2"],
    )


def test_generate_book_note_has_frontmatter(sample_book):
    """Test book note has proper YAML frontmatter."""
    content = generate_book_note(sample_book, [], [])

    assert "---" in content
    assert 'title: "Test Book"' in content
    assert 'author: "Test Author"' in content
    assert "processed:" in content
    assert "highlights:" in content


def test_generate_book_note_has_sections(sample_book):
    """Test book note has all expected sections."""
    concepts = [
        ExtractedConcept(
            name="Concept 1",
            description="Desc",
            supporting_highlights=[0],
            relevance_score=0.9,
        )
    ]
    actions = [
        ExtractedAction(
            title="Action 1",
            description="Desc",
            source_highlight=0,
            priority="high",
            category="work",
        )
    ]

    content = generate_book_note(sample_book, concepts, actions)

    assert "## Key Concepts" in content
    assert "[[Concept 1]]" in content
    assert "## Action Items" in content
    assert "Action 1" in content
    assert "## Beautiful Quotes" in content
    assert "Blue quote" in content
    assert "## Disagreements" in content
    assert "Orange disagreement" in content


def test_generate_book_note_with_asana_links(sample_book):
    """Test book note includes Asana links when provided."""
    actions = [
        ExtractedAction(
            title="Test Action",
            description="Desc",
            source_highlight=0,
            priority="high",
            category="work",
        )
    ]
    asana_urls = {"Test Action": "https://app.asana.com/0/123/456"}

    content = generate_book_note(sample_book, [], actions, asana_urls)

    assert "[Asana](https://app.asana.com/0/123/456)" in content


def test_generate_concept_note_has_all_sections(sample_concept, sample_filled_template, sample_metadata):
    """Test concept note includes all template sections."""
    content = generate_concept_note(sample_concept, sample_filled_template, sample_metadata)

    # Check frontmatter
    assert "---" in content
    assert 'title: "Test Concept"' in content
    assert 'source: "[[Test Book]]"' in content
    assert "relevance: 0.85" in content

    # Check all major sections
    assert "## 📚 Trivium" in content
    assert "## 🗣 Dialectic" in content
    assert "## ⚖️ Polarity Thinking" in content
    assert "## ❓ Socratic Method" in content
    assert "## 🧪 Scientific Method" in content
    assert "## ⏳ Kairos" in content
    assert "## 🔗 Connections" in content
    assert "## ⚙️ Practical Applications" in content
    assert "## ❓ Open Questions" in content


def test_generate_concept_note_has_filled_content(sample_concept, sample_filled_template, sample_metadata):
    """Test concept note contains filled template content."""
    content = generate_concept_note(sample_concept, sample_filled_template, sample_metadata)

    assert "Core idea explanation" in content
    assert "How it works" in content
    assert "The synthesis" in content
    assert "[[Related Note 1]]" in content
    assert "Work application" in content
    assert "Question 1" in content
