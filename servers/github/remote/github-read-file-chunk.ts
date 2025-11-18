// servers/github/remote/github-read-file-chunk.ts
import { callMCPTool } from '../../client.js';

export interface GithubReadFileChunkInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** File path in repository */
  path: string;
  /** 1-based starting line number */
  start_line: number;
  /** Number of lines to read (max 500) */
  num_lines: number;
  /** Branch, tag, or commit SHA (defaults to default branch) */
  ref?: string | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
}

/**
 * Read a specific range of lines from a GitHub repository file.
 
 * 
 * Examples:
 * - "Read lines 50-100 of main.py from main branch"
 * - "Show me the first 20 lines of README.md"
 * - "Read the function starting at line 150"

 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_read_file_chunk(
    input: GithubReadFileChunkInput
): Promise<string> {
    return callMCPTool<string>(
        'github_read_file_chunk',
        input
    );
}
