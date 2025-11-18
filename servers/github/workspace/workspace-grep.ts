// servers/github/workspace/workspace-grep.ts
import { callMCPTool } from '../../client.js';

export interface WorkspaceGrepInput {
  /** Regex pattern to search for */
  pattern: string;
  /** Optional subdirectory to search within (relative to repo root) */
  repo_path: string;
  /** Number of lines before/after match to include (0-5) */
  context_lines: number;
  /** Maximum matches to return (1-500) */
  max_results: number;
  /** Glob pattern for files to search (e.g., '*.py', '*.md') */
  file_pattern: string;
  /** Whether search is case-sensitive */
  case_sensitive: boolean;
  /** Output format (markdown or json) */
  response_format: 'markdown' | 'json';
}

/**
 * Search for patterns in workspace files using grep.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function workspace_grep(
    input: WorkspaceGrepInput
): Promise<string> {
    return callMCPTool<string>(
        'workspace_grep',
        input
    );
}
