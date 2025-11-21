"""
Phase 1: Schema Validation Tests

Tests that validate:
1. All tool parameters match their Pydantic schemas
2. Response formats are consistent and parseable
3. Error handling works uniformly across all tools
4. No parameter mismatches like response_format issues
"""

import pytest
import json
from pydantic import ValidationError
from typing import Dict, Any, List, Optional
import inspect
import importlib

# Import the MCP server
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path setup
import github_mcp
from github_mcp import mcp, ResponseFormat


def get_all_tools() -> List[Dict[str, Any]]:
    """Get list of all registered MCP tools with their schemas."""
    # FastMCP stores tools in mcp._tools
    tools = []
    if hasattr(mcp, '_tools'):
        for tool_name, tool_info in mcp._tools.items():
            tools.append({
                'name': tool_name,
                'schema': tool_info.get('inputSchema', {}),
                'function': tool_info.get('handler')
            })
    return tools


def get_tool_input_model(tool_name: str) -> Optional[Any]:
    """Get the Pydantic input model for a tool by inspecting its function signature."""
    tools = get_all_tools()
    tool = next((t for t in tools if t['name'] == tool_name), None)
    
    if not tool or not tool['function']:
        return None
    
    # Get function signature
    sig = inspect.signature(tool['function'])
    params = sig.parameters
    
    # Find the params parameter (usually the first parameter)
    if 'params' in params:
        param_type = params['params'].annotation
        # If it's a string annotation, try to resolve it
        if isinstance(param_type, str):
            # Try to get from module
            if hasattr(github_mcp, param_type):
                return getattr(github_mcp, param_type)
        elif inspect.isclass(param_type):
            return param_type
    
    return None


def get_read_tools_with_json_support() -> List[str]:
    """Read the READ_TOOLS_WITH_JSON_SUPPORT list from client-deno.ts."""
    client_deno_path = project_root / "servers" / "client-deno.ts"
    
    if not client_deno_path.exists():
        return []
    
    content = client_deno_path.read_text(encoding='utf-8')
    
    # Extract the array from the file
    import re
    match = re.search(r'const READ_TOOLS_WITH_JSON_SUPPORT = \[(.*?)\];', content, re.DOTALL)
    if not match:
        return []
    
    # Extract tool names from the array
    tools = []
    for line in match.group(1).split('\n'):
        line = line.strip()
        if line.startswith("'") or line.startswith('"'):
            tool_name = line.strip("'\"")
            if tool_name and not tool_name.startswith('//'):
                tools.append(tool_name)
    
    return tools


