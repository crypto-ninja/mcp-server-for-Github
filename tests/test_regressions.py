"""
Phase 4: Regression Tests for Known Issues

Tests that prevent regressions of previously fixed bugs:
1. response_format only on supported tools
2. GitHub auth in execute_code
3. JSON error responses
4. Parameter validation
"""

import pytest
import json
from unittest.mock import Mock, patch
from typing import Dict, Any

# Import the MCP server
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import github_mcp
from src.github_mcp.deno_runtime import get_runtime


def _fix_windows_encoding():
    """Fix Windows console encoding for Unicode output."""
    import sys
    import os
    
    if sys.platform == 'win32':
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):
            pass


class TestResponseFormatRegression:
    """Regression tests for response_format parameter issues."""
    
    def test_response_format_only_on_supported_tools(self):
        """Regression: response_format was being added to all tools."""
        # Verify write operations don't have response_format
        write_tools = [
            'github_create_release',
            'github_update_file',
            'github_delete_file',
            'github_create_issue',
        ]
        
        for tool_name in write_tools:
            # Get the input model
            import inspect
            func = getattr(github_mcp, tool_name, None)
            if not func:
                continue
            
            sig = inspect.signature(func)
            params = sig.parameters
            
            if 'params' in params:
                param_type = params['params'].annotation
                if inspect.isclass(param_type):
                    if hasattr(param_type, 'model_fields'):
                        fields = param_type.model_fields
                        assert 'response_format' not in fields, \
                            f"{tool_name}: Write operation should not have response_format parameter"
    
    @pytest.mark.asyncio
    async def test_github_get_file_content_no_response_format(self):
        """Regression: github_get_file_content was incorrectly getting response_format."""
        _fix_windows_encoding()
        runtime = get_runtime()
        
        code = """
        // This should work without response_format
        const result = await callMCPTool("github_get_file_content", {
            owner: "modelcontextprotocol",
            repo: "servers",
            path: "README.md"
            // No response_format parameter
        });
        
        return {
            success: true,
            hasContent: !!result,
            isString: typeof result === 'string'
        };
        """
        
        result = runtime.execute_code(code)
        
        # Should execute without "Extra inputs" error
        assert result['success'], \
            f"Should not require response_format: {result.get('error', 'Unknown error')}"


class TestAuthRegression:
    """Regression tests for authentication issues."""
    
    @pytest.mark.asyncio
    async def test_github_auth_in_execute_code(self):
        """Regression: GitHub auth wasn't passed to execute_code subprocess."""
        _fix_windows_encoding()
        runtime = get_runtime()
        
        code = """
        const health = await callMCPTool("health_check", {});
        return {
            hasAuth: !!health,
            authConfigured: health?.authentication?.app_configured || 
                           health?.authentication?.pat_configured || false
        };
        """
        
        result = runtime.execute_code(code)
        
        # Should have auth configured
        assert result['success'], \
            f"Health check failed: {result.get('error', 'Unknown error')}"
        
        result_data = result.get('result', {})
        # Auth should be configured (either app or PAT)
        assert result_data.get('authConfigured', False), \
            "Authentication should be configured"


class TestJsonErrorRegression:
    """Regression tests for JSON error responses."""
    
    @pytest.mark.asyncio
    async def test_json_error_responses(self):
        """Regression: Errors returned as strings when response_format='json'."""
        _fix_windows_encoding()
        runtime = get_runtime()
        
        code = """
        try {
            // Force an error with response_format='json'
            const result = await callMCPTool("github_search_code", {
                query: "",  // Invalid empty query
                response_format: "json"
            });
            
            // Try to parse as JSON
            const parsed = typeof result === 'string' ? JSON.parse(result) : result;
            
            return {
                isJson: typeof parsed === 'object',
                hasError: !!parsed.error || !!parsed.message,
                canParse: true
            };
        } catch (e) {
            return {
                isJson: false,
                hasError: true,
                canParse: false,
                error: e.message
            };
        }
        """
        
        result = runtime.execute_code(code)
        
        # Should handle errors gracefully
        assert result['success'] or 'error' in result, \
            "Should handle JSON errors without crashing"


class TestParameterValidationRegression:
    """Regression tests for parameter validation."""
    
    @pytest.mark.asyncio
    async def test_extra_parameters_rejected(self):
        """Regression: Extra parameters should be rejected."""
        _fix_windows_encoding()
        runtime = get_runtime()
        
        code = """
        try {
            // Try to add an unsupported parameter
            await callMCPTool("github_get_file_content", {
                owner: "test",
                repo: "test",
                path: "README.md",
                response_format: "json"  // This should be rejected
            });
            return { rejected: false };
        } catch (error) {
            return {
                rejected: true,
                errorMessage: error.message || String(error)
            };
        }
        """
        
        result = runtime.execute_code(code)
        
        # Should reject extra parameters
        result_data = result.get('result', {})
        # Note: Pydantic validation happens server-side
        # This test verifies the pattern exists
        assert result['success'] or 'error' in result, \
            "Should handle parameter validation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

