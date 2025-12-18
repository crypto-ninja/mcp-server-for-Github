"""Branch management tools for GitHub MCP Server."""

import json
from typing import Dict, Any, List, Union, cast

from ..models.inputs import (
    ListBranchesInput,
    CreateBranchInput,
    GetBranchInput,
    DeleteBranchInput,
    CompareBranchesInput,
)
from ..models.enums import ResponseFormat
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp
from ..utils.compact_format import format_response


async def github_list_branches(params: ListBranchesInput) -> str:
    """
    List all branches in a GitHub repository.

    Returns branch names, latest commit SHA, protection status, and whether
    it's the default branch. Essential for branch management workflows.

    Args:
        params (ListBranchesInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - protected (Optional[bool]): Filter by protected status
            - limit (Optional[int]): Maximum results (1-100, default 10)
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of branches with details

    Examples:
        - Use when: "List all branches in my repository"
        - Use when: "Show me only protected branches"
        - Use when: "What branches exist in this repo?"

    Error Handling:
        - Returns error if repository not found (404)
        - Returns error if authentication fails (401/403)
    """
    try:
        auth_token = await _get_auth_token_fallback(params.token)

        endpoint = f"repos/{params.owner}/{params.repo}/branches"
        query_params: Dict[str, Any] = {
            "per_page": params.limit,
            "page": params.page,
        }

        if params.protected is not None:
            query_params["protected"] = "true" if params.protected else "false"

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            endpoint, method="GET", token=auth_token, params=query_params
        )

        repo_info: Dict[str, Any] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}", method="GET", token=auth_token
        )
        default_branch = repo_info.get("default_branch", "main")

        # GitHub API returns a list for branches endpoint
        branches: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                branches, ResponseFormat.COMPACT.value, "branch"
            )
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(
                {
                    "owner": params.owner,
                    "repo": params.repo,
                    "default_branch": default_branch,
                    "total_branches": len(branches),
                    "branches": [
                        {
                            "name": b["name"],
                            "commit_sha": b["commit"]["sha"],
                            "protected": b.get("protected", False),
                            "is_default": b["name"] == default_branch,
                        }
                        for b in branches
                    ],
                },
                indent=2,
            )
        else:
            result = f"# Branches: {params.owner}/{params.repo}\n\n"
            result += f"**Default Branch:** {default_branch}\n"
            result += f"**Total Branches:** {len(branches)}\n\n"

            if branches:
                result += "| Branch | Commit | Protected | Default |\n"
                result += "|--------|--------|-----------|----------|\n"
                for b in branches:
                    sha = b["commit"]["sha"][:7]
                    protected = "🔒" if b.get("protected", False) else "🔓"
                    is_default = "⭐" if b["name"] == default_branch else ""
                    result += f"| {b['name']} | {sha} | {protected} | {is_default} |\n"
            else:
                result += "*No branches found*\n"

            return result

    except Exception as e:
        return _handle_api_error(e)


