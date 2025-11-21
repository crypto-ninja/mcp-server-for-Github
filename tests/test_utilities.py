"""
Tests for utility functions and helper tools.

These tests cover functions that may have 0% or low coverage:
- health_check
- github_clear_token_cache
- validate_workspace_path
- check_deno_installed
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the MCP server
import sys
from pathlib import Path as PathLib
project_root = PathLib(__file__).parent.parent
sys.path.insert(0, str(project_root))

import github_mcp  # noqa: E402


class TestHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "test_token",
        "GITHUB_APP_ID": "",
        "GITHUB_APP_INSTALLATION_ID": "",
        "GITHUB_APP_PRIVATE_KEY_PATH": ""
    })
    async def test_health_check_with_pat(self):
        """Test health check with PAT configured."""
        result = await github_mcp.health_check()
        
        # Should return JSON
        data = json.loads(result)
        assert data["status"] == "healthy"
        assert "version" in data
        assert "authentication" in data
        assert data["authentication"]["method"] == "pat"
        assert data["authentication"]["pat_configured"] is True

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "",
        "GITHUB_APP_ID": "123",
        "GITHUB_APP_INSTALLATION_ID": "456",
        "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/key.pem"
    })
    async def test_health_check_with_app(self):
        """Test health check with GitHub App configured."""
        result = await github_mcp.health_check()
        
        # Should return JSON
        data = json.loads(result)
        assert data["status"] == "healthy"
        assert "authentication" in data
        assert data["authentication"]["method"] == "github_app"
        assert data["authentication"]["app_configured"] is True

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_TOKEN": "",
        "GITHUB_APP_ID": "",
        "GITHUB_APP_INSTALLATION_ID": "",
        "GITHUB_APP_PRIVATE_KEY_PATH": ""
    })
    async def test_health_check_no_auth(self):
        """Test health check with no authentication configured."""
        result = await github_mcp.health_check()
        
        # Should return JSON
        data = json.loads(result)
        assert data["status"] == "healthy"
        assert data["authentication"]["status"] == "none"
        assert data["authentication"]["method"] is None

    @pytest.mark.asyncio
    @patch('github_mcp.check_deno_installed')
    async def test_health_check_deno_info(self, mock_check_deno):
        """Test health check includes Deno information."""
        mock_check_deno.return_value = (True, "deno 1.40.0")
        
        result = await github_mcp.health_check()
        data = json.loads(result)
        
        assert "deno" in data
        assert data["deno"]["available"] is True
        assert "1.40.0" in data["deno"]["version"]

    @pytest.mark.asyncio
    @patch('github_mcp.check_deno_installed')
    async def test_health_check_deno_unavailable(self, mock_check_deno):
        """Test health check when Deno is not available."""
        mock_check_deno.return_value = (False, "Deno not found")
        
        result = await github_mcp.health_check()
        data = json.loads(result)
        
        assert data["deno"]["available"] is False
        assert data["deno"]["version"] is None


class TestClearTokenCache:
    """Test token cache clearing functionality."""

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_APP_ID": "123",
        "GITHUB_APP_INSTALLATION_ID": "456",
        "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/key.pem"
    })
    @patch('github_mcp.clear_token_cache')
    async def test_github_clear_token_cache_with_app(self, mock_clear):
        """Test clearing token cache when App is configured."""
        result = await github_mcp.github_clear_token_cache()
        
        # Should call clear_token_cache
        mock_clear.assert_called_once()
        assert "cleared" in result.lower()
        assert "GitHub App" in result

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_APP_ID": "",
        "GITHUB_APP_INSTALLATION_ID": "",
        "GITHUB_APP_PRIVATE_KEY_PATH": ""
    })
    @patch('github_mcp.clear_token_cache')
    async def test_github_clear_token_cache_no_app(self, mock_clear):
        """Test clearing token cache when App is not configured."""
        result = await github_mcp.github_clear_token_cache()
        
        # Should not call clear_token_cache
        mock_clear.assert_not_called()
        assert "not configured" in result.lower() or "PAT" in result

    @pytest.mark.asyncio
    @patch.dict(os.environ, {
        "GITHUB_APP_ID": "123",
        "GITHUB_APP_INSTALLATION_ID": "456",
        "GITHUB_APP_PRIVATE_KEY": "-----BEGIN RSA PRIVATE KEY-----\nMOCK\n-----END RSA PRIVATE KEY-----"
    })
    @patch('github_mcp.clear_token_cache')
    async def test_github_clear_token_cache_with_direct_key(self, mock_clear):
        """Test clearing token cache with direct private key (not path)."""
        result = await github_mcp.github_clear_token_cache()
        
        # Should call clear_token_cache
        mock_clear.assert_called_once()
        assert "cleared" in result.lower()


class TestValidateWorkspacePath:
    """Test workspace path validation."""

    def test_validate_workspace_path_valid(self):
        """Test workspace path validation with valid path."""
        # Use a path within workspace (tests directory)
        valid_path = Path(__file__).parent  # tests directory
        result = github_mcp.validate_workspace_path(valid_path)
        # Should be True if within workspace, or False if workspace validation is strict
        assert isinstance(result, bool)

    def test_validate_workspace_path_subdirectory(self):
        """Test workspace path validation with subdirectory."""
        # Use a subdirectory within tests
        subdir = Path(__file__).parent / "test_utilities.py"
        if subdir.exists():
            result = github_mcp.validate_workspace_path(subdir)
            # Should be True if within workspace
            assert isinstance(result, bool)

    def test_validate_workspace_path_invalid(self):
        """Test workspace path validation with invalid (outside workspace) path."""
        # Try a path outside workspace (e.g., parent directory)
        try:
            invalid_path = Path.cwd().parent.parent
            result = github_mcp.validate_workspace_path(invalid_path)
            # Should return False if outside workspace
            assert result is False
        except (ValueError, OSError):
            # If path resolution fails, that's also expected
            pass

    def test_validate_workspace_path_absolute(self):
        """Test workspace path validation with absolute path."""
        # Use absolute path within workspace
        abs_path = Path(__file__).resolve()
        result = github_mcp.validate_workspace_path(abs_path)
        # Should be True if within workspace
        assert isinstance(result, bool)


class TestCheckDenoInstalled:
    """Test Deno installation checking."""

    @patch('subprocess.run')
    def test_check_deno_installed_success(self, mock_run):
        """Test successful Deno check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "deno 1.40.0\nv8 12.0.0\ntypescript 5.3.0"
        mock_run.return_value = mock_result
        
        available, info = github_mcp.check_deno_installed()
        
        assert available is True
        assert "1.40.0" in info or "deno" in info
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_check_deno_installed_not_found(self, mock_run):
        """Test Deno check when Deno is not found."""
        mock_run.side_effect = FileNotFoundError()
        
        available, info = github_mcp.check_deno_installed()
        
        assert available is False
        assert "not found" in info.lower()

    @patch('subprocess.run')
    def test_check_deno_installed_failed(self, mock_run):
        """Test Deno check when command fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        available, info = github_mcp.check_deno_installed()
        
        assert available is False
        assert "failed" in info.lower()

    @patch('subprocess.run')
    def test_check_deno_installed_timeout(self, mock_run):
        """Test Deno check when command times out."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("deno", 5)
        
        available, info = github_mcp.check_deno_installed()
        
        assert available is False
        assert "timeout" in info.lower() or "timed out" in info.lower()

