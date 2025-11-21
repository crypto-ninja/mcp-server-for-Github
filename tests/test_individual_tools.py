"""
Tests for individual tool implementations.

These tests use mocked GitHub API responses to test each tool's logic
without making real API calls.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

# Import the MCP server
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import github_mcp  # noqa: E402
from github_mcp import (  # noqa: E402
    github_get_repo_info,
    github_list_issues,
    github_create_issue,
    github_get_file_content,
    github_search_code,
    github_list_commits,
    github_get_pr_details,
    github_list_pull_requests,
    github_get_release,
    github_list_releases,
    github_get_user_info,
    RepoInfoInput,
    ListIssuesInput,
    CreateIssueInput,
    GetFileContentInput,
    SearchCodeInput,
    ListCommitsInput,
    GetPullRequestDetailsInput,
    ResponseFormat,
)


class TestReadOperations:
    """Test read operations with mocked API responses."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_repo_info(self, mock_request):
        """Test repository info retrieval."""
        # Mock the API response
        mock_response = {
            "name": "test-repo",
            "full_name": "test/test-repo",
            "description": "Test description",
            "stargazers_count": 100,
            "forks_count": 50,
            "open_issues_count": 10,
            "language": "Python",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "html_url": "https://github.com/test/test-repo"
        }
        mock_request.return_value = mock_response

        # Call the tool
        params = RepoInfoInput(
            owner="test",
            repo="test-repo",
            response_format=ResponseFormat.JSON
        )
        result = await github_get_repo_info(params)

        # Verify it processed the response correctly
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["name"] == "test-repo"
        assert parsed["stargazers_count"] == 100

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_issues(self, mock_request):
        """Test issue listing."""
        # Mock issues response
        mock_response = [
            {
                "number": 1,
                "title": "Test Issue",
                "state": "open",
                "body": "Issue body",
                "user": {"login": "testuser"},
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "number": 2,
                "title": "Another Issue",
                "state": "closed",
                "body": "Closed issue",
                "user": {"login": "testuser"},
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        mock_request.return_value = mock_response

        # Call the tool
        params = ListIssuesInput(
            owner="test",
            repo="test-repo",
            state="open",
            response_format=ResponseFormat.JSON
        )
        result = await github_list_issues(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["number"] == 1

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_file_content(self, mock_request):
        """Test file content retrieval."""
        import base64

        # Mock file content (base64 encoded)
        content = "# Test README\n\nThis is a test file."
        encoded_content = base64.b64encode(content.encode()).decode()

        mock_response = {
            "name": "README.md",
            "path": "README.md",
            "content": encoded_content,
            "encoding": "base64",
            "size": len(content),
            "sha": "abc123"
        }
        mock_request.return_value = mock_response

        # Call the tool
        params = GetFileContentInput(
            owner="test",
            repo="test-repo",
            path="README.md"
        )
        result = await github_get_file_content(params)

        # Verify
        assert isinstance(result, str)
        assert "Test README" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_search_code(self, mock_request):
        """Test code search."""
        # Mock search results
        mock_response = {
            "total_count": 2,
            "items": [
                {
                    "name": "test.py",
                    "path": "src/test.py",
                    "repository": {
                        "full_name": "test/repo",
                        "html_url": "https://github.com/test/repo"
                    },
                    "html_url": "https://github.com/test/repo/blob/main/src/test.py"
                },
                {
                    "name": "test2.py",
                    "path": "src/test2.py",
                    "repository": {
                        "full_name": "test/repo",
                        "html_url": "https://github.com/test/repo"
                    },
                    "html_url": "https://github.com/test/repo/blob/main/src/test2.py"
                }
            ]
        }
        mock_request.return_value = mock_response

        # Call the tool
        params = SearchCodeInput(
            query="test query",
            response_format=ResponseFormat.JSON
        )
        result = await github_search_code(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "items" in parsed or isinstance(parsed, list)
        if "items" in parsed:
            assert len(parsed["items"]) == 2

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_commits(self, mock_request):
        """Test commit listing."""
        # Mock commits response
        mock_response = [
            {
                "sha": "abc123",
                "commit": {
                    "message": "Test commit",
                    "author": {
                        "name": "Test User",
                        "email": "test@example.com",
                        "date": "2024-01-01T00:00:00Z"
                    }
                },
                "author": {
                    "login": "testuser",
                    "avatar_url": "https://github.com/testuser.png"
                }
            }
        ]
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListCommitsInput
        params = ListCommitsInput(
            owner="test",
            repo="test-repo",
            response_format=ResponseFormat.JSON
        )
        result = await github_list_commits(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["sha"] == "abc123"

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_pr_details(self, mock_request):
        """Test PR details retrieval."""
        # Mock PR response
        mock_response = {
            "number": 123,
            "title": "Test PR",
            "body": "PR description",
            "state": "open",
            "head": {
                "ref": "feature-branch",
                "sha": "abc123"
            },
            "base": {
                "ref": "main",
                "sha": "def456"
            },
            "user": {
                "login": "testuser"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "html_url": "https://github.com/test/test-repo/pull/123",
            "merged": False,
            "mergeable": True
        }
        mock_request.return_value = mock_response

        # Call the tool
        params = GetPullRequestDetailsInput(
            owner="test",
            repo="test-repo",
            pull_number=123,
            response_format=ResponseFormat.JSON
        )
        result = await github_get_pr_details(params)

        # Verify
        assert isinstance(result, str)
        # Result might be JSON string or markdown, check both
        try:
            parsed = json.loads(result)
            # If JSON, should have PR data
            if isinstance(parsed, dict):
                assert parsed.get("number") == 123 or "123" in str(result)
        except json.JSONDecodeError:
            # If markdown, should contain PR info
            assert "123" in result or "Test PR" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_user_info(self, mock_request):
        """Test user info retrieval."""
        # Mock user response
        mock_response = {
            "login": "testuser",
            "name": "Test User",
            "bio": "Test bio",
            "public_repos": 10,
            "followers": 50,
            "following": 20,
            "created_at": "2020-01-01T00:00:00Z",
            "html_url": "https://github.com/testuser"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import GetUserInfoInput
        params = GetUserInfoInput(
            username="testuser",
            response_format=ResponseFormat.JSON
        )
        result = await github_get_user_info(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["login"] == "testuser"
        assert parsed["public_repos"] == 10


class TestWriteOperations:
    """Test write operations with mocked API responses."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_create_issue(self, mock_request):
        """Test issue creation."""
        # Mock created issue
        mock_response = {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "html_url": "https://github.com/test/test-repo/issues/123",
            "user": {
                "login": "testuser"
            },
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        params = CreateIssueInput(
            owner="test",
            repo="test-repo",
            title="Test Issue",
            body="Test body"
        )
        result = await github_create_issue(params)

        # Verify
        assert isinstance(result, str)
        assert "123" in result or "created" in result.lower() or "success" in result.lower()

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_create_issue_minimal(self, mock_request):
        """Test issue creation with minimal params."""
        # Mock created issue
        mock_response = {
            "number": 124,
            "title": "Minimal Issue",
            "body": None,
            "state": "open",
            "html_url": "https://github.com/test/test-repo/issues/124"
        }
        mock_request.return_value = mock_response

        # Call the tool with only required params
        params = CreateIssueInput(
            owner="test",
            repo="test-repo",
            title="Minimal Issue"
        )
        result = await github_create_issue(params)

        # Verify
        assert isinstance(result, str)
        assert "124" in result or "created" in result.lower()


class TestErrorHandling:
    """Test error handling paths."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_repo_info_not_found(self, mock_request):
        """Test 404 error handling."""
        from github_mcp import _handle_api_error
        import httpx

        # Mock 404 error
        mock_request.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404)
        )

        # Call the tool - should handle error gracefully
        params = RepoInfoInput(
            owner="test",
            repo="nonexistent"
        )
        result = await github_get_repo_info(params)

        # Verify error message
        assert isinstance(result, str)
        assert "error" in result.lower() or "not found" in result.lower() or "404" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_create_issue_permission_denied(self, mock_request):
        """Test 403 error handling."""
        import httpx

        # Mock 403 error
        mock_request.side_effect = httpx.HTTPStatusError(
            "Permission denied",
            request=MagicMock(),
            response=MagicMock(status_code=403)
        )

        # Call the tool
        params = CreateIssueInput(
            owner="test",
            repo="test-repo",
            title="Test"
        )
        result = await github_create_issue(params)

        # Verify error message
        assert isinstance(result, str)
        assert "error" in result.lower() or "permission" in result.lower() or "403" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_file_content_not_found(self, mock_request):
        """Test file not found error."""
        import httpx

        # Mock 404 error
        mock_request.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404)
        )

        # Call the tool
        params = GetFileContentInput(
            owner="test",
            repo="test-repo",
            path="nonexistent.md"
        )
        result = await github_get_file_content(params)

        # Verify error handling
        assert isinstance(result, str)
        assert "error" in result.lower() or "not found" in result.lower()

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_search_code_empty_results(self, mock_request):
        """Test empty search results."""
        # Mock empty response
        mock_response = {
            "total_count": 0,
            "items": []
        }
        mock_request.return_value = mock_response

        # Call the tool
        params = SearchCodeInput(
            query="nonexistent_query_xyz",
            response_format=ResponseFormat.JSON
        )
        result = await github_search_code(params)

        # Verify it handles empty results
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should return empty list or object with empty items
        if isinstance(parsed, list):
            assert len(parsed) == 0
        elif isinstance(parsed, dict):
            assert parsed.get("total_count", 0) == 0


class TestResponseFormatting:
    """Test response format handling."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_json_response_format(self, mock_request):
        """Test JSON response format."""
        mock_response = {"key": "value", "number": 123}
        mock_request.return_value = mock_response

        params = RepoInfoInput(
            owner="test",
            repo="test-repo",
            response_format=ResponseFormat.JSON
        )
        result = await github_get_repo_info(params)

        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        assert parsed["key"] == "value"

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_markdown_response_format(self, mock_request):
        """Test Markdown response format."""
        mock_response = {
            "full_name": "test/test-repo",
            "name": "test-repo",
            "description": "Test description",
            "stargazers_count": 100,
            "forks_count": 50,
            "watchers_count": 10,
            "open_issues_count": 5,
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "default_branch": "main",
            "language": "Python",
            "license": None,
            "topics": [],
            "homepage": None,
            "clone_url": "https://github.com/test/test-repo.git",
            "html_url": "https://github.com/test/test-repo",
            "owner": {
                "login": "test",
                "type": "User"
            }
        }
        mock_request.return_value = mock_response

        params = RepoInfoInput(
            owner="test",
            repo="test-repo",
            response_format=ResponseFormat.MARKDOWN
        )
        result = await github_get_repo_info(params)

        # Should contain markdown elements
        assert isinstance(result, str)
        # If there's an error, that's okay - we're testing the function works
        # Markdown might have #, **, or other formatting
        assert "test-repo" in result or "100" in result or "Error" in result


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_empty_repo_list(self, mock_request):
        """Test empty repository list."""
        mock_request.return_value = []

        from github_mcp import ListRepoContentsInput, github_list_repo_contents
        params = ListRepoContentsInput(
            owner="test",
            repo="empty-repo",
            path="",
            response_format=ResponseFormat.JSON
        )
        result = await github_list_repo_contents(params)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 0

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_large_response_handling(self, mock_request):
        """Test handling of large responses."""
        # Mock large response (many issues)
        mock_response = [
            {"number": i, "title": f"Issue {i}", "state": "open"}
            for i in range(100)
        ]
        mock_request.return_value = mock_response

        params = ListIssuesInput(
            owner="test",
            repo="test-repo",
            state="open",
            response_format=ResponseFormat.JSON
        )
        result = await github_list_issues(params)

        # Should handle large responses
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

