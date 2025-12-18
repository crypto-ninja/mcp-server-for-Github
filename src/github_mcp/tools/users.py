"""Users tools for GitHub MCP Server."""

from typing import Dict, Any, List, Union, cast
import json

from ..models.inputs import (
    GetAuthenticatedUserInput,
    GetUserInfoInput,
    SearchUsersInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import (
    _format_timestamp,
    _truncate_response,
    _slim_search_response,
)
from ..utils.compact_format import format_response


async def github_get_user_info(params: GetUserInfoInput) -> str:
    """
    Retrieve information about a GitHub user or organization.

    Fetches profile information including bio, location, public repos,
    followers, and activity statistics.

    Args:
        params (GetUserInfoInput): Validated input parameters containing:
            - username (str): GitHub username
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: User profile information in requested format

    Examples:
        - Use when: "Get info about user torvalds"
        - Use when: "Show me the profile for facebook organization"
        - Use when: "Look up GitHub user details"

    Error Handling:
        - Returns error if user not found (404)
        - Handles both users and organizations
        - Returns appropriate data for account type
    """
    try:
        data: Dict[str, Any] = await _make_github_request(
            f"users/{params.username}", token=params.token
        )

        # Compact JSON response with only key identity fields
        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "user"
            )
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result)

        # Markdown format
        markdown = f"# {data['name'] or data['login']}\n\n"

        if data.get("bio"):
            markdown += f"**Bio:** {data['bio']}\n\n"

        markdown += f"**Username:** @{data['login']}\n"
        markdown += f"**Type:** {data['type']}\n"

        if data.get("company"):
            markdown += f"**Company:** {data['company']}\n"

        if data.get("location"):
            markdown += f"**Location:** {data['location']}\n"

        if data.get("email"):
            markdown += f"**Email:** {data['email']}\n"

        if data.get("blog"):
            markdown += f"**Website:** {data['blog']}\n"

        if data.get("twitter_username"):
            markdown += f"**Twitter:** @{data['twitter_username']}\n"

        markdown += "\n## Statistics\n"
        markdown += f"- 📦 **Public Repos:** {data['public_repos']:,}\n"
        markdown += f"- 👥 **Followers:** {data['followers']:,}\n"
        markdown += f"- 👤 **Following:** {data['following']:,}\n"

        if data.get("public_gists") is not None:
            markdown += f"- 📝 **Public Gists:** {data['public_gists']:,}\n"

        markdown += f"\n**Joined:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"**Last Updated:** {_format_timestamp(data['updated_at'])}\n"
        markdown += f"**Profile URL:** {data['html_url']}\n"

        return _truncate_response(markdown)

    except Exception as e:
        return _handle_api_error(e)


async def github_get_authenticated_user(params: GetAuthenticatedUserInput) -> str:
    """
    Get the authenticated user's profile (the 'me' endpoint).
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for retrieving the authenticated user. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        data: Dict[str, Any] = await _make_github_request("user", token=auth_token)

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(data, ResponseFormat.COMPACT.value, "user")
            return json.dumps(compact_data, indent=2)

        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


async def github_search_users(params: SearchUsersInput) -> str:
    """
    Search for GitHub users using the public search API.
    """
    try:
        query_params: Dict[str, Any] = {
            "q": params.query,
            "per_page": params.limit,
            "page": params.page,
        }
        if params.sort:
            query_params["sort"] = params.sort
        if params.order:
            from enum import Enum

            query_params["order"] = (
                params.order.value if isinstance(params.order, Enum) else params.order
            )

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            "search/users", token=params.token, params=query_params
        )
        # Search API returns dict with 'items' list
        search_result: Dict[str, Any] = (
            cast(Dict[str, Any], data)
            if isinstance(data, dict)
            else {"total_count": 0, "items": []}
        )
        slim_result = _slim_search_response(search_result, "user")

        if params.response_format == ResponseFormat.COMPACT:
            compact_items = format_response(
                slim_result.get("items", []), ResponseFormat.COMPACT.value, "user"
            )
            return json.dumps(
                {
                    "total_count": slim_result.get("total_count", 0),
                    "items": compact_items,
                },
                indent=2,
            )

        return json.dumps(slim_result, indent=2)
    except Exception as e:
        return _handle_api_error(e)
