"""Pytest configuration for test utilities."""

import pytest


@pytest.fixture(autouse=True, scope="function")
async def cleanup_deno_pool():
    """Ensure the global Deno pool is closed before the event loop ends."""
    yield
    try:
        from src.github_mcp.utils.deno_pool import close_pool
        await close_pool()
    except Exception:
        # If pool is already closed or not available, ignore
        pass
