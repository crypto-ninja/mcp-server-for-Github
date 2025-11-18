// servers/github/repos/github-update-repository.ts
import { callMCPTool } from '../../client.js';

export interface GithubUpdateRepositoryInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** New repository name */
  name?: string | undefined;
  /** New description */
  description?: string | undefined;
  /** Homepage URL */
  homepage?: string | undefined;
  /** Set repository visibility */
  private?: boolean | undefined;
  /** Enable issues */
  has_issues?: boolean | undefined;
  /** Enable projects */
  has_projects?: boolean | undefined;
  /** Enable wiki */
  has_wiki?: boolean | undefined;
  /** Set default branch */
  default_branch?: string | undefined;
  /** Archive/unarchive repository */
  archived?: boolean | undefined;
  /** GitHub personal access token */
  token?: string | undefined;
}

/**
 * Update repository settings such as description, visibility, and features.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_update_repository(
    input: GithubUpdateRepositoryInput
): Promise<string> {
    return callMCPTool<string>(
        'github_update_repository',
        input
    );
}
