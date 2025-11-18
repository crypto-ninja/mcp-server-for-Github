// servers/github/files/github-update-file.ts
import { callMCPTool } from '../../client.js';

export interface GithubUpdateFileInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** File path to update */
  path: string;
  /** New file content */
  content: string;
  /** Commit message */
  message: string;
  /** SHA of the file being replaced (get from github_get_file_content) */
  sha: string;
  /** Branch name (defaults to repository's default branch) */
  branch?: string | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Update an existing file in a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_update_file(
    input: GithubUpdateFileInput
): Promise<string> {
    return callMCPTool<string>(
        'github_update_file',
        input
    );
}
