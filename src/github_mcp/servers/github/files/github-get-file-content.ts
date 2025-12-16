// servers/github/files/github-get-file-content.ts
import { callMCPTool } from '../../client.js';

export interface GithubGetFileContentInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** File path in the repository (e.g., 'src/main.py', 'README.md') */
  path: string;
  /** Branch, tag, or commit SHA (defaults to repository's default branch) */
  ref?: string | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
}

/**
 * Retrieve the content of a file from a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_get_file_content(
    input: GithubGetFileContentInput
): Promise<string> {
    return callMCPTool<string>(
        'github_get_file_content',
        input
    );
}
