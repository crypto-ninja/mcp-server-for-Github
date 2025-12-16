"""Health check and diagnostic utilities for GitHub MCP Server."""

import os
import json
from typing import Dict, Any
from ..server import check_deno_installed
from ..auth.github_app import clear_token_cache


async def health_check() -> str:
    """
    Check server health status.

    Returns:
        JSON string with health status, version, authentication, and Deno info
    """
    # Get version from package or default
    try:
        import importlib.metadata

        version = importlib.metadata.version("github-mcp-server")
    except Exception:
        version = "2.5.4"

    # Check authentication
    has_pat = bool(os.getenv("GITHUB_TOKEN"))
    has_app_id = bool(os.getenv("GITHUB_APP_ID"))
    has_app_installation = bool(os.getenv("GITHUB_APP_INSTALLATION_ID"))
    has_app_key = bool(os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")) or bool(
        os.getenv("GITHUB_APP_PRIVATE_KEY")
    )

    auth_method = None
    if has_app_id and has_app_installation and has_app_key:
        auth_method = "github_app"
    elif has_pat:
        auth_method = "pat"

    # Check Deno
    deno_available, deno_info = check_deno_installed()

    health_data: Dict[str, Any] = {
        "status": "healthy",
        "version": version,
        "authentication": {
            "method": auth_method,
            "pat_configured": has_pat,
            "app_configured": has_app_id and has_app_installation and has_app_key,
            "status": auth_method if auth_method else "none",
        },
        "deno": {
            "available": deno_available,
            "version": deno_info if deno_available else None,
        },
    }

    return json.dumps(health_data, indent=2)


async def github_clear_token_cache() -> str:
    """
    Clear GitHub App installation token cache.

    Returns:
        Confirmation message
    """
    has_app_id = bool(os.getenv("GITHUB_APP_ID"))
    has_app_installation = bool(os.getenv("GITHUB_APP_INSTALLATION_ID"))
    has_app_key = bool(os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")) or bool(
        os.getenv("GITHUB_APP_PRIVATE_KEY")
    )

    if has_app_id and has_app_installation and has_app_key:
        clear_token_cache()
        return "✅ GitHub App token cache cleared. Next API call will use a fresh token with current permissions."
    else:
        return (
            "ℹ️ GitHub App not configured. Using PAT authentication (no cache to clear)."
        )
