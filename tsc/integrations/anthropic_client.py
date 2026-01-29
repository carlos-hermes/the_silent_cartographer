"""Anthropic Claude API client."""

from typing import Optional

import anthropic

from tsc.config import get_settings


_client: Optional[anthropic.AsyncAnthropic] = None


def get_anthropic_client() -> anthropic.AsyncAnthropic:
    """Get or create Anthropic async client.

    Returns:
        AsyncAnthropic client instance.

    Raises:
        ValueError: If API key is not configured.
    """
    global _client

    if _client is None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not configured. "
                "Please set it in config.env"
            )
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    return _client


def reset_client() -> None:
    """Reset client instance (useful for testing)."""
    global _client
    _client = None
