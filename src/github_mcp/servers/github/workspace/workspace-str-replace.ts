// servers/github/workspace/workspace-str-replace.ts
import { callMCPTool } from '../../client.js';

export interface WorkspaceStrReplaceInput {
  /** Relative path to file under repository root */
  path: string;
  /** Exact string to find and replace (must be unique match) */
  old_str: string;
  /** Replacement string */
  new_str: string;
  /** Optional description of the change */
  description?: string | undefined;
}

/**
 * [LOCAL] Replace an exact string match in a local workspace file.
 * 
 * For editing files on GitHub remote, use github_str_replace instead.
 * 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function workspace_str_replace(
    input: WorkspaceStrReplaceInput
): Promise<string> {
    return callMCPTool<string>(
        'workspace_str_replace',
        input
    );
}

