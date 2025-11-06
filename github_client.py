import asyncio
import hashlib
from typing import Any, Dict, Optional, Tuple

import httpx
import os


def _cache_key(method: str, url_path: str, params: Optional[Dict[str, Any]]) -> Tuple[str, str, str]:
    """Build a stable cache key for conditional requests.

    Uses sorted params to avoid ordering differences; params are hashed to keep the key compact.
    """
    normalized = ""
    if params:
        items = sorted((str(k), str(v)) for k, v in params.items())
        normalized = hashlib.sha256(str(items).encode("utf-8")).hexdigest()
    return method.upper(), url_path, normalized


class GhClient:
    """Shared async HTTP client with connection pooling, timeouts and polite retries.

    - Reuses connections for performance
    - Supports conditional requests via ETag caching
    - Applies exponential backoff on 5xx and honors Retry-After on 429/403-secondary
    """

    _instance: Optional["GhClient"] = None

    def __init__(self, base_url: str = "https://api.github.com", timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        # (method, path, paramsHash) -> etag / last-modified
        self._etags: Dict[Tuple[str, str, str], str] = {}
        self._last_modified: Dict[Tuple[str, str, str], str] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def instance(cls) -> "GhClient":
        if cls._instance is None:
            cls._instance = GhClient()
        return cls._instance

    async def request(
        self,
        method: str,
        path: str,
        token: Optional[str] = None,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Any = None,
        max_retries: int = 3,
    ) -> httpx.Response:
        request_headers: Dict[str, str] = {}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)

        key = _cache_key(method, path, params)

        # Add conditional headers if we have an ETag
        if method.upper() == "GET":
            etag = self._etags.get(key)
            if etag:
                request_headers["If-None-Match"] = etag
            lm = self._last_modified.get(key)
            if lm:
                request_headers["If-Modified-Since"] = lm

        backoff_seconds = 1.0
        last_exc: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                resp = await self._client.request(
                    method,
                    path,
                    params=params,
                    headers=request_headers,
                    json=json,
                    data=data,
                )
                # Optional debug: show safe rate-limit info
                if os.getenv("GITHUB_MCP_DEBUG"):
                    rl = {
                        "limit": resp.headers.get("X-RateLimit-Limit"),
                        "remaining": resp.headers.get("X-RateLimit-Remaining"),
                        "reset": resp.headers.get("X-RateLimit-Reset"),
                    }
                    print(f"[github-client] {method} {path} -> {resp.status_code} rate={rl}")

                # Store new ETag on successful responses
                if resp.status_code == 200 and method.upper() == "GET":
                    etag = resp.headers.get("ETag")
                    last_mod = resp.headers.get("Last-Modified")
                    if etag or last_mod:
                        async with self._lock:
                            if etag:
                                self._etags[key] = etag
                            if last_mod:
                                self._last_modified[key] = last_mod

                # 304 Not Modified treated as cache hit by caller
                if resp.status_code == 304:
                    return resp

                # Respect Retry-After for 429 / 403 secondary rate limit
                if resp.status_code in (429, 403) and "Retry-After" in resp.headers:
                    retry_after = resp.headers.get("Retry-After")
                    try:
                        delay = max(1.0, float(retry_after))
                    except Exception:
                        delay = backoff_seconds
                    await asyncio.sleep(delay)
                    continue

                if 500 <= resp.status_code < 600:
                    await asyncio.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue

                return resp
            except (httpx.TimeoutException, httpx.NetworkError) as exc:  # transient
                last_exc = exc
                await asyncio.sleep(backoff_seconds)
                backoff_seconds *= 2

        # Exhausted retries; raise last response error if any, otherwise last exception
        if last_exc:
            raise last_exc
        raise RuntimeError("Retry budget exceeded for GitHub request")


