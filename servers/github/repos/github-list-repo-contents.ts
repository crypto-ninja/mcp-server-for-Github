// servers/github/repos/github-list-repo-contents.ts
import { callMCPTool } from '../../client.js';

export interface GithubListRepoContentsInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Directory path (empty for root directory) */
  path?: string | undefined;
  /** Branch, tag, or commit */
  ref?: string | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * List files and directories in a repository path.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_list_repo_contents(
    input: GithubListRepoContentsInput
): Promise<string> {
    return callMCPTool<string>(
        'github_list_repo_contents',
        input
    );
}
