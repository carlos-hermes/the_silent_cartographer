"""Route highlights by color for appropriate processing."""

from dataclasses import dataclass

from tsc.parsers.models import Highlight, HighlightColor, ParsedBook


@dataclass
class RoutedHighlights:
    """Highlights organized by processing type."""

    concepts: list[Highlight]  # Yellow -> concept extraction
    actions: list[Highlight]   # Pink -> action extraction
    quotes: list[Highlight]    # Blue -> beautiful quotes
    disagreements: list[Highlight]  # Orange -> disagreements


def route_highlights(book: ParsedBook) -> RoutedHighlights:
    """Route highlights by color for appropriate processing.

    Color mapping:
    - YELLOW: Key concepts -> LLM extracts top 10 concepts -> concept notes
    - PINK: Actions -> LLM extracts top 3 actions -> Asana tasks
    - BLUE: Beautiful quotes -> stored directly in book note
    - ORANGE: Disagreements -> stored directly in book note

    Args:
        book: Parsed book with all highlights.

    Returns:
        RoutedHighlights with highlights organized by processing type.
    """
    return RoutedHighlights(
        concepts=book.yellow_highlights,
        actions=book.pink_highlights,
        quotes=book.blue_highlights,
        disagreements=book.orange_highlights,
    )
