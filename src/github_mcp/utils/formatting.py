"""Response formatting utilities for GitHub MCP Server."""

from typing import Any, Dict, Optional
from datetime import datetime
import json

# Character limit for responses
CHARACTER_LIMIT = 50000


def _format_timestamp(timestamp: str) -> str:
    """Convert ISO timestamp to human-readable format."""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return timestamp


def _truncate_response(response: str, data_count: Optional[int] = None) -> str:
    """
    Truncate response if it exceeds CHARACTER_LIMIT.

    Args:
        response: The response string to check
        data_count: Optional count of items in the response

    Returns:
        Original or truncated response with notice
    """
    if len(response) <= CHARACTER_LIMIT:
        return response

    # If this looks like JSON, return a small structured warning instead of truncating
    # to avoid emitting invalid JSON that downstream clients try to parse.
    stripped = response.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        warning = {
            "error": True,
            "message": "Response truncated due to size. Use pagination or filters to reduce result size.",
            "truncated": True,
            "character_limit": CHARACTER_LIMIT,
        }
        if data_count is not None:
            warning["data_count"] = data_count
        return json.dumps(warning, indent=2)

    truncated = response[:CHARACTER_LIMIT]
    truncation_notice = f"\n\n[Response truncated at {CHARACTER_LIMIT} characters"

    if data_count:
        truncation_notice += (
            " - showing partial results. Use pagination or filters to see more."
        )
    else:
        truncation_notice += ". Use filters or pagination to reduce result size."

    truncation_notice += "]"

    return truncated + truncation_notice


def _slim_code_search_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Slim a code search result item to essential fields."""
    slim: Dict[str, Any] = {
        "name": item.get("name"),
        "path": item.get("path"),
        "sha": item.get("sha"),
        "html_url": item.get("html_url"),
        "score": item.get("score"),
    }
    if "repository" in item:
        repo = item["repository"]
        slim["repository"] = {
            "full_name": repo.get("full_name"),
            "html_url": repo.get("html_url"),
            "owner": repo.get("owner", {}).get("login"),
        }
    if "text_matches" in item:
        slim["text_matches"] = item["text_matches"]
    return slim


def _slim_repository_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Slim a repository search result item to essential fields."""
    return {
        "id": item.get("id"),
        "full_name": item.get("full_name"),
        "html_url": item.get("html_url"),
        "description": item.get("description"),
        "stargazers_count": item.get("stargazers_count"),
        "forks_count": item.get("forks_count"),
        "language": item.get("language"),
        "topics": item.get("topics", [])[:10],
        "updated_at": item.get("updated_at"),
        "created_at": item.get("created_at"),
        "owner": {
            "login": item.get("owner", {}).get("login"),
            "html_url": item.get("owner", {}).get("html_url"),
        },
        "visibility": item.get("visibility"),
        "default_branch": item.get("default_branch"),
    }


def _slim_issue_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Slim an issue search result item to essential fields."""
    slim: Dict[str, Any] = {
        "number": item.get("number"),
        "title": item.get("title"),
        "html_url": item.get("html_url"),
        "state": item.get("state"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "comments": item.get("comments"),
        "body": item.get("body", "")[:500] if item.get("body") else None,
    }
    if "user" in item:
        slim["user"] = {
            "login": item["user"].get("login"),
            "html_url": item["user"].get("html_url"),
        }
    if "labels" in item:
        slim["labels"] = [
            {"name": label.get("name"), "color": label.get("color")}
            for label in item.get("labels", [])
        ]
    if "assignees" in item:
        slim["assignees"] = [
            {"login": a.get("login")} for a in item.get("assignees", [])
        ]
    # Extract repo from URL if present
    html_url = item.get("html_url", "")
    if "/issues/" in html_url or "/pull/" in html_url:
        parts = html_url.split("/")
        if len(parts) >= 5:
            slim["repository"] = f"{parts[3]}/{parts[4]}"
    return slim


def _slim_user_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Slim a user search result item to essential fields."""
    return {
        "login": item.get("login"),
        "id": item.get("id"),
        "html_url": item.get("html_url"),
        "avatar_url": item.get("avatar_url"),
        "type": item.get("type"),
        "score": item.get("score"),
    }


def _slim_search_response(
    search_result: Dict[str, Any], item_type: str
) -> Dict[str, Any]:
    """
    Slim a GitHub search API response to reduce size.

    Args:
        search_result: Raw GitHub search API response
        item_type: One of 'code', 'repository', 'issue', 'user'

    Returns:
        Slimmed response with only essential fields
    """
    slim_funcs = {
        "code": _slim_code_search_item,
        "repository": _slim_repository_item,
        "issue": _slim_issue_item,
        "user": _slim_user_item,
    }

    slim_func = slim_funcs.get(item_type)
    if not slim_func:
        return search_result  # Return as-is if unknown type

    items = search_result.get("items", [])
    return {
        "total_count": search_result.get("total_count", 0),
        "incomplete_results": search_result.get("incomplete_results", False),
        "items": [slim_func(item) for item in items],
    }
