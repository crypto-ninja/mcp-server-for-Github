// servers/github/files/github-create-file.ts
import { callMCPTool } from '../../client.js';

export interface GithubCreateFileInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** File path (e.g., 'docs/README.md', 'src/main.py') */
  path: string;
  /** File content (will be base64 encoded automatically) */
  content: string;
  /** Commit message */
  message: string;
  /** Branch name (defaults to repository's default branch) */
  branch?: string | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Create a new file in a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_create_file(
    input: GithubCreateFileInput
): Promise<string> {
    return callMCPTool<string>(
        'github_create_file',
        input
    );
}
