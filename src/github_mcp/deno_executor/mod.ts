/**
 * GitHub MCP Server - Deno Executor (Unified)
 *
 * Unified executor supporting both pooled and single-shot execution modes.
 *
 * Pooled Mode (default):
 * - Reads code from stdin in a loop, allowing process reuse
 * - Each line of input is treated as a separate code execution
 * - Keeps MCP connection alive across executions for performance
 * - Used by connection pool for efficient process reuse
 *
 * Single-Shot Mode (--single-shot flag):
 * - Reads code from stdin once, executes, and exits
 * - Initializes and closes MCP connection per execution
 * - Used for synchronous/non-pooled execution paths
 */

// Deno global type declaration for TypeScript
declare const Deno: {
  stdin: {
    readable: ReadableStream<Uint8Array>;
  };
  stdout: {
    write(data: Uint8Array): Promise<number>;
  };
  exit(code?: number): never;
  args: string[];
};

import {
  callMCPTool,
  closeMCPClient,
  getToolInfo as mcpGetToolInfo,
  initializeMCPClient,
  isConnected,
  listAvailableTools as mcpListAvailableTools,
} from "../servers/client-deno.ts";
import {
  getCategories,
  getCompactToolsByCategory,
  getToolsByCategory,
  GITHUB_TOOLS,
  type ToolDefinition,
  type ToolParameter,
} from "./tool-definitions.ts";
import { sanitizeErrorMessage, validateCode } from "./code-validator.ts";
import { ErrorCodes } from "./error-codes.ts";

// Persistent MCP connection (created once, reused across executions)
let mcpConnectionInitialized = false;
let connectionInitializing = false;

/**
 * Ensure MCP connection is initialized (only once)
 */
