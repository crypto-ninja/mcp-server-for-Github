// servers/github/advisor/github-suggest-workflow.ts
import { callMCPTool } from '../../client.js';

export interface GithubSuggestWorkflowInput {
  /** Operation type (e.g., 'update_readme', 'create_release', 'multiple_file_edits') */
  operation: string;
  /** Estimated file size in bytes */
  file_size?: number | undefined;
  /** Number of separate edit operations */
  num_edits?: number | undefined;
  /** Number of files being modified */
  file_count?: number | undefined;
  /** Additional context about the task */
  description?: string | undefined;
  /** Optional GitHub token */
  token?: string | undefined;
  /** Output format */
  response_format: 'markdown' | 'json';
}

/**
 * Recommend whether to use API tools, local git, or a hybrid approach.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_suggest_workflow(
    input: GithubSuggestWorkflowInput
): Promise<string> {
    return callMCPTool<string>(
        'github_suggest_workflow',
        input
    );
}
