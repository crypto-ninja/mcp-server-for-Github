// servers/github/pulls/github-create-pull-request.ts
import { callMCPTool } from '../../client.js';

export interface GithubCreatePullRequestInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Pull request title */
  title: string;
  /** Source branch name */
  head: string;
  /** Target branch name (default: main) */
  base: string;
  /** Pull request description in Markdown format */
  body?: string | undefined;
  /** Create as draft pull request */
  draft?: boolean | undefined;
  /** Allow maintainers to modify the PR */
  maintainer_can_modify?: boolean | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Create a new pull request in a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_create_pull_request(
    input: GithubCreatePullRequestInput
): Promise<string> {
    return callMCPTool<string>(
        'github_create_pull_request',
        input
    );
}
