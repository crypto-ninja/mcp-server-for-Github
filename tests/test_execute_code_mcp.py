"""
Test execute_code tool via MCP protocol
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

# Import using importlib (like test_smoke.py)
import importlib  # noqa: E402
# Force reload to get the root module, not the package
if "github_mcp" in sys.modules:
    del sys.modules["github_mcp"]
github_mcp = importlib.import_module("github_mcp")
mcp = github_mcp.mcp


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


async def test_tool_registration():
    """Verify execute_code tool is registered"""
    _fix_windows_encoding()
    print("Testing tool registration...\n")
    
    # Get tools list
    tools_response = await mcp.list_tools()
    # FastMCP returns a list directly, not an object with .tools
    tools = tools_response if isinstance(tools_response, list) else tools_response.tools
    
    print(f"Total tools registered: {len(tools)}")
    
    # Find execute_code
    execute_tool = [t for t in tools if t.name == 'execute_code']
    
    if execute_tool:
        tool = execute_tool[0]
        print("✅ execute_code tool found!")
        print(f"   Name: {tool.name}")
        print(f"   Description: {tool.description[:100]}...")
        print()
        return True
    else:
        print("❌ execute_code tool not found!")
        print("Available tools:")
        for t in tools[:10]:
            print(f"  - {t.name}")
        print()
        return False


async def test_tool_call():
    """Test calling execute_code via MCP"""
    _fix_windows_encoding()
    print("Testing execute_code tool call...\n")
    
    # Simple test code
    code = """
    const result = {
        message: "Hello from MCP execute_code!",
        timestamp: Date.now(),
        test: "success"
    };
    return result;
    """
    
    try:
        # Call the tool
        result = await mcp.call_tool("execute_code", {"code": code})
        
        print("✅ Tool call successful!")
        print(f"Response type: {type(result)}")
        
        # Extract content
        if hasattr(result, 'content') and result.content:
            content = result.content[0]
            if hasattr(content, 'text'):
                print(f"\nResponse:\n{content.text[:500]}")
            else:
                print(f"\nResponse: {content}")
        else:
            print(f"\nResponse: {result}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Tool call failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def main():
    print("=" * 60)
    print("Testing execute_code via MCP Protocol")
    print("=" * 60)
    print()
    
    # Test 1: Registration
    registered = await test_tool_registration()
    
    if registered:
        # Test 2: Tool call
        await test_tool_call()
    
    print("=" * 60)
    print("Tests completed!")


if __name__ == "__main__":
    asyncio.run(main())

