"""Labels tools for GitHub MCP Server."""

from typing import Dict, Any, List, Union, cast
import json

from ..models.inputs import (
    CreateLabelInput,
    DeleteLabelInput,
    ListLabelsInput,
)
from ..models.enums import ResponseFormat
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.compact_format import format_response


async def github_list_labels(params: ListLabelsInput) -> str:
    """
    List all labels in a repository.
    """
    try:
        query: Dict[str, Any] = {}
        if params.limit:
            query["per_page"] = params.limit
        if params.page:
            query["page"] = params.page

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/labels",
            token=params.token,
            params=query,
        )
        # GitHub API returns a list for labels endpoint
        labels_list: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                labels_list, ResponseFormat.COMPACT.value, "label"
            )
            return json.dumps(compact_data, indent=2)

        return json.dumps(labels_list, indent=2)
    except Exception as e:
        return _handle_api_error(e)


async def github_create_label(params: CreateLabelInput) -> str:
    """
    Create a new label in a repository.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating labels. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload: Dict[str, Any] = {
            "name": params.name,
            "color": params.color.lstrip("#"),
        }
        if params.description is not None:
            payload["description"] = params.description

        data: Dict[str, Any] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/labels",
            method="POST",
            token=auth_token,
            json=payload,
        )
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


async def github_delete_label(params: DeleteLabelInput) -> str:
    """
    Delete a label from a repository.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for deleting labels. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/labels/{params.name}",
            method="DELETE",
            token=auth_token,
        )
        return json.dumps(
            {
                "success": True,
                "message": f"Label '{params.name}' deleted from {params.owner}/{params.repo}.",
            },
            indent=2,
        )
    except Exception as e:
        return _handle_api_error(e)
