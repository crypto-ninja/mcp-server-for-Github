/**
 * MCP Client Bridge
 * 
 * Connects TypeScript wrappers to the Python GitHub MCP Server via stdio.
 * Enables programmatic tool calls for code execution workflows.
 * 
 * Architecture:
 * - Spawns Python MCP server as child process
 * - Communicates via JSON-RPC over stdio
 * - Handles tool calls and responses
 * - Manages lifecycle (connect, disconnect, cleanup)
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

// Use Deno-compatible imports (works in both Node.js and Deno)
// @ts-ignore - Deno compatibility
const fileURLToPath = (url: string | URL) => {
    if (typeof Deno !== 'undefined') {
        // Deno: convert file:// URL to path
        if (url instanceof URL) {
            return url.pathname.replace(/^\/([a-z]:)/i, '$1').replace(/\//g, '\\');
        }
        return url.replace(/^file:\/\//, '').replace(/^\/([a-z]:)/i, '$1').replace(/\//g, '\\');
    } else {
        // Node.js: use built-in
        // @ts-ignore
        const { fileURLToPath: nodeFileURLToPath } = await import('node:url');
        return nodeFileURLToPath(url);
    }
};

// @ts-ignore - Deno compatibility
const dirname = (path: string) => {
    if (typeof Deno !== 'undefined') {
        // Deno: use Deno's path utilities
        return Deno.cwd(); // Simplified - would need proper path parsing
    } else {
        // Node.js: use built-in
        // @ts-ignore
        const { dirname: nodeDirname } = await import('node:path');
        return nodeDirname(path);
    }
};

// @ts-ignore - Deno compatibility
const resolve = (...paths: string[]) => {
    if (typeof Deno !== 'undefined') {
        // Deno: use Deno's path utilities
        return paths.join('/');
    } else {
        // Node.js: use built-in
        // @ts-ignore
        const { resolve: nodeResolve } = await import('node:path');
        return nodeResolve(...paths);
    }
};

// Global client instance (singleton)
let mcpClient: Client | null = null;
let mcpTransport: StdioClientTransport | null = null;
let isInitializing = false;

/**
 * Configuration for MCP server connection
 */
interface MCPConfig {
    command: string;
    args: string[];
    env?: Record<string, string>;
}

/**
 * Get MCP server configuration from environment or defaults
 */
