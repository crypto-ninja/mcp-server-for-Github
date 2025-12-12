"""Error handling utilities for GitHub MCP Server."""

import httpx


def _handle_api_error(e: Exception) -> str:
    """
    Consistent error formatting across all tools.

    Args:
        e: The exception that occurred

    Returns:
        User-friendly error message
    """
    if isinstance(e, httpx.HTTPStatusError):
        status_code = e.response.status_code
        # Avoid echoing full response text to prevent leaking sensitive data
        safe_excerpt = ""
        try:
            txt = e.response.text or ""
            safe_excerpt = (txt[:200] + "...") if len(txt) > 200 else txt
        except Exception:
            safe_excerpt = ""

        if status_code == 401:
            return (
                "Error: Authentication required. Provide a valid token.\n"
                "Hint: Set GITHUB_TOKEN or enable GitHub App auth (GITHUB_APP_ID, PRIVATE_KEY, INSTALLATION_ID)."
            )
        if status_code == 403:
            return (
                "Error: Permission denied.\n"
                "Hint: Check token scopes/installation permissions. Common needs: contents:write for file ops; pull_requests:write for PR ops."
            )
        if status_code == 404:
            return (
                "Error: Resource not found.\n"
                "Hint: Verify owner/repo/number and token access to private repos."
            )
        if status_code == 409:
            return (
                "Error: Conflict.\n"
                "Hint: For file updates, ensure SHA matches current head; for merges, resolve conflicts first."
            )
        if status_code == 422:
            return (
                "Error: Validation failed.\n"
                "Hint: Check required fields and enum values; see API docs for this endpoint."
            )
        if status_code == 429:
            retry_after = e.response.headers.get("Retry-After")
            retry_hint = f"retry after {retry_after}s" if retry_after else "retry later"
            return f"Error: Rate limit exceeded, {retry_hint}. Consider enabling conditional requests and backoff."
        if 500 <= status_code < 600:
            return "Error: GitHub service error. Hint: Retry shortly (transient)."
        return f"Error: GitHub API request failed with status {status_code}. {safe_excerpt}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    elif isinstance(e, httpx.NetworkError):
        return "Error: Network error occurred. Please check your connection."
    return f"Error: Unexpected error occurred: {str(e)}"
