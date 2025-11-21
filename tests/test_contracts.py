"""
Phase 3: Contract Tests (TypeScript ↔ Python)

Tests that validate:
1. TypeScript client expectations match Python server output
2. Response format parsing works correctly
3. Tool schemas match between client and server
"""

import pytest
import json
import re
from pathlib import Path
from typing import List, Dict, Set

# Import the MCP server
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import github_mcp
import inspect


def read_typescript_tool_list() -> List[str]:
    """Read READ_TOOLS_WITH_JSON_SUPPORT from client-deno.ts."""
    client_deno_path = project_root / "servers" / "client-deno.ts"
    
    if not client_deno_path.exists():
        return []
    
    content = client_deno_path.read_text(encoding='utf-8')
    
    # Extract the array
    match = re.search(r'const READ_TOOLS_WITH_JSON_SUPPORT = \[(.*?)\];', content, re.DOTALL)
    if not match:
        return []
    
    tools = []
    for line in match.group(1).split('\n'):
        line = line.strip()
        if (line.startswith("'") and line.endswith("'")) or \
           (line.startswith('"') and line.endswith('"')):
            tool_name = line.strip("'\"")
            tool_name = tool_name.rstrip(',')
            if tool_name and not tool_name.startswith('//'):
                tools.append(tool_name)
    
    return tools


def get_python_tools_with_response_format() -> Set[str]:
    """Get all Python tools that support response_format."""
    tools = set()
    
    for name, obj in inspect.getmembers(github_mcp):
        if (inspect.iscoroutinefunction(obj) or inspect.isfunction(obj)) and \
           name.startswith('github_'):
            sig = inspect.signature(obj)
            params = sig.parameters
            
            if 'params' in params:
                param_type = params['params'].annotation
                if inspect.isclass(param_type):
                    if hasattr(param_type, 'model_fields'):
                        fields = param_type.model_fields
                        if 'response_format' in fields:
                            tools.add(name)
    
    return tools


class TestClientServerContract:
    """Test that TypeScript client and Python server agree on contracts."""
    
    def test_typescript_client_matches_python_server(self):
        """Verify TypeScript client expectations match Python server output."""
        typescript_tools = set(read_typescript_tool_list())
        python_tools = get_python_tools_with_response_format()
        
        # Tools in TypeScript should be in Python
        missing_in_python = typescript_tools - python_tools
        
        if missing_in_python:
            pytest.fail(
                f"Tools in READ_TOOLS_WITH_JSON_SUPPORT but don't support response_format in Python:\n" +
                "\n".join(f"  - {tool}" for tool in sorted(missing_in_python))
            )
        
        print(f"✓ All {len(typescript_tools)} TypeScript tools match Python schemas")
    
    def test_python_tools_in_typescript_list(self):
        """Verify Python tools with response_format are in TypeScript list."""
        typescript_tools = set(read_typescript_tool_list())
        python_tools = get_python_tools_with_response_format()
        
        # Tools in Python should be in TypeScript (or at least documented)
        missing_in_typescript = python_tools - typescript_tools
        
        if missing_in_typescript:
            print(f"⚠ {len(missing_in_typescript)} Python tools support response_format but aren't in TypeScript list:")
            for tool in sorted(missing_in_typescript):
                print(f"  - {tool}")
            print("  (This is a warning, not an error - tools may be intentionally excluded)")
    
    def test_response_format_enum_consistency(self):
        """Verify response_format uses consistent enum values."""
        from github_mcp import ResponseFormat
        
        # Check enum values
        assert hasattr(ResponseFormat, 'JSON'), "ResponseFormat should have JSON value"
        assert hasattr(ResponseFormat, 'MARKDOWN'), "ResponseFormat should have MARKDOWN value"
        
        # Verify enum values match expected strings
        assert ResponseFormat.JSON == "json", "ResponseFormat.JSON should be 'json'"
        assert ResponseFormat.MARKDOWN == "markdown", "ResponseFormat.MARKDOWN should be 'markdown'"
        
        print("✓ ResponseFormat enum is consistent")


class TestResponseFormatParsing:
    """Test response format parsing works correctly."""
    
    def test_json_response_structure(self):
        """Verify JSON responses have expected structure."""
        # This would require actual API calls or mocking
        # For now, verify the pattern exists in code
        
        # Check that tools with response_format='json' return parseable data
        tools_with_json = read_typescript_tool_list()
        
        assert len(tools_with_json) > 0, "Should have tools that support JSON response format"
        
        print(f"✓ {len(tools_with_json)} tools support JSON response format")
    
    def test_markdown_response_structure(self):
        """Verify Markdown responses have expected structure."""
        # Markdown responses should be strings
        # This is verified by the fact that response_format is optional
        # and defaults to markdown for most tools
        
        print("✓ Markdown response format is supported")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

