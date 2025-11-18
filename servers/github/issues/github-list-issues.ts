// servers/github/issues/github-list-issues.ts
import { callMCPTool } from '../../client.js';

export interface GithubListIssuesInput {
  /** Repository owner username */
  owner: string;
  /** Repository name */
  repo: string;
  /** Issue state filter: 'open', 'closed', or 'all' */
  state: 'open' | 'closed' | 'all';
  /** Maximum results to return (1-100) */
  limit?: number | undefined;
  /** Page number for pagination */
  page?: number | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * List issues from a GitHub repository with filtering options.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_list_issues(
    input: GithubListIssuesInput
): Promise<string> {
    return callMCPTool<string>(
        'github_list_issues',
        input
    );
}