async function ensureMCPConnection(): Promise<void> {
  if (mcpConnectionInitialized && isConnected()) {
    return;
  }

  if (connectionInitializing) {
    // Wait for initialization to complete
    while (connectionInitializing) {
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    return;
  }

  connectionInitializing = true;
  try {
    await initializeMCPClient();
    mcpConnectionInitialized = true;
    console.error("[Pooled Executor] MCP connection initialized");
  } catch (error) {
    console.error(
      "[Pooled Executor] Failed to initialize MCP connection:",
      error,
    );
    throw error;
  } finally {
    connectionInitializing = false;
  }
}

/**
 * Health check for MCP connection
 * Uses the actual MCP client's listTools method
 */
async function healthCheck(): Promise<boolean> {
  try {
    if (!isConnected()) {
      return false;
    }
    // Try a lightweight operation to verify connection
    // Use the actual MCP function
    try {
      await mcpListAvailableTools();
      return true;
    } catch (healthError) {
      console.error("[Pooled Executor] Health check failed:", healthError);
      return false;
    }
  } catch {
    return false;
  }
}

/**
 * Execute user code with persistent MCP connection
 */
async function executeWithPersistentConnection(code: string): Promise<any> {
  try {
    // Validate code before execution
    const validationResult = validateCode(code);
    if (!validationResult.valid) {
      const errorMessage = validationResult.errors.join("; ");
      const errorResponse = {
        error: true,
        message: `Code validation failed: ${errorMessage}`,
        code: ErrorCodes.VALIDATION_ERROR,
        details: { validationErrors: validationResult.errors },
      };
      console.log(JSON.stringify(errorResponse));
      return errorResponse;
    }

    // Log warnings (but don't block execution)
    if (validationResult.warnings.length > 0) {
      console.warn(
        "Code validation warnings:",
        validationResult.warnings.join("; "),
      );
    }

    // Ensure MCP connection is alive (lazy initialization)
    // Initialize on first use, not at startup, to avoid blocking pool creation
    try {
      if (!isConnected() || !mcpConnectionInitialized) {
        mcpConnectionInitialized = false;
        console.error("[Pooled Executor] Initializing MCP connection...");
        await ensureMCPConnection();
        console.error("[Pooled Executor] MCP connection ready");
      } else {
        // Verify connection is actually working
        const healthy = await healthCheck();
        if (!healthy) {
          console.error(
            "[Pooled Executor] Connection unhealthy, reconnecting...",
          );
          // Close existing connection
          try {
            await closeMCPClient();
          } catch {
            // Ignore close errors
          }
          mcpConnectionInitialized = false;
          await ensureMCPConnection();
        }
      }
    } catch (connError) {
      console.error(
        "[Pooled Executor] Connection error, reconnecting:",
        connError,
      );
      mcpConnectionInitialized = false;
      try {
        await closeMCPClient();
      } catch {
        // Ignore close errors
      }
      await ensureMCPConnection();
    }

    // Create execution context with callMCPTool and discovery functions available
    const userFunction = new Function(
      "callMCPTool",
      "listAvailableTools",
      "searchTools",
      "getToolInfo",
      "getToolsInCategory",
      `return (async () => {
        ${code}
      })();`,
    );

    // Helper functions for tool discovery
    /**
     * List all available tools (compact format)
     * Returns tool names grouped by category - use getToolInfo(toolName) for full details
     */
    function listAvailableToolsHelper() {
      return {
        totalTools: GITHUB_TOOLS.length,
        categories: getCompactToolsByCategory(),
        usage: "Use getToolInfo(toolName) for full details, or callMCPTool(toolName, params) to execute",
        tip: "Use searchTools(keyword) to find tools by name, description, or category"
      };
    }

    /**
     * Search for tools by keyword (compact format with relevance)
     * Returns matching tool names sorted by relevance - use getToolInfo(toolName) for full details
     */
    function searchToolsHelper(keyword: string) {
      const searchTerm = keyword.toLowerCase();
      const results: Array<{
        name: string;
        category: string;
        description: string;
        relevance: number;
        matchedIn: string[];
      }> = [];
      
      for (const tool of GITHUB_TOOLS) {
        const matches: string[] = [];
        let relevance = 0;
        
        // Check tool name (highest relevance)
        if (tool.name.toLowerCase().includes(searchTerm)) {
          matches.push("name");
          relevance += 10;
        }
        
        // Check description
        if (tool.description?.toLowerCase().includes(searchTerm)) {
          matches.push("description");
          relevance += 5;
        }
        
        // Check category
        if (tool.category.toLowerCase().includes(searchTerm)) {
          matches.push("category");
          relevance += 3;
        }
        
        // Check parameter names and descriptions
        if (tool.parameters) {
          for (const [paramName, paramInfo] of Object.entries(tool.parameters)) {
            const param = paramInfo as ToolParameter;
            if (paramName.toLowerCase().includes(searchTerm)) {
              matches.push(`parameter: ${paramName}`);
              relevance += 2;
            }
            if (param.description?.toLowerCase().includes(searchTerm)) {
              matches.push(`parameter description: ${paramName}`);
              relevance += 1;
            }
          }
        }
        
        // If matches found, add to results
        if (matches.length > 0) {
          results.push({
            name: tool.name,
            category: tool.category,
            description: tool.description,
            relevance: relevance,
            matchedIn: matches,
          });
        }
      }
      
      // Sort by relevance (highest first)
      results.sort((a, b) => b.relevance - a.relevance);
      
      return results;
    }

    function getToolInfoHelper(toolName: string) {
      const tool = GITHUB_TOOLS.find((t) => t.name === toolName);
      
      if (tool) {
        // Get category count for metadata
        const categoryCount = GITHUB_TOOLS.filter(t => t.category === tool.category).length;
        
        return {
          ...tool,
          usage: `await callMCPTool("${toolName}", parameters)`,
          metadata: {
            totalTools: GITHUB_TOOLS.length,
            categoryTools: categoryCount,
            relatedCategory: tool.category,
          },
        };
      }

      // Tool not found - return helpful error for AI user
      return {
        error: `Tool "${toolName}" not found`,
        suggestion: "Use searchTools() to find available tools",
        availableTools: GITHUB_TOOLS.length,
      };
    }

    function getToolsInCategoryHelper(category: string) {
      return getToolsByCategory(category);
    }

    // Execute user code with all helpers injected
    // Note: listAvailableToolsHelper uses local GITHUB_TOOLS, not MCP call
    // This is faster and doesn't require MCP connection for discovery
    const result = await userFunction(
      callMCPTool, // This uses the persistent MCP connection
      listAvailableToolsHelper,
      searchToolsHelper,
      getToolInfoHelper,
      getToolsInCategoryHelper,
    );

    // Wait a brief moment to ensure all responses are fully processed
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Return structured success response (DO NOT close connection!)
    const successResponse = {
      error: false,
      data: result,
    };
    // Flush stdout to ensure output is sent immediately
    console.log(JSON.stringify(successResponse));
    // Force flush stdout
    await Deno.stdout.write(new TextEncoder().encode("\n"));
    return successResponse;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("[Pooled Executor] Error during execution:", errorMessage);

    // Check if it's a connection error
    const isConnError = errorMessage.includes("socket") ||
      errorMessage.includes("connection") ||
      errorMessage.includes("ECONNRESET") ||
      errorMessage.includes("Connection lost");

    if (isConnError) {
      // Reset connection state, will reconnect on next execution
      mcpConnectionInitialized = false;
    }

    const errorResponse = {
      error: true,
      message: sanitizeErrorMessage(errorMessage),
      code: ErrorCodes.EXECUTION_ERROR,
      details: {
        ...(error instanceof Error && error.stack &&
          { stack: sanitizeErrorMessage(error.stack) }),
      },
    };

    console.log(JSON.stringify(errorResponse));
    return errorResponse;
  }
}

/**
 * Read full stdin content (for single-shot mode)
 */
async function readFullStdin(): Promise<string> {
  const reader = Deno.stdin.readable.getReader();
  const chunks: Uint8Array[] = [];
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    if (value) chunks.push(value);
  }
  reader.releaseLock();
  if (chunks.length === 0) return "";
  const total = chunks.reduce((acc, c) => acc + c.length, 0);
  const all = new Uint8Array(total);
  let offset = 0;
  for (const c of chunks) {
    all.set(c, offset);
    offset += c.length;
  }
  return new TextDecoder().decode(all).trim();
}

