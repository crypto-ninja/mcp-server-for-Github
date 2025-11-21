/**
 * Deno Runtime Executor
 * Executes user TypeScript code with access to GitHub MCP tools
 */

// Note: We need to use the compiled version or import directly
// For Deno, we'll import from the TypeScript source
// Use Deno-compatible client
import { initializeMCPClient, callMCPTool, closeMCPClient } from "../servers/client-deno.ts";
import { GITHUB_TOOLS, getToolsByCategory, getCategories, type ToolDefinition } from "./tool-definitions.ts";

/**
 * List all available GitHub MCP tools with complete schemas
 * This enables intelligent tool discovery without loading all tools into context
 */
function listAvailableTools() {
  // Group by category
  const byCategory: Record<string, ToolDefinition[]> = {};
  
  for (const tool of GITHUB_TOOLS) {
    if (!byCategory[tool.category]) {
      byCategory[tool.category] = [];
    }
    byCategory[tool.category].push(tool);
  }
  
  return {
    totalTools: GITHUB_TOOLS.length,
    categories: getCategories(),
    tools: byCategory,
    usage: "Call any tool via: await callMCPTool(toolName, parameters)",
    quickReference: {
      "Repository Management": GITHUB_TOOLS.filter(t => t.category === "Repository Management").map(t => t.name),
      "Issues": GITHUB_TOOLS.filter(t => t.category === "Issues").map(t => t.name),
      "Pull Requests": GITHUB_TOOLS.filter(t => t.category === "Pull Requests").map(t => t.name),
      "Files": GITHUB_TOOLS.filter(t => t.category === "File Operations").map(t => t.name),
    },
    exampleTool: GITHUB_TOOLS[0]
  };
}

/**
 * Search for tools by name, description, or category
 * @param query Search term to match against tool name, description, or category
 * @returns Array of matching tools
 */
function searchTools(query: string): ToolDefinition[] {
  const lowerQuery = query.toLowerCase();
  return GITHUB_TOOLS.filter(tool => 
    tool.name.toLowerCase().includes(lowerQuery) ||
    tool.description.toLowerCase().includes(lowerQuery) ||
    tool.category.toLowerCase().includes(lowerQuery)
  );
}

/**
 * Get detailed information about a specific tool
 * @param toolName The exact tool name
 * @returns Tool definition or undefined if not found
 */
function getToolInfo(toolName: string): ToolDefinition | undefined {
  return GITHUB_TOOLS.find(tool => tool.name === toolName);
}

/**
 * Get tools in a specific category
 * @param category Category name
 * @returns Array of tools in that category
 */
function getToolsInCategory(category: string): ToolDefinition[] {
  return getToolsByCategory(category);
}

/**
 * Execute user code with MCP tool access
 */
async function executeUserCode(code: string): Promise<any> {
  try {
    // Initialize MCP bridge
    await initializeMCPClient();

    // Create execution context with callMCPTool and discovery functions available
    // User code can call: callMCPTool("tool_name", { params })
    // And use: listAvailableTools(), searchTools(), getToolInfo(), getToolsInCategory()
    const userFunction = new Function(
      "callMCPTool",
      "listAvailableTools",
      "searchTools",
      "getToolInfo",
      "getToolsInCategory",
      `return (async () => {
        ${code}
      })();`
    );

    // Execute user code with all helpers injected
    const result = await userFunction(
      callMCPTool,
      listAvailableTools,
      searchTools,
      getToolInfo,
      getToolsInCategory
    );

    // Wait a brief moment to ensure all responses are fully processed
    // This prevents connection from closing while responses are still being flushed
    // This is especially important for HTTP requests that may still be processing
    await new Promise(resolve => setTimeout(resolve, 200));

    // Close connection gracefully
    await closeMCPClient();

    return {
      success: true,
      result: result
    };

  } catch (error) {
    // Log the actual error before closing
    // This helps diagnose connection closing issues
    console.error('[Execute Code] Error during execution:', error);
    console.error('[Execute Code] Error stack:', error instanceof Error ? error.stack : 'No stack');
    
    // Close connection on error
    try {
      await closeMCPClient();
    } catch {
      // Ignore close errors
    }

    // CRITICAL: Always output JSON to stdout, even on error
    // This ensures Python subprocess can always parse the result
    const errorResult = {
      success: false,
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    };
    
    // Ensure this is logged to stdout (not stderr) so Python can parse it
    console.log(JSON.stringify(errorResult));
    
    return errorResult;
  }
}

/**
 * Main entry point
 * 
 * Reads code from stdin (to avoid Windows command-line character escaping issues)
 * Falls back to Deno.args[0] for backward compatibility
 * 
 * Includes timeout-based fallback for test environments where stdin may not be immediately ready
 */
if (import.meta.main) {
  let code: string;
  
  try {
    // Try reading from stdin first (production mode)
    const decoder = new TextDecoder();
    const reader = Deno.stdin.readable.getReader();
    const readPromise = reader.read();
    
    // Add timeout for test environments where stdin may not be immediately ready
    // This prevents hanging in pytest subprocess execution
    const timeoutPromise = new Promise<{value?: Uint8Array, done: boolean}>((resolve) => 
      setTimeout(() => resolve({ value: undefined, done: true }), 100)
    );
    
    const result = await Promise.race([readPromise, timeoutPromise]);
    
    if (result.value && result.value.length > 0) {
      code = decoder.decode(result.value).trim();
    } else {
      // Fall back to command-line args (test mode or empty stdin)
      code = Deno.args[0] || "";
    }
    
    // Clean up reader
    reader.releaseLock();
  } catch (e) {
    // If stdin fails completely, use command-line args
    // This is expected in some test environments
    code = Deno.args[0] || "";
  }
  
  if (!code || code.trim() === "") {
    console.log(JSON.stringify({
      success: false,
      error: "No code provided via stdin or command-line arguments"
    }));
    Deno.exit(1);
  }

  const result = await executeUserCode(code);
  console.log(JSON.stringify(result));
  Deno.exit(result.success ? 0 : 1);
}

