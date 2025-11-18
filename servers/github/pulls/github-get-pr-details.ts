// servers/github/pulls/github-get-pr-details.ts
import { callMCPTool } from '../../client.js';

export interface GithubGetPrDetailsInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Pull request number */
  pull_number: number;
  /** Include review information */
  include_reviews?: boolean | undefined;
  /** Include commit information */
  include_commits?: boolean | undefined;
  /** Include changed files (can be large) */
  include_files?: boolean | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * Get comprehensive details about a specific pull request.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_get_pr_details(
    input: GithubGetPrDetailsInput
): Promise<string> {
    return callMCPTool<string>(
        'github_get_pr_details',
        input
    );
}
