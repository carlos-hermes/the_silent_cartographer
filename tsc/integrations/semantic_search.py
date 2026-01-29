"""Semantic search for finding related notes in the vault."""

from pathlib import Path
from typing import Optional
import re

from tsc.config import get_settings


class SemanticSearch:
    """Search for semantically related notes in the Obsidian vault.

    For now, this uses simple text matching. Can be upgraded to use
    sentence-transformers for true semantic similarity.
    """

    def __init__(self, vault_path: Optional[Path] = None):
        """Initialize search with vault path.

        Args:
            vault_path: Path to Obsidian vault. Uses config if not provided.
        """
        settings = get_settings()
        self.vault_path = vault_path or settings.tsc_vault_path
        self._note_cache: Optional[dict[str, str]] = None

    def _load_notes(self) -> dict[str, str]:
        """Load all markdown notes from vault.

        Returns:
            Dict mapping note title to content.
        """
        if self._note_cache is not None:
            return self._note_cache

        notes = {}
        ideas_dir = self.vault_path / "Ideas"

        if ideas_dir.exists():
            for md_file in ideas_dir.glob("**/*.md"):
                title = md_file.stem
                try:
                    content = md_file.read_text(encoding="utf-8")
                    notes[title] = content
                except Exception:
                    pass

        self._note_cache = notes
        return notes

    def get_all_note_titles(self) -> list[str]:
        """Get all note titles in the Ideas folder.

        Returns:
            List of note titles (without .md extension).
        """
        notes = self._load_notes()
        return list(notes.keys())

    def find_related(
        self,
        concept_name: str,
        concept_description: str,
        top_k: int = 5,
    ) -> list[str]:
        """Find notes related to a concept.

        Uses simple keyword matching for now. Can be upgraded to
        use embeddings for semantic similarity.

        Args:
            concept_name: Name of the concept.
            concept_description: Description of the concept.
            top_k: Maximum number of related notes to return.

        Returns:
            List of related note titles.
        """
        notes = self._load_notes()

        if not notes:
            return []

        # Extract keywords from concept
        keywords = set()
        for text in [concept_name, concept_description]:
            # Simple tokenization
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            keywords.update(words)

        # Remove common words
        stopwords = {
            'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was',
            'were', 'been', 'being', 'have', 'has', 'had', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can',
            'need', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'under', 'again', 'further', 'then',
            'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'only',
            'own', 'same', 'than', 'too', 'very', 'just', 'also',
        }
        keywords -= stopwords

        if not keywords:
            return []

        # Score each note by keyword overlap
        scores = []
        for title, content in notes.items():
            content_lower = content.lower()
            title_lower = title.lower()

            # Count keyword matches
            score = 0
            for keyword in keywords:
                if keyword in title_lower:
                    score += 3  # Title match worth more
                if keyword in content_lower:
                    score += content_lower.count(keyword)

            if score > 0:
                scores.append((title, score))

        # Sort by score and return top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return [title for title, _ in scores[:top_k]]


async def find_related_notes(
    concept_name: str,
    concept_description: str,
    top_k: int = 5,
) -> list[str]:
    """Find notes related to a concept.

    Args:
        concept_name: Name of the concept.
        concept_description: Description of the concept.
        top_k: Maximum number of related notes.

    Returns:
        List of related note titles.
    """
    search = SemanticSearch()
    return search.find_related(concept_name, concept_description, top_k)
