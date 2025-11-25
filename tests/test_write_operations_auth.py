"""
Tests for write operations authentication validation.

These tests verify that all write operations properly validate authentication
tokens before making API calls, ensuring consistent error handling.
"""

import pytest
import json
from unittest.mock import patch

# Import the MCP server
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from github_mcp import (  # noqa: E402
    github_create_file,
    github_update_file,
    github_delete_file,
    github_create_release,
    github_update_release,
    github_create_repository,
    github_delete_repository,
    github_update_repository,
    github_transfer_repository,
    github_archive_repository,
    github_merge_pull_request,
    CreateFileInput,
    UpdateFileInput,
    DeleteFileInput,
    CreateReleaseInput,
    UpdateReleaseInput,
    CreateRepositoryInput,
    DeleteRepositoryInput,
    UpdateRepositoryInput,
    TransferRepositoryInput,
    ArchiveRepositoryInput,
    MergePullRequestInput,
)


class TestWriteOperationsAuthValidation:
    """Test authentication validation in write operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_create_file_no_auth(self, mock_get_token):
        """Test github_create_file returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = CreateFileInput(
            owner="test",
            repo="test-repo",
            path="test.txt",
            content="test",
            message="test"
        )
        
        result = await github_create_file(params)
        
        # Should return JSON error
        assert isinstance(result, str)
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert "success" in data
        assert data["success"] is False
        # Should not call API
        mock_get_token.assert_called_once()

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    @patch('github_mcp._make_github_request')
    async def test_github_create_file_with_auth(self, mock_request, mock_get_token):
        """Test github_create_file works with valid auth."""
        mock_get_token.return_value = "valid_token"
        mock_request.return_value = {
            "content": {"html_url": "https://github.com/test/test-repo/blob/main/test.txt"},
            "commit": {"sha": "abc123", "author": {"name": "test", "date": "2024-01-01"}}
        }
        
        params = CreateFileInput(
            owner="test",
            repo="test-repo",
            path="test.txt",
            content="test",
            message="test"
        )
        
        result = await github_create_file(params)
        
        # Should succeed
        assert isinstance(result, str)
        assert "created" in result.lower() or "success" in result.lower()
        mock_request.assert_called_once()

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_update_file_no_auth(self, mock_get_token):
        """Test github_update_file returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = UpdateFileInput(
            owner="test",
            repo="test-repo",
            path="test.txt",
            content="updated",
            message="update",
            sha="abc123"
        )
        
        result = await github_update_file(params)
        
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_delete_file_no_auth(self, mock_get_token):
        """Test github_delete_file returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = DeleteFileInput(
            owner="test",
            repo="test-repo",
            path="test.txt",
            message="delete",
            sha="abc123"
        )
        
        result = await github_delete_file(params)
        
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_create_release_no_auth(self, mock_get_token):
        """Test github_create_release returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = CreateReleaseInput(
            owner="test",
            repo="test-repo",
            tag_name="v1.0.0",
            name="Release"
        )
        
        result = await github_create_release(params)
        
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_update_release_no_auth(self, mock_get_token):
        """Test github_update_release returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = UpdateReleaseInput(
            owner="test",
            repo="test-repo",
            release_id="123"
        )
        
        result = await github_update_release(params)
        
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_create_repository_no_auth(self, mock_get_token):
        """Test github_create_repository returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = CreateRepositoryInput(
            name="test-repo"
        )
        
        result = await github_create_repository(params)
        
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_delete_repository_no_auth(self, mock_get_token):
        """Test github_delete_repository returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = DeleteRepositoryInput(
            owner="test",
            repo="test-repo"
        )
        
        result = await github_delete_repository(params)
        
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_update_repository_no_auth(self, mock_get_token):
        """Test github_update_repository returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = UpdateRepositoryInput(
            owner="test",
            repo="test-repo",
            description="Updated"
        )
        
        result = await github_update_repository(params)
        
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_transfer_repository_no_auth(self, mock_get_token):
        """Test github_transfer_repository returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = TransferRepositoryInput(
            owner="test",
            repo="test-repo",
            new_owner="new-owner"
        )
        
        result = await github_transfer_repository(params)
        
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_archive_repository_no_auth(self, mock_get_token):
        """Test github_archive_repository returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = ArchiveRepositoryInput(
            owner="test",
            repo="test-repo",
            archived=True
        )
        
        result = await github_archive_repository(params)
        
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch('github_mcp._get_auth_token_fallback')
    async def test_github_merge_pull_request_no_auth(self, mock_get_token):
        """Test github_merge_pull_request returns error when no auth token."""
        mock_get_token.return_value = None
        
        params = MergePullRequestInput(
            owner="test",
            repo="test-repo",
            pull_number=1
        )
        
        result = await github_merge_pull_request(params)
        
        data = json.loads(result)
        assert data["error"] == "Authentication required"
        assert data["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

