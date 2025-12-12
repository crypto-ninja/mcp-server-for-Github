"""Tests for Deno connection pool."""

import pytest
import asyncio
from src.github_mcp.utils.deno_pool import DenoConnectionPool


class TestDenoPool:
    """Test suite for Deno connection pool."""

    @pytest.mark.asyncio
    async def test_pool_initialization(self):
        """Test pool initializes with minimum processes."""
        pool = DenoConnectionPool(min_size=1, max_size=5)
        await pool.initialize()

        assert len(pool._pool) >= 1
        assert pool._initialized is True

        await pool.shutdown()

    @pytest.mark.asyncio
    async def test_acquire_release(self):
        """Test acquiring and releasing processes."""
        pool = DenoConnectionPool(min_size=1, max_size=3)
        await pool.initialize()

        # Acquire a process
        process = await pool.acquire()
        if process:  # May be None if Deno not available
            assert process.state.value == "busy"

            # Release it
            await pool.release(process)
            assert process.state.value == "idle"

        await pool.shutdown()

    @pytest.mark.asyncio
    async def test_pool_stats(self):
        """Test pool statistics."""
        pool = DenoConnectionPool(min_size=1, max_size=5)
        await pool.initialize()

        stats = pool.stats
        assert "total" in stats
        assert "idle" in stats
        assert "busy" in stats
        assert "min_size" in stats
        assert "max_size" in stats
        assert stats["total"] >= 1

        await pool.shutdown()

    @pytest.mark.asyncio
    async def test_pool_max_size(self):
        """Test pool respects max size limit."""
        pool = DenoConnectionPool(min_size=1, max_size=2)
        await pool.initialize()

        # Try to acquire more than max_size
        processes = []
        for _ in range(3):
            proc = await pool.acquire()
            if proc:
                processes.append(proc)

        # Should not exceed max_size
        assert len(processes) <= 2

        # Release all
        for proc in processes:
            await pool.release(proc)

        await pool.shutdown()

    @pytest.mark.asyncio
    async def test_pool_cleanup(self):
        """Test pool cleanup of idle processes."""
        pool = DenoConnectionPool(
            min_size=1,
            max_size=5,
            max_idle_time=0.1,  # Very short idle time for testing
            health_check_interval=0.2,
        )
        await pool.initialize()

        # Acquire and release a process
        proc = await pool.acquire()
        if proc:
            await pool.release(proc)

            # Wait for cleanup
            await asyncio.sleep(0.3)

            # Pool should still have at least min_size
            assert len(pool._pool) >= pool.min_size

        await pool.shutdown()
