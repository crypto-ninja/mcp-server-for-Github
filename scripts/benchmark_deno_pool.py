#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Benchmark Deno execution with and without pooling."""

import asyncio
import time
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def single_execution(
    runtime, code: str = "return 1 + 1;"
) -> tuple[float, bool, dict]:
    """Execute code and return (elapsed_ms, success, result)."""
    start = time.perf_counter()
    try:
        if hasattr(runtime, "execute_code_async"):
            result = await runtime.execute_code_async(code)
        else:
            result = runtime.execute_code(code)
        elapsed = (time.perf_counter() - start) * 1000
        success = not result.get("error", False)
        return elapsed, success, result
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        print(f"    Error: {e}")
        return elapsed, False, {"error": str(e)}


async def benchmark_baseline(iterations: int = 5) -> list[float]:
    """Benchmark without pooling (fresh process each time using sync execute_code)."""
    # Use sync execute_code which uses --single-shot mode (no pooling)
    from src.github_mcp.deno_runtime import DenoRuntime

    print(f"\nBaseline (no pool) - {iterations} iterations:")
    times = []

    for i in range(iterations):
        runtime = DenoRuntime()
        elapsed, success, result = await single_execution(runtime, "return 1 + 1;")
        status = "OK" if success else "ERR"
        error_msg = ""
        if not success and result.get("message"):
            error_msg = f" - {result.get('message')[:50]}"
        print(f"  [{i + 1}] {elapsed:.0f}ms {status}{error_msg}")
        if success:
            times.append(elapsed)
        await asyncio.sleep(0.1)  # Small delay between runs

    return times


async def benchmark_pooled(iterations: int = 5, warmup: int = 2) -> list[float]:
    """Benchmark with pooling (default behavior)."""

    from src.github_mcp.deno_runtime import DenoRuntime
    from src.github_mcp.utils.deno_pool import get_pool

    print(f"\nPooled - {warmup} warmup + {iterations} iterations:")

    # Initialize and warm up pool
    print("  Initializing pool...")
    pool = await get_pool()
    runtime = DenoRuntime()

    # Warmup runs (not counted)
    print("  Warming up...")
    for i in range(warmup):
        elapsed, success, _ = await single_execution(runtime, "return 'warmup';")
        status = "OK" if success else "ERR"
        print(f"    Warmup {i + 1}: {elapsed:.0f}ms {status}")
        await asyncio.sleep(0.2)  # Delay between warmup runs

    print("  Measuring...")
    times = []

    for i in range(iterations):
        elapsed, success, result = await single_execution(runtime, "return 1 + 1;")
        status = "OK" if success else "ERR"
        error_msg = ""
        if not success and result.get("message"):
            error_msg = f" - {result.get('message')[:50]}"
        print(f"  [{i + 1}] {elapsed:.0f}ms {status}{error_msg}")
        if success:
            times.append(elapsed)
        await asyncio.sleep(0.1)  # Small delay to avoid overwhelming

    await pool.shutdown()
    return times


async def main():
    print("=" * 60)
    print("Deno Connection Pool Benchmark")
    print("=" * 60)

    # Run baseline
    baseline_times = await benchmark_baseline(5)

    # Small pause between tests
    await asyncio.sleep(2)

    # Run pooled
    pooled_times = await benchmark_pooled(5, warmup=2)

    # Results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    if baseline_times:
        baseline_avg = sum(baseline_times) / len(baseline_times)
        print("\nBaseline (no pool):")
        print(f"  Successful runs: {len(baseline_times)}/5")
        print(f"  Average: {baseline_avg:.0f}ms")
        print(f"  Min: {min(baseline_times):.0f}ms")
        print(f"  Max: {max(baseline_times):.0f}ms")
    else:
        print("\nBaseline: No successful runs!")
        baseline_avg = 0

    print()

    if pooled_times:
        pooled_avg = sum(pooled_times) / len(pooled_times)
        print("Pooled:")
        print(f"  Successful runs: {len(pooled_times)}/5")
        print(f"  Average: {pooled_avg:.0f}ms")
        print(f"  Min: {min(pooled_times):.0f}ms")
        print(f"  Max: {max(pooled_times):.0f}ms")
    else:
        print("Pooled: No successful runs!")
        pooled_avg = 0

    print()

    if baseline_avg > 0 and pooled_avg > 0:
        improvement = (1 - pooled_avg / baseline_avg) * 100
        speedup = baseline_avg / pooled_avg
        print(f"Improvement: {improvement:.1f}% faster")
        print(f"Speedup: {speedup:.2f}x")
    elif baseline_avg > 0:
        print("⚠️  Pooled execution had errors - cannot calculate improvement")
    else:
        print("ERROR: Both baseline and pooled had errors")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
