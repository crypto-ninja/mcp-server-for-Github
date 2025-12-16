// servers/github/repos/github-get-repo-info.ts
import { callMCPTool } from '../../client.js';

export interface GithubGetRepoInfoInput {
  /** Repository owner username or organization (e.g., 'octocat', 'github') */
  owner: string;
  /** Repository name (e.g., 'hello-world', 'docs') */
  repo: string;
  /** Optional GitHub personal access token for authenticated requests */
  token?: string | undefined;
  /** Output format: 'markdown' for human-readable or 'json' for machine-readable */
  response_format: 'markdown' | 'json';
}

/**
 * Retrieve detailed information about a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_get_repo_info(
    input: GithubGetRepoInfoInput
): Promise<string> {
    return callMCPTool<string>(
        'github_get_repo_info',
        input
    );
}
