"""
Test the Deno runtime integration
"""
import sys
import io
from pathlib import Path

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from github_mcp.deno_runtime import get_runtime


def test_simple_execution():
    """Test executing simple TypeScript code"""
    runtime = get_runtime()
    
    code = """
    const result = { message: "Hello from Deno!", timestamp: Date.now() };
    return result;
    """
    
    result = runtime.execute_code(code)
    print("Test 1: Simple execution")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Result: {result['result']}")
    else:
        print(f"Error: {result['error']}")
    print()


def test_mcp_tool_call():
    """Test calling MCP tool from Deno"""
    runtime = get_runtime()
    
    code = """
    const repoInfo = await callMCPTool("github_get_repo_info", {
        owner: "modelcontextprotocol",
        repo: "servers"
    });
    
    return { 
        toolCalled: "github_get_repo_info",
        resultLength: repoInfo.length,
        preview: repoInfo.substring(0, 100)
    };
    """
    
    result = runtime.execute_code(code)
    print("Test 2: MCP tool call")
    print(f"Success: {result['success']}")
    if result['success']:
        result_data = result['result']
        if isinstance(result_data, dict):
            print(f"Result keys: {list(result_data.keys())}")
            if 'preview' in result_data:
                print(f"Preview: {result_data['preview'][:100]}...")
            else:
                print(f"Result: {str(result_data)[:200]}")
        else:
            print(f"Result type: {type(result_data).__name__}, length: {len(str(result_data))}")
    else:
        print(f"Error: {result.get('error', 'Unknown')[:200]}")
    print()


def test_error_handling():
    """Test error handling in Deno runtime"""
    runtime = get_runtime()
    
    code = """
    throw new Error("Intentional test error");
    """
    
    result = runtime.execute_code(code)
    print("Test 3: Error handling")
    print(f"Success: {result['success']}")
    print(f"Error caught: {result.get('error', 'N/A')[:100]}")
    print()


def test_multiple_tool_calls():
    """Test multiple sequential tool calls"""
    runtime = get_runtime()
    
    code = """
    // Call multiple tools
    const repo = await callMCPTool("github_get_repo_info", {
        owner: "modelcontextprotocol",
        repo: "servers"
    });
    
    const issues = await callMCPTool("github_list_issues", {
        owner: "modelcontextprotocol",
        repo: "servers",
        state: "open",
        limit: 5
    });
    
    return {
        repoFetched: true,
        issuesFetched: true,
        repoLength: repo.length,
        issuesLength: issues.length
    };
    """
    
    result = runtime.execute_code(code)
    print("Test 4: Multiple tool calls")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Result: {result['result']}")
    else:
        print(f"Error: {result['error']}")
    print()


if __name__ == "__main__":
    print("Testing Deno Runtime Integration\n")
    print("=" * 50)
    print()
    
    test_simple_execution()
    test_mcp_tool_call()
    test_error_handling()
    test_multiple_tool_calls()
    
    print("=" * 50)
    print("All tests completed!")

