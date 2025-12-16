// servers/github/issues/github-search-issues.ts
import { callMCPTool } from '../../client.js';

export interface GithubSearchIssuesInput {
  /** Issue search query (e.g., 'bug language:python', 'security in:title') */
  query: string;
  /** Sort field: 'created', 'updated', 'comments' */
  sort?: string | undefined;
  /** Sort order: 'asc' or 'desc' */
  order?: 'asc' | 'desc' | undefined;
  /** Maximum results (1-100) */
  limit?: number | undefined;
  /** Page number */
  page?: number | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * Search for issues across GitHub repositories with advanced filtering.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_search_issues(
    input: GithubSearchIssuesInput
): Promise<string> {
    return callMCPTool<string>(
        'github_search_issues',
        input
    );
}
