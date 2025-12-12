#!/usr/bin/env python3
"""
GitHub MCP Server - Entry Point

This is a simple entry point that imports and runs the MCP server
from the modular structure in src/github_mcp/.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env file (needed before imports)
SCRIPT_DIR = Path(__file__).parent
env_path = SCRIPT_DIR / ".env"
load_dotenv(env_path)

# Import license manager for entry point (after dotenv)
from license_manager import check_license_on_startup  # noqa: E402

# Import server components (after dotenv)
from src.github_mcp.server import run  # noqa: E402

# No backward compatibility exports needed - all code uses direct imports
__all__ = [
    "run",
]

# Entry point - maintain original CLI interface
if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(description="GitHub MCP Server")
    parser.add_argument(
        "--auth",
        choices=["pat", "app"],
        default=None,
        help="Authentication mode: pat (default) or app",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default=None,
        help="Transport type",
    )
    parser.add_argument(
        "--port", type=int, default=None, help="Port for HTTP/SSE transport"
    )
    args, unknown = parser.parse_known_args()

    if args.auth:
        os.environ["GITHUB_AUTH_MODE"] = args.auth

    # Run license check first on its own event loop, then start MCP server
    asyncio.run(check_license_on_startup())
    if args.transport in ("http", "sse"):
        run(transport=args.transport, port=(args.port or 8080))
    else:
        run()
