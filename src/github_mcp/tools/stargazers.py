"""Stargazer tools for GitHub MCP Server."""

from typing import Dict, Any, List, Union, cast
import json

from ..models.inputs import (
    ListStargazersInput,
    StarRepositoryInput,
    UnstarRepositoryInput,
)
from ..models.enums import ResponseFormat
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.compact_format import format_response


async def github_list_stargazers(params: ListStargazersInput) -> str:
    """
    List users who have starred a repository.
    """
    try:
        query: Dict[str, Any] = {}
        if params.limit:
            query["per_page"] = params.limit
        if params.page:
            query["page"] = params.page

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/stargazers",
            token=params.token,
            params=query,
        )
        # GitHub API returns a list for stargazers endpoint
        stargazers_list: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                stargazers_list, ResponseFormat.COMPACT.value, "stargazer"
            )
            return json.dumps(compact_data, indent=2)

        return json.dumps(stargazers_list, indent=2)
    except Exception as e:
        return _handle_api_error(e)


async def github_star_repository(params: StarRepositoryInput) -> str:
    """
    Star a repository for the authenticated user.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for starring repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # PUT returns 204 No Content on success
        await _make_github_request(
            f"user/starred/{params.owner}/{params.repo}", method="PUT", token=auth_token
        )
        return json.dumps(
            {
                "success": True,
                "message": f"Repository {params.owner}/{params.repo} has been starred.",
            },
            indent=2,
        )
    except Exception as e:
        return _handle_api_error(e)


async def github_unstar_repository(params: UnstarRepositoryInput) -> str:
    """
    Unstar a repository for the authenticated user.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for unstarring repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        await _make_github_request(
            f"user/starred/{params.owner}/{params.repo}",
            method="DELETE",
            token=auth_token,
        )
        return json.dumps(
            {
                "success": True,
                "message": f"Repository {params.owner}/{params.repo} has been unstarred.",
            },
            indent=2,
        )
    except Exception as e:
        return _handle_api_error(e)