async def github_create_branch(params: CreateBranchInput) -> str:
    """
    Create a new branch in a GitHub repository.

    Creates a new branch from a specified ref (branch, tag, or commit).
    Uses Git References API for reliability.

    Args:
        params (CreateBranchInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - branch (str): New branch name
            - from_ref (str): Branch, tag, or commit SHA to branch from (default: "main")
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation message with branch details

    Examples:
        - Use when: "Create a new feature branch from main"
        - Use when: "Create branch from specific commit"
        - Use when: "Branch off from tag v1.0.0"

    Error Handling:
        - Returns error if branch already exists (422)
        - Returns error if from_ref doesn't exist (404)
        - Returns error if authentication fails (401/403)
    """
    try:
        auth_token = await _get_auth_token_fallback(params.token)

        if not auth_token:
            return json.dumps(
                {
                    "error": "Authentication required",
                    "message": "GitHub token required for creating branches.",
                    "success": False,
                },
                indent=2,
            )

        ref_endpoint = (
            f"repos/{params.owner}/{params.repo}/git/ref/heads/{params.from_ref}"
        )
        try:
            ref_data = await _make_github_request(
                ref_endpoint, method="GET", token=auth_token
            )
            sha = ref_data["object"]["sha"]
        except Exception:
            commit_endpoint = (
                f"repos/{params.owner}/{params.repo}/commits/{params.from_ref}"
            )
            commit_data = await _make_github_request(
                commit_endpoint, method="GET", token=auth_token
            )
            sha = commit_data["sha"]

        create_endpoint = f"repos/{params.owner}/{params.repo}/git/refs"
        result = await _make_github_request(
            create_endpoint,
            method="POST",
            token=auth_token,
            json={"ref": f"refs/heads/{params.branch}", "sha": sha},
        )

        return json.dumps(
            {
                "success": True,
                "branch": params.branch,
                "ref": result.get("ref"),
                "sha": result.get("object", {}).get("sha") or sha,
                "url": f"https://github.com/{params.owner}/{params.repo}/tree/{params.branch}",
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_get_branch(params: GetBranchInput) -> str:
    """
    Get detailed information about a branch including protection status,
    latest commit, and whether it's ahead/behind the default branch.

    Args:
        params (GetBranchInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - branch (str): Branch name
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed branch information

    Examples:
        - Use when: "Get details about the feature branch"
        - Use when: "Check if branch is protected"
        - Use when: "Show me the latest commit on this branch"

    Error Handling:
        - Returns error if branch not found (404)
        - Returns error if authentication fails (401/403)
    """
    try:
        auth_token = await _get_auth_token_fallback(params.token)

        endpoint = f"repos/{params.owner}/{params.repo}/branches/{params.branch}"
        data = await _make_github_request(endpoint, method="GET", token=auth_token)

        if params.response_format == ResponseFormat.COMPACT:
            from ..utils.compact_format import format_response

            compact_data = format_response(data, ResponseFormat.COMPACT.value, "branch")
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(
                {
                    "branch": data["name"],
                    "protected": data.get("protected", False),
                    "commit": {
                        "sha": data["commit"]["sha"],
                        "message": data["commit"]["commit"]["message"].split("\n")[0],
                        "author": data["commit"]["commit"]["author"]["name"],
                        "date": data["commit"]["commit"]["author"]["date"],
                    },
                    "url": f"https://github.com/{params.owner}/{params.repo}/tree/{params.branch}",
                },
                indent=2,
            )
        else:
            result = f"# Branch: {data['name']}\n\n"
            result += f"**Repository:** {params.owner}/{params.repo}\n"
            result += f"**Protected:** {'🔒 Yes' if data.get('protected', False) else '🔓 No'}\n\n"
            result += "## Latest Commit\n\n"
            result += f"**SHA:** {data['commit']['sha'][:7]}\n"
            result += f"**Message:** {data['commit']['commit']['message'].split(chr(10))[0]}\n"
            result += f"**Author:** {data['commit']['commit']['author']['name']}\n"
            result += f"**Date:** {_format_timestamp(data['commit']['commit']['author']['date'])}\n\n"
            result += f"**URL:** https://github.com/{params.owner}/{params.repo}/tree/{params.branch}\n"

            return result

    except Exception as e:
        return _handle_api_error(e)


async def github_delete_branch(params: DeleteBranchInput) -> str:
    """
    Delete a branch from a GitHub repository.

    Safety: Cannot delete the default branch or protected branches.
    Use with caution - this is permanent!

    Args:
        params (DeleteBranchInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - branch (str): Branch name to delete
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation message

    Examples:
        - Use when: "Delete the old feature branch"
        - Use when: "Clean up merged branches"
        - Use when: "Remove test branch"

    Error Handling:
        - Returns error if trying to delete default branch
        - Returns error if trying to delete protected branch
        - Returns error if branch not found (404)
    """
    try:
        auth_token = await _get_auth_token_fallback(params.token)

        if not auth_token:
            return json.dumps(
                {"error": "Authentication required", "success": False}, indent=2
            )

        repo_info = await _make_github_request(
            f"repos/{params.owner}/{params.repo}", method="GET", token=auth_token
        )

        if params.branch == repo_info.get("default_branch"):
            return json.dumps(
                {
                    "error": "Cannot delete default branch",
                    "message": f"'{params.branch}' is the default branch and cannot be deleted.",
                    "success": False,
                },
                indent=2,
            )

        try:
            branch_data = await _make_github_request(
                f"repos/{params.owner}/{params.repo}/branches/{params.branch}",
                method="GET",
                token=auth_token,
            )
            if branch_data.get("protected", False):
                return json.dumps(
                    {
                        "error": "Cannot delete protected branch",
                        "message": f"'{params.branch}' is protected and cannot be deleted.",
                        "success": False,
                    },
                    indent=2,
                )
        except Exception:
            pass

        endpoint = f"repos/{params.owner}/{params.repo}/git/refs/heads/{params.branch}"
        await _make_github_request(endpoint, method="DELETE", token=auth_token)

        return json.dumps(
            {
                "success": True,
                "branch": params.branch,
                "message": f"Branch '{params.branch}' deleted successfully",
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_compare_branches(params: CompareBranchesInput) -> str:
    """
    Compare two branches to see commits ahead/behind and files changed.

    Useful before merging to understand what will change.

    Args:
        params (CompareBranchesInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - base (str): Base branch name
            - head (str): Head branch name to compare
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Comparison results with commits and files changed

    Examples:
        - Use when: "Compare feature branch to main"
        - Use when: "See what's different between branches"
        - Use when: "Check if branch is ready to merge"

    Error Handling:
        - Returns error if branches not found (404)
        - Returns error if authentication fails (401/403)
    """
    try:
        auth_token = await _get_auth_token_fallback(params.token)

        endpoint = (
            f"repos/{params.owner}/{params.repo}/compare/{params.base}...{params.head}"
        )
        data: Dict[str, Any] = await _make_github_request(
            endpoint, method="GET", token=auth_token
        )

        summary = {
            "base": params.base,
            "head": params.head,
            "status": data["status"],
            "ahead_by": data["ahead_by"],
            "behind_by": data["behind_by"],
            "total_commits": data["total_commits"],
            "files_changed": len(data.get("files", [])),
        }

        if params.response_format == ResponseFormat.COMPACT:
            # Compact comparison summary without full commit/file details
            return json.dumps(summary, indent=2)

        if params.response_format == ResponseFormat.JSON:
            details = {
                **summary,
                "commits": [
                    {
                        "sha": c["sha"][:7],
                        "message": c["commit"]["message"].split("\n")[0],
                        "author": c["commit"]["author"]["name"],
                    }
                    for c in data["commits"][:10]
                ],
            }
            return json.dumps(details, indent=2)
        else:
            result = "# Branch Comparison\n\n"
            result += f"**Base:** {params.base} → **Head:** {params.head}\n\n"
            result += f"**Status:** {data['status']}\n"
            result += f"**Commits Ahead:** {data['ahead_by']}\n"
            result += f"**Commits Behind:** {data['behind_by']}\n"
            result += f"**Files Changed:** {len(data.get('files', []))}\n\n"

            if data["ahead_by"] > 0:
                result += f"## Commits in {params.head} (not in {params.base})\n\n"
                for commit in data["commits"][:5]:
                    sha = commit["sha"][:7]
                    msg = commit["commit"]["message"].split("\n")[0]
                    result += f"- {sha}: {msg}\n"
                if data["total_commits"] > 5:
                    result += f"\n*...and {data['total_commits'] - 5} more commits*\n"

            return result

    except Exception as e:
        return _handle_api_error(e)
