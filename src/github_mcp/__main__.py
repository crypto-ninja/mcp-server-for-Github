"""
Entry point for running the MCP server as a module.

This allows: python -m github_mcp.server
"""

from .server import run

if __name__ == "__main__":
    run()
