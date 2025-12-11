import asyncio
import warnings

import pytest


@pytest.fixture(autouse=True, scope="function")
async def cleanup_event_loop():
    """Ensure clean event loop state after each async test."""
    yield
    await asyncio.sleep(0)


@pytest.fixture(autouse=True, scope="function")
async def cleanup_deno_pool():
    """Clean up Deno pool after tests that use it."""
    yield
    try:
        from src.github_mcp.utils.deno_pool import _pool
        if _pool:
            await _pool.close()
    except ImportError:
        pass


def pytest_configure(config):
    """Suppress asyncio event loop warnings."""
    warnings.filterwarnings(
        "ignore",
        message=".*Event loop is closed.*",
        category=pytest.PytestUnraisableExceptionWarning,
    )
