// servers/github/workflows/github-get-workflow-runs.ts
import { callMCPTool } from '../../client.js';

export interface GithubGetWorkflowRunsInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** Workflow ID or name (optional - gets all workflows if not specified) */
  workflow_id?: string | undefined;
  /** Filter by run status */
  status?: 'queued' | 'in_progress' | 'completed' | 'waiting' | 'requested' | 'pending' | undefined;
  /** Filter by run conclusion */
  conclusion?: 'success' | 'failure' | 'neutral' | 'cancelled' | 'skipped' | 'timed_out' | 'action_required' | undefined;
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
 * Get GitHub Actions workflow run history and status.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_get_workflow_runs(
    input: GithubGetWorkflowRunsInput
): Promise<string> {
    return callMCPTool<string>(
        'github_get_workflow_runs',
        input
    );
}
