"""Repository management tools for GitHub MCP Server."""

from typing import Optional, Dict, Any, List, Union, cast
import json
import httpx

from ..models.inputs import (
    RepoInfoInput,
    CreateRepositoryInput,
    UpdateRepositoryInput,
    ArchiveRepositoryInput,
    ListUserReposInput,
    ListOrgReposInput,
)
from ..models.enums import ResponseFormat
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response
from ..utils.compact_format import format_response


async def github_get_repo_info(params: RepoInfoInput) -> str:
    """
    Retrieve detailed information about a GitHub repository.

    This tool fetches comprehensive metadata about a repository including description,
    statistics, languages, and ownership information. It does NOT modify the repository.

    Args:
        params (RepoInfoInput): Validated input parameters containing:
            - owner (str): Repository owner username or organization
            - repo (str): Repository name
            - token (Optional[str]): GitHub token for authenticated requests
            - response_format (ResponseFormat): Output format preference

    Returns:
        str: Repository information in requested format (JSON or Markdown)

    Examples:
        - Use when: "Tell me about the tensorflow repository"
        - Use when: "What's the license for facebook/react?"
        - Use when: "Get details on microsoft/vscode"

    Error Handling:
        - Returns error if repository doesn't exist (404)
        - Returns error if authentication required but not provided (403)
        - Includes actionable suggestions for resolving errors
    """
    try:
        data: Dict[str, Any] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}", token=params.token
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result)

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(data, ResponseFormat.COMPACT.value, "repo")
            return json.dumps(compact_data, indent=2)

        # Markdown format
        markdown = f"""# {data["full_name"]}

**Description:** {data["description"] or "No description provided"}

## Statistics
- ⭐ Stars: {data["stargazers_count"]:,}
- 🍴 Forks: {data["forks_count"]:,}
- 👁️ Watchers: {data["watchers_count"]:,}
- 🐛 Open Issues: {data["open_issues_count"]:,}

## Details
- **Owner:** {data["owner"]["login"]} ({data["owner"]["type"]})
- **Created:** {_format_timestamp(data["created_at"])}
- **Last Updated:** {_format_timestamp(data["updated_at"])}
- **Default Branch:** {data["default_branch"]}
- **Language:** {data["language"] or "Not specified"}
- **License:** {data["license"]["name"] if data.get("license") else "No license"}
- **Topics:** {", ".join(data.get("topics", [])) or "None"}

## URLs
- **Homepage:** {data["homepage"] or "None"}
- **Clone URL:** {data["clone_url"]}
- **Repository:** {data["html_url"]}

## Status
- Archived: {"Yes" if data["archived"] else "No"}
- Disabled: {"Yes" if data["disabled"] else "No"}
- Private: {"Yes" if data["private"] else "No"}
- Fork: {"Yes" if data["fork"] else "No"}
"""

        return _truncate_response(markdown)

    except Exception as e:
        return _handle_api_error(e)


async def github_create_repository(params: CreateRepositoryInput) -> str:
    """
    Create a new repository for the authenticated user or in an organization.
    """
    auth_token = await _get_auth_token_fallback(params.token)

    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        body = {
            "name": params.name,
            "description": params.description,
            "private": params.private,
            "auto_init": params.auto_init,
            "allow_squash_merge": params.allow_squash_merge,
            "allow_merge_commit": params.allow_merge_commit,
            "allow_rebase_merge": params.allow_rebase_merge,
            "delete_branch_on_merge": params.delete_branch_on_merge,
            "allow_auto_merge": params.allow_auto_merge,
            "allow_update_branch": params.allow_update_branch,
        }
        if params.gitignore_template:
            body["gitignore_template"] = params.gitignore_template
        if params.license_template:
            body["license_template"] = params.license_template
        if params.squash_merge_commit_title:
            body["squash_merge_commit_title"] = params.squash_merge_commit_title
        if params.squash_merge_commit_message:
            body["squash_merge_commit_message"] = params.squash_merge_commit_message

        if params.owner:
            endpoint = f"orgs/{params.owner}/repos"
        else:
            endpoint = "user/repos"

        data = await _make_github_request(
            endpoint, method="POST", token=auth_token, json=body
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


async def github_update_repository(params: UpdateRepositoryInput) -> str:
    """
    Update repository settings such as description, visibility, and features.
    """
    auth_token = await _get_auth_token_fallback(params.token)

    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for updating repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        body: Dict[str, Any] = {}
        for field in [
            "name",
            "description",
            "homepage",
            "private",
            "has_issues",
            "has_projects",
            "has_wiki",
            "default_branch",
            "archived",
            "allow_squash_merge",
            "allow_merge_commit",
            "allow_rebase_merge",
            "delete_branch_on_merge",
            "allow_auto_merge",
            "allow_update_branch",
            "squash_merge_commit_title",
            "squash_merge_commit_message",
        ]:
            value = getattr(params, field)
            if value is not None:
                body[field] = value
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}",
            method="PATCH",
            token=auth_token,
            json=body,
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


async def github_archive_repository(params: ArchiveRepositoryInput) -> str:
    """
    Archive or unarchive a repository by toggling the archived flag.
    """
    auth_token = await _get_auth_token_fallback(params.token)

    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for archiving repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        body = {"archived": params.archived}
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}",
            method="PATCH",
            token=auth_token,
            json=body,
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


async def github_list_user_repos(params: ListUserReposInput) -> str:
    """
    List repositories for the authenticated user or a specified user.
    """
    # When username is omitted, we must use the authenticated endpoint and require auth
    auth_token: Optional[str] = None
    if params.username is None:
        auth_token = await _get_auth_token_fallback(params.token)
        if not auth_token:
            return json.dumps(
                {
                    "error": "Authentication required",
                    "message": "GitHub token required for listing your own repositories. Set GITHUB_TOKEN or pass a token, or provide a username to list public repos.",
                    "success": False,
                },
                indent=2,
            )
    else:
        auth_token = params.token

    try:
        query: Dict[str, Any] = {}
        if params.type:
            query["type"] = params.type
        if params.sort:
            query["sort"] = params.sort
        if params.direction:
            query["direction"] = params.direction
        if params.limit:
            query["per_page"] = params.limit
        if params.page:
            query["page"] = params.page

        if params.username:
            endpoint = f"users/{params.username}/repos"
        else:
            endpoint = "user/repos"

        data = await _make_github_request(endpoint, token=auth_token, params=query)

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(data, ResponseFormat.COMPACT.value, "repo")
            return json.dumps(compact_data, indent=2)

        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


async def github_list_org_repos(params: ListOrgReposInput) -> str:
    """
    List repositories for an organization.
    """
    try:
        query: Dict[str, Any] = {}
        if params.type:
            query["type"] = params.type
        if params.sort:
            query["sort"] = params.sort
        if params.direction:
            query["direction"] = params.direction
        if params.limit:
            query["per_page"] = params.limit
        if params.page:
            query["page"] = params.page

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            f"orgs/{params.org}/repos", token=params.token, params=query
        )
        # GitHub API returns a list for org repos endpoint
        repos_list: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                repos_list, ResponseFormat.COMPACT.value, "repo"
            )
            return json.dumps(compact_data, indent=2)

        return json.dumps(repos_list, indent=2)
    except Exception as e:
        return _handle_api_error(e)
