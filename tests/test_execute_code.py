"""
Test the execute_code tool through MCP
"""
import asyncio
import sys
import io
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the tool directly
from github_mcp import execute_code  # noqa: E402


def _fix_windows_encoding():
    """Fix Windows console encoding for Unicode output (only when printing)."""
    if sys.platform == 'win32':
        # Only wrap if not already wrapped and not in pytest capture mode
        if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except (AttributeError, ValueError):
                # Python < 3.7 or already wrapped - skip
                pass


async def test_simple_code():
    """Test executing simple code"""
    _fix_windows_encoding()
    code = """
    const message = "Hello from code execution!";
    const timestamp = Date.now();
    return { message, timestamp };
    """
    
    result = await execute_code(code)
    print("Test 1: Simple code execution")
    print(result)
    print()


async def test_tool_call():
    """Test calling GitHub tools from code"""
    _fix_windows_encoding()
    code = """
    const info = await callMCPTool("github_get_repo_info", {
        owner: "modelcontextprotocol",
        repo: "servers"
    });
    
    return {
        toolCalled: "github_get_repo_info",
        resultLength: info.length,
        success: true
    };
    """
    
    result = await execute_code(code)
    print("Test 2: Tool call from code")
    print(result)
    print()


async def test_multiple_tools():
    """Test calling multiple tools"""
    _fix_windows_encoding()
    code = """
    // Get repo info
    const repoInfo = await callMCPTool("github_get_repo_info", {
        owner: "modelcontextprotocol",
        repo: "servers"
    });
    
    // List issues
    const issues = await callMCPTool("github_list_issues", {
        owner: "modelcontextprotocol",
        repo: "servers",
        state: "open",
        limit: 5
    });
    
    return {
        repoFetched: repoInfo.length > 0,
        issuesFetched: issues.length > 0,
        issueCount: issues.includes("Found") ? "yes" : "unknown"
    };
    """
    
    result = await execute_code(code)
    print("Test 3: Multiple tool calls")
    print(result)
    print()


async def test_error_handling():
    """Test error handling"""
    _fix_windows_encoding()
    code = """
    throw new Error("Test error from user code");
    """
    
    result = await execute_code(code)
    print("Test 4: Error handling")
    print(result)
    print()


async def test_complex_workflow():
    """Test complex workflow with logic"""
    _fix_windows_encoding()
    code = """
    // Get repo information
    const repoInfo = await callMCPTool("github_get_repo_info", {
        owner: "facebook",
        repo: "react"
    });
    
    // Parse star count from response (it's in markdown format)
    const hasStars = repoInfo.includes("⭐") || repoInfo.includes("stars");
    
    // Conditional logic
    if (hasStars) {
        return {
            repo: "facebook/react",
            status: "popular",
            hasStarInfo: true
        };
    } else {
        return {
            repo: "facebook/react",
            status: "unknown",
            hasStarInfo: false
        };
    }
    """
    
    result = await execute_code(code)
    print("Test 5: Complex workflow with logic")
    print(result)
    print()


async def main():
    print("Testing execute_code tool")
    print("=" * 60)
    print()
    
    await test_simple_code()
    await test_tool_call()
    await test_multiple_tools()
    await test_error_handling()
    await test_complex_workflow()
    
    print("=" * 60)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())

