"""
Tests for authentication flows.

Tests GitHub App authentication, token caching, and fallback logic.
"""

import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import os

# Import the MCP server
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from auth.github_app import GitHubAppAuth, get_auth_token, clear_token_cache  # noqa: E402


class TestGitHubAppAuth:
    """Test GitHub App authentication."""

    def test_token_caching_initial_state(self):
        """Test that tokens are None initially."""
        auth = GitHubAppAuth()

        # Token should be None initially
        assert auth._token is None
        assert auth._expires_at == 0.0

    @pytest.mark.asyncio
    @patch('auth.github_app.httpx.AsyncClient')
    @patch('auth.github_app.jwt.encode')
    async def test_get_token_success(self, mock_jwt, mock_client_class):
        """Test successful token retrieval."""
        # Mock JWT
        mock_jwt.return_value = "mock_jwt_token"
        
        # Mock httpx client
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "mock_access_token",
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        auth = GitHubAppAuth()

        token = await auth.get_installation_token(
            app_id="123",
            private_key_pem="test_key",
            installation_id="456"
        )

        assert token == "mock_access_token"
        assert auth._token == "mock_access_token"
        assert auth._expires_at > 0

    @pytest.mark.asyncio
    @patch('auth.github_app.httpx.AsyncClient')
    @patch('auth.github_app.jwt.encode')
    async def test_token_cache_used_when_valid(self, mock_jwt, mock_client_class):
        """Test that cached token is used when still valid."""
        # Mock JWT
        mock_jwt.return_value = "mock_jwt_token"
        
        # Mock httpx client
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "cached_token",
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        auth = GitHubAppAuth()

        # First call - should fetch from API
        token1 = await auth.get_installation_token(
            app_id="123",
            private_key_pem="test_key",
            installation_id="456"
        )
        assert token1 == "cached_token"
        assert mock_client.post.call_count == 1

        # Second call - should use cache
        token2 = await auth.get_installation_token(
            app_id="123",
            private_key_pem="test_key",
            installation_id="456"
        )
        assert token2 == "cached_token"
        # Should not call API again (cache used)
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    @patch('auth.github_app.httpx.AsyncClient')
    @patch('auth.github_app.jwt.encode')
    async def test_token_refresh_on_expiry(self, mock_jwt, mock_client_class):
        """Test that expired tokens are refreshed."""
        # Mock JWT
        mock_jwt.return_value = "mock_jwt_token"
        
        # Mock httpx client
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "new_token",
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        auth = GitHubAppAuth()

        # Set expired token (expires_at is in seconds since epoch)
        # Make it clearly expired (1 hour ago)
        auth._token = "old_token"
        auth._expires_at = time.time() - (60 * 60)  # Expired 1 hour ago

        # Should refresh token
        token = await auth.get_installation_token(
            app_id="123",
            private_key_pem="test_key",
            installation_id="456",
            force_refresh=False
        )

        # Should have called API to refresh
        assert token == "new_token"
        assert auth._token == "new_token"

    def test_clear_token_cache(self):
        """Test cache clearing."""
        auth = GitHubAppAuth()

        auth._token = "test_token"
        auth._expires_at = time.time()

        auth.clear_token_cache()

        assert auth._token is None
        assert auth._expires_at == 0.0

    @pytest.mark.asyncio
    @patch('auth.github_app.httpx.AsyncClient')
    @patch('auth.github_app.jwt.encode')
    async def test_force_refresh(self, mock_jwt, mock_client_class):
        """Test force refresh parameter."""
        # Mock JWT
        mock_jwt.return_value = "mock_jwt_token"
        
        # Mock httpx client
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "refreshed_token",
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        auth = GitHubAppAuth()

        # Set valid token
        auth._token = "old_token"
        auth._expires_at = time.time() + (55 * 60)  # Valid for 55 minutes

        # Force refresh should get new token
        token = await auth.get_installation_token(
            app_id="123",
            private_key_pem="test_key",
            installation_id="456",
            force_refresh=True
        )

        assert token == "refreshed_token"
        assert auth._token == "refreshed_token"


class TestAuthFallback:
    """Test authentication fallback logic."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_get_auth_token_no_auth_configured(self):
        """Test get_auth_token when no auth is configured."""
        # Clear all auth env vars
        token = await get_auth_token()

        # Should return None when nothing is configured
        assert token is None

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GITHUB_TOKEN": "test_pat_token"})
    async def test_get_auth_token_pat_fallback(self):
        """Test PAT fallback when GitHub App not configured."""
        token = await get_auth_token()

        # Should return PAT
        assert token == "test_pat_token"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_APP_ID": "123",
        "GITHUB_APP_INSTALLATION_ID": "456",
        "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/key.pem"
    })
    @patch('auth.github_app.GitHubAppAuth.get_installation_token')
    async def test_get_auth_token_app_priority(self, mock_get_token):
        """Test GitHub App takes priority over PAT."""
        mock_get_token.return_value = "app_token"

        # Even if PAT is set, App should be used
        with patch.dict(os.environ, {"GITHUB_TOKEN": "pat_token"}):
            token = await get_auth_token()

        # Should use App token
        assert token == "app_token"
        mock_get_token.assert_called_once()

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_APP_ID": "123",
        "GITHUB_APP_INSTALLATION_ID": "456",
        "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/key.pem"
    })
    @patch('auth.github_app.GitHubAppAuth.get_installation_token')
    async def test_get_auth_token_app_fallback_to_pat(self, mock_get_token):
        """Test fallback to PAT when App fails."""
        mock_get_token.return_value = None

        with patch.dict(os.environ, {"GITHUB_TOKEN": "pat_token"}):
            token = await get_auth_token()

        # Should fall back to PAT
        assert token == "pat_token"

    def test_clear_token_cache_function(self):
        """Test the clear_token_cache function."""
        # This should work even if no auth is configured
        try:
            clear_token_cache()
            # Should not raise an error
            assert True
        except Exception:
            pytest.fail("clear_token_cache should not raise errors")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

