"""Unified LLM client supporting both CLI and API modes."""

import asyncio
import subprocess
from typing import Optional

from tsc.config import get_settings


async def query_llm(prompt: str, max_tokens: int = 4096) -> str:
    """Query LLM using configured mode (cli or api).

    Args:
        prompt: The prompt to send to the LLM.
        max_tokens: Maximum tokens for response (used in API mode).

    Returns:
        The LLM's response text.

    Raises:
        RuntimeError: If LLM query fails.
        ValueError: If API mode is used without API key configured.
    """
    settings = get_settings()

    if settings.llm_mode == "cli":
        return await _query_cli(prompt)
    else:
        return await _query_api(prompt, max_tokens)


async def _query_cli(prompt: str) -> str:
    """Call claude CLI with prompt.

    Uses `claude -p --output-format text` to get response.

    Args:
        prompt: The prompt to send.

    Returns:
        The CLI response text.

    Raises:
        RuntimeError: If CLI call fails.
    """
    import shutil

    loop = asyncio.get_event_loop()

    # Find claude executable
    claude_path = shutil.which("claude")
    if not claude_path:
        raise RuntimeError(
            "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        )

    # Pass prompt via stdin to handle long prompts that exceed command-line limits
    result = await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            [claude_path, "-p", "--output-format", "text"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ),
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed with code {result.returncode}: {result.stderr}"
        )

    if not result.stdout.strip():
        raise RuntimeError(
            f"Claude CLI returned empty response. stderr: {result.stderr}"
        )

    return result.stdout


async def _query_api(prompt: str, max_tokens: int) -> str:
    """Use Anthropic API for LLM query.

    Args:
        prompt: The prompt to send.
        max_tokens: Maximum tokens for response.

    Returns:
        The API response text.

    Raises:
        ValueError: If API key is not configured.
    """
    from tsc.integrations.anthropic_client import get_anthropic_client

    client = get_anthropic_client()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
