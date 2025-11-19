"""
Test execute_code tool via MCP protocol
"""
import asyncio
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from github_mcp import mcp  # noqa: E402


async def test_tool_registration():
    """Verify execute_code tool is registered"""
    print("Testing tool registration...\n")
    
    # Get tools list
    tools_response = await mcp.list_tools()
    tools = tools_response.tools
    
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

