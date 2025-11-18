// servers/github/pulls/github-get-pr-overview-graphql.ts
import { callMCPTool } from '../../client.js';

export interface GithubGetPrOverviewGraphqlInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Pull request number */
  pull_number: number;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * Fetch PR title, author, review states, commits count, and files changed in one GraphQL query.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_get_pr_overview_graphql(
    input: GithubGetPrOverviewGraphqlInput
): Promise<string> {
    return callMCPTool<string>(
        'github_get_pr_overview_graphql',
        input
    );
}
