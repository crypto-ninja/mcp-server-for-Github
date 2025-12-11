"""Pytest configuration."""

import warnings
import pytest


def pytest_configure(config):
    """Configure pytest - suppress known benign warnings."""
    warnings.filterwarnings(
        "ignore",
        message=".*Event loop is closed.*",
    )
    warnings.filterwarnings(
        "ignore",
        category=pytest.PytestUnraisableExceptionWarning,
    )