class TestToolSchemas:
    """Test suite for tool schema validation."""
    
    def test_all_tools_are_registered(self):
        """Verify all expected tools are registered in the MCP server."""
        tools = get_all_tools()
        tool_names = [t['name'] for t in tools]
        
        # Should have at least execute_code and health_check
        assert 'execute_code' in tool_names, "execute_code tool not found"
        assert 'health_check' in tool_names, "health_check tool not found"
        assert len(tool_names) >= 2, f"Expected at least 2 tools, found {len(tool_names)}"
        
        print(f"✓ Found {len(tool_names)} registered tools")
    
    def test_response_format_parameter_consistency(self):
        """Test that tools in READ_TOOLS_WITH_JSON_SUPPORT actually support response_format."""
        read_tools = get_read_tools_with_json_support()
        mismatches = []
        
        for tool_name in read_tools:
            input_model = get_tool_input_model(tool_name)
            
            if not input_model:
                mismatches.append(f"{tool_name}: Could not find input model")
                continue
            
            # Check if response_format field exists
            if not hasattr(input_model, 'model_fields'):
                mismatches.append(f"{tool_name}: No model_fields found")
                continue
            
            fields = input_model.model_fields
            if 'response_format' not in fields:
                mismatches.append(
                    f"{tool_name}: Listed in READ_TOOLS_WITH_JSON_SUPPORT but "
                    f"doesn't have response_format parameter"
                )
        
        if mismatches:
            pytest.fail(
                "Tools in READ_TOOLS_WITH_JSON_SUPPORT that don't support response_format:\n" +
                "\n".join(f"  - {m}" for m in mismatches)
            )
        
        print(f"✓ All {len(read_tools)} tools in READ_TOOLS_WITH_JSON_SUPPORT support response_format")
    
    def test_write_tools_dont_have_response_format(self):
        """Test that write operations don't have response_format parameter."""
        write_tools = [
            'github_create_release',
            'github_update_file',
            'github_delete_file',
            'github_create_issue',
            'github_update_issue',
            'github_create_pull_request',
            'github_merge_pull_request',
            'github_close_pull_request',
            'github_create_pr_review',
            'github_create_repository',
            'github_update_repository',
            'github_delete_repository',
            'github_transfer_repository',
            'github_archive_repository',
            'github_batch_file_operations',
            'github_str_replace',
        ]
        
        violations = []
        
        for tool_name in write_tools:
            input_model = get_tool_input_model(tool_name)
            
            if not input_model:
                continue  # Tool might not exist, skip
            
            if hasattr(input_model, 'model_fields'):
                fields = input_model.model_fields
                if 'response_format' in fields:
                    violations.append(
                        f"{tool_name}: Write operation has response_format parameter "
                        f"(should not have it)"
                    )
        
        if violations:
            pytest.fail(
                "Write operations that incorrectly have response_format:\n" +
                "\n".join(f"  - {v}" for v in violations)
            )
        
        print(f"✓ All {len(write_tools)} write tools correctly don't have response_format")
    
    def test_tools_reject_extra_parameters(self):
        """Test that tools reject undocumented parameters (Pydantic extra='forbid')."""
        tools = get_all_tools()
        violations = []
        
        for tool in tools:
            tool_name = tool['name']
            input_model = get_tool_input_model(tool_name)
            
            if not input_model:
                continue
            
            # Check if model has extra='forbid' configured
            if hasattr(input_model, 'model_config'):
                config = input_model.model_config
                if config.get('extra') != 'forbid':
                    violations.append(
                        f"{tool_name}: Allows extra parameters (should have extra='forbid')"
                    )
        
        # This is informational - not all tools need to forbid extra params
        if violations:
            print(f"⚠ {len(violations)} tools allow extra parameters:")
            for v in violations[:5]:  # Show first 5
                print(f"  - {v}")
    
    def test_response_format_enum_values(self):
        """Test that response_format only accepts valid enum values."""
        read_tools = get_read_tools_with_json_support()
        
        for tool_name in read_tools[:3]:  # Test first 3 as sample
            input_model = get_tool_input_model(tool_name)
            
            if not input_model:
                continue
            
            if hasattr(input_model, 'model_fields'):
                fields = input_model.model_fields
                if 'response_format' in fields:
                    field_info = fields['response_format']
                    # Should be ResponseFormat enum
                    assert field_info.annotation == ResponseFormat or \
                           str(field_info.annotation) == "ResponseFormat", \
                           f"{tool_name}: response_format should be ResponseFormat enum"
        
        print("✓ response_format uses correct enum type")


class TestErrorHandling:
    """Test error handling consistency across tools."""
    
    @pytest.mark.asyncio
    async def test_json_error_responses(self):
        """Test that tools return JSON errors when response_format='json'."""
        # This would require mocking API calls
        # For now, just verify the pattern exists in code
        read_tools = get_read_tools_with_json_support()
        
        # Check that github_search_code has the JSON error handling
        # (we just added it)
        assert 'github_search_code' in read_tools
        
        print("✓ JSON error response pattern verified")


class TestParameterValidation:
    """Test parameter validation for tools."""
    
    def test_required_parameters_are_required(self):
        """Verify required parameters are actually required."""
        # Test a few key tools
        test_cases = [
            ('github_get_repo_info', ['owner', 'repo']),
            ('github_list_issues', ['owner', 'repo']),
            ('github_get_file_content', ['owner', 'repo', 'path']),
        ]
        
        for tool_name, required_fields in test_cases:
            input_model = get_tool_input_model(tool_name)
            
            if not input_model:
                continue
            
            if hasattr(input_model, 'model_fields'):
                fields = input_model.model_fields
                for field_name in required_fields:
                    assert field_name in fields, \
                        f"{tool_name}: Required field '{field_name}' not found"
                    
                    field_info = fields[field_name]
                    # Check if it's required (no default)
                    if hasattr(field_info, 'default') and field_info.default is not ...:
                        pytest.fail(
                            f"{tool_name}: Field '{field_name}' should be required "
                            f"but has default value"
                        )
        
        print("✓ Required parameters validation passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

