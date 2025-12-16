// servers/github/search/github-search-repositories.ts
import { callMCPTool } from '../../client.js';

export interface GithubSearchRepositoriesInput {
  /** Search query (e.g., 'language:python stars:>1000', 'machine learning') */
  query: string;
  /** Sort field: 'stars', 'forks', 'updated', 'help-wanted-issues' */
  sort?: string | undefined;
  /** Sort order: 'asc' or 'desc' */
  order?: 'asc' | 'desc' | undefined;
  /** Maximum results (1-100) */
  limit?: number | undefined;
  /** Page number */
  page?: number | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * Search for repositories on GitHub with advanced filtering.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_search_repositories(
    input: GithubSearchRepositoriesInput
): Promise<string> {
    return callMCPTool<string>(
        'github_search_repositories',
        input
    );
}
