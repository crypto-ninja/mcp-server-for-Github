"""
GitHub App Authentication Module

Supports GitHub App authentication with automatic fallback to Personal Access Token.
Handles JWT generation, installation token caching, and credential loading from
environment variables or file paths.
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Optional

import httpx
import jwt  # PyJWT


class GitHubAppAuth:
    """GitHub App authentication handler with token caching."""

    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    def clear_token_cache(self) -> None:
        """Manually clear the cached installation token.
        
        Call this after:
        - Updating GitHub App permissions
        - Re-installing the app
        - Any permission-related changes
        """
        self._token = None
        self._expires_at = 0.0

    async def get_installation_token(
        self, *, app_id: str, private_key_pem: str, installation_id: str, force_refresh: bool = False
    ) -> str:
        """
        Get installation access token with 1-hour caching.
        
        Args:
            app_id: GitHub App ID
            private_key_pem: Private key in PEM format (string)
            installation_id: Installation ID
            force_refresh: If True, clear cache and get fresh token
            
        Returns:
            Installation access token
        """
        if force_refresh:
            self.clear_token_cache()
            
        now = time.time()
        async with self._lock:
            # Refresh 60 seconds before expiry (tokens last ~1 hour)
            if self._token and now < self._expires_at - 60:
                return self._token
            
            # Generate JWT and request new installation token
            jwt_token = self._generate_jwt(app_id, private_key_pem)
            
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={"Accept": "application/vnd.github+json"}
            ) as client:
                response = await client.post(
                    f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                    headers={"Authorization": f"Bearer {jwt_token}"},
                )
                response.raise_for_status()
                data = response.json()
                
                self._token = data["token"]
                # GitHub tokens expire in 1 hour; cache for 55 minutes to be safe
                self._expires_at = now + (55 * 60)
                
                return self._token

    def _generate_jwt(self, app_id: str, private_key_pem: str) -> str:
        """
        Generate JWT token for GitHub App authentication.
        
        Args:
            app_id: GitHub App ID
            private_key_pem: Private key in PEM format
            
        Returns:
            JWT token string
        """
        now = int(time.time())
        payload = {
            "iat": now - 60,  # Issued 60 seconds ago (clock skew tolerance)
            "exp": now + (9 * 60),  # Expires in 9 minutes (max 10 min allowed)
            "iss": app_id
        }
        return jwt.encode(payload, private_key_pem, algorithm="RS256")

    def get_auth_headers(self, token: str) -> dict:
        """
        Get authorization headers for GitHub API requests.
        
        Args:
            token: Installation access token or PAT
            
        Returns:
            Dictionary with Authorization header
        """
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }


# Global instance for token caching
_app_auth = GitHubAppAuth()


def load_private_key_from_file(key_path: str) -> Optional[str]:
    """
    Load private key from file path.
    
    Supports both absolute and relative paths, with Windows path handling.
    
    Args:
        key_path: Path to private key file (.pem)
        
    Returns:
        Private key content as string, or None if file not found
    """
    try:
        key_file = Path(key_path)
        if not key_file.is_absolute():
            # Try relative to current working directory
            key_file = Path.cwd() / key_path
        
        if not key_file.exists():
            return None
            
        with open(key_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


async def get_installation_token_from_env() -> Optional[str]:
    """
    Get installation token from environment variables.
    
    Supports both:
    - GITHUB_APP_PRIVATE_KEY (key content as string)
    - GITHUB_APP_PRIVATE_KEY_PATH (path to key file)
    
    Returns:
        Installation token if configured, None otherwise
    """
    app_id = os.getenv("GITHUB_APP_ID")
    installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
    
    if not app_id or not installation_id:
        return None
    
    # Try private key from environment variable first
    private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
    
    # If not found, try loading from file path
    if not private_key:
        key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
        if key_path:
            private_key = load_private_key_from_file(key_path)
    
    if not private_key:
        return None
    
    try:
        return await _app_auth.get_installation_token(
            app_id=app_id,
            private_key_pem=private_key,
            installation_id=installation_id
        )
    except Exception:
        # Graceful fallback - return None if App auth fails
        return None


async def verify_installation_access(token: str, owner: str, repo: str) -> tuple:
    """
    Verify if the installation token has access to a specific repository.
    
    Args:
        token: Installation access token
        owner: Repository owner
        repo: Repository name
        
    Returns:
        Tuple of (has_access, message)
    """
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            }
        ) as client:
            # Try to get installation info
            response = await client.get("https://api.github.com/app/installation")
            if response.status_code == 200:
                installation = response.json()
                account_type = installation.get("account", {}).get("type", "unknown")
                
                # Check repository access
                repos_response = await client.get(
                    f"https://api.github.com/app/installations/{installation['id']}/repositories"
                )
                
                if repos_response.status_code == 200:
                    repos_data = repos_response.json()
                    repos = repos_data.get("repositories", [])
                    repo_full_names = [r["full_name"] for r in repos]
                    target_repo = f"{owner}/{repo}"
                    
                    if target_repo in repo_full_names:
                        return True, f"✅ Repository {target_repo} is in installation access list"
                    else:
                        # Check if it's user-level installation
                        if account_type == "User" and len(repos) == 0:
                            return True, f"⚠️ User-level installation - has access to ALL user repos (including {target_repo})"
                        else:
                            return False, f"❌ Repository {target_repo} NOT in installation access list. Access: {repo_full_names[:5]}"
                
            return True, "⚠️ Could not verify repository access (API call failed)"
    except Exception as e:
        return True, f"⚠️ Could not verify access: {str(e)}"


def clear_token_cache() -> None:
    """
    Clear the cached GitHub App installation token.
    
    Call this after:
    - Updating GitHub App permissions
    - Re-installing the app
    - Any permission-related changes
    
    This forces the next API call to get a fresh token with current permissions.
    """
    _app_auth.clear_token_cache()


async def get_auth_token() -> Optional[str]:
    """
    Get authentication token with automatic fallback.
    
    Tries GitHub App first, then falls back to PAT.
    
    Returns:
        Token string if available, None otherwise
    """
    import sys
    
    # Diagnostic logging (only if DEBUG_AUTH is enabled)
    DEBUG_AUTH = os.getenv("GITHUB_MCP_DEBUG_AUTH", "false").lower() == "true"
    
    if DEBUG_AUTH:
        print("🔍 AUTH DIAGNOSTIC:", file=sys.stderr)
        print(f"  GITHUB_TOKEN present: {bool(os.getenv('GITHUB_TOKEN'))}", file=sys.stderr)
        print(f"  GITHUB_APP_ID present: {bool(os.getenv('GITHUB_APP_ID'))}", file=sys.stderr)
        print(f"  GITHUB_APP_INSTALLATION_ID present: {bool(os.getenv('GITHUB_APP_INSTALLATION_ID'))}", file=sys.stderr)
        print(f"  GITHUB_APP_PRIVATE_KEY_PATH present: {bool(os.getenv('GITHUB_APP_PRIVATE_KEY_PATH'))}", file=sys.stderr)
        print(f"  GITHUB_APP_PRIVATE_KEY present: {bool(os.getenv('GITHUB_APP_PRIVATE_KEY'))}", file=sys.stderr)
    
    # Try GitHub App first
    app_token = await get_installation_token_from_env()
    if app_token:
        if DEBUG_AUTH:
            token_type = "App Installation Token" if app_token.startswith("ghs_") else "Unknown Token Type"
            print(f"  ✅ Using GitHub App token (prefix: {app_token[:10]}..., type: {token_type})", file=sys.stderr)
        return app_token
    
    # Fall back to PAT
    pat_token = os.getenv("GITHUB_TOKEN")
    if DEBUG_AUTH:
        if pat_token:
            print(f"  ⚠️ Using PAT token (prefix: {pat_token[:10]}...)", file=sys.stderr)
        else:
            print("  ❌ No authentication token available", file=sys.stderr)
    return pat_token
