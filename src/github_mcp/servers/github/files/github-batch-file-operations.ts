// servers/github/files/github-batch-file-operations.ts
import { callMCPTool } from '../../client.js';

export interface GithubBatchFileOperationsInput {
  /** Repository owner */
  owner: string;
  /** Repository name */
  repo: string;
  /** List of file operations to perform */
  operations: any[];
  /** Commit message for all operations */
  message: string;
  /** Target branch (defaults to default branch) */
  branch?: string | undefined;
  /** GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided) */
  token?: string | undefined;
}

/**
 * Perform multiple file operations (create/update/delete) in a single commit.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function github_batch_file_operations(
    input: GithubBatchFileOperationsInput
): Promise<string> {
    return callMCPTool<string>(
        'github_batch_file_operations',
        input
    );
}