/**
 * Main entry point for pooled execution
 *
 * Reads JSON lines from stdin; each line should be a JSON object with a `code` field.
 * Falls back to executing raw line if JSON parse fails (backward compatibility).
 * Outputs JSON result for each execution, then continues to next line.
 *
 * KEY: Keeps MCP connection alive across executions
 */
if (import.meta.main) {
  // Check for single-shot mode (non-pooled execution)
  const singleShot = Deno.args.includes("--single-shot");
  
  if (singleShot) {
    // Single-shot mode: read stdin once, execute, exit
    const code = await readFullStdin();
    if (!code || code.trim() === "") {
      console.log(JSON.stringify({
        error: true,
        message: "No code provided",
        code: "CODE_EMPTY"
      }));
      Deno.exit(1);
    }
    
    // Initialize MCP for single execution
    await ensureMCPConnection();
    const result = await executeWithPersistentConnection(code);
    await closeMCPClient();
    Deno.exit(result.error ? 1 : 0);
  }
  
  // Pooled mode: read JSON lines in a loop
  const decoder = new TextDecoder();
  const reader = Deno.stdin.readable.getReader();

  // Initialize MCP connection once at startup
  try {
    await ensureMCPConnection();
    console.error("[Pooled Executor] Ready for code execution");
  } catch (error) {
    console.error("[Pooled Executor] Failed to initialize:", error);
    Deno.exit(1);
  }

  let buffer = "";

  while (true) {
    try {
      const { value, done } = await reader.read();

      if (done) {
        console.error("[Pooled Executor] Stdin closed, closing connection");
        await closeMCPClient();
        Deno.exit(0);
      }

      if (value) {
        buffer += decoder.decode(value, { stream: true });
      }

      let newlineIndex: number;
      while ((newlineIndex = buffer.indexOf("\n")) >= 0) {
        const line = buffer.substring(0, newlineIndex).trim();
        buffer = buffer.substring(newlineIndex + 1);

        if (!line) {
          continue;
        }

        let code = "";
        try {
          const parsed = JSON.parse(line);
          code = parsed?.code || "";
        } catch {
          // Not JSON; treat as raw code for backward compatibility
          code = line;
        }

        if (!code || code.trim() === "") {
          console.log(
            JSON.stringify({
              error: true,
              message: "No code provided in request",
            }),
          );
          continue;
        }

        await executeWithPersistentConnection(code);
      }
    } catch (error) {
      const errorResponse = {
        error: true,
        message: `Pooled executor error: ${
          error instanceof Error ? error.message : String(error)
        }`,
        code: "POOLED_EXECUTOR_ERROR",
      };
      console.log(JSON.stringify(errorResponse));
    }
  }
}
