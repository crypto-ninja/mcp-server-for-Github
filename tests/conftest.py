"""Pytest configuration and fixtures."""

import warnings
import pytest


def pytest_configure(config):
    """Configure pytest settings."""
    # Suppress asyncio subprocess cleanup warning on Linux
    # This is a known Python/asyncio timing issue where subprocess transports
    # get garbage collected after the event loop closes. It's benign -
    # our cleanup fixtures DO run, but GC timing on Linux differs from Windows.
    # See: https://github.com/python/cpython/issues/88050
    warnings.filterwarnings(
        "ignore",
        message=r".*Event loop is closed.*",
        category=pytest.PytestUnraisableExceptionWarning,
    )


@pytest.fixture(autouse=True)
async def cleanup_deno_pool():
    """Clean up Deno pool after each test to prevent resource leaks."""
    yield
    from src.github_mcp.utils.deno_pool import close_pool

    await close_pool()
