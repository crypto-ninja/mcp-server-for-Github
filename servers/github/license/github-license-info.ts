// servers/github/license/github-license-info.ts
import { callMCPTool } from '../../client.js';



/**
 * Display current license information and status for the GitHub MCP Server.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_license_info(
    input: any
): Promise<string> {
    return callMCPTool<string>(
        'github_license_info',
        input
    );
}
