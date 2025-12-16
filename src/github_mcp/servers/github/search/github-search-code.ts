// servers/github/search/github-search-code.ts
import { callMCPTool } from '../../client.js';

export interface GithubSearchCodeInput {
  /** Code search query (e.g., 'TODO language:python', 'function authenticate') */
  query: string;
  /** Sort field: 'indexed' (default) */
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
 * Search for code snippets across GitHub repositories.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_search_code(
    input: GithubSearchCodeInput
): Promise<string> {
    return callMCPTool<string>(
        'github_search_code',
        input
    );
}
