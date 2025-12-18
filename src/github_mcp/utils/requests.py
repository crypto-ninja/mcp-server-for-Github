"""GitHub API request utilities."""

from typing import Optional, Dict, Any
from .github_client import GhClient
from ..auth.github_app import get_auth_token


async def _get_auth_token_fallback(param_token: Optional[str] = None) -> Optional[str]:
    """
    Get authentication token with fallback logic.

    Priority:
    1. Parameter token (if provided)
    2. GitHub App token (if configured)
    3. Personal Access Token (if configured)

    Args:
        param_token: Token from function parameter

    Returns:
        Token string or None
    """
    if param_token:
        return param_token
    return await get_auth_token()


async def _make_github_request(
    endpoint: str,
    method: str = "GET",
    token: Optional[str] = None,
    skip_cache_headers: bool = False,
    **kwargs,
) -> Any:
    """
    Reusable function for all GitHub API calls using a shared pooled client.

    Returns parsed JSON. For 304, returns cached JSON data when available.
    """
    headers = kwargs.pop("headers", None)
    params = kwargs.pop("params", None)
    json_body = kwargs.pop("json", None)
    data_body = kwargs.pop("data", None)

    # If no token provided, try GitHub App first, then fall back to PAT
    if token is None:
        token = await get_auth_token()

    client = GhClient.instance()
    response = await client.request(
        method=method,
        path=f"/{endpoint}",
        token=token,
        params=params,
        headers=headers,
        json=json_body,
        data=data_body,
        skip_cache_headers=skip_cache_headers,
    )
    # Handle 304 Not Modified by returning cached JSON data when present.
    if response.status_code == 304:
        cached_data = getattr(response, "_cached_json", None)
        if cached_data is not None:
            return cached_data
        # Fallback marker if, for some reason, we received a 304
        # without any cached JSON (should be rare).
        return {"_from_cache": True, "_no_data": True}
    response.raise_for_status()
    # Some endpoints (DELETE) may return empty body
    if response.content is None or len(response.content) == 0:
        return {"success": True}
    return response.json()


async def _make_graphql_request(
    query: str, variables: Optional[Dict[str, Any]] = None, token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Make a GraphQL request to GitHub API.

    Args:
        query: GraphQL query string
        variables: Optional variables for the query
        token: Optional authentication token

    Returns:
        GraphQL response data
    """
    if token is None:
        token = await get_auth_token()

    from .graphql_client import GraphQLClient

    client = GraphQLClient()
    return await client.query(token, query, variables)
