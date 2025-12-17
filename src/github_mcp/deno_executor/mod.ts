/**
 * GitHub MCP Server - Deno Executor
 *
 * PRIMARY USER: AI Agents (LLMs like Claude, GPT, etc.)
 * SECONDARY USER: Human developers
 * END BENEFICIARY: Users getting AI assistance
 *
 * Design Philosophy:
 * These functions (searchTools, getToolInfo, callMCPTool) are used BY AI agents
 * to help humans. When designing features, we ask: "Can the AI agent use this
 * effectively?" rather than "Can a developer use this?"
 *
 * The Moment of Realization:
 * During v2.3.1 development, Dave kept asking Claude: "Can YOU use these tools?"
 * Claude kept analyzing from a "developer perspective" until the breakthrough:
 * "Wait... I'M the one calling searchTools(). I'M the user!"
 *
 * This shift in perspective led to:
 * - searchTools() with relevance scoring (AI needs best-match-first)
 * - getToolInfo() with complete metadata (AI needs full context)
 * - 70% → 95% AI confidence boost (AI can now help users better)
 *
 * This is AI-first design: Optimize for AI capability → Better human outcomes
 *
 * The Future of Development:
 * This project was built through human-AI collaboration, where the AI is both
 * the builder AND the primary user. Dave and Claude worked together—testing,
 * debugging, designing—with Claude using the very tools it was helping to create.
 * This is not "AI-generated code"—this is genuine partnership, where both human
 * and AI contribute their unique strengths.
 *
 * Available functions in execution context:
 * - listAvailableTools() - Get all tools organized by category
 * - searchTools(keyword) - Search for tools by keyword
 * - getToolInfo(toolName) - Get detailed info about a specific tool
 * - getToolsInCategory(category) - Get all tools in a category
 * - callMCPTool(name, params) - Call any MCP tool
 */

// Note: We need to use the compiled version or import directly
// For Deno, we'll import from the TypeScript source
// Use Deno-compatible client
import {
  callMCPTool,
  closeMCPClient,
  initializeMCPClient,
} from "../servers/client-deno.ts";
import {
  getCategories,
  getCompactToolsByCategory,
  getToolsByCategory,
  GITHUB_TOOLS,
  type ToolDefinition,
  type ToolParameter,
} from "./tool-definitions.ts";
import {
  sanitizeErrorMessage,
  validateCode,
  type ValidationResult,
} from "./code-validator.ts";
import { type ErrorCode, ErrorCodes } from "./error-codes.ts";

/**
 * Standardized error response format
 */
export interface ErrorResponse {
  error: true;
  message: string;
  code?: ErrorCode;
  details?: Record<string, unknown>;
}

/**
 * Standardized success response format
 */
export interface SuccessResponse<T = unknown> {
  error: false;
  data: T;
}

export type MCPResponse<T = unknown> = ErrorResponse | SuccessResponse<T>;

/**
 * Create a standardized error response
 */
function createErrorResponse(
  message: string,
  code?: ErrorCode,
  details?: Record<string, unknown>,
): string {
  const response: ErrorResponse = {
    error: true,
    message,
    ...(code && { code }),
    ...(details && { details }),
  };
  return JSON.stringify(response);
}

/**
 * Create a standardized success response
 */
function createSuccessResponse<T>(data: T): string {
  const response: SuccessResponse<T> = {
    error: false,
    data,
  };
  return JSON.stringify(response);
}

/**
 * List all available GitHub MCP tools (compact format)
 * Returns tool names grouped by category - use getToolInfo(toolName) for full details
 * 
 * This compact format prevents buffer overflow with 112+ tools
 */
function listAvailableTools() {
  return {
    totalTools: GITHUB_TOOLS.length,
    categories: getCompactToolsByCategory(),
    usage: "Use getToolInfo(toolName) for full details, or callMCPTool(toolName, params) to execute",
    tip: "Use searchTools(keyword) to find tools by name, description, or category"
  };
}

/**
 * Search for tools by keyword
 * Searches tool names, descriptions, categories, and parameter descriptions
 * Returns matching tools sorted by relevance
 *
 * @param keyword - Search term (case-insensitive)
 * @returns Array of matching tools with relevance scores
 *
 * @example
 * const issueTools = searchTools("issue");
 * // Returns all tools related to issues
 *
 * const createTools = searchTools("create");
 * // Returns all tools that create resources
 */
/**
 * Search for tools by keyword (compact format)
 * Returns matching tool names with descriptions - use getToolInfo(toolName) for full details
 */
