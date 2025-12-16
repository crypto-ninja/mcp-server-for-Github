// servers/github/users/github-get-user-info.ts
import { callMCPTool } from '../../client.js';

export interface GithubGetUserInfoInput {
  /** GitHub username (e.g., 'octocat') */
  username: string;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * Retrieve information about a GitHub user or organization.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_get_user_info(
    input: GithubGetUserInfoInput
): Promise<string> {
    return callMCPTool<string>(
        'github_get_user_info',
        input
    );
}
