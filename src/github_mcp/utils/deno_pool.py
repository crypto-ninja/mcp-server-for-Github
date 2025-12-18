"""Deno subprocess connection pool for efficient code execution."""

import asyncio
import time
import json
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PooledProcessState(Enum):
    IDLE = "idle"
    BUSY = "busy"
    UNHEALTHY = "unhealthy"


@dataclass
class PooledDenoProcess:
    """A pooled Deno subprocess."""

    process: asyncio.subprocess.Process
    state: PooledProcessState = PooledProcessState.IDLE
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    request_count: int = 0
    mcp_connected: bool = False  # Track MCP connection state (set by executor)

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at

    @property
    def idle_seconds(self) -> float:
        return time.time() - self.last_used


class DenoConnectionPool:
    """Connection pool for Deno subprocesses."""

    def __init__(
        self,
        min_size: int = 1,
        max_size: int = 5,
        max_idle_time: float = 300.0,  # 5 minutes
        max_lifetime: float = 3600.0,  # 1 hour
        max_requests_per_process: int = 1000,
        health_check_interval: float = 30.0,
    ):
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.max_lifetime = max_lifetime
        self.max_requests_per_process = max_requests_per_process
        self.health_check_interval = health_check_interval

        # Get package root (go up from src/github_mcp/utils/ to src/github_mcp/)
        project_root = Path(
            __file__
        ).parent.parent  # utils -> github_mcp (package root)
        self.deno_executor_path = project_root / "deno_executor" / "mod.ts"
        self.project_root = project_root

        self._pool: List[PooledDenoProcess] = []
        self._lock = asyncio.Lock()
        self._initialized = False
        self._shutdown = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._waiting_requests: List[asyncio.Future] = []

    async def initialize(self):
        """Initialize the pool with minimum processes."""
        if self._initialized:
            return

        async with self._lock:
            for _ in range(self.min_size):
                process = await self._create_process()
                if process:
                    self._pool.append(process)

            self._initialized = True
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info(f"Deno pool initialized with {len(self._pool)} processes")

    async def _create_process(self) -> Optional[PooledDenoProcess]:
        """Create a new Deno subprocess."""
        try:
            # Use unified executor (mod.ts supports both pooled and single-shot modes)
            executor_path = self.deno_executor_path

            # Start Deno process with the MCP bridge
            process = await asyncio.create_subprocess_exec(
                "deno",
                "run",
                "--allow-all",  # All permissions (read, run, env, net)
                str(executor_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_root),
                env={
                    **os.environ,
                    "MCP_WORKSPACE_ROOT": os.environ.get(
                        "MCP_WORKSPACE_ROOT", str(self.project_root)
                    ),
                },
            )

            return PooledDenoProcess(process=process)
        except Exception as e:
            logger.error(f"Failed to create Deno process: {e}")
            return None

    async def acquire(self) -> Optional[PooledDenoProcess]:
        """Acquire a process from the pool."""
        async with self._lock:
            # Find an idle process
            for pooled in self._pool:
                if pooled.state == PooledProcessState.IDLE:
                    if self._is_process_healthy(pooled):
                        pooled.state = PooledProcessState.BUSY
                        pooled.last_used = time.time()
                        pooled.request_count += 1
                        return pooled
                    else:
                        # Remove unhealthy process
                        await self._terminate_process(pooled)
                        self._pool.remove(pooled)

            # No idle process available, create new if under max
            if len(self._pool) < self.max_size:
                new_process = await self._create_process()
                if new_process:
                    new_process.state = PooledProcessState.BUSY
                    new_process.request_count = 1
                    self._pool.append(new_process)
                    return new_process

            # Pool exhausted, wait for one to become available
            return None

    async def release(self, pooled: PooledDenoProcess):
        """Release a process back to the pool."""
        async with self._lock:
            if pooled in self._pool:
                if self._is_process_healthy(pooled):
                    pooled.state = PooledProcessState.IDLE
                    pooled.last_used = time.time()

                    # Notify waiting requests
                    if self._waiting_requests:
                        future = self._waiting_requests.pop(0)
                        if not future.done():
                            future.set_result(None)
                else:
                    await self._terminate_process(pooled)
                    self._pool.remove(pooled)

                    # Maintain minimum pool size
                    if len(self._pool) < self.min_size:
                        new_process = await self._create_process()
                        if new_process:
                            self._pool.append(new_process)

    def _is_process_healthy(self, pooled: PooledDenoProcess) -> bool:
        """Check if a process is healthy."""
        # Check if process is still running
        if pooled.process.returncode is not None:
            return False

        # Check lifetime
        if pooled.age_seconds > self.max_lifetime:
            return False

        # Check request count
        if pooled.request_count >= self.max_requests_per_process:
            return False

        return True

    async def _terminate_process(self, pooled: PooledDenoProcess):
        """Terminate a process."""
        try:
            if pooled.process.stdin:
                pooled.process.stdin.close()
            if pooled.process.returncode is None:
                pooled.process.terminate()
                try:
                    await asyncio.wait_for(pooled.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    pooled.process.kill()
                    await pooled.process.wait()
        except Exception as e:
            logger.error(f"Error terminating process: {e}")

    async def _health_check_loop(self):
        """Periodic health check loop."""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._cleanup_idle_processes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    async def _cleanup_idle_processes(self):
        """Clean up idle processes that have been idle too long."""
        async with self._lock:
            to_remove = []
            for pooled in self._pool:
                if pooled.state == PooledProcessState.IDLE:
                    if pooled.idle_seconds > self.max_idle_time:
                        if len(self._pool) - len(to_remove) > self.min_size:
                            to_remove.append(pooled)

            for pooled in to_remove:
                await self._terminate_process(pooled)
                self._pool.remove(pooled)
                logger.info(
                    f"Removed idle Deno process (idle for {pooled.idle_seconds:.1f}s)"
                )

    async def shutdown(self):
        """Shutdown the pool."""
        self._shutdown = True

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            for pooled in self._pool:
                await self._terminate_process(pooled)
            self._pool.clear()

        logger.info("Deno pool shutdown complete")

    async def close(self):
        """Alias for shutdown to match typical pool API."""
        await self.shutdown()

    @property
    def stats(self) -> dict:
        """Get pool statistics."""
        idle = sum(1 for p in self._pool if p.state == PooledProcessState.IDLE)
        busy = sum(1 for p in self._pool if p.state == PooledProcessState.BUSY)
        return {
            "total": len(self._pool),
            "idle": idle,
            "busy": busy,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "waiting_requests": len(self._waiting_requests),
        }


# Global pool instance
_pool: Optional[DenoConnectionPool] = None


async def get_pool() -> DenoConnectionPool:
    """Get or create the global pool instance."""
    global _pool
    if _pool is None:
        min_size = int(os.environ.get("DENO_POOL_MIN_SIZE", "1"))
        max_size = int(os.environ.get("DENO_POOL_MAX_SIZE", "5"))
        max_idle_time = float(os.environ.get("DENO_POOL_MAX_IDLE_TIME", "300"))
        max_lifetime = float(os.environ.get("DENO_POOL_MAX_LIFETIME", "3600"))
        max_requests = int(os.environ.get("DENO_POOL_MAX_REQUESTS", "1000"))

        _pool = DenoConnectionPool(
            min_size=min_size,
            max_size=max_size,
            max_idle_time=max_idle_time,
            max_lifetime=max_lifetime,
            max_requests_per_process=max_requests,
        )
        await _pool.initialize()
    return _pool


async def close_pool():
    """Close and reset the global pool if it exists."""
    global _pool
    if _pool is not None:
        try:
            await _pool.shutdown()
        finally:
            _pool = None


async def execute_with_pool(code: str) -> Dict[str, Any]:
    """Execute code using a pooled Deno process."""
    pool = await get_pool()
    pooled = await pool.acquire()

    if pooled is None:
        return {
            "error": True,
            "message": "No available Deno processes in pool (pool exhausted)",
            "code": "POOL_EXHAUSTED",
        }

    try:
        # Send code to process and get result
        result = await _execute_on_process(pooled, code)
        return result
    finally:
        await pool.release(pooled)


async def _execute_on_process(pooled: PooledDenoProcess, code: str) -> Dict[str, Any]:
    """Execute code on a specific pooled process."""
    try:
        process = pooled.process

        # Check if process is still alive
        if process.returncode is not None:
            return {
                "error": True,
                "message": f"Deno process terminated (exit code: {process.returncode})",
                "code": "PROCESS_TERMINATED",
            }

        # Write code to stdin
        if not process.stdin:
            return {
                "error": True,
                "message": "Process stdin is closed",
                "code": "STDIN_CLOSED",
            }

        # Send code as JSON line to support multiline snippets
        request = json.dumps({"code": code}) + "\n"
        code_bytes = request.encode("utf-8")
        process.stdin.write(code_bytes)
        await process.stdin.drain()

        logger.debug(f"Sent code to pooled process: {len(code_bytes)} bytes")

        # Read response from stdout with timeout
        if not process.stdout:
            return {
                "error": True,
                "message": "Process stdout is closed",
                "code": "STDOUT_CLOSED",
            }

        # Read output line by line until we get JSON
        # The Deno executor outputs JSON to stdout
        # Stderr messages go to stderr (MCP connection logs)
        output_lines = []
        timeout = 60.0  # 60 second timeout
        start_time = time.time()
        last_json_line = None

        # Read stderr in background to prevent blocking (MCP logs go here)
        stderr_task = None
        if process.stderr:

            async def read_stderr():
                try:
                    while True:
                        line = await process.stderr.readline()
                        if not line:
                            break
                        # Just consume stderr, don't process it
                        logger.debug(
                            f"Stderr: {line.decode('utf-8', errors='replace').strip()[:100]}"
                        )
                except Exception as e:
                    logger.debug(f"Stderr reader error: {e}")

            stderr_task = asyncio.create_task(read_stderr())

        # Give the process a moment to start processing
        # The pooled executor initializes MCP connection at startup, which may take time
        # Wait a bit longer for first execution
        await asyncio.sleep(0.1)

        while True:
            if time.time() - start_time > timeout:
                if stderr_task and not stderr_task.done():
                    stderr_task.cancel()
                return {
                    "error": True,
                    "message": "Code execution timed out (60s limit)",
                    "code": "TIMEOUT",
                }

            try:
                # Read a line with timeout
                line = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)

                if not line:
                    # No more data immediately, wait a bit for buffered output
                    await asyncio.sleep(0.2)
                    # Try one more read
                    try:
                        line = await asyncio.wait_for(
                            process.stdout.readline(), timeout=0.3
                        )
                    except asyncio.TimeoutError:
                        # Really no more data, check if we have a JSON line
                        if last_json_line:
                            try:
                                result = json.loads(last_json_line)
                                logger.debug(
                                    f"Found JSON after EOF: {last_json_line[:100]}"
                                )
                                if stderr_task and not stderr_task.done():
                                    stderr_task.cancel()
                                return result
                            except json.JSONDecodeError:
                                pass
                        break

                line_text = line.decode("utf-8", errors="replace").strip()
                if not line_text:
                    continue

                output_lines.append(line_text)
                logger.debug(f"Read line: {line_text[:100]}")

                # Check if this line is JSON (starts with { or [)
                if line_text and (
                    line_text.startswith("{") or line_text.startswith("[")
                ):
                    try:
                        # Try to parse as JSON
                        result = json.loads(line_text)
                        last_json_line = line_text
                        logger.debug(
                            f"Parsed JSON successfully: {result.get('error', 'success')}"
                        )
                        # This looks like valid JSON, wait a tiny bit to see if there's more
                        try:
                            await asyncio.wait_for(
                                process.stdout.readline(), timeout=0.1
                            )
                        except (asyncio.TimeoutError, Exception):
                            # No more data, return this result
                            pass
                        if stderr_task and not stderr_task.done():
                            stderr_task.cancel()
                        return result
                    except json.JSONDecodeError as e:
                        # Not valid JSON, continue
                        logger.debug(f"JSON parse error: {e}, line: {line_text[:100]}")
                        continue

            except asyncio.TimeoutError:
                # Timeout reading, check if we have a JSON result
                if last_json_line:
                    try:
                        result = json.loads(last_json_line)
                        logger.debug(
                            f"Found JSON after timeout: {last_json_line[:100]}"
                        )
                        if stderr_task and not stderr_task.done():
                            stderr_task.cancel()
                        return result
                    except json.JSONDecodeError:
                        pass
                # Continue reading
                continue
            except Exception as e:
                # If we have a JSON result, return it even if there's an error
                if last_json_line:
                    try:
                        result = json.loads(last_json_line)
                        logger.debug(f"Found JSON after error: {last_json_line[:100]}")
                        if stderr_task and not stderr_task.done():
                            stderr_task.cancel()
                        return result
                    except json.JSONDecodeError:
                        pass
                logger.error(f"Error reading from process: {e}")
                if stderr_task and not stderr_task.done():
                    stderr_task.cancel()
                return {
                    "error": True,
                    "message": f"Error reading from process: {str(e)}",
                    "code": "READ_ERROR",
                }

        # Cancel stderr reader if still running
        if stderr_task and not stderr_task.done():
            stderr_task.cancel()
            try:
                await stderr_task
            except asyncio.CancelledError:
                pass

        # If we get here, we didn't find JSON
        output_text = "\n".join(output_lines)
        if last_json_line:
            try:
                return json.loads(last_json_line)
            except json.JSONDecodeError:
                pass

        # Debug: log what we actually received
        logger.debug(
            f"Pool execution - No JSON found. Lines: {len(output_lines)}, Output: {output_text[:200]}"
        )

        return {
            "error": True,
            "message": f"No JSON output found. Output: {output_text[:500]}",
            "code": "NO_JSON_OUTPUT",
            "details": {
                "raw_output": output_text[:1000],
                "line_count": len(output_lines),
            },
        }

    except Exception as e:
        return {
            "error": True,
            "message": f"Execution error: {str(e)}",
            "code": "EXECUTION_ERROR",
        }
