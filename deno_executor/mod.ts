/**
 * Deno Runtime Executor
 * Executes user TypeScript code with access to GitHub MCP tools
 */

// Note: We need to use the compiled version or import directly
// For Deno, we'll import from the TypeScript source
// Use Deno-compatible client
import { initializeMCPClient, callMCPTool, closeMCPClient } from "../servers/client-deno.ts";

// Note: We can't import the tool wrappers directly because they import client.ts
// Instead, we'll just provide callMCPTool directly to user code
// The tool namespaces are available for type checking but not needed at runtime

/**
 * Execute user code with MCP tool access
 */
async function executeUserCode(code: string): Promise<any> {
  try {
    // Initialize MCP bridge
    await initializeMCPClient();

    // Create execution context with callMCPTool available
    // User code can call: callMCPTool("tool_name", { params })
    const userFunction = new Function(
      "callMCPTool",
      `return (async () => {
        ${code}
      })();`
    );

    // Execute user code with callMCPTool injected
    const result = await userFunction(callMCPTool);

    // Close connection
    await closeMCPClient();

    return {
      success: true,
      result: result
    };

  } catch (error) {
    // Close connection on error
    try {
      await closeMCPClient();
    } catch {
      // Ignore close errors
    }

    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    };
  }
}

/**
 * Main entry point
 */
if (import.meta.main) {
  const code = Deno.args[0];
  
  if (!code) {
    console.log(JSON.stringify({
      success: false,
      error: "No code provided"
    }));
    Deno.exit(1);
  }

  const result = await executeUserCode(code);
  console.log(JSON.stringify(result));
  Deno.exit(result.success ? 0 : 1);
}

