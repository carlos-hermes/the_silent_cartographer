"""Tests for memory tracker."""

import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from tsc.memory.tracker import (
    MemoryTracker,
    ProcessedRecord,
    SpacedRepetitionEntry,
)


@pytest.fixture
def temp_memory_file():
    """Create a temporary memory file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    yield path
    if path.exists():
        path.unlink()


def test_tracker_is_processed_empty(temp_memory_file):
    """Test is_processed on empty tracker."""
    tracker = MemoryTracker(temp_memory_file)
    assert not tracker.is_processed("test.html")


def test_tracker_add_and_check_processed(temp_memory_file):
    """Test adding and checking processed records."""
    tracker = MemoryTracker(temp_memory_file)

    record = ProcessedRecord(
        source_file="test.html",
        book_title="Test Book",
        book_author="Test Author",
        highlight_counts={"yellow": 5, "pink": 2, "blue": 3, "orange": 1},
        concepts_created=["Concept 1", "Concept 2"],
        actions_created=["Action 1"],
        book_note_path="/path/to/note.md",
    )

    tracker.add_processed_record(record)

    # Create new tracker instance to test persistence
    tracker2 = MemoryTracker(temp_memory_file)
    assert tracker2.is_processed("test.html")
    assert not tracker2.is_processed("other.html")


def test_spaced_repetition_schedule():
    """Test spaced repetition scheduling."""
    entry = SpacedRepetitionEntry(
        concept_name="Test Concept",
        concept_path="/path/to/concept.md",
        source_book="Test Book",
    )

    # Initial state
    assert entry.review_count == 0
    assert entry.next_review == date.today()

    # First review: next in 1 day
    entry.schedule_next_review()
    assert entry.review_count == 1
    assert entry.next_review == date.today() + timedelta(days=1)

    # Second review: next in 3 days
    entry.schedule_next_review()
    assert entry.review_count == 2
    assert entry.next_review == date.today() + timedelta(days=3)

    # Third review: next in 7 days
    entry.schedule_next_review()
    assert entry.review_count == 3
    assert entry.next_review == date.today() + timedelta(days=7)


def test_get_due_reviews(temp_memory_file):
    """Test getting due reviews."""
    tracker = MemoryTracker(temp_memory_file)

    # Add an entry due today
    entry_due = SpacedRepetitionEntry(
        concept_name="Due Concept",
        concept_path="/path/to/due.md",
        source_book="Test Book",
        next_review=date.today(),
    )
    tracker.add_spaced_repetition_entry(entry_due)

    # Add an entry due in the future
    entry_future = SpacedRepetitionEntry(
        concept_name="Future Concept",
        concept_path="/path/to/future.md",
        source_book="Test Book",
        next_review=date.today() + timedelta(days=7),
    )
    tracker.add_spaced_repetition_entry(entry_future)

    due = tracker.get_due_reviews()
    assert len(due) == 1
    assert due[0].concept_name == "Due Concept"


def test_get_stats(temp_memory_file):
    """Test statistics generation."""
    tracker = MemoryTracker(temp_memory_file)

    # Add some data
    record = ProcessedRecord(
        source_file="test.html",
        book_title="Test Book",
        book_author="Test Author",
        highlight_counts={"yellow": 5, "pink": 2, "blue": 3, "orange": 1},
        concepts_created=["C1", "C2", "C3"],
        actions_created=["A1", "A2"],
        book_note_path="/path/to/note.md",
    )
    tracker.add_processed_record(record)

    entry = SpacedRepetitionEntry(
        concept_name="Test",
        concept_path="/path",
        source_book="Book",
        next_review=date.today(),
    )
    tracker.add_spaced_repetition_entry(entry)

    stats = tracker.get_stats()

    assert stats["books_processed"] == 1
    assert stats["total_highlights"] == 11
    assert stats["concepts_created"] == 3
    assert stats["actions_created"] == 2
    assert stats["pending_reviews"] == 1
    assert stats["total_in_rotation"] == 1
