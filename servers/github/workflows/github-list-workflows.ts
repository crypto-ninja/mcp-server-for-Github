// servers/github/workflows/github-list-workflows.ts
import { callMCPTool } from '../../client.js';

export interface GithubListWorkflowsInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * List GitHub Actions workflows for a repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_list_workflows(
    input: GithubListWorkflowsInput
): Promise<string> {
    return callMCPTool<string>(
        'github_list_workflows',
        input
    );
}
