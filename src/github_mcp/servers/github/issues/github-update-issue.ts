// servers/github/issues/github-update-issue.ts
import { callMCPTool } from '../../client.js';

export interface GithubUpdateIssueInput {
  /** Repository owner username or organization */
  owner: string;
  /** Repository name */
  repo: string;
  /** Issue number to update */
  issue_number: number;
  /** Issue state: 'open' or 'closed' */
  state?: string | undefined;
  /** New issue title */
  title?: string | undefined;
  /** New issue body/description in Markdown format */
  body?: string | undefined;
  /** List of label names to apply (replaces existing) */
  labels?: string[] | undefined;
  /** List of usernames to assign (replaces existing) */
  assignees?: string[] | undefined;
  /** Milestone number (use null to remove milestone) */
  milestone?: number | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Update an existing GitHub issue.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_update_issue(
    input: GithubUpdateIssueInput
): Promise<string> {
    return callMCPTool<string>(
        'github_update_issue',
        input
    );
}
