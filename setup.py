#!/usr/bin/env python3
"""
Setup script for GitHub MCP Server.
"""

from setuptools import setup
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="github-mcp-server",
    version="2.1.0",
    author="MCP Labs",
    author_email="licensing@mcplabs.co.uk",
    description="A comprehensive Model Context Protocol server for GitHub integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crypto-ninja/github-mcp-server",
    py_modules=["github_mcp"],
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.0.0",
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="mcp model-context-protocol github api ai assistant claude",
    project_urls={
        "Bug Reports": "https://github.com/crypto-ninja/github-mcp-server/issues",
        "Source": "https://github.com/crypto-ninja/github-mcp-server",
        "Documentation": "https://github.com/crypto-ninja/github-mcp-server/blob/main/README.md",
        "Website": "https://mcplabs.co.uk",
        "Licensing": "https://github.com/crypto-ninja/github-mcp-server/blob/main/LICENSING.md",
    },
    entry_points={
        "console_scripts": [
            "github-mcp=github_mcp:main",
        ],
    },
)
