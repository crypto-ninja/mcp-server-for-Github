// servers/github/remote/github-str-replace.ts
import { callMCPTool } from '../../client.js';

export interface GithubStrReplaceInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** File path in repository */
  path: string;
  /** Exact string to find and replace (must be unique match) */
  old_str: string;
  /** Replacement string */
  new_str: string;
  /** Branch, tag, or commit SHA (defaults to default branch) */
  ref?: string | undefined;
  /** Custom commit message (auto-generated if not provided) */
  commit_message?: string | undefined;
  /** Optional description of the change */
  description?: string | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
}

/**
 * Replace an exact string match in a GitHub repository file with a new string.
 
 * 
 * Examples:
 * - "Replace version number in README.md on GitHub"
 * - "Update configuration value in remote file"
 * - "Fix typo in GitHub documentation"

 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_str_replace(
    input: GithubStrReplaceInput
): Promise<string> {
    return callMCPTool<string>(
        'github_str_replace',
        input
    );
}
