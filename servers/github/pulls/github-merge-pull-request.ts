// servers/github/pulls/github-merge-pull-request.ts
import { callMCPTool } from '../../client.js';

export interface GithubMergePullRequestInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Pull request number */
  pull_number: number;
  /** Merge method: 'merge', 'squash', or 'rebase' */
  merge_method?: string | undefined;
  /** Custom commit title for merge commit */
  commit_title?: string | undefined;
  /** Custom commit message for merge commit */
  commit_message?: string | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Merge a pull request using the specified merge method.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_merge_pull_request(
    input: GithubMergePullRequestInput
): Promise<string> {
    return callMCPTool<string>(
        'github_merge_pull_request',
        input
    );
}
