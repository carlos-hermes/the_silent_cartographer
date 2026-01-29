"""Asana integration for task creation."""

from typing import Optional

import asana
from asana.rest import ApiException

from tsc.config import get_settings
from tsc.processors.action_extractor import ExtractedAction
from tsc.parsers.models import BookMetadata


class AsanaClient:
    """Client for Asana API operations."""

    def __init__(self):
        """Initialize Asana client with configured credentials."""
        settings = get_settings()

        if not settings.asana_access_token:
            raise ValueError(
                "ASANA_ACCESS_TOKEN not configured. "
                "Please set it in config.env"
            )

        configuration = asana.Configuration()
        configuration.access_token = settings.asana_access_token
        self.api_client = asana.ApiClient(configuration)
        self.tasks_api = asana.TasksApi(self.api_client)
        self.workspace_gid = settings.asana_workspace_gid
        self.project_gid = settings.asana_project_gid

    def create_task(
        self,
        action: ExtractedAction,
        metadata: BookMetadata,
        highlight_text: str,
    ) -> dict:
        """Create an Asana task from an extracted action.

        Args:
            action: The extracted action to create as a task.
            metadata: Book metadata for context.
            highlight_text: The original highlight text that inspired this action.

        Returns:
            Dict containing task data including 'gid' and 'permalink_url'.

        Raises:
            ApiException: If Asana API call fails.
        """
        # Build task description with context
        notes = f"""📖 From: "{metadata.title}" by {metadata.author}

## Action
{action.description}

## Original Highlight
> {highlight_text}

---
*Created by The Silent Cartographer*
"""

        task_data = {
            "data": {
                "name": action.title,
                "notes": notes,
                "workspace": self.workspace_gid,
            }
        }

        # Add to project if configured
        if self.project_gid:
            task_data["data"]["projects"] = [self.project_gid]

        # Create the task
        opts = {"opt_fields": "gid,permalink_url,name"}
        result = self.tasks_api.create_task(task_data, opts)

        return result

    def get_task_url(self, task_gid: str) -> str:
        """Get the web URL for a task.

        Args:
            task_gid: The task's global ID.

        Returns:
            URL to the task in Asana web interface.
        """
        return f"https://app.asana.com/0/{self.project_gid}/{task_gid}"


async def create_task(
    action: ExtractedAction,
    metadata: BookMetadata,
    highlight_text: str,
) -> Optional[str]:
    """Create an Asana task and return its URL.

    Args:
        action: The extracted action to create as a task.
        metadata: Book metadata for context.
        highlight_text: The original highlight text.

    Returns:
        URL to the created task, or None if creation fails.
    """
    try:
        client = AsanaClient()
        result = client.create_task(action, metadata, highlight_text)
        return result.get("permalink_url") or client.get_task_url(result["gid"])
    except (ValueError, ApiException) as e:
        # Log error but don't fail the whole process
        print(f"Warning: Failed to create Asana task: {e}")
        return None
