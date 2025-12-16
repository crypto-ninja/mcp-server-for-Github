// servers/github/workspace/repo-read-file-chunk.ts
import { callMCPTool } from '../../client.js';

export interface RepoReadFileChunkInput {
  /** Relative path under the server's repository root */
  path: string;
  /** 1-based starting line number */
  start_line: number;
  /** Number of lines to read (max 500) */
  num_lines: number;
}

/**
 * Read a specific range of lines from a local file under the workspace root.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function repo_read_file_chunk(
    input: RepoReadFileChunkInput
): Promise<string> {
    return callMCPTool<string>(
        'repo_read_file_chunk',
        input
    );
}
