"""
Test tool discovery functionality
"""
import sys
import io
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.github_mcp.deno_runtime import get_runtime  # noqa: E402


def _fix_windows_encoding():
    """Fix Windows console encoding for Unicode output (only when printing)."""
    import os
    
    # Skip if running under pytest (pytest handles encoding)
    if 'pytest' in sys.modules or hasattr(sys.stdout, '_pytest') or os.environ.get('PYTEST_CURRENT_TEST'):
        return
    
    if sys.platform == 'win32':
        # Only reconfigure if not already UTF-8 and not in pytest capture
        try:
            # Check if stdout has buffer and encoding attributes before accessing
            if (hasattr(sys.stdout, 'buffer') and 
                hasattr(sys.stdout, 'encoding') and 
                getattr(sys.stdout, 'encoding', None) != 'utf-8'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if (hasattr(sys.stderr, 'buffer') and 
                hasattr(sys.stderr, 'encoding') and 
                getattr(sys.stderr, 'encoding', None) != 'utf-8'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):
            # Python < 3.7, already wrapped, or pytest capture - skip silently
            pass


def test_list_available_tools():
    """Test listing all available tools"""
    _fix_windows_encoding()
    runtime = get_runtime()
    
    code = """
    const tools = listAvailableTools();
    return {
        totalTools: tools.totalTools,
        categories: tools.categories,
        firstTool: tools.tools["Repository Management"][0].name
    };
    """
    
    result = runtime.execute_code(code)
    print("Test 1: List Available Tools")
    print(f"Success: {result['success']}")
    if result['success']:
        data = result['result']
        print(f"Total tools: {data['totalTools']}")
        print(f"Categories: {len(data['categories'])}")
        print(f"First tool: {data['firstTool']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()


def test_search_tools():
    """Test searching for tools"""
    _fix_windows_encoding()
    runtime = get_runtime()
    
    code = """
    const issueTools = searchTools("issue");
    return {
        searchQuery: "issue",
        resultsFound: issueTools.length,
        toolNames: issueTools.map(t => t.name)
    };
    """
    
    result = runtime.execute_code(code)
    print("Test 2: Search Tools")
    print(f"Success: {result['success']}")
    if result['success']:
        data = result['result']
        print(f"Found {data['resultsFound']} tools")
        print(f"Tools: {data['toolNames']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()


def test_get_tool_info():
    """Test getting specific tool info"""
    _fix_windows_encoding()
    runtime = get_runtime()
    
    code = """
    const toolInfo = getToolInfo("github_create_issue");
    return {
        toolName: toolInfo.name,
        category: toolInfo.category,
        hasExample: !!toolInfo.example,
        paramCount: Object.keys(toolInfo.parameters).length
    };
    """
    
    result = runtime.execute_code(code)
    print("Test 3: Get Tool Info")
    print(f"Success: {result['success']}")
    if result['success']:
        data = result['result']
        print(f"Tool: {data['toolName']}")
        print(f"Category: {data['category']}")
        print(f"Has example: {data['hasExample']}")
        print(f"Parameters: {data['paramCount']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()


def test_discovery_then_use():
    """Test discovering a tool then using it"""
    _fix_windows_encoding()
    runtime = get_runtime()
    
    code = """
    // Discover the tool first
    const toolInfo = getToolInfo("github_get_repo_info");
    
    // Now use it
    const repoInfo = await callMCPTool("github_get_repo_info", {
        owner: "modelcontextprotocol",
        repo: "servers"
    });
    
    return {
        discoveredTool: toolInfo.name,
        toolUsed: true,
        repoDataLength: repoInfo.length
    };
    """
    
    result = runtime.execute_code(code)
    print("Test 4: Discovery + Usage")
    print(f"Success: {result['success']}")
    if result['success']:
        data = result['result']
        print(f"Discovered: {data['discoveredTool']}")
        print(f"Used successfully: {data['toolUsed']}")
        print(f"Got repo data: {data['repoDataLength']} chars")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print()


if __name__ == "__main__":
    print("Testing Tool Discovery Functionality")
    print("=" * 60)
    print()
    
    test_list_available_tools()
    test_search_tools()
    test_get_tool_info()
    test_discovery_then_use()
    
    print("=" * 60)
    print("All tests completed!")

