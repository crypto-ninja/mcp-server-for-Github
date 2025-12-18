"""Collaborators tools for GitHub MCP Server."""

import json
from typing import Dict, Any, List, Union, cast

from ..models.inputs import (
    CheckCollaboratorInput,
    ListRepoCollaboratorsInput,
    ListRepoTeamsInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _truncate_response


async def github_list_repo_collaborators(params: ListRepoCollaboratorsInput) -> str:
    """
    List collaborators for a repository.

    Retrieves all users who have access to the repository, including
    their permission levels. Supports filtering by affiliation and permission.

    Args:
        params (ListRepoCollaboratorsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - affiliation (str): Filter by affiliation (default: 'all')
            - permission (Optional[str]): Filter by permission level
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of collaborators with permissions

    Examples:
        - Use when: "Show me all collaborators"
        - Use when: "List users with admin access"
    """
    try:
        params_dict = {
            "affiliation": params.affiliation,
            "per_page": params.per_page,
            "page": params.page,
        }
        if params.permission:
            params_dict["permission"] = params.permission

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/collaborators",
            token=params.token,
            params=params_dict,
        )

        # GitHub API returns a list for collaborators endpoint
        collaborators_list: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(collaborators_list, indent=2)
            return _truncate_response(result, len(collaborators_list))

        markdown = f"# Collaborators for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Collaborators:** {len(collaborators_list)}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(collaborators_list)} collaborators\n\n"

        if not collaborators_list:
            markdown += "No collaborators found.\n"
        else:
            for collaborator in collaborators_list:
                markdown += f"## {collaborator['login']}\n"
                permissions = collaborator.get("permissions", {})
                markdown += f"- **Admin:** {permissions.get('admin', False)}\n"
                markdown += f"- **Push:** {permissions.get('push', False)}\n"
                markdown += f"- **Pull:** {permissions.get('pull', False)}\n"
                markdown += f"- **URL:** {collaborator['html_url']}\n\n"

        return _truncate_response(markdown, len(collaborators_list))

    except Exception as e:
        return _handle_api_error(e)


async def github_check_collaborator(params: CheckCollaboratorInput) -> str:
    """
    Check if a user is a collaborator on a repository.

    Returns 204 if the user is a collaborator, 404 if not. Useful for
    permission checks before performing operations.

    Args:
        params (CheckCollaboratorInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - username (str): GitHub username to check
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Collaborator status (is collaborator or not)

    Examples:
        - Use when: "Check if user123 is a collaborator"
        - Use when: "Verify user has access to this repo"
    """
    try:
        from ..utils.github_client import GhClient

        auth_token = await _get_auth_token_fallback(params.token)
        client = GhClient.instance()

        response = await client.request(
            "GET",
            f"repos/{params.owner}/{params.repo}/collaborators/{params.username}",
            token=auth_token,
            headers={"Accept": "application/vnd.github.v3+json"},
        )

        is_collaborator = response.status_code == 204

        payload = {
            "is_collaborator": is_collaborator,
            "username": params.username,
            "repository": f"{params.owner}/{params.repo}",
        }

        if params.response_format in (
            ResponseFormat.JSON,
            ResponseFormat.COMPACT,
        ):
            # Compact matches JSON shape here; response is already minimal
            return json.dumps(payload, indent=2)

        markdown = f"# Collaborator Check: {params.username}\n\n"
        markdown += f"- **Repository:** {params.owner}/{params.repo}\n"
        markdown += (
            f"- **Is Collaborator:** {'✅ Yes' if is_collaborator else '❌ No'}\n"
        )

        return markdown

    except Exception as e:
        # 404 means not a collaborator, which is valid
        if (
            hasattr(e, "response")
            and hasattr(e.response, "status_code")
            and e.response.status_code == 404
        ):
            payload = {
                "is_collaborator": False,
                "username": params.username,
                "repository": f"{params.owner}/{params.repo}",
            }
            if params.response_format in (
                ResponseFormat.JSON,
                ResponseFormat.COMPACT,
            ):
                return json.dumps(payload, indent=2)
            return (
                f"# Collaborator Check: {params.username}\n\n"
                f"- **Repository:** {params.owner}/{params.repo}\n"
                "- **Is Collaborator:** ❌ No\n"
            )
        return _handle_api_error(e)


async def github_list_repo_teams(params: ListRepoTeamsInput) -> str:
    """
    List teams with access to a repository.

    Retrieves all teams that have been granted access to the repository,
    including their permission levels.

    Args:
        params (ListRepoTeamsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of teams with permissions

    Examples:
        - Use when: "Show me all teams with access"
        - Use when: "List teams that can access this repo"
    """
    try:
        params_dict = {"per_page": params.per_page, "page": params.page}

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/teams",
            token=params.token,
            params=params_dict,
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))

        markdown = f"# Teams with Access to {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Teams:** {len(data)}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(data)} teams\n\n"

        if not data:
            markdown += "No teams found.\n"
        else:
            for team in data:
                markdown += f"## {team['name']}\n"
                markdown += f"- **ID:** {team['id']}\n"
                markdown += f"- **Permission:** {team.get('permission', 'N/A')}\n"
                markdown += f"- **Slug:** {team.get('slug', 'N/A')}\n"
                markdown += f"- **URL:** {team['html_url']}\n\n"

        return _truncate_response(markdown, len(data))

    except Exception as e:
        return _handle_api_error(e)
