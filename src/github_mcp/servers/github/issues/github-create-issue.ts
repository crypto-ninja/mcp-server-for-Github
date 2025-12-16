// servers/github/issues/github-create-issue.ts
import { callMCPTool } from '../../client.js';

export interface GithubCreateIssueInput {
  /** Repository owner username */
  owner: string;
  /** Repository name */
  repo: string;
  /** Issue title */
  title: string;
  /** Issue description/body in Markdown format */
  body?: string | undefined;
  /** List of label names to apply */
  labels?: string[] | undefined;
  /** List of usernames to assign */
  assignees?: string[] | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Create a new issue in a GitHub repository.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_create_issue(
    input: GithubCreateIssueInput
): Promise<string> {
    return callMCPTool<string>(
        'github_create_issue',
        input
    );
}
