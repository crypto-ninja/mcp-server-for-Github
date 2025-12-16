// servers/github/files/github-delete-file.ts
import { callMCPTool } from '../../client.js';

export interface GithubDeleteFileInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** File path to delete */
  path: string;
  /** Commit message */
  message: string;
  /** SHA of the file being deleted (get from github_get_file_content) */
  sha: string;
  /** Branch name (defaults to repository's default branch) */
  branch?: string | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Delete a file from a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_delete_file(
    input: GithubDeleteFileInput
): Promise<string> {
    return callMCPTool<string>(
        'github_delete_file',
        input
    );
}
