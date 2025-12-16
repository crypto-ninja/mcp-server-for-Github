"""
GitHub MCP Server - Main server initialization and tool registration.

This module initializes the FastMCP server and registers all GitHub tools,
supporting both code-first mode (execute_code only) and traditional mode (all tools).
"""

import os
import sys
import subprocess
import json
import inspect
from typing import Optional, Any, Dict, Callable, Tuple, Type, cast
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP


# Check Deno installation
def check_deno_installed() -> Tuple[bool, str]:
    """Check if Deno is installed and accessible."""
    try:
        result = subprocess.run(
            ["deno", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0]
            return True, version
        else:
            return False, "Deno command failed"
    except FileNotFoundError:
        return False, "Deno not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "Deno version check timed out"
    except Exception as e:
        return False, f"Error checking Deno: {str(e)}"


# Check Deno at startup
deno_available, deno_info = check_deno_installed()
if not deno_available:
    print("=" * 60, file=sys.stderr)
    print("❌ DENO NOT FOUND", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Error: {deno_info}", file=sys.stderr)
    print(
        "\nGitHub MCP Server requires Deno to execute TypeScript code.", file=sys.stderr
    )
    print("\nInstallation:", file=sys.stderr)
    print("  Windows: irm https://deno.land/install.ps1 | iex", file=sys.stderr)
    print("  macOS:    brew install deno", file=sys.stderr)
    print("  Linux:    curl -fsSL https://deno.land/install.sh | sh", file=sys.stderr)
    print("\nOr visit: https://deno.land", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    sys.exit(1)

# Code-First Mode: Expose only execute_code to Claude Desktop for token efficiency
# Deno runtime will connect with CODE_FIRST_MODE=false to access all tools internally
CODE_FIRST_MODE = os.getenv("MCP_CODE_FIRST_MODE", "true").lower() == "true"

# Initialize the MCP server
mcp = FastMCP("github_mcp")

# Print startup message based on mode
if CODE_FIRST_MODE:
    print(">> GitHub MCP Server v2.5.4 - Code-First Mode (execute_code only)")
    print(">> Token usage: ~800 tokens (98% savings!)")
    print(f">> Deno: {deno_info}")
else:
    print(">> GitHub MCP Server v2.5.4 - Internal Mode (all internal tools)")
    print(">> Used by Deno runtime for tool execution")
    print(f">> Deno: {deno_info}")


# Conditional tool registration decorator
def conditional_tool(
    *args: Any, **kwargs: Any
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Only register tool if not in code-first mode.
    In code-first mode, only execute_code is exposed to Claude Desktop.
    """
    if CODE_FIRST_MODE:
        # Return a no-op decorator that doesn't register the tool
        def noop_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return noop_decorator
    else:
        # Return the actual mcp.tool decorator
        return mcp.tool(*args, **kwargs)


# Import all tools (after mcp initialization)
from .tools import __all__ as all_tools  # noqa: E402
from .tools import *  # noqa: E402, F403, F405  # Import all tool functions


# Register all tools conditionally
# We'll use a helper to get tool metadata from the original file
# For now, register with default annotations - we can refine this later
def register_all_tools() -> None:
    """Register all GitHub tools with the MCP server."""
    # Get tool metadata from original file (we'll extract this properly later)
    # For now, register with default annotations based on tool name patterns
    tool_metadata: Dict[str, Any] = {}

    # Try to extract metadata from git history (original file before refactor)
    # For now, we'll use default annotations based on tool name patterns
    # Metadata extraction can be refined later if needed
    # The important thing is that all tools are registered correctly

    # Register each tool
    for tool_name in all_tools:
        tool_func = globals()[tool_name]  # type: ignore[misc]
        metadata = tool_metadata.get(tool_name, {})

        # Determine default annotations based on tool name patterns
        is_readonly = metadata.get(
            "readOnlyHint",
            tool_name.startswith("github_list")
            or tool_name.startswith("github_get")
            or tool_name.startswith("github_search")
            or tool_name.startswith("github_check"),
        )
        is_destructive = metadata.get(
            "destructiveHint",
            "delete" in tool_name or "remove" in tool_name or "close" in tool_name,
        )
        is_idempotent = metadata.get(
            "idempotentHint",
            not (
                "create" in tool_name or "update" in tool_name or "delete" in tool_name
            ),
        )
        is_open_world = metadata.get("openWorldHint", True)

        # Create wrapper function with proper closure
        def create_tool_wrapper(
            name: str,
            func: Callable[..., Any],
            readonly: bool,
            destructive: bool,
            idempotent: bool,
            open_world: bool,
        ) -> Callable[..., Any]:
            """Create a tool wrapper with proper closure."""
            # Special case for github_license_info (no params)
            if name == "github_license_info":

                @conditional_tool(
                    name=name,
                    annotations={
                        "title": name.replace("github_", "").replace("_", " ").title(),
                        "readOnlyHint": readonly,
                        "destructiveHint": destructive,
                        "idempotentHint": idempotent,
                        "openWorldHint": open_world,
                    },
                )
                async def wrapper() -> Any:
                    return await func()

                wrapper.__name__ = name
                return wrapper
            else:

                @conditional_tool(
                    name=name,
                    annotations={
                        "title": name.replace("github_", "").replace("_", " ").title(),
                        "readOnlyHint": readonly,
                        "destructiveHint": destructive,
                        "idempotentHint": idempotent,
                        "openWorldHint": open_world,
                    },
                )
                async def wrapper(params: Any) -> Any:
                    model_cls: Optional[Type[BaseModel]] = None
                    try:
                        sig = inspect.signature(func)
                        first_param = next(iter(sig.parameters.values()))
                        ann = first_param.annotation
                        # Check if annotation is a type (not a string forward reference)
                        if ann is not inspect.Parameter.empty and isinstance(ann, type):
                            # Use cast to help mypy understand this is a type
                            ann_type = cast(type, ann)
                            if issubclass(ann_type, BaseModel):
                                model_cls = cast(Type[BaseModel], ann_type)
                    except (TypeError, AttributeError, ValueError):
                        # Annotation might be a string, empty, or not a BaseModel subclass
                        model_cls = None

                    parsed_params = params
                    if model_cls and isinstance(params, dict):
                        parsed_params = model_cls(**params)
                    return await func(parsed_params)

                wrapper.__name__ = name
                return wrapper

        # Register the tool
        wrapped = create_tool_wrapper(
            tool_name,
            tool_func,
            is_readonly,
            is_destructive,
            is_idempotent,
            is_open_world,
        )
        # Store in module namespace (the decorator already registered it with FastMCP)
        globals()[tool_name + "_registered"] = wrapped  # type: ignore[misc]


# Register all tools
register_all_tools()


# Register execute_code (always exposed)
@mcp.tool(
    name="execute_code",
    annotations={  # type: ignore[arg-type]
        "title": "Execute TypeScript Code",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def execute_code(code: str) -> str:
    """
    Execute TypeScript code with access to all GitHub MCP tools.

    🚀 REVOLUTIONARY: 98% token reduction through code-first execution!

    💡 TOOL DISCOVERY:
    To see all available tools with complete schemas, use this in your code:
    ```typescript
    const tools = listAvailableTools();
    return tools;
    ```

    This returns a structured catalog of all 109 GitHub tools including:
    - Tool names and descriptions
    - Required/optional parameters with types
    - Return value descriptions
    - Usage examples for each tool
    - Organized by category

    📚 Quick Start Example:
    ```typescript
    // 1. Discover what's available (optional - only if you need to know)
    const tools = listAvailableTools();

    // 2. Use any tool directly
    const info = await callMCPTool("github_get_repo_info", {
        owner: "facebook",
        repo: "react"
    });

    return { availableTools: tools.totalTools, repoInfo: info };
    ```

    🔍 Search for Specific Tools:
    ```typescript
    // Find tools related to a topic
    const issueTools = searchTools("issue");

    // Get detailed info about a specific tool
    const toolInfo = getToolInfo("github_create_issue");
    ```

    🎯 Common Tool Categories:
    - Repository Management (8 tools): github_get_repo_info, github_create_repository, etc.
    - Issues (4 tools): github_list_issues, github_create_issue, etc.
    - Pull Requests (7 tools): github_list_pull_requests, github_merge_pull_request, etc.
    - Files (9 tools): github_get_file_content, github_create_file, etc.
    - Search (3 tools): github_search_code, github_search_repositories, etc.
    - Releases (4 tools): github_list_releases, github_create_release, etc.
    - Actions (15 tools): github_list_workflows, github_get_workflow_runs, etc.
    - And 14 more categories...

    📖 Full documentation: https://github.com/crypto-ninja/mcp-server-for-Github#tools

    All tools are called via: await callMCPTool(toolName, parameters)

    Benefits:
        - 98%+ token reduction vs traditional MCP
        - Full TypeScript type safety
        - Complex workflows in single execution
        - Conditional logic and loops
        - Error handling with try/catch
    """
    try:
        from .deno_runtime import get_runtime

        runtime = get_runtime()
        # Use async execution if available (for connection pooling)
        if hasattr(runtime, "execute_code_async"):
            result = await runtime.execute_code_async(code)
        else:
            # Fallback to sync version
            result = runtime.execute_code(code)

        # Handle new format: {error: true/false, message/data: ...}
        if not isinstance(result, dict):
            return f"❌ Unexpected error: result is not a dictionary: {type(result)}"

        is_error = result.get("error", True)

        if is_error:
            # Format error
            error = result.get("message", "Unknown error")
            details: Dict[str, Any] = result.get("details", {})
            stack = details.get("stack", "") if isinstance(details, dict) else ""
            code = result.get("code", "")

            error_msg = "❌ Code execution failed"
            if code:
                error_msg += f" ({code})"
            error_msg += f"\n\n**Error:**\n```\n{error}\n```"
            if stack:
                error_msg += f"\n\n**Stack Trace:**\n```\n{stack}\n```"

            return error_msg
        else:
            # Format successful result
            return_value = result.get("data", "Code executed successfully")

            # Return raw JSON for structured data (dict/list) so TypeScript can parse it
            if isinstance(return_value, (dict, list)):
                # Return raw JSON string - TypeScript client expects JSON, not markdown
                return json.dumps(return_value)
            elif isinstance(return_value, str):
                # For strings, check if it's already JSON
                if return_value.strip().startswith(("{", "[")):
                    # Already JSON string, return as-is
                    return return_value
                else:
                    # Plain string, format as markdown for readability
                    return f"✅ Code executed successfully\n\n**Result:**\n```\n{return_value}\n```"
            else:
                # Other types (numbers, booleans, etc.) - convert to JSON
                return json.dumps(return_value)

    except ImportError as e:
        return f"❌ Error: Deno runtime not available. {str(e)}\n\nPlease ensure:\n1. Deno is installed\n2. src/github_mcp/deno_runtime.py exists"
    except Exception as e:
        return f"❌ Unexpected error during code execution: {str(e)}"


def run(transport: Optional[str] = None, port: Optional[int] = None) -> None:
    """
    Run the MCP server.

    Args:
        transport: Transport type ("stdio", "sse", or "streamable-http")
        port: Port number for HTTP/SSE transport (not used by FastMCP.run)
    """
    if transport in ("sse", "streamable-http"):
        # FastMCP.run accepts transport as literal type, not port parameter
        mcp.run(transport=transport)  # type: ignore[arg-type]
    else:
        mcp.run()
