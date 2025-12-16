// servers/github/releases/github-list-releases.ts
import { callMCPTool } from '../../client.js';

export interface GithubListReleasesInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Results per page (1-100, default 30) */
  per_page?: number | undefined;
  /** Page number (default 1) */
  page?: number | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * List all releases from a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_list_releases(
    input: GithubListReleasesInput
): Promise<string> {
    return callMCPTool<string>(
        'github_list_releases',
        input
    );
}
