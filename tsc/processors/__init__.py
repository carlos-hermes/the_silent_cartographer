"""Processors for extracting concepts and actions from highlights."""

from tsc.processors.concept_extractor import extract_concepts
from tsc.processors.action_extractor import extract_actions
from tsc.processors.highlight_router import route_highlights

__all__ = [
    "extract_concepts",
    "extract_actions",
    "route_highlights",
]
