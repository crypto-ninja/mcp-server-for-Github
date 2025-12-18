"""Commits tools for GitHub MCP Server."""

import json
from typing import Dict, Any, List, Union, cast

from ..models.inputs import (
    ListCommitsInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response
from ..utils.compact_format import format_response


async def github_list_commits(params: ListCommitsInput) -> str:
    """
    List commits from a GitHub repository.

    Retrieves commit history with optional filtering by branch, author, path, and date range.
    Shows commit SHA, author, date, message, and statistics.

    Args:
        params (ListCommitsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - sha (Optional[str]): Branch, tag, or commit SHA
            - path (Optional[str]): File path filter
            - author (Optional[str]): Author filter
            - since (Optional[str]): Start date (ISO 8601)
            - until (Optional[str]): End date (ISO 8601)
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of commits with details

    Examples:
        - Use when: "Show me recent commits in the main branch"
        - Use when: "List commits by user octocat"
        - Use when: "Get commits that modified README.md"

    Error Handling:
        - Returns error if repository not found (404)
        - Returns error if branch/SHA doesn't exist (404)
        - Handles pagination for large histories
    """
    try:
        token = await _get_auth_token_fallback(params.token)
        query_params: Dict[str, Any] = {"per_page": params.limit, "page": params.page}
        if params.sha:
            query_params["sha"] = params.sha
        if params.path:
            query_params["path"] = params.path
        if params.author:
            query_params["author"] = params.author
        if params.since:
            query_params["since"] = params.since
        if params.until:
            query_params["until"] = params.until

        commits_data: Union[
            Dict[str, Any], List[Dict[str, Any]]
        ] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/commits",
            token=token,
            params=query_params,
        )

        # GitHub API returns a list for commits endpoint; tests may mock dict with "items"
        if isinstance(commits_data, list):
            commits: List[Dict[str, Any]] = cast(List[Dict[str, Any]], commits_data)
        elif isinstance(commits_data, dict):
            commits = cast(List[Dict[str, Any]], commits_data.get("items", []))
        else:
            commits = []

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                commits, ResponseFormat.COMPACT.value, "commit"
            )
            return _truncate_response(json.dumps(compact_data, indent=2), len(commits))

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(commits, indent=2)

        response = f"# Commits for {params.owner}/{params.repo}\n\n"
        if params.sha:
            response += f"**Branch/SHA:** {params.sha}\n"
        if params.path:
            response += f"**Path:** {params.path}\n"
        if params.author:
            response += f"**Author:** {params.author}\n"
        if params.since or params.until:
            response += f"**Date Range:** {params.since or 'beginning'} to {params.until or 'now'}\n"

        response += (
            f"\n**Page:** {params.page} | **Showing:** {len(commits)} commits\n\n"
        )
        response += "---\n\n"

        for commit in commits:
            sha_short = commit["sha"][:7]
            author_name = commit["commit"]["author"]["name"]
            author_email = commit["commit"]["author"]["email"]
            date = _format_timestamp(commit["commit"]["author"]["date"])
            message_first = commit["commit"]["message"].split("\n")[0]

            stats = ""
            if "stats" in commit:
                additions = commit["stats"].get("additions", 0)
                deletions = commit["stats"].get("deletions", 0)
                stats = f" (+{additions}/-{deletions})"

            response += f"### {sha_short} - {message_first}{stats}\n\n"
            response += f"**Author:** {author_name} <{author_email}>  \n"
            response += f"**Date:** {date}  \n"
            response += f"**Full SHA:** `{commit['sha']}`  \n"

            if commit.get("parents"):
                parent_shas = [p["sha"][:7] for p in commit["parents"]]
                response += f"**Parents:** {', '.join(parent_shas)}  \n"

            response += f"**URL:** {commit['html_url']}\n\n"

            full_message = commit["commit"]["message"]
            if "\n" in full_message:
                response += f"**Full message:**\n```\n{full_message}\n```\n\n"

            response += "---\n\n"

        if len(commits) == params.limit:
            current_page = params.page or 1
            response += f"\n*More commits may be available. Use `page={current_page + 1}` to see the next page.*\n"

        return _truncate_response(response, len(commits))

    except Exception as e:
        return _handle_api_error(e)
