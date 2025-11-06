import asyncio
import time
from typing import Optional

import httpx
import jwt  # PyJWT


class AppTokenCache:
    """Caches the current installation token and refreshes before expiry."""

    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_token(self, *, app_id: str, private_key_pem: str, installation_id: str) -> str:
        now = time.time()
        async with self._lock:
            if self._token and now < self._expires_at - 60:  # refresh 60s before expiry
                return self._token
            token = _make_app_jwt(app_id, private_key_pem)
            async with httpx.AsyncClient(timeout=30.0, headers={
                "Accept": "application/vnd.github+json"
            }) as hx:
                resp = await hx.post(
                    f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                    headers={"Authorization": f"Bearer {token}"},
                )
                resp.raise_for_status()
                data = resp.json()
                self._token = data["token"]
                # GitHub returns expires_at in ISO 8601; approximate with max 55 minutes
                self._expires_at = now + 55 * 60
                return self._token


def _make_app_jwt(app_id: str, private_key_pem: str) -> str:
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 9 * 60, "iss": app_id}
    return jwt.encode(payload, private_key_pem, algorithm="RS256")


_CACHE = AppTokenCache()


async def get_installation_token_from_env() -> Optional[str]:
    """Return an installation token if required env vars are set; else None."""
    import os

    app_id = os.getenv("GITHUB_APP_ID")
    private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
    installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
    if not app_id or not private_key or not installation_id:
        return None
    return await _CACHE.get_token(app_id=app_id, private_key_pem=private_key, installation_id=installation_id)


