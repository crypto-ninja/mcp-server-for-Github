// servers/github/pulls/github-create-pr-review.ts
import { callMCPTool } from '../../client.js';

export interface GithubCreatePrReviewInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Pull request number */
  pull_number: number;
  /** Review action: 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT' */
  event: string;
  /** General review comment (Markdown) */
  body?: string | undefined;
  /** Line-specific comments */
  comments?: any[] | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Create a review on a pull request with optional line-specific comments.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_create_pr_review(
    input: GithubCreatePrReviewInput
): Promise<string> {
    return callMCPTool<string>(
        'github_create_pr_review',
        input
    );
}
