// servers/github/repos/github-archive-repository.ts
import { callMCPTool } from '../../client.js';

export interface GithubArchiveRepositoryInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** True to archive, False to unarchive */
  archived: boolean;
  /** GitHub personal access token */
  token?: string | undefined;
}

/**
 * Archive or unarchive a repository by toggling the archived flag.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_archive_repository(
    input: GithubArchiveRepositoryInput
): Promise<string> {
    return callMCPTool<string>(
        'github_archive_repository',
        input
    );
}
