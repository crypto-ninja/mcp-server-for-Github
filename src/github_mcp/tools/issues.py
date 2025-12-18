"""Issue management tools for GitHub MCP Server."""

import json
import httpx
from typing import Dict, Any, List, Union, cast

from ..models.inputs import (
    ListIssuesInput,
    CreateIssueInput,
    UpdateIssueInput,
)
from ..models.enums import ResponseFormat
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response
from ..utils.compact_format import format_response


async def github_list_issues(params: ListIssuesInput) -> str:
    """
    List issues from a GitHub repository with filtering options.

    This tool retrieves issues from a repository, supporting state filtering and
    pagination. It does NOT create or modify issues.

    Args:
        params (ListIssuesInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - state (IssueState): Filter by state ('open', 'closed', 'all')
            - limit (int): Maximum results per page (1-100, default 20)
            - page (int): Page number for pagination (default 1)
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of issues in requested format with pagination info

    Examples:
        - Use when: "Show me open issues in react repository"
        - Use when: "List all closed issues for tensorflow/tensorflow"
        - Use when: "Get the first 50 issues from microsoft/vscode"

    Error Handling:
        - Returns error if repository not found
        - Handles rate limiting with clear guidance
        - Provides pagination info for continued browsing
    """
    try:
        params_dict = {
            "state": params.state.value,
            "per_page": params.limit,
            "page": params.page,
        }

        raw_data: Union[
            Dict[str, Any], List[Dict[str, Any]]
        ] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/issues",
            token=params.token,
            params=params_dict,
        )

        # GitHub issues endpoint returns a list; tests may mock dict with "items"
        if isinstance(raw_data, list):
            issues: List[Dict[str, Any]] = cast(List[Dict[str, Any]], raw_data)
        elif isinstance(raw_data, dict):
            issues = cast(List[Dict[str, Any]], raw_data.get("items", []))
        else:
            issues = []

        # For compact/markdown output, skip pull requests that appear in the issues feed
        issues = [issue for issue in issues if "pull_request" not in issue]

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                issues, ResponseFormat.COMPACT.value, "issue"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(issues))

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(issues, indent=2)
            return _truncate_response(result, len(issues))

        # Markdown format
        markdown = f"# Issues for {params.owner}/{params.repo}\n\n"
        markdown += (
            f"**State:** {params.state.value} | **Page:** {params.page} | "
            f"**Showing:** {len(issues)} issues\n\n"
        )

        if not issues:
            markdown += f"No {params.state.value} issues found.\n"
        else:
            for issue in issues:
                markdown += f"## #{issue['number']}: {issue['title']}\n"
                markdown += f"- **State:** {issue['state']}\n"
                markdown += f"- **Author:** @{issue['user']['login']}\n"
                markdown += f"- **Created:** {_format_timestamp(issue['created_at'])}\n"
                markdown += f"- **Updated:** {_format_timestamp(issue['updated_at'])}\n"

                if issue.get("labels"):
                    labels = ", ".join(
                        [f"`{label['name']}`" for label in issue["labels"]]
                    )
                    markdown += f"- **Labels:** {labels}\n"

                if issue.get("assignees"):
                    assignees = ", ".join(
                        [f"@{a['login']}" for a in issue["assignees"]]
                    )
                    markdown += f"- **Assignees:** {assignees}\n"

                markdown += f"- **Comments:** {issue['comments']}\n"
                markdown += f"- **URL:** {issue['html_url']}\n\n"

                if issue.get("body"):
                    body_preview = (
                        issue["body"][:200] + "..."
                        if len(issue["body"]) > 200
                        else issue["body"]
                    )
                    markdown += f"**Preview:** {body_preview}\n\n"

                markdown += "---\n\n"

        return _truncate_response(markdown, len(issues))

    except Exception as e:
        return _handle_api_error(e)


