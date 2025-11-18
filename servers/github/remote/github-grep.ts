// servers/github/remote/github-grep.ts
import { callMCPTool } from '../../client.js';

export interface GithubGrepInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Regex pattern to search for */
  pattern: string;
  /** Branch, tag, or commit SHA (defaults to default branch) */
  ref?: string | undefined;
  /** Glob pattern for files (e.g., '*.py', '*.md') */
  file_pattern?: string | undefined;
  /** Optional subdirectory to search within */
  path?: string | undefined;
  /** Whether search is case-sensitive */
  case_sensitive?: boolean | undefined;
  /** Number of lines before/after match to include (0-5) */
  context_lines?: number | undefined;
  /** Maximum matches to return (1-500) */
  max_results?: number | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format (markdown or json) */
  response_format: 'markdown' | 'json';
}

/**
 * Search for patterns in GitHub repository files using grep-like functionality.
 
 * 
 * Examples:
 * - "Find all TODOs in Python files"
 * - "Search for 'async def' in main branch"
 * - "Find error handling patterns after my last push"

 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_grep(
    input: GithubGrepInput
): Promise<string> {
    return callMCPTool<string>(
        'github_grep',
        input
    );
}
