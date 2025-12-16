"""Minimal setup.py for backward compatibility with older pip versions."""

from setuptools import setup, find_packages

# All metadata is defined in pyproject.toml.
# This file exists only for compatibility with older tools.

setup(
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
