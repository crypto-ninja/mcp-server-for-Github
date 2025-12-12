"""Pool statistics utility for monitoring Deno connection pool."""

from typing import Dict, Any


async def get_pool_stats() -> Dict[str, Any]:
    """Get Deno connection pool statistics."""
    try:
        from .deno_pool import get_pool

        pool = await get_pool()
        return pool.stats
    except ImportError:
        return {"error": "Pool not available", "enabled": False}
    except Exception as e:
        return {"error": str(e), "enabled": False}
