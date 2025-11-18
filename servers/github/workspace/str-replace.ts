// servers/github/workspace/str-replace.ts
import { callMCPTool } from '../../client.js';

export interface StrReplaceInput {
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
 * Replace an exact string match in a file with a new string.
 
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function str_replace(
    input: StrReplaceInput
): Promise<string> {
    return callMCPTool<string>(
        'str_replace',
        input
    );
}
