// servers/github/releases/github-delete-release.ts
import { callMCPTool } from '../../client.js';

export interface GithubDeleteReleaseInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Release ID to delete */
  release_id: number;
  /** Optional GitHub token */
  token?: string | undefined;
}

/**
 * Delete a release from a GitHub repository.
 * 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_delete_release(
    input: GithubDeleteReleaseInput
): Promise<string> {
    return callMCPTool<string>(
        'github_delete_release',
        input
    );
}
