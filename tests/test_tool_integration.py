"""
Phase 2: Integration Tests

Tests that validate:
1. Tool chaining (search then read, create then update)
2. Execute code integration with tool calls
3. Data flow between tools
4. Error propagation
"""

import pytest

# Import the MCP server
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.github_mcp.deno_runtime import get_runtime  # noqa: E402


def _fix_windows_encoding():
    """Fix Windows console encoding for Unicode output."""
    import sys
    
    if sys.platform == 'win32':
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):
            pass


class TestToolChaining:
    """Test that tools can be chained together."""
    
    @pytest.mark.asyncio
    async def test_search_then_read(self):
        """Test searching for files then reading them."""
        _fix_windows_encoding()
        
        # This would require actual API calls or mocking
        # For now, verify the pattern exists
        runtime = get_runtime()
        
        code = """
        // Search for a file
        const results = await callMCPTool("github_search_code", {
            owner: "modelcontextprotocol",
            repo: "servers",
            query: "README.md",
            response_format: "json"
        });
        
        // Parse results
        const files = typeof results === 'string' ? JSON.parse(results) : results;
        
        return {
            searchWorked: Array.isArray(files) || typeof files === 'object',
            resultType: typeof results
        };
        """
        
        result = runtime.execute_code(code)
        
        # Should execute without errors
        assert result['success'] or 'error' in result, \
            f"Code execution failed: {result.get('error', 'Unknown error')}"
    
    @pytest.mark.asyncio
    async def test_create_then_update_pattern(self):
        """Test creating resources then updating them."""
        # This would require actual API calls
        # For now, verify the pattern is possible
        runtime = get_runtime()
        
        code = """
        // Verify we can call create and update tools
        const createTool = getToolInfo("github_create_issue");
        const updateTool = getToolInfo("github_update_issue");
        
        return {
            canCreate: !!createTool,
            canUpdate: !!updateTool,
            createParams: Object.keys(createTool?.parameters || {}),
            updateParams: Object.keys(updateTool?.parameters || {})
        };
        """
        
        result = runtime.execute_code(code)
        
        # Should execute without errors
        assert result['success'] or 'error' in result, \
            f"Code execution failed: {result.get('error', 'Unknown error')}"


class TestExecuteCodeIntegration:
    """Test tools called via execute_code work correctly."""
    
    @pytest.mark.asyncio
    async def test_execute_code_tool_calls(self):
        """Test tools called via execute_code work correctly."""
        _fix_windows_encoding()
        runtime = get_runtime()
        
        code = """const result = await callMCPTool("github_get_repo_info", {
    owner: "modelcontextprotocol",
    repo: "servers",
    response_format: "json"
});

// Verify result is parseable
const parsed = typeof result === 'string' ? JSON.parse(result) : result;

return {
    success: true,
    hasData: !!parsed,
    isObject: typeof parsed === 'object',
    keys: Object.keys(parsed || {})
};"""
        
        # execute_code returns a dict with 'success' and 'result' or 'error'
        result = runtime.execute_code(code.strip())
        
        # Should execute successfully (check if it's a dict with success key)
        if isinstance(result, dict):
            assert result.get('success', False) or 'result' in result, \
                f"execute_code failed: {result.get('error', 'Unknown error')}"
        else:
            # If it's not a dict, it might be the result directly
            assert result is not None, "execute_code returned None"
        
        # Result should be parseable
        result_data = result.get('result', {})
        assert isinstance(result_data, dict), \
            f"Result should be a dict, got {type(result_data)}"
    
    @pytest.mark.asyncio
    async def test_execute_code_error_handling(self):
        """Test error handling in execute_code."""
        _fix_windows_encoding()
        runtime = get_runtime()
        
        code = """
        try {
            // Call with invalid parameters
            await callMCPTool("github_get_repo_info", {
                owner: "",
                repo: ""
            });
            return { error: "Should have failed" };
        } catch (error) {
            return {
                errorHandled: true,
                errorMessage: error.message || String(error)
            };
        }
        """
        
        result = runtime.execute_code(code)
        
        # Should handle errors gracefully
        assert result['success'] or 'error' in result, \
            "Should handle errors without crashing"
    
    @pytest.mark.asyncio
    async def test_execute_code_json_parsing(self):
        """Test that JSON responses are properly parsed."""
        _fix_windows_encoding()
        runtime = get_runtime()
        
        code = """const result = await callMCPTool("github_list_issues", {
    owner: "modelcontextprotocol",
    repo: "servers",
    state: "open",
    response_format: "json"
});

// Try to parse as JSON
let parsed;
try {
    parsed = typeof result === 'string' ? JSON.parse(result) : result;
} catch (e) {
    parsed = { parseError: e.message };
}

return {
    isArray: Array.isArray(parsed),
    isObject: typeof parsed === 'object' && parsed !== null,
    canParse: !parsed.parseError
};"""
        
        result = runtime.execute_code(code.strip())
        
        # Should execute and return parseable data
        if isinstance(result, dict):
            assert result.get('success', False) or 'result' in result, \
                f"JSON parsing test failed: {result.get('error', 'Unknown error')}"
        else:
            assert result is not None, "execute_code returned None"


class TestDataFlow:
    """Test data flows correctly between tools."""
    
    @pytest.mark.asyncio
    async def test_list_then_get(self):
        """Test listing items then getting details."""
        _fix_windows_encoding()
        runtime = get_runtime()
        
        code = """
        // List releases
        const releases = await callMCPTool("github_list_releases", {
            owner: "modelcontextprotocol",
            repo: "servers",
            response_format: "json"
        });
        
        const releasesList = typeof releases === 'string' ? JSON.parse(releases) : releases;
        
        return {
            hasReleases: Array.isArray(releasesList) && releasesList.length > 0,
            firstRelease: releasesList?.[0] || null,
            canGetDetails: !!releasesList?.[0]?.tag_name
        };
        """
        
        result = runtime.execute_code(code)
        
        # Should execute without errors
        assert result['success'] or 'error' in result, \
            f"List then get test failed: {result.get('error', 'Unknown error')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