function getMCPConfig(): MCPConfig {
    const isWindows = process.platform === 'win32';
    
    // Check for custom configuration
    const customCommand = process.env.MCP_PYTHON_COMMAND;
    const customArgs = process.env.MCP_PYTHON_ARGS;
    
    if (customCommand) {
        return {
            command: customCommand,
            args: customArgs ? customArgs.split(' ') : ['-m', 'github_mcp_server'],
            env: {
                ...process.env,
                MCP_CODE_EXECUTION_MODE: 'true',
            }
        };
    }
    
    // Default configuration - use the actual path to github_mcp.py
    // Since we're in the servers directory, we need to go up to find github_mcp.py
    let githubMcpPath: string;
    if (typeof Deno !== 'undefined') {
        // Deno: use Deno.cwd() and construct path
        const projectRoot = Deno.cwd();
        githubMcpPath = `${projectRoot}/github_mcp.py`.replace(/\//g, '\\');
    } else {
        // Node.js: use import.meta.url
        const __filename = fileURLToPath(import.meta.url);
        const __dirname = dirname(__filename);
        githubMcpPath = resolve(__dirname, '..', 'github_mcp.py');
    }
    
    if (isWindows) {
        return {
            command: 'cmd',
            args: ['/c', 'python', githubMcpPath],
            env: {
                ...process.env,
                MCP_CODE_EXECUTION_MODE: 'true',
            }
        };
    } else {
        return {
            command: 'python',
            args: [githubMcpPath],
            env: {
                ...process.env,
                MCP_CODE_EXECUTION_MODE: 'true',
            }
        };
    }
}

/**
 * Initialize connection to Python MCP server
 * 
 * @throws Error if connection fails
 */
export async function initializeMCPClient(): Promise<void> {
    // Already initialized
    if (mcpClient) {
        return;
    }
    
    // Another initialization in progress
    if (isInitializing) {
        // Wait for initialization to complete
        while (isInitializing) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        return;
    }
    
    isInitializing = true;
    
    try {
        const config = getMCPConfig();
        
        console.error('[MCP Bridge] Connecting to Python MCP server...');
        console.error(`[MCP Bridge] Command: ${config.command} ${config.args.join(' ')}`);
        
        // Create stdio transport
        mcpTransport = new StdioClientTransport({
            command: config.command,
            args: config.args,
            env: config.env
        });
        
        // Create MCP client
        mcpClient = new Client({
            name: 'github-mcp-code-executor',
            version: '2.0.0'
        }, {
            capabilities: {}
        });
        
        // Connect to server
        await mcpClient.connect(mcpTransport);
        
        console.error('[MCP Bridge] ✓ Connected to GitHub MCP Server');
        
        // List available tools
        const tools = await mcpClient.listTools();
        console.error(`[MCP Bridge] ✓ Found ${tools.tools.length} available tools`);
        
    } catch (error) {
        mcpClient = null;
        mcpTransport = null;
        console.error('[MCP Bridge] ✗ Connection failed:', error);
        throw new Error(`Failed to connect to MCP server: ${error}`);
    } finally {
        isInitializing = false;
    }
}

/**
 * Call an MCP tool and return typed result
 * 
 * This is the main function that all generated wrappers use.
 * 
 * @template T - Expected return type
 * @param toolName - Name of the MCP tool (e.g., 'github_create_issue')
 * @param params - Tool parameters
 * @returns Typed tool result
 * @throws Error if tool call fails
 */
export async function callMCPTool<T = string>(
    toolName: string,
    params: any
): Promise<T> {
    // Ensure connection is established
    if (!mcpClient) {
        await initializeMCPClient();
    }
    
    if (!mcpClient) {
        throw new Error('MCP client not initialized');
    }
    
    try {
        console.error(`[MCP Bridge] Calling tool: ${toolName}`);
        
        // FastMCP expects arguments wrapped in a 'params' object
        // when the function signature has a single 'params' parameter
        const wrappedParams = Object.keys(params).length > 0 ? { params } : {};
        
        const response = await mcpClient.callTool({
            name: toolName,
            arguments: wrappedParams
        });
        
        // Extract content from response
        // Response structure can vary, handle both CallToolResult and direct responses
        const responseAny = response as any;
        
        if (responseAny.content && Array.isArray(responseAny.content) && responseAny.content.length > 0) {
            const content = responseAny.content[0];
            
            if (content.type === 'text') {
                const text = content.text;
                
                // Try to parse as JSON if possible
                if (text.trim().startsWith('{') || text.trim().startsWith('[')) {
                    try {
                        return JSON.parse(text) as T;
                    } catch {
                        // Not JSON, return as-is
                        return text as unknown as T;
                    }
                }
                
                // Return text as-is
                return text as unknown as T;
            }
            
            throw new Error(`Unexpected content type: ${content.type}`);
        }
        
        // Handle case where response has toolResult directly
        if (responseAny.toolResult) {
            return responseAny.toolResult as T;
        }
        
        throw new Error('No content in tool response');
        
    } catch (error) {
        console.error(`[MCP Bridge] Tool call failed: ${toolName}`, error);
        throw error;
    }
}

/**
 * List all available tools from the MCP server
 * 
 * Useful for debugging and validation.
 * 
 * @returns Array of tool names
 */
export async function listAvailableTools(): Promise<string[]> {
    if (!mcpClient) {
        await initializeMCPClient();
    }
    
    if (!mcpClient) {
        throw new Error('MCP client not initialized');
    }
    
    const tools = await mcpClient.listTools();
    return tools.tools.map(t => t.name);
}

/**
 * Get detailed information about a specific tool
 * 
 * @param toolName - Name of the tool
 * @returns Tool information including schema
 */
export async function getToolInfo(toolName: string): Promise<any> {
    if (!mcpClient) {
        await initializeMCPClient();
    }
    
    if (!mcpClient) {
        throw new Error('MCP client not initialized');
    }
    
    const tools = await mcpClient.listTools();
    const tool = tools.tools.find(t => t.name === toolName);
    
    if (!tool) {
        throw new Error(`Tool not found: ${toolName}`);
    }
    
    return tool;
}

/**
 * Close the MCP client connection
 * 
 * Should be called when done using the client to clean up resources.
 */
export async function closeMCPClient(): Promise<void> {
    if (mcpClient) {
        console.error('[MCP Bridge] Closing connection...');
        
        try {
            await mcpClient.close();
        } catch (error) {
            console.error('[MCP Bridge] Error during close:', error);
        }
        
        mcpClient = null;
        mcpTransport = null;
        
        console.error('[MCP Bridge] ✓ Connection closed');
    }
}

/**
 * Check if client is connected
 */
export function isConnected(): boolean {
    return mcpClient !== null;
}

// Cleanup on process exit
process.on('beforeExit', () => {
    if (mcpClient) {
        closeMCPClient().catch(console.error);
    }
});

process.on('SIGINT', () => {
    if (mcpClient) {
        closeMCPClient().catch(console.error);
    }
    process.exit(0);
});

process.on('SIGTERM', () => {
    if (mcpClient) {
        closeMCPClient().catch(console.error);
    }
    process.exit(0);
});
