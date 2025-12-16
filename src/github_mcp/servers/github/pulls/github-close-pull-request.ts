// servers/github/pulls/github-close-pull-request.ts
import { callMCPTool } from '../../client.js';

export interface GithubClosePullRequestInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Pull request number to close */
  pull_number: number;
  /** Optional comment to add when closing */
  comment?: string | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Close a pull request without merging.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_close_pull_request(
    input: GithubClosePullRequestInput
): Promise<string> {
    return callMCPTool<string>(
        'github_close_pull_request',
        input
    );
}
