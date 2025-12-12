"""
Smoke tests for GitHub MCP Server
Verifies basic imports and tool registration
"""

import importlib
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_import_server():
    """Test that the main server module can be imported"""
    from src.github_mcp.server import mcp

    assert mcp is not None, "Module should have 'mcp' FastMCP instance"


def test_has_execute_code_tool():
    """Test that the revolutionary execute_code tool exists"""
    from src.github_mcp.server import execute_code

    assert execute_code is not None, "Module should have 'execute_code' tool"


def test_has_core_tools():
    """Test that core GitHub tools exist"""
    from src.github_mcp.tools import (
        github_get_repo_info,
        github_list_issues,
        github_create_pull_request,
        github_get_file_content,
    )

    # Test a few key tools from different categories
    core_tools = [
        github_get_repo_info,
        github_list_issues,
        github_create_pull_request,
        github_get_file_content,
    ]

    for tool in core_tools:
        assert tool is not None, f"Tool {tool.__name__} should exist"


def test_code_first_mode_env():
    """Test that CODE_FIRST_MODE can be imported"""
    from src.github_mcp.server import CODE_FIRST_MODE

    assert CODE_FIRST_MODE is not None, "Module should have CODE_FIRST_MODE variable"


def test_deno_runtime_module():
    """Test that deno_runtime module exists"""
    try:
        mod = importlib.import_module("src.github_mcp.deno_runtime")
        assert hasattr(mod, "get_runtime"), (
            "deno_runtime should have get_runtime function"
        )
    except ImportError:
        # Deno runtime might not be importable without Deno installed
        pass
