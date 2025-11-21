"""
Command-line utilities for GitHub MCP Server debugging and diagnostics.

These utilities are NOT exposed as MCP tools - they're for developers and operators
to diagnose issues, check health, and manage the server.
"""

"""
Command-line utilities for GitHub MCP Server debugging and diagnostics.

These utilities are NOT exposed as MCP tools - they're for developers and operators
to diagnose issues, check health, and manage the server.
"""

import asyncio
import json
import click
import os
import sys
from pathlib import Path

# Add project root to path to import github_mcp
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import functions (these are now internal, not MCP tools)
import github_mcp
from auth.github_app import clear_token_cache


@click.group()
def cli():
    """GitHub MCP Server diagnostic utilities."""
    pass


@cli.command()
def health():
    """Check server health status."""
    try:
        result = asyncio.run(github_mcp.health_check())
        # Try to pretty-print JSON if it's JSON
        try:
            data = json.loads(result)
            click.echo(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            click.echo(result)
    except Exception as e:
        click.echo(f"❌ Error checking health: {e}", err=True)
        sys.exit(1)


@cli.command()
def clear_cache():
    """Clear GitHub App installation token cache."""
    has_app_id = bool(os.getenv("GITHUB_APP_ID"))
    has_app_installation = bool(os.getenv("GITHUB_APP_INSTALLATION_ID"))
    has_app_key = bool(os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")) or bool(os.getenv("GITHUB_APP_PRIVATE_KEY"))
    
    if has_app_id and has_app_installation and has_app_key:
        clear_token_cache()
        click.echo("✅ GitHub App token cache cleared. Next API call will use a fresh token with current permissions.")
    else:
        click.echo("ℹ️ GitHub App not configured. Using PAT authentication (no cache to clear).")


@cli.command()
def check_deno():
    """Verify Deno installation."""
    installed, info = github_mcp.check_deno_installed()
    if installed:
        click.echo(f"✅ Deno is installed: {info}")
    else:
        click.echo(f"❌ Deno not found: {info}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()

