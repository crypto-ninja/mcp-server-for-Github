// servers/github/releases/github-get-release.ts
import { callMCPTool } from '../../client.js';

export interface GithubGetReleaseInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Release tag (e.g., 'v1.1.0') or 'latest' for most recent */
  tag?: string | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * Get detailed information about a specific release or the latest release.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_get_release(
    input: GithubGetReleaseInput
): Promise<string> {
    return callMCPTool<string>(
        'github_get_release',
        input
    );
}
