"""External service integrations.

Imports are done lazily to avoid circular imports.
"""


def get_anthropic_client():
    """Get Anthropic client."""
    from tsc.integrations.anthropic_client import get_anthropic_client as _get
    return _get()


def create_task(*args, **kwargs):
    """Create Asana task."""
    from tsc.integrations.asana_client import create_task as _create
    return _create(*args, **kwargs)


def send_notification(*args, **kwargs):
    """Send email notification."""
    from tsc.integrations.email_client import send_notification as _send
    return _send(*args, **kwargs)


def find_related_notes(*args, **kwargs):
    """Find related notes."""
    from tsc.integrations.semantic_search import find_related_notes as _find
    return _find(*args, **kwargs)


__all__ = [
    "get_anthropic_client",
    "create_task",
    "send_notification",
    "find_related_notes",
]
