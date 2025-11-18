// servers/github/releases/github-create-release.ts
import { callMCPTool } from '../../client.js';

export interface GithubCreateReleaseInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Git tag name for the release (e.g., 'v1.2.0') */
  tag_name: string;
  /** Release title (defaults to tag_name if not provided) */
  name?: string | undefined;
  /** Release notes/description in Markdown format */
  body?: string | undefined;
  /** Create as draft release (not visible publicly) */
  draft?: boolean | undefined;
  /** Mark as pre-release (not production ready) */
  prerelease?: boolean | undefined;
  /** Commit SHA, branch, or tag to create release from (defaults to default branch) */
  target_commitish?: string | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Create a new release in a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_create_release(
    input: GithubCreateReleaseInput
): Promise<string> {
    return callMCPTool<string>(
        'github_create_release',
        input
    );
}
