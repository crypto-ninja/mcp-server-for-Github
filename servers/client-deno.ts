/**
 * MCP Client Bridge - Deno-compatible version
 * 
 * Connects TypeScript wrappers to the Python GitHub MCP Server via stdio.
 * This is a Deno-compatible version that doesn't use Node.js built-ins.
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

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
    const isWindows = Deno.build.os === "windows";
    
    // Check for custom configuration
    const customCommand = Deno.env.get("MCP_PYTHON_COMMAND");
    const customArgs = Deno.env.get("MCP_PYTHON_ARGS");
    
    // Get environment variables (Deno-compatible)
    const env: Record<string, string> = {};
    for (const [key, value] of Object.entries(Deno.env.toObject())) {
        env[key] = value;
    }
    env['MCP_CODE_EXECUTION_MODE'] = 'true';
    
    // CRITICAL: Force traditional mode (all tools) for Deno runtime
    // This ensures execute_code can access all 41 tools internally,
    // even when Claude Desktop only sees execute_code
    env['MCP_CODE_FIRST_MODE'] = 'false';
    
    if (customCommand) {
        return {
            command: customCommand,
            args: customArgs ? customArgs.split(' ') : ['-m', 'github_mcp_server'],
            env: env
        };
    }
    
    // Default configuration - use the actual path to github_mcp.py
    const projectRoot = Deno.cwd();
    const githubMcpPath = `${projectRoot}/github_mcp.py`.replace(/\//g, isWindows ? '\\' : '/');
    
    if (isWindows) {
        return {
            command: 'cmd',
            args: ['/c', 'python', githubMcpPath],
            env: env
        };
    } else {
        return {
            command: 'python',
            args: [githubMcpPath],
            env: env
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
        
        // CRITICAL: Force traditional mode for internal Deno runtime connection
        // This ensures all 41 tools are available to execute_code,
        // even when Claude Desktop is in code-first mode
        if (config.env) {
            config.env['MCP_CODE_FIRST_MODE'] = 'false';
        }
        
        console.error('[MCP Bridge] Connecting to Python MCP server...');
        console.error(`[MCP Bridge] Command: ${config.command} ${config.args.join(' ')}`);
        console.error('[MCP Bridge] Mode: TRADITIONAL (all 41 tools available internally)');
        
        // Create stdio transport
        mcpTransport = new StdioClientTransport({
            command: config.command,
            args: config.args,
            env: config.env
        });
        
        // Create MCP client
        mcpClient = new Client({
            name: 'github-mcp-code-executor',
            version: '2.1.0'
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