function searchTools(keyword: string): Array<{
  name: string;
  category: string;
  description: string;
  relevance: number;
  matchedIn: string[];
}> {
  const results: Array<{
    name: string;
    category: string;
    description: string;
    relevance: number;
    matchedIn: string[];
  }> = [];
  const searchTerm = keyword.toLowerCase();

  // Get all tools from GITHUB_TOOLS
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

/**
 * Get detailed information about a specific tool
 * Returns complete tool metadata including parameters, examples, and usage
 *
 * @param toolName - Name of the tool (e.g., "github_create_issue")
 * @returns Complete tool information or null if not found
 *
 * @example
 * const info = getToolInfo("github_create_issue");
 * console.log(info.description);
 * console.log(info.parameters);
 * console.log(info.example);
 */
function getToolInfo(toolName: string): any {
  // Search through GITHUB_TOOLS directly for full tool definition
  const tool = GITHUB_TOOLS.find(t => t.name === toolName);
  
  if (tool) {
    // Get category count for metadata
    const categoryCount = GITHUB_TOOLS.filter(t => t.category === tool.category).length;
    
    return {
      ...tool,
      usage: `await callMCPTool("${toolName}", parameters)`,
      // Add helpful metadata
      metadata: {
        totalTools: GITHUB_TOOLS.length,
        categoryTools: categoryCount,
        relatedCategory: tool.category,
      },
    };
  }

  // Tool not found
  return {
    error: `Tool "${toolName}" not found`,
    suggestion: "Use searchTools() to find available tools",
    availableTools: GITHUB_TOOLS.length,
  };
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
export async function executeUserCode(code: string): Promise<any> {
  try {
    // Validate code before execution
    const validationResult = validateCode(code);
    if (!validationResult.valid) {
      const errorMessage = validationResult.errors.join("; ");
      console.error("Code validation failed:", errorMessage);
      // Return structured error response (for Python to parse)
      const errorResponse = createErrorResponse(
        `Code validation failed: ${errorMessage}`,
        ErrorCodes.VALIDATION_ERROR,
        { validationErrors: validationResult.errors },
      );
      console.log(errorResponse);
      // Return object for main entry point to check
      return {
        error: true,
        message: `Code validation failed: ${errorMessage}`,
        code: ErrorCodes.VALIDATION_ERROR,
        details: { validationErrors: validationResult.errors },
      };
    }

    // Log warnings (but don't block execution)
    if (validationResult.warnings.length > 0) {
      console.warn(
        "Code validation warnings:",
        validationResult.warnings.join("; "),
      );
    }

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
      })();`,
    );

    // Execute user code with all helpers injected
    const result = await userFunction(
      callMCPTool,
      listAvailableTools,
      searchTools,
      getToolInfo,
      getToolsInCategory,
    );

    // Wait a brief moment to ensure all responses are fully processed
    // This prevents connection from closing while responses are still being flushed
    // This is especially important for HTTP requests that may still be processing
    await new Promise((resolve) => setTimeout(resolve, 200));

    // Close connection gracefully
    await closeMCPClient();

    // Return structured success response (for Python to parse)
    const successResponse = createSuccessResponse(result);
    console.log(successResponse);
    // Return object for main entry point to check
    return { error: false, data: result };
  } catch (error) {
    // Log the actual error before closing
    // This helps diagnose connection closing issues
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("[Execute Code] Error during execution:", errorMessage);
    console.error(
      "[Execute Code] Error stack:",
      error instanceof Error ? error.stack : "No stack",
    );

    // Close connection on error
    try {
      await closeMCPClient();
    } catch {
      // Ignore close errors
    }

    // CRITICAL: Always output JSON to stdout, even on error
    // This ensures Python subprocess can always parse the result
    const errorResponse = createErrorResponse(
      sanitizeErrorMessage(errorMessage),
      ErrorCodes.EXECUTION_ERROR,
      {
        ...(error instanceof Error && error.stack &&
          { stack: sanitizeErrorMessage(error.stack) }),
      },
    );

    // Ensure this is logged to stdout (not stderr) so Python can parse it
    console.log(errorResponse);

    // Return object for main entry point to check
    return {
      error: true,
      message: sanitizeErrorMessage(errorMessage),
      code: ErrorCodes.EXECUTION_ERROR,
      details: {
        ...(error instanceof Error && error.stack &&
          { stack: sanitizeErrorMessage(error.stack) }),
      },
    };
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

if (import.meta.main) {
  // Prefer command-line arg if provided (compat), else read entire stdin
  let code = Deno.args.length > 0 ? Deno.args[0] : await readFullStdin();

  if (!code || code.trim() === "") {
    const errorResponse = createErrorResponse(
      "No code provided via stdin or command-line arguments",
      ErrorCodes.CODE_EMPTY,
    );
    console.log(errorResponse);
    Deno.exit(1);
  }

  const result = await executeUserCode(code);
  // Result is already logged inside executeUserCode, but we need to check error for exit code
  Deno.exit(result.error ? 1 : 0);
}
