// servers/github/workspace/workspace-read-file.ts
import { callMCPTool } from '../../client.js';

export interface WorkspaceReadFileInput {
  /** Relative path under the server's repository root */
  path: string;
  /** 1-based starting line number */
  start_line: number;
  /** Number of lines to read (max 500) */
  num_lines: number;
}

/**
 * [LOCAL] Read a specific range of lines from a local workspace file.
 * 
 * For reading files from GitHub remote, use github_get_file_content instead.
 * 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function workspace_read_file(
    input: WorkspaceReadFileInput
): Promise<string> {
    return callMCPTool<string>(
        'workspace_read_file',
        input
    );
}

