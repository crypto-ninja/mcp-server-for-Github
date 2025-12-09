#!/usr/bin/env python3
"""Simple test of pool execution."""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["DENO_POOL_ENABLED"] = "true"

from src.github_mcp.utils.deno_pool import get_pool, execute_with_pool

async def test():
    print("Initializing pool...")
    pool = await get_pool()
    print(f"Pool initialized: {pool.stats}")
    
    print("\nExecuting simple code...")
    result = await execute_with_pool('return 1 + 1;')
    print(f"Result: {result}")
    print(f"Error: {result.get('error')}")
    print(f"Data: {result.get('data')}")
    
    await pool.shutdown()

if __name__ == "__main__":
    asyncio.run(test())

