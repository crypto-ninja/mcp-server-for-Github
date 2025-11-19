"""
Test tool discovery functionality
"""
import sys
import io
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from src.github_mcp.deno_runtime import get_runtime  # noqa: E402


def test_list_available_tools():
    """Test listing all available tools"""
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

