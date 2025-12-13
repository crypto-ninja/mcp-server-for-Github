"""
GitHub MCP Server - Modular Package Structure

This package provides a comprehensive Model Context Protocol server for GitHub integration.

Import directly from submodules:
- Tools: from src.github_mcp.tools import github_get_repo_info
- Models: from src.github_mcp.models import RepoInfoInput
- Utils: from src.github_mcp.utils.health import health_check
"""

# Re-export server components only
from .server import mcp, run, execute_code, CODE_FIRST_MODE

__all__ = [
    "mcp",
    "run",
    "execute_code",
    "CODE_FIRST_MODE",
]

__version__ = "2.5.4"
