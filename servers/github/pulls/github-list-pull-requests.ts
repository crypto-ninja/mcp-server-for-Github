// servers/github/pulls/github-list-pull-requests.ts
import { callMCPTool } from '../../client.js';

export interface GithubListPullRequestsInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** PR state: 'open', 'closed', or 'all' */
  state: 'open' | 'closed' | 'all';
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
 * List pull requests from a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_list_pull_requests(
    input: GithubListPullRequestsInput
): Promise<string> {
    return callMCPTool<string>(
        'github_list_pull_requests',
        input
    );
}
