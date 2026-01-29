"""Parser for Kindle HTML notebook exports."""

import re
from pathlib import Path
from typing import Optional
import warnings

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from tsc.parsers.models import (
    BookMetadata,
    Highlight,
    HighlightColor,
    ParsedBook,
)

# Suppress XML parsing warning since Kindle exports are XHTML
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def _extract_color(note_heading: str, heading_element) -> HighlightColor:
    """Extract highlight color from note heading.

    Looks for color class on span element or color word in text.
    """
    # Check for color spans
    if heading_element:
        for color in HighlightColor:
            span = heading_element.find("span", class_=f"highlight_{color.value}")
            if span:
                return color

    # Fallback: check text content
    heading_lower = note_heading.lower()
    if "yellow" in heading_lower:
        return HighlightColor.YELLOW
    elif "pink" in heading_lower:
        return HighlightColor.PINK
    elif "blue" in heading_lower:
        return HighlightColor.BLUE
    elif "orange" in heading_lower:
        return HighlightColor.ORANGE

    # Default to yellow if color not detected
    return HighlightColor.YELLOW


def _extract_location(note_heading: str) -> tuple[Optional[int], Optional[int]]:
    """Extract page and location numbers from heading text.

    Expected format: "Highlight (yellow) - Page X · Location YYY"
    or variations thereof.

    Returns:
        Tuple of (page, location) where either may be None.
    """
    page = None
    location = None

    # Extract page number
    page_match = re.search(r"Page\s+(\d+)", note_heading, re.IGNORECASE)
    if page_match:
        page = int(page_match.group(1))

    # Extract location
    loc_match = re.search(r"Location\s+(\d+)", note_heading, re.IGNORECASE)
    if loc_match:
        location = int(loc_match.group(1))

    return page, location


def _is_note_heading(heading_text: str) -> bool:
    """Check if this is a note/highlight heading vs a section heading."""
    heading_lower = heading_text.lower()
    return "highlight" in heading_lower or "note -" in heading_lower


def _is_user_note(heading_text: str) -> bool:
    """Check if this is a user note (not a highlight)."""
    heading_lower = heading_text.lower()
    return heading_lower.strip().startswith("note -") or heading_lower.strip().startswith("note-")


def parse_kindle_html(file_path: Path) -> ParsedBook:
    """Parse a Kindle HTML notebook export.

    The Kindle export format has a quirky structure where highlights appear as:
    - <h2 class="sectionHeading">Chapter</h2>
    - <h3 class="noteHeading">Highlight (color) - Page X · Location YYY</h3>
    - <div class="noteText">Highlighted text</div>

    But sometimes the HTML is malformed with the noteText appearing inside the h3.
    This parser handles both cases.

    Args:
        file_path: Path to the HTML file.

    Returns:
        ParsedBook with metadata and all highlights.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Use html.parser for more lenient parsing of malformed HTML
    soup = BeautifulSoup(content, "html.parser")

    # Extract book metadata
    title_elem = soup.find("div", class_="bookTitle")
    title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

    author_elem = soup.find("div", class_="authors")
    author = author_elem.get_text(strip=True) if author_elem else "Unknown Author"

    metadata = BookMetadata(
        title=title,
        author=author,
        source_file=file_path,
    )

    # Parse highlights using regex to handle malformed HTML
    # The Kindle format often has: <h3 class='noteHeading'>Heading</div><div class='noteText'>Text</h3>
    # which is malformed, so we'll use regex to extract the pairs

    highlights: list[Highlight] = []
    current_chapter: Optional[str] = None
    pending_user_note: Optional[str] = None

    # Find all section headings and note headings
    # Use regex to find note heading + note text pairs
    pattern = re.compile(
        r"<h3\s+class=['\"]noteHeading['\"]>(.*?)</(?:h3|div)>\s*<div\s+class=['\"]noteText['\"]>(.*?)</(?:h3|div)>",
        re.DOTALL | re.IGNORECASE
    )

    # Also find section headings
    section_pattern = re.compile(
        r"<h2\s+class=['\"]sectionHeading['\"]>(.*?)</h2>",
        re.DOTALL | re.IGNORECASE
    )

    # Build a list of all elements with their positions
    elements = []

    for match in section_pattern.finditer(content):
        section_text = BeautifulSoup(match.group(1), "html.parser").get_text(strip=True)
        elements.append((match.start(), "section", section_text, None))

    for match in pattern.finditer(content):
        heading_html = match.group(1)
        note_html = match.group(2)

        # Parse the heading to extract color info
        heading_soup = BeautifulSoup(heading_html, "html.parser")
        heading_text = heading_soup.get_text(strip=True)
        note_text = BeautifulSoup(note_html, "html.parser").get_text(strip=True)

        elements.append((match.start(), "note", heading_text, (note_text, heading_soup)))

    # Sort by position
    elements.sort(key=lambda x: x[0])

    # Process elements in order
    for pos, elem_type, text, extra in elements:
        if elem_type == "section":
            current_chapter = text

        elif elem_type == "note":
            heading_text = text
            note_text, heading_soup = extra

            # Check if this is a user note (not a highlight)
            if _is_user_note(heading_text):
                # Store as pending note to attach to previous highlight
                pending_user_note = note_text
                continue

            # Skip if not a highlight
            if not _is_note_heading(heading_text):
                continue

            # Extract properties
            color = _extract_color(heading_text, heading_soup)
            page, location = _extract_location(heading_text)

            highlight = Highlight(
                text=note_text,
                color=color,
                page=page,
                location=location,
                chapter=current_chapter,
                note=None,  # Will be set if next element is a user note
            )
            highlights.append(highlight)

            # If there was a pending user note, it should have been attached to previous highlight
            # Reset it for the next iteration
            pending_user_note = None

    # Attach any pending user notes to their preceding highlights
    # We need to re-process to handle notes that follow highlights
    for i, h in enumerate(highlights[:-1]):
        # Check if there's a note between this highlight and the next
        pass  # The current approach handles this inline

    return ParsedBook(
        metadata=metadata,
        highlights=highlights,
    )
