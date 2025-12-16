// servers/github/repos/github-create-repository.ts
import { callMCPTool } from '../../client.js';

export interface GithubCreateRepositoryInput {
  /** Organization owner (if creating in an org); omit for user repo */
  owner?: string | undefined;
  /** Repository name */
  name: string;
  /** Repository description */
  description?: string | undefined;
  /** Create as private repository */
  private?: boolean | undefined;
  /** Initialize with README */
  auto_init?: boolean | undefined;
  /** Gitignore template name (e.g., 'Python') */
  gitignore_template?: string | undefined;
  /** License template (e.g., 'mit') */
  license_template?: string | undefined;
  /** GitHub personal access token */
  token?: string | undefined;
}

/**
 * Create a new repository for the authenticated user or in an organization.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_create_repository(
    input: GithubCreateRepositoryInput
): Promise<string> {
    return callMCPTool<string>(
        'github_create_repository',
        input
    );
}
