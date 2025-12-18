"""
Deno Runtime for executing TypeScript code with MCP tool access.

This module spawns a Deno subprocess to execute user-provided TypeScript code
with access to GitHub MCP tools via the MCP client bridge.

Supports connection pooling for improved performance.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class DenoRuntime:
    """Manages Deno subprocess for executing TypeScript code."""

    def __init__(self):
        # Get package root (this file lives in src/github_mcp/)
        project_root = Path(__file__).parent  # src/github_mcp/ (package root)
        self.deno_executor_path = project_root / "deno_executor" / "mod.ts"
        self.servers_path = project_root / "servers"
        self.project_root = project_root

    async def execute_code_async(self, code: str) -> Dict[str, Any]:
        """
        Execute TypeScript code asynchronously using connection pool.

        Args:
            code: TypeScript code to execute

        Returns:
            Dict with 'error', 'message'/'data', and optional 'code' keys
        """
        from .utils.deno_pool import execute_with_pool

        return await execute_with_pool(code)

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
                    "--allow-all",  # All permissions (read, run, env, net)
                    str(self.deno_executor_path),
                    "--single-shot",  # Use single-shot mode for non-pooled execution
                ],
                input=code,  # Pass code via stdin instead of command-line args
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",  # Replace invalid characters instead of failing
                timeout=60,  # 60 second timeout
                cwd=str(self.project_root),  # Run from project root
                env={
                    **os.environ,  # Pass through all environment variables (includes GitHub auth)
                    # Ensure workspace root is set
                    "MCP_WORKSPACE_ROOT": os.environ.get(
                        "MCP_WORKSPACE_ROOT", str(self.project_root)
                    ),
                },
            )

            # Parse JSON output
            if result.returncode == 0:
                try:
                    # Deno outputs to stdout, try to parse as JSON
                    stdout_text = result.stdout.strip() if result.stdout else ""
                    if not stdout_text:
                        return {
                            "error": True,
                            "message": "No output from Deno execution",
                            "code": "NO_OUTPUT",
                        }

                    output_lines = stdout_text.split("\n")
                    # Find the last line that looks like JSON (the result)
                    json_output = None
                    for line in reversed(output_lines):
                        line = line.strip()
                        if line and (line.startswith("{") or line.startswith("[")):
                            try:
                                json_output = json.loads(line)
                                break
                            except json.JSONDecodeError:
                                continue

                    if json_output:
                        # Return new format as-is: {error: true/false, message/data: ...}
                        return json_output
                    else:
                        # If no JSON found, return stdout as error
                        return {
                            "error": True,
                            "message": f"No JSON output found. stdout: {stdout_text[:500]}",
                            "code": "NO_JSON_OUTPUT",
                            "details": {"raw_stdout": stdout_text[:1000]},
                        }
                except Exception as e:
                    return {
                        "error": True,
                        "message": f"Error parsing output: {str(e)}",
                        "code": "PARSE_ERROR",
                        "details": {
                            "stdout": result.stdout[:500] if result.stdout else None,
                            "stderr": result.stderr[:500] if result.stderr else None,
                        },
                    }
            else:
                # Non-zero exit code - try to parse error from stderr
                error_msg = result.stderr or result.stdout
                return {
                    "error": True,
                    "message": error_msg[:1000] if error_msg else "Unknown error",
                    "code": "EXECUTION_FAILED",
                    "details": {
                        "stderr": result.stderr[:500] if result.stderr else None,
                        "stdout": result.stdout[:500] if result.stdout else None,
                    },
                }

        except subprocess.TimeoutExpired:
            return {
                "error": True,
                "message": "Code execution timed out (60s limit)",
                "code": "TIMEOUT",
            }
        except FileNotFoundError:
            return {
                "error": True,
                "message": "Deno not found. Please install Deno: https://deno.land",
                "code": "DENO_NOT_FOUND",
            }
        except Exception as e:
            return {
                "error": True,
                "message": f"Execution error: {str(e)}",
                "code": "EXECUTION_ERROR",
            }

    async def execute(self, code: str) -> Dict[str, Any]:
        """Alias for execute_code_async for convenience/backward compatibility."""
        return await self.execute_code_async(code)


# Global instance
_runtime: Optional[DenoRuntime] = None


def get_runtime() -> DenoRuntime:
    """Get or create the global Deno runtime instance."""
    global _runtime
    if _runtime is None:
        _runtime = DenoRuntime()
    return _runtime
