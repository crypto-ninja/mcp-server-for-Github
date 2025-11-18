// servers/github/repos/github-transfer-repository.ts
import { callMCPTool } from '../../client.js';

export interface GithubTransferRepositoryInput {
  /** Current repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** New owner (user or org) */
  new_owner: string;
  /** IDs of teams to add to the repository (org only) */
  team_ids?: number[] | undefined;
  /** GitHub personal access token */
  token?: string | undefined;
}

/**
 * Transfer a repository to a new owner (user or organization).
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_transfer_repository(
    input: GithubTransferRepositoryInput
): Promise<string> {
    return callMCPTool<string>(
        'github_transfer_repository',
        input
    );
}
