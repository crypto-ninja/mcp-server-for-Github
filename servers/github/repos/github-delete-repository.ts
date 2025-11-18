// servers/github/repos/github-delete-repository.ts
import { callMCPTool } from '../../client.js';

export interface GithubDeleteRepositoryInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** GitHub personal access token */
  token?: string | undefined;
}

/**
 * Delete a repository. Destructive; requires appropriate permissions.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_delete_repository(
    input: GithubDeleteRepositoryInput
): Promise<string> {
    return callMCPTool<string>(
        'github_delete_repository',
        input
    );
}
