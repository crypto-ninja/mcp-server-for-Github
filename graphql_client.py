from typing import Any, Dict, Optional
import httpx


class GraphQLClient:
    def __init__(self, base_url: str = "https://api.github.com/graphql") -> None:
        self._url = base_url

    async def query(self, token: str, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }) as client:
            resp = await client.post(self._url, json={"query": query, "variables": variables or {}})
            resp.raise_for_status()
            return resp.json()


