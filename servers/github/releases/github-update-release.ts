// servers/github/releases/github-update-release.ts
import { callMCPTool } from '../../client.js';

export interface GithubUpdateReleaseInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Release ID or tag name (e.g., 'v1.2.0') */
  release_id: string;
  /** New tag name (use carefully!) */
  tag_name?: string | undefined;
  /** New release title */
  name?: string | undefined;
  /** New release notes/description in Markdown format */
  body?: string | undefined;
  /** Set draft status */
  draft?: boolean | undefined;
  /** Set pre-release status */
  prerelease?: boolean | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Update an existing GitHub release.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_update_release(
    input: GithubUpdateReleaseInput
): Promise<string> {
    return callMCPTool<string>(
        'github_update_release',
        input
    );
}
