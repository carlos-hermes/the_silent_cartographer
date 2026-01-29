"""Data models for parsed highlights."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class HighlightColor(str, Enum):
    """Kindle highlight colors with semantic meanings."""

    YELLOW = "yellow"  # Key concepts -> Extract to concept notes
    PINK = "pink"      # Action items -> Create Asana tasks
    BLUE = "blue"      # Beautiful quotes -> Store in book note
    ORANGE = "orange"  # Disagreements -> Store in book note


class Highlight(BaseModel):
    """A single highlight from a book."""

    text: str = Field(..., description="The highlighted text")
    color: HighlightColor = Field(..., description="Highlight color")
    page: Optional[int] = Field(None, description="Page number if available")
    location: Optional[int] = Field(None, description="Kindle location")
    chapter: Optional[str] = Field(None, description="Chapter or section heading")
    note: Optional[str] = Field(None, description="User note attached to highlight")

    def location_str(self) -> str:
        """Format location as readable string."""
        parts = []
        if self.page:
            parts.append(f"Page {self.page}")
        if self.location:
            parts.append(f"Location {self.location}")
        return ", ".join(parts) if parts else "Unknown location"


class BookMetadata(BaseModel):
    """Metadata about a book."""

    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Author name(s)")
    source_file: Path = Field(..., description="Original export file path")


class ParsedBook(BaseModel):
    """A fully parsed book with all highlights."""

    metadata: BookMetadata = Field(..., description="Book metadata")
    highlights: list[Highlight] = Field(default_factory=list, description="All highlights")
    parsed_at: datetime = Field(default_factory=datetime.now, description="When parsing occurred")

    @property
    def yellow_highlights(self) -> list[Highlight]:
        """Get key concept highlights."""
        return [h for h in self.highlights if h.color == HighlightColor.YELLOW]

    @property
    def pink_highlights(self) -> list[Highlight]:
        """Get action item highlights."""
        return [h for h in self.highlights if h.color == HighlightColor.PINK]

    @property
    def blue_highlights(self) -> list[Highlight]:
        """Get beautiful quote highlights."""
        return [h for h in self.highlights if h.color == HighlightColor.BLUE]

    @property
    def orange_highlights(self) -> list[Highlight]:
        """Get disagreement highlights."""
        return [h for h in self.highlights if h.color == HighlightColor.ORANGE]

    def highlight_counts(self) -> dict[str, int]:
        """Get counts by color."""
        return {
            "yellow": len(self.yellow_highlights),
            "pink": len(self.pink_highlights),
            "blue": len(self.blue_highlights),
            "orange": len(self.orange_highlights),
        }
