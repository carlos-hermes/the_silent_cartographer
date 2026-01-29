"""Memory tracking for processed books and spaced repetition."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from tsc.config import get_settings


class ProcessedRecord(BaseModel):
    """Record of a processed book."""

    source_file: str = Field(..., description="Original HTML filename")
    book_title: str = Field(..., description="Book title")
    book_author: str = Field(..., description="Book author")
    processed_at: datetime = Field(default_factory=datetime.now)
    highlight_counts: dict[str, int] = Field(default_factory=dict)
    concepts_created: list[str] = Field(default_factory=list)
    actions_created: list[str] = Field(default_factory=list)
    book_note_path: str = Field(..., description="Path to generated book note")


class SpacedRepetitionEntry(BaseModel):
    """Entry for spaced repetition review schedule."""

    concept_name: str = Field(..., description="Concept to review")
    concept_path: str = Field(..., description="Path to concept note")
    source_book: str = Field(..., description="Source book title")
    created_at: date = Field(default_factory=date.today)
    last_reviewed: Optional[date] = Field(None, description="Last review date")
    review_count: int = Field(0, description="Number of reviews completed")
    next_review: date = Field(default_factory=date.today)

    def schedule_next_review(self) -> None:
        """Schedule next review using spaced repetition intervals.

        Intervals: 1 day, 3 days, 1 week, 2 weeks, 1 month, 3 months
        """
        intervals = [1, 3, 7, 14, 30, 90]
        interval_index = min(self.review_count, len(intervals) - 1)
        days = intervals[interval_index]

        self.last_reviewed = date.today()
        self.review_count += 1
        self.next_review = date.today() + timedelta(days=days)


class MemoryState(BaseModel):
    """Complete memory state persisted to disk."""

    processed_books: list[ProcessedRecord] = Field(default_factory=list)
    spaced_repetition: list[SpacedRepetitionEntry] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)


class MemoryTracker:
    """Manages persistent memory state for TSC."""

    def __init__(self, memory_file: Optional[Path] = None):
        """Initialize tracker with memory file path.

        Args:
            memory_file: Path to .memory.json file.
        """
        settings = get_settings()
        self.memory_file = memory_file or settings.memory_file
        self._state: Optional[MemoryState] = None

    def _load(self) -> MemoryState:
        """Load state from disk."""
        if self._state is not None:
            return self._state

        if self.memory_file.exists():
            try:
                data = json.loads(self.memory_file.read_text(encoding="utf-8"))
                self._state = MemoryState(**data)
            except Exception:
                self._state = MemoryState()
        else:
            self._state = MemoryState()

        return self._state

    def _save(self) -> None:
        """Save state to disk."""
        if self._state is None:
            return

        self._state.last_updated = datetime.now()
        self.memory_file.write_text(
            self._state.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def is_processed(self, source_file: str) -> bool:
        """Check if a file has already been processed.

        Args:
            source_file: Filename to check.

        Returns:
            True if already processed.
        """
        state = self._load()
        return any(r.source_file == source_file for r in state.processed_books)

    def add_processed_record(self, record: ProcessedRecord) -> None:
        """Add a record of a processed book.

        Args:
            record: Processing record to add.
        """
        state = self._load()
        state.processed_books.append(record)
        self._save()

    def add_spaced_repetition_entry(self, entry: SpacedRepetitionEntry) -> None:
        """Add a concept to spaced repetition schedule.

        Args:
            entry: Spaced repetition entry to add.
        """
        state = self._load()
        state.spaced_repetition.append(entry)
        self._save()

    def get_due_reviews(self) -> list[SpacedRepetitionEntry]:
        """Get concepts due for review.

        Returns:
            List of entries due for review today or earlier.
        """
        state = self._load()
        today = date.today()
        return [e for e in state.spaced_repetition if e.next_review <= today]

    def mark_reviewed(self, concept_name: str) -> None:
        """Mark a concept as reviewed and schedule next review.

        Args:
            concept_name: Name of the concept reviewed.
        """
        state = self._load()
        for entry in state.spaced_repetition:
            if entry.concept_name == concept_name:
                entry.schedule_next_review()
                break
        self._save()

    def get_stats(self) -> dict:
        """Get statistics about processed content.

        Returns:
            Dict with various statistics.
        """
        state = self._load()

        total_highlights = sum(
            sum(r.highlight_counts.values())
            for r in state.processed_books
        )

        return {
            "books_processed": len(state.processed_books),
            "total_highlights": total_highlights,
            "concepts_created": sum(
                len(r.concepts_created) for r in state.processed_books
            ),
            "actions_created": sum(
                len(r.actions_created) for r in state.processed_books
            ),
            "pending_reviews": len(self.get_due_reviews()),
            "total_in_rotation": len(state.spaced_repetition),
        }

    def get_recent_books(self, limit: int = 10) -> list[ProcessedRecord]:
        """Get recently processed books.

        Args:
            limit: Maximum number of books to return.

        Returns:
            List of recent processing records.
        """
        state = self._load()
        sorted_books = sorted(
            state.processed_books,
            key=lambda r: r.processed_at,
            reverse=True,
        )
        return sorted_books[:limit]
