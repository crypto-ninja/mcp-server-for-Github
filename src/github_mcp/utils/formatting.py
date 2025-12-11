"""Response formatting utilities for GitHub MCP Server."""

from typing import Optional
from datetime import datetime
import json

# Character limit for responses
CHARACTER_LIMIT = 50000


def _format_timestamp(timestamp: str) -> str:
    """Convert ISO timestamp to human-readable format."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
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
    truncation_notice = (
        f"\n\n[Response truncated at {CHARACTER_LIMIT} characters"
    )
    
    if data_count:
        truncation_notice += " - showing partial results. Use pagination or filters to see more."
    else:
        truncation_notice += ". Use filters or pagination to reduce result size."
    
    truncation_notice += "]"
    
    return truncated + truncation_notice

