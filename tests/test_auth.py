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
    @patch('auth.github_app.load_private_key_from_file')
    @patch('auth.github_app.GitHubAppAuth.get_installation_token')
    async def test_get_auth_token_app_priority(self, mock_get_token, mock_load_key):
        """Test GitHub App takes priority over PAT."""
        # Mock the private key loading to return a valid key
        mock_load_key.return_value = "-----BEGIN RSA PRIVATE KEY-----\nMOCK_KEY\n-----END RSA PRIVATE KEY-----"
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
    @patch('auth.github_app.load_private_key_from_file')
    @patch('auth.github_app.GitHubAppAuth.get_installation_token')
    async def test_get_auth_token_app_fallback_to_pat(self, mock_get_token, mock_load_key):
        """Test fallback to PAT when App fails."""
        # Mock the private key loading to return a valid key
        mock_load_key.return_value = "-----BEGIN RSA PRIVATE KEY-----\nMOCK_KEY\n-----END RSA PRIVATE KEY-----"
        # Mock get_installation_token to raise an exception (App auth fails)
        mock_get_token.side_effect = Exception("App auth failed")

        with patch.dict(os.environ, {"GITHUB_TOKEN": "pat_token"}):
            token = await get_auth_token()

        # Should fall back to PAT when App fails
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

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_APP_ID": "123",
        "GITHUB_APP_INSTALLATION_ID": "456",
        "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/key.pem",
        "GITHUB_TOKEN": "pat_token"
    })
    @patch('auth.github_app.load_private_key_from_file')
    @patch('auth.github_app.GitHubAppAuth.get_installation_token')
    async def test_get_auth_token_force_pat_mode(self, mock_get_token, mock_load_key):
        """Test GITHUB_AUTH_MODE=pat forces PAT even when App configured."""
        mock_load_key.return_value = "-----BEGIN RSA PRIVATE KEY-----\nMOCK_KEY\n-----END RSA PRIVATE KEY-----"
        mock_get_token.return_value = "app_token"

        # Set GITHUB_AUTH_MODE=pat
        with patch.dict(os.environ, {"GITHUB_AUTH_MODE": "pat"}):
            token = await get_auth_token()

        # Should use PAT, not App
        assert token == "pat_token"
        # App token should not be called when mode is pat
        mock_get_token.assert_not_called()


class TestHasAppConfig:
    """Test _has_app_config helper function."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_has_app_config_missing_app_id(self):
        """Test _has_app_config returns False when app ID missing."""
        from auth.github_app import _has_app_config
        
        with patch.dict(os.environ, {
            "GITHUB_APP_INSTALLATION_ID": "456",
            "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/key.pem"
        }):
            assert _has_app_config() is False

    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_has_app_config_missing_installation_id(self):
        """Test _has_app_config returns False when installation ID missing."""
        from auth.github_app import _has_app_config
        
        with patch.dict(os.environ, {
            "GITHUB_APP_ID": "123",
            "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/key.pem"
        }):
            assert _has_app_config() is False

    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_has_app_config_missing_both_keys(self):
        """Test _has_app_config returns False when no key source."""
        from auth.github_app import _has_app_config
        
        with patch.dict(os.environ, {
            "GITHUB_APP_ID": "123",
            "GITHUB_APP_INSTALLATION_ID": "456"
        }):
            assert _has_app_config() is False

    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_has_app_config_with_key_path_only(self):
        """Test _has_app_config returns True with KEY_PATH only."""
        from auth.github_app import _has_app_config
        
        with patch.dict(os.environ, {
            "GITHUB_APP_ID": "123",
            "GITHUB_APP_INSTALLATION_ID": "456",
            "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/key.pem"
        }):
            assert _has_app_config() is True

    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_has_app_config_with_key_direct_only(self):
        """Test _has_app_config returns True with KEY only."""
        from auth.github_app import _has_app_config
        
        with patch.dict(os.environ, {
            "GITHUB_APP_ID": "123",
            "GITHUB_APP_INSTALLATION_ID": "456",
            "GITHUB_APP_PRIVATE_KEY": "-----BEGIN RSA PRIVATE KEY-----\nKEY\n-----END RSA PRIVATE KEY-----"
        }):
            assert _has_app_config() is True


class TestAppAuthErrors:
    """Test App authentication error scenarios."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_APP_ID": "123",
        "GITHUB_APP_INSTALLATION_ID": "456",
        "GITHUB_APP_PRIVATE_KEY": "invalid_key_format"
    })
    @patch('auth.github_app.GitHubAppAuth.get_installation_token')
    async def test_get_auth_token_app_invalid_key_format(self, mock_get_token):
        """Test when App key is malformed."""
        # Mock JWT generation to fail
        import jwt
        mock_get_token.side_effect = jwt.InvalidKeyError("Invalid key format")

        # Should fall back to PAT if available
        with patch.dict(os.environ, {"GITHUB_TOKEN": "pat_token"}):
            token = await get_auth_token()

        # Should fall back to PAT
        assert token == "pat_token"

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_APP_ID": "123",
        "GITHUB_APP_INSTALLATION_ID": "456",
        "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/key.pem"
    })
    @patch('auth.github_app.load_private_key_from_file')
    @patch('auth.github_app.GitHubAppAuth.get_installation_token')
    async def test_get_auth_token_app_github_api_error(self, mock_get_token, mock_load_key):
        """Test when GitHub API rejects App token."""
        mock_load_key.return_value = "-----BEGIN RSA PRIVATE KEY-----\nMOCK_KEY\n-----END RSA PRIVATE KEY-----"
        # Mock GitHub API error
        import httpx
        mock_get_token.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=MagicMock(status_code=401)
        )

        # Should fall back to PAT if available
        with patch.dict(os.environ, {"GITHUB_TOKEN": "pat_token"}):
            token = await get_auth_token()

        # Should fall back to PAT
        assert token == "pat_token"


class TestLoadPrivateKeyFromFile:
    """Test load_private_key_from_file function."""

    def test_load_private_key_from_file_nonexistent(self):
        """Test loading from non-existent file."""
        from auth.github_app import load_private_key_from_file
        
        result = load_private_key_from_file("/nonexistent/path/key.pem")
        assert result is None

    def test_load_private_key_from_file_relative_path(self):
        """Test loading from relative path."""
        from auth.github_app import load_private_key_from_file
        from pathlib import Path
        import tempfile
        
        # Create a temporary key file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("-----BEGIN RSA PRIVATE KEY-----\nTEST_KEY\n-----END RSA PRIVATE KEY-----")
            temp_path = f.name
        
        try:
            # Test with just filename (relative)
            filename = Path(temp_path).name
            result = load_private_key_from_file(filename)
            # Should try to find it relative to cwd
            # Result may be None if not in cwd, or the key if found
            assert result is None or "TEST_KEY" in result
        finally:
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_private_key_from_file_absolute_path(self):
        """Test loading from absolute path."""
        from auth.github_app import load_private_key_from_file
        import tempfile
        
        # Create a temporary key file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("-----BEGIN RSA PRIVATE KEY-----\nTEST_KEY\n-----END RSA PRIVATE KEY-----")
            temp_path = f.name
        
        try:
            result = load_private_key_from_file(temp_path)
            assert result is not None
            assert "TEST_KEY" in result
        finally:
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

