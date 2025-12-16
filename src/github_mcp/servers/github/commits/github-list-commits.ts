// servers/github/commits/github-list-commits.ts
import { callMCPTool } from '../../client.js';

export interface GithubListCommitsInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Branch name, tag, or commit SHA (defaults to default branch) */
  sha?: string | undefined;
  /** Only commits containing this file path */
  path?: string | undefined;
  /** Filter by commit author (username or email) */
  author?: string | undefined;
  /** Only commits after this date (ISO 8601 format) */
  since?: string | undefined;
  /** Only commits before this date (ISO 8601 format) */
  until?: string | undefined;
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
 * List commits from a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_list_commits(
    input: GithubListCommitsInput
): Promise<string> {
    return callMCPTool<string>(
        'github_list_commits',
        input
    );
}