async def github_create_issue(params: CreateIssueInput) -> str:
    """
    Create a new issue in a GitHub repository.

    This tool creates a new issue with specified title, body, labels, and assignees.
    Requires authentication with a GitHub token that has repository access.

    Args:
        params (CreateIssueInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - title (str): Issue title (required)
            - body (Optional[str]): Issue description in Markdown
            - labels (Optional[List[str]]): Label names to apply
            - assignees (Optional[List[str]]): Usernames to assign
            - milestone (Optional[int]): Milestone number to associate with this issue
            - token (Optional[str]): GitHub token (optional - uses GITHUB_TOKEN env var if not provided)

    Returns:
        str: Created issue details including issue number and URL

    Examples:
        - Use when: "Create a bug report in myrepo"
        - Use when: "Open a new feature request issue"
        - Use when: "File an issue about the documentation"

    Error Handling:
        - Returns error if authentication fails (401)
        - Returns error if insufficient permissions (403)
        - Returns error if labels/assignees don't exist (422)
    """
    # Get token (try param, then GitHub App, then PAT)
    auth_token = await _get_auth_token_fallback(params.token)

    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating issues. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload: Dict[str, Any] = {
            "title": params.title,
        }

        if params.body:
            payload["body"] = params.body
        if params.labels:
            payload["labels"] = params.labels  # type: ignore[assignment]
        if params.assignees:
            payload["assignees"] = params.assignees  # type: ignore[assignment]
        if params.milestone:
            payload["milestone"] = params.milestone

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/issues",
            method="POST",
            token=auth_token,
            json=payload,
        )

        # Return the FULL GitHub API response as JSON
        return json.dumps(data, indent=2)

    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {"success": False, "error": str(e), "type": type(e).__name__}

        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = (
                    e.response.text[:200] if e.response.text else "Unknown error"
                )
        else:
            error_info["message"] = str(e)

        return json.dumps(error_info, indent=2)


async def github_update_issue(params: UpdateIssueInput) -> str:
    """
    Update an existing GitHub issue.

    This tool modifies issue properties including state (open/closed),
    title, body, labels, assignees, and milestone. Only provided fields
    will be updated - others remain unchanged.

    Args:
        params (UpdateIssueInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - issue_number (int): Issue number to update
            - state (Optional[str]): 'open' or 'closed'
            - title (Optional[str]): New title
            - body (Optional[str]): New description
            - labels (Optional[List[str]]): Label names
            - assignees (Optional[List[str]]): Usernames to assign
            - milestone (Optional[int]): Milestone number
            - state_reason (Optional[str]): Reason for state change ('completed', 'not_planned', 'reopened')
            - token (Optional[str]): GitHub token

    Returns:
        str: Updated issue details with confirmation message

    Examples:
        - Use when: "Close issue #28"
        - Use when: "Update issue #29 labels"
        - Use when: "Reassign issue #30 to user"

    Error Handling:
        - Returns error if issue not found (404)
        - Returns error if authentication fails (401/403)
        - Returns error if invalid parameters (422)
    """

    # Get token (try param, then GitHub App, then PAT)
    token = await _get_auth_token_fallback(params.token)
    if not token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for updating issues. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    # Validate state if provided
    if params.state and params.state not in ["open", "closed"]:
        return f"Error: Invalid state '{params.state}'. Must be 'open' or 'closed'."

    try:
        # Build update payload
        update_data: Dict[str, Any] = {}
        if params.state is not None:
            update_data["state"] = params.state
        if params.title is not None:
            update_data["title"] = params.title
        if params.body is not None:
            update_data["body"] = params.body
        if params.labels is not None:
            update_data["labels"] = params.labels  # type: ignore[assignment]
        if params.assignees is not None:
            update_data["assignees"] = params.assignees  # type: ignore[assignment]
        if params.milestone is not None:
            update_data["milestone"] = params.milestone
        if params.state_reason is not None:
            update_data["state_reason"] = params.state_reason

        # Make request
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/issues/{params.issue_number}",
            method="PATCH",
            token=token,
            json=update_data,
        )

        # Format response
        changes = []
        if params.state:
            changes.append(f"State: {params.state}")
        if params.title:
            changes.append("Title updated")
        if params.body:
            changes.append("Description updated")
        if params.labels:
            changes.append(f"Labels: {', '.join(params.labels)}")
        if params.assignees:
            changes.append(f"Assignees: {', '.join(params.assignees)}")
        if params.milestone:
            changes.append(f"Milestone: #{params.milestone}")

        result = f"""✅ Issue Updated Successfully!

**Issue:** #{data["number"]} - {data["title"]}
**Repository:** {params.owner}/{params.repo}
**URL:** {data["html_url"]}

**Changes Applied:**
{chr(10).join(f"- {change}" for change in changes)}

**Current State:** {data["state"]}
**Updated:** {_format_timestamp(data["updated_at"])}
"""

        return result

    except Exception as e:
        return _handle_api_error(e)
