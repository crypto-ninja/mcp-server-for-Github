"""
Deno Runtime for executing TypeScript code with MCP tool access.

This module spawns a Deno subprocess to execute user-provided TypeScript code
with access to GitHub MCP tools via the MCP client bridge.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class DenoRuntime:
    """Manages Deno subprocess for executing TypeScript code."""
    
    def __init__(self):
        # Get project root (assuming this file is in src/github_mcp/)
        project_root = Path(__file__).parent.parent.parent
        self.deno_executor_path = project_root / "deno_executor" / "mod.ts"
        self.servers_path = project_root / "servers"
        self.project_root = project_root
        
    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Execute TypeScript code in Deno runtime.
        
        Args:
            code: TypeScript code to execute
            
        Returns:
            Dict with 'success', 'result', and optional 'error' keys
        """
        try:
            # Prepare execution command
            # Pass code via stdin to avoid Windows command-line character escaping issues
            # This prevents "Bad control" errors with special characters (backticks, quotes, etc.)
            result = subprocess.run(
                [
                    "deno",
                    "run",
                    "--allow-read",  # Read MCP server files
                    "--allow-run",   # Spawn MCP server process
                    "--allow-env",   # Access environment variables
                    "--allow-net",   # Network access for GitHub API
                    str(self.deno_executor_path)
                ],
                input=code,  # Pass code via stdin instead of command-line args
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid characters instead of failing
                timeout=60,  # 60 second timeout
                cwd=str(self.project_root),  # Run from project root
                env={
                    **os.environ,  # Pass through all environment variables (includes GitHub auth)
                    # Ensure workspace root is set
                    "MCP_WORKSPACE_ROOT": os.environ.get("MCP_WORKSPACE_ROOT", str(self.project_root)),
                }
            )
            
            # Parse JSON output
            if result.returncode == 0:
                try:
                    # Deno outputs to stdout, try to parse as JSON
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    if not stdout_text:
                        return {
                            "success": False,
                            "error": "No output from Deno execution"
                        }
                    
                    output_lines = stdout_text.split('\n')
                    # Find the last line that looks like JSON (the result)
                    json_output = None
                    for line in reversed(output_lines):
                        line = line.strip()
                        if line and (line.startswith('{') or line.startswith('[')):
                            try:
                                json_output = json.loads(line)
                                break
                            except json.JSONDecodeError:
                                continue
                    
                    if json_output:
                        return json_output
                    else:
                        # If no JSON found, return stdout as error
                        return {
                            "success": False,
                            "error": f"No JSON output found. stdout: {stdout_text[:500]}",
                            "raw_stdout": stdout_text[:1000]
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Error parsing output: {str(e)}",
                        "stdout": result.stdout[:500] if result.stdout else None,
                        "stderr": result.stderr[:500] if result.stderr else None
                    }
            else:
                # Non-zero exit code - try to parse error from stderr
                error_msg = result.stderr or result.stdout
                return {
                    "success": False,
                    "error": error_msg[:1000] if error_msg else "Unknown error",
                    "stderr": result.stderr[:500] if result.stderr else None,
                    "stdout": result.stdout[:500] if result.stdout else None
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Code execution timed out (60s limit)"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Deno not found. Please install Deno: https://deno.land"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}"
            }


# Global instance
_runtime: Optional[DenoRuntime] = None


def get_runtime() -> DenoRuntime:
    """Get or create the global Deno runtime instance."""
    global _runtime
    if _runtime is None:
        _runtime = DenoRuntime()
    return _runtime

