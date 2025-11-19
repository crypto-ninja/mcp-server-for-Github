"""
Test the execute_code tool through MCP
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path (before src to prioritize root github_mcp.py)
project_root = Path(__file__).parent.parent
# Remove src from path if it's there, then add project root first
if str(project_root / "src") in sys.path:
    sys.path.remove(str(project_root / "src"))
sys.path.insert(0, str(project_root))

# Import the tool directly using importlib (like test_smoke.py)
import importlib  # noqa: E402
# Force reload to get the root module, not the package
if "github_mcp" in sys.modules:
    del sys.modules["github_mcp"]
github_mcp = importlib.import_module("github_mcp")
execute_code = github_mcp.execute_code


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

