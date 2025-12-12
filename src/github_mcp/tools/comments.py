"""Comments tools for GitHub MCP Server."""

import json
from typing import Dict, Any

from ..models.inputs import (
    AddIssueCommentInput,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error


async def github_add_issue_comment(params: AddIssueCommentInput) -> str:
    """
    Add a comment to an existing GitHub issue.

    This tool posts a new comment to the specified issue using the
    authenticated user's identity.

    Args:
        params (AddIssueCommentInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - issue_number (int): Issue number to comment on
            - body (str): Comment content in Markdown format
            - token (Optional[str]): GitHub token (optional - uses GITHUB_TOKEN env var if not provided)

    Returns:
        str: JSON string with the created comment details including id, URL, and body.
    """
    # Get token (try param, then GitHub App, then PAT)
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for adding issue comments. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload = {
            "body": params.body,
        }

        data: Dict[str, Any] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/issues/{params.issue_number}/comments",
            method="POST",
            token=auth_token,
            json=payload,
        )

        # Return the FULL GitHub API response as JSON for programmatic use
        return json.dumps(data, indent=2)

    except Exception as e:
        # Reuse generic error handler for consistent error surfaces
        return _handle_api_error(e)
