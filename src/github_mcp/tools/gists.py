"""Gists tools for GitHub MCP Server."""

from typing import Optional, Dict, Any, List, Union, cast
import json

from ..models.inputs import (
    CreateGistInput,
    GetGistInput,
    ListGistsInput,
    UpdateGistInput,
    DeleteGistInput,
)
from ..models.enums import ResponseFormat
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.compact_format import format_response


async def github_list_gists(params: ListGistsInput) -> str:
    """
    List gists for the authenticated user or a specified user.

    If a username is provided, public gists for that user are returned and
    authentication is optional. If username is omitted, the authenticated
    user's gists are listed and a token is required.
    """
    # Only require auth when listing for the authenticated user
    auth_token: Optional[str] = None
    if params.username is None:
        auth_token = await _get_auth_token_fallback(params.token)
        if not auth_token:
            return json.dumps(
                {
                    "error": "Authentication required",
                    "message": "GitHub token required for listing your own gists. Set GITHUB_TOKEN or pass a token parameter, or provide a username to list public gists.",
                    "success": False,
                },
                indent=2,
            )
    else:
        # Allow anonymous listing of another user's public gists
        auth_token = params.token

    try:
        query: Dict[str, Any] = {}
        if params.since:
            query["since"] = params.since
        if params.limit:
            query["per_page"] = params.limit
        if params.page:
            query["page"] = params.page

        if params.username:
            endpoint = f"users/{params.username}/gists"
        else:
            endpoint = "gists"

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            endpoint, token=auth_token, params=query
        )
        # GitHub API returns a list for gists endpoint
        gists_list: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                gists_list, ResponseFormat.COMPACT.value, "gist"
            )
            return json.dumps(compact_data, indent=2)

        return json.dumps(gists_list, indent=2)
    except Exception as e:
        return _handle_api_error(e)


async def github_get_gist(params: GetGistInput) -> str:
    """
    Get detailed information about a specific gist including files and metadata.
    """
    try:
        data: Dict[str, Any] = await _make_github_request(
            f"gists/{params.gist_id}", token=params.token
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(data, ResponseFormat.COMPACT.value, "gist")
            return json.dumps(compact_data, indent=2)

        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


async def github_create_gist(params: CreateGistInput) -> str:
    """
    Create a new gist with one or more files.

    Requires authentication with a token that has gist scope.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating gists. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        files_payload: Dict[str, Dict[str, str]] = {}
        for filename, file_def in params.files.items():
            files_payload[filename] = {"content": file_def.content}

        payload: Dict[str, Any] = {
            "files": files_payload,
            "public": bool(params.public),
        }
        if params.description is not None:
            payload["description"] = params.description

        data: Dict[str, Any] = await _make_github_request(
            "gists", method="POST", token=auth_token, json=payload
        )

        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


async def github_update_gist(params: UpdateGistInput) -> str:
    """
    Update an existing gist's description and files.

    To delete a file, set its value to null in the files mapping.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for updating gists. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload: Dict[str, Any] = {}
        if params.description is not None:
            payload["description"] = params.description

        if params.files is not None:
            files_payload: Dict[str, Any] = {}
            for filename, file_def in params.files.items():
                if file_def is None:
                    # Delete this file from the gist
                    files_payload[filename] = None
                else:
                    files_payload[filename] = {"content": file_def.content}
            payload["files"] = files_payload

        data: Dict[str, Any] = await _make_github_request(
            f"gists/{params.gist_id}", method="PATCH", token=auth_token, json=payload
        )

        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


async def github_delete_gist(params: DeleteGistInput) -> str:
    """
    Delete a gist.

    Args:
        params (DeleteGistInput): Validated input parameters containing:
            - gist_id (str): Gist ID to delete
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation message

    Examples:
        - Use when: "Delete gist abc123"
        - Use when: "Remove the old gist"

    Error Handling:
        - Returns error if gist not found (404)
        - Returns error if authentication fails (401/403)
    """
    auth_token = await _get_auth_token_fallback(params.token)

    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for deleting gists. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        await _make_github_request(
            f"gists/{params.gist_id}", method="DELETE", token=auth_token
        )
        return json.dumps(
            {"success": True, "message": f"Gist {params.gist_id} deleted successfully"},
            indent=2,
        )
    except Exception as e:
        return _handle_api_error(e)
