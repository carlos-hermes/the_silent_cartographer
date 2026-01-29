"""Tests for Kindle HTML parser."""

import tempfile
from pathlib import Path

import pytest

from tsc.parsers.kindle_html import parse_kindle_html
from tsc.parsers.models import HighlightColor


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Notebook Export</title>
</head>
<body>
    <div class="bookTitle">The Art of Doing Science and Engineering</div>
    <div class="authors">Richard W. Hamming</div>

    <h2 class="sectionHeading">Chapter 1 - Introduction</h2>

    <h3 class="noteHeading">
        Highlight (<span class="highlight_yellow">yellow</span>) - Page 15 · Location 234
    </h3>
    <div class="noteText">
        The purpose of computing is insight, not numbers.
    </div>

    <h3 class="noteHeading">
        Highlight (<span class="highlight_pink">pink</span>) - Page 23 · Location 456
    </h3>
    <div class="noteText">
        You must study the lives of great scientists to learn how to be one.
    </div>

    <h2 class="sectionHeading">Chapter 2 - Foundations</h2>

    <h3 class="noteHeading">
        Highlight (<span class="highlight_blue">blue</span>) - Page 45 · Location 789
    </h3>
    <div class="noteText">
        In science if you know what you are doing you should not be doing it.
    </div>

    <h3 class="noteHeading">
        Highlight (<span class="highlight_orange">orange</span>) - Page 67 · Location 1011
    </h3>
    <div class="noteText">
        What you learn from others you can use to follow; what you learn for yourself you can use to lead.
    </div>
</body>
</html>
"""


def test_parse_kindle_html_metadata():
    """Test that metadata is extracted correctly."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_HTML)
        f.flush()
        path = Path(f.name)

    try:
        book = parse_kindle_html(path)

        assert book.metadata.title == "The Art of Doing Science and Engineering"
        assert book.metadata.author == "Richard W. Hamming"
        assert book.metadata.source_file == path
    finally:
        path.unlink()


def test_parse_kindle_html_highlights():
    """Test that highlights are extracted correctly."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_HTML)
        f.flush()
        path = Path(f.name)

    try:
        book = parse_kindle_html(path)

        assert len(book.highlights) == 4

        # Check colors
        assert book.highlights[0].color == HighlightColor.YELLOW
        assert book.highlights[1].color == HighlightColor.PINK
        assert book.highlights[2].color == HighlightColor.BLUE
        assert book.highlights[3].color == HighlightColor.ORANGE
    finally:
        path.unlink()


def test_parse_kindle_html_locations():
    """Test that page and location are extracted."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_HTML)
        f.flush()
        path = Path(f.name)

    try:
        book = parse_kindle_html(path)

        # First highlight
        assert book.highlights[0].page == 15
        assert book.highlights[0].location == 234

        # Second highlight
        assert book.highlights[1].page == 23
        assert book.highlights[1].location == 456
    finally:
        path.unlink()


def test_parse_kindle_html_chapters():
    """Test that chapter context is tracked."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_HTML)
        f.flush()
        path = Path(f.name)

    try:
        book = parse_kindle_html(path)

        # First two in Chapter 1
        assert "Chapter 1" in book.highlights[0].chapter
        assert "Chapter 1" in book.highlights[1].chapter

        # Last two in Chapter 2
        assert "Chapter 2" in book.highlights[2].chapter
        assert "Chapter 2" in book.highlights[3].chapter
    finally:
        path.unlink()


def test_highlight_counts():
    """Test highlight counting by color."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_HTML)
        f.flush()
        path = Path(f.name)

    try:
        book = parse_kindle_html(path)
        counts = book.highlight_counts()

        assert counts["yellow"] == 1
        assert counts["pink"] == 1
        assert counts["blue"] == 1
        assert counts["orange"] == 1
    finally:
        path.unlink()


def test_color_property_filters():
    """Test that color property filters work."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_HTML)
        f.flush()
        path = Path(f.name)

    try:
        book = parse_kindle_html(path)

        assert len(book.yellow_highlights) == 1
        assert len(book.pink_highlights) == 1
        assert len(book.blue_highlights) == 1
        assert len(book.orange_highlights) == 1

        assert "insight" in book.yellow_highlights[0].text
        assert "great scientists" in book.pink_highlights[0].text
    finally:
        path.unlink()
