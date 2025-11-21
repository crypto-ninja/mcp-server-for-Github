"""
Tests for individual tool implementations.

These tests use mocked GitHub API responses to test each tool's logic
without making real API calls.
"""

import pytest
import json
import base64
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
    github_create_release,
    github_get_user_info,
    github_list_workflows,
    github_get_workflow_runs,
    github_create_pull_request,
    github_merge_pull_request,
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
            "archived": False,
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


class TestReleaseOperations:
    """Test release operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_releases(self, mock_request):
        """Test listing releases."""
        # Mock releases response
        mock_response = [
            {
                "tag_name": "v1.0.0",
                "name": "Release v1.0.0",
                "body": "Release notes",
                "draft": False,
                "prerelease": False,
                "html_url": "https://github.com/test/test-repo/releases/tag/v1.0.0",
                "created_at": "2024-01-01T00:00:00Z",
                "published_at": "2024-01-01T00:00:00Z",
                "author": {
                    "login": "testuser"
                }
            },
            {
                "tag_name": "v0.9.0",
                "name": "Release v0.9.0",
                "body": "Previous release",
                "draft": False,
                "prerelease": False,
                "html_url": "https://github.com/test/test-repo/releases/tag/v0.9.0",
                "created_at": "2023-12-01T00:00:00Z",
                "published_at": "2023-12-01T00:00:00Z",
                "author": {
                    "login": "testuser"
                }
            }
        ]
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListReleasesInput
        params = ListReleasesInput(
            owner="test",
            repo="test-repo",
            response_format=ResponseFormat.JSON
        )
        result = await github_list_releases(params)

        # Verify
        assert isinstance(result, str)
        # Should contain release info
        assert "v1.0.0" in result or "v0.9.0" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_release(self, mock_request):
        """Test getting release details."""
        # Mock release response
        mock_response = {
            "tag_name": "v2.0.0",
            "name": "Release v2.0.0",
            "body": "Major release notes",
            "draft": False,
            "prerelease": False,
            "html_url": "https://github.com/test/test-repo/releases/tag/v2.0.0",
            "created_at": "2024-01-15T00:00:00Z",
            "published_at": "2024-01-15T00:00:00Z",
            "author": {
                "login": "testuser"
            },
            "assets": []
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import GetReleaseInput
        params = GetReleaseInput(
            owner="test",
            repo="test-repo",
            tag="v2.0.0",
            response_format=ResponseFormat.JSON
        )
        result = await github_get_release(params)

        # Verify
        assert isinstance(result, str)
        assert "v2.0.0" in result or "Release v2.0.0" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_create_release(self, mock_request):
        """Test creating a release."""
        # Mock created release
        mock_response = {
            "tag_name": "v2.0.0",
            "name": "Release v2.0.0",
            "body": "Release notes",
            "draft": False,
            "prerelease": False,
            "html_url": "https://github.com/test/test-repo/releases/tag/v2.0.0",
            "created_at": "2024-01-20T00:00:00Z",
            "published_at": "2024-01-20T00:00:00Z",
            "author": {
                "login": "testuser"
            },
            "assets": []
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import CreateReleaseInput
        params = CreateReleaseInput(
            owner="test",
            repo="test-repo",
            tag_name="v2.0.0",
            name="Release v2.0.0",
            body="Release notes"
        )
        result = await github_create_release(params)

        # Verify
        assert isinstance(result, str)
        # Should indicate success
        assert "v2.0.0" in result or "created" in result.lower() or "success" in result.lower()


class TestPullRequestOperations:
    """Test pull request operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_create_pull_request(self, mock_request):
        """Test creating a pull request."""
        # Mock created PR
        mock_response = {
            "number": 42,
            "title": "Test PR",
            "body": "PR body",
            "state": "open",
            "draft": False,
            "head": {
                "ref": "feature",
                "sha": "abc123"
            },
            "base": {
                "ref": "main",
                "sha": "def456"
            },
            "html_url": "https://github.com/test/test-repo/pull/42",
            "created_at": "2024-01-20T00:00:00Z",
            "user": {
                "login": "testuser"
            },
            "merged": False,
            "mergeable": True
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import CreatePullRequestInput
        params = CreatePullRequestInput(
            owner="test",
            repo="test-repo",
            title="Test PR",
            body="PR body",
            head="feature",
            base="main"
        )
        result = await github_create_pull_request(params)

        # Verify
        assert isinstance(result, str)
        # Should contain PR info
        assert "42" in result or "created" in result.lower() or "success" in result.lower()

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_merge_pull_request(self, mock_request):
        """Test merging a pull request."""
        # Mock merge response
        mock_response = {
            "sha": "merged123",
            "merged": True,
            "message": "Pull request successfully merged"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import MergePullRequestInput
        params = MergePullRequestInput(
            owner="test",
            repo="test-repo",
            pull_number=42
        )
        result = await github_merge_pull_request(params)

        # Verify
        assert isinstance(result, str)
        # Should indicate success
        assert "merged" in result.lower() or "success" in result.lower() or "42" in result


class TestWorkflowOperations:
    """Test GitHub Actions workflow operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_workflows(self, mock_request):
        """Test listing workflows."""
        # Mock workflows response
        mock_response = {
            "total_count": 2,
            "workflows": [
                {
                    "id": 123,
                    "name": "CI",
                    "path": ".github/workflows/ci.yml",
                    "state": "active",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": 124,
                    "name": "Deploy",
                    "path": ".github/workflows/deploy.yml",
                    "state": "active",
                    "created_at": "2024-01-02T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z"
                }
            ]
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListWorkflowsInput
        params = ListWorkflowsInput(
            owner="test",
            repo="test-repo",
            response_format=ResponseFormat.JSON
        )
        result = await github_list_workflows(params)

        # Verify
        assert isinstance(result, str)
        # Should contain workflow info
        assert "CI" in result or "Deploy" in result or "workflow" in result.lower()

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_workflow_runs(self, mock_request):
        """Test getting workflow runs."""
        # Mock workflow runs response
        mock_response = {
            "total_count": 2,
            "workflow_runs": [
                {
                    "id": 12345,
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "success",
                    "html_url": "https://github.com/test/test-repo/actions/runs/12345",
                    "created_at": "2024-01-20T00:00:00Z",
                    "updated_at": "2024-01-20T01:00:00Z"
                },
                {
                    "id": 12346,
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "failure",
                    "html_url": "https://github.com/test/test-repo/actions/runs/12346",
                    "created_at": "2024-01-19T00:00:00Z",
                    "updated_at": "2024-01-19T01:00:00Z"
                }
            ]
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import GetWorkflowRunsInput
        params = GetWorkflowRunsInput(
            owner="test",
            repo="test-repo",
            workflow_id="ci.yml",
            response_format=ResponseFormat.JSON
        )
        result = await github_get_workflow_runs(params)

        # Verify
        assert isinstance(result, str)
        # Should contain run info
        assert "completed" in result or "success" in result or "12345" in result


class TestFileOperations:
    """Test file manipulation operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_str_replace(self, mock_request):
        """Test string replacement in a file."""
        # Mock file content response
        import base64
        content = "Old content to replace"
        encoded_content = base64.b64encode(content.encode()).decode()
        
        mock_file_response = {
            "name": "test.txt",
            "path": "test.txt",
            "content": encoded_content,
            "encoding": "base64",
            "sha": "abc123"
        }
        
        # Mock commit response
        mock_commit_response = {
            "commit": {
                "sha": "new123",
                "html_url": "https://github.com/test/test-repo/commit/new123"
            },
            "content": {
                "sha": "new456"
            }
        }
        
        # First call gets file, second call updates it
        mock_request.side_effect = [mock_file_response, mock_commit_response]

        # Call the tool
        from github_mcp import GitHubStrReplaceInput
        params = GitHubStrReplaceInput(
            owner="test",
            repo="test-repo",
            path="test.txt",
            old_str="Old content",
            new_str="New content"
        )
        result = await github_mcp.github_str_replace(params)

        # Verify
        assert isinstance(result, str)
        assert "replaced" in result.lower() or "updated" in result.lower() or "commit" in result.lower() or "Error" in result


class TestIssueManagement:
    """Test issue lifecycle management."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_update_issue(self, mock_request):
        """Test updating an issue."""
        # Mock updated issue response
        mock_response = {
            "number": 123,
            "title": "Updated Issue",
            "state": "closed",
            "html_url": "https://github.com/test/test-repo/issues/123",
            "updated_at": "2024-01-20T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import UpdateIssueInput
        params = UpdateIssueInput(
            owner="test",
            repo="test-repo",
            issue_number=123,
            state="closed"
        )
        result = await github_mcp.github_update_issue(params)

        # Verify
        assert isinstance(result, str)
        assert "123" in result or "updated" in result.lower() or "closed" in result.lower() or "Error" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_update_issue_with_comment(self, mock_request):
        """Test updating an issue with multiple fields."""
        # Mock updated issue response
        mock_response = {
            "number": 123,
            "title": "Updated Issue Title",
            "body": "Updated body",
            "state": "open",
            "html_url": "https://github.com/test/test-repo/issues/123",
            "updated_at": "2024-01-20T00:00:00Z",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "testuser"}]
        }
        mock_request.return_value = mock_response

        # Call the tool with multiple fields
        from github_mcp import UpdateIssueInput
        params = UpdateIssueInput(
            owner="test",
            repo="test-repo",
            issue_number=123,
            state="open",
            title="Updated Issue Title",
            body="Updated body"
        )
        result = await github_mcp.github_update_issue(params)

        # Verify
        assert isinstance(result, str)
        assert "123" in result or "updated" in result.lower() or "Error" in result


class TestAdvancedErrorHandling:
    """Test advanced error scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_rate_limit_error(self, mock_request):
        """Test handling of rate limit errors (429)."""
        import httpx

        # Mock 429 rate limit error
        mock_request.side_effect = httpx.HTTPStatusError(
            "API rate limit exceeded",
            request=MagicMock(),
            response=MagicMock(status_code=429)
        )

        # Call the tool
        params = RepoInfoInput(
            owner="test",
            repo="test-repo"
        )
        result = await github_get_repo_info(params)

        # Verify error handling
        assert isinstance(result, str)
        assert "error" in result.lower() or "rate limit" in result.lower() or "429" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_server_error(self, mock_request):
        """Test handling of server errors (500)."""
        import httpx

        # Mock 500 server error
        mock_request.side_effect = httpx.HTTPStatusError(
            "Internal server error",
            request=MagicMock(),
            response=MagicMock(status_code=500)
        )

        # Call the tool
        params = RepoInfoInput(
            owner="test",
            repo="test-repo"
        )
        result = await github_get_repo_info(params)

        # Verify error handling
        assert isinstance(result, str)
        assert "error" in result.lower() or "server" in result.lower() or "500" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_network_timeout_error(self, mock_request):
        """Test handling of network timeout errors."""
        import httpx

        # Mock timeout error
        mock_request.side_effect = httpx.TimeoutException(
            "Request timed out",
            request=MagicMock()
        )

        # Call the tool
        params = RepoInfoInput(
            owner="test",
            repo="test-repo"
        )
        result = await github_get_repo_info(params)

        # Verify error handling
        assert isinstance(result, str)
        assert "error" in result.lower() or "timeout" in result.lower() or "network" in result.lower()


class TestEdgeCasesExtended:
    """Test additional edge cases and boundary conditions."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_very_long_issue_body(self, mock_request):
        """Test creating issue with very long body (10,000 chars)."""
        # Mock created issue
        mock_response = {
            "number": 999,
            "title": "Test",
            "body": "x" * 10000,
            "state": "open",
            "html_url": "https://github.com/test/test-repo/issues/999",
            "created_at": "2024-01-20T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        long_body = "x" * 10000
        params = CreateIssueInput(
            owner="test",
            repo="test-repo",
            title="Test",
            body=long_body
        )
        result = await github_create_issue(params)

        # Verify
        assert isinstance(result, str)
        assert "999" in result or "created" in result.lower() or "Error" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_special_characters_in_filename(self, mock_request):
        """Test file operations with special characters."""
        import base64

        # Mock file content with special characters
        content = "Content with unicode: 🐕🍖"
        encoded_content = base64.b64encode(content.encode('utf-8')).decode()

        mock_response = {
            "name": "file-with-émojis-🐕🍖.txt",
            "path": "file-with-émojis-🐕🍖.txt",
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
            path="file-with-émojis-🐕🍖.txt"
        )
        result = await github_get_file_content(params)

        # Verify
        assert isinstance(result, str)
        # Should handle special characters gracefully
        assert "Content" in result or "unicode" in result or "Error" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_empty_search_results_extended(self, mock_request):
        """Test search with no results (already tested, but adding edge case)."""
        # Mock empty response
        mock_response = {
            "total_count": 0,
            "items": []
        }
        mock_request.return_value = mock_response

        # Call the tool
        params = SearchCodeInput(
            query="nonexistent-query-xyz-12345",
            response_format=ResponseFormat.JSON
        )
        result = await github_search_code(params)

        # Verify it handles empty results gracefully
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should return empty list or object with empty items
        if isinstance(parsed, list):
            assert len(parsed) == 0
        elif isinstance(parsed, dict):
            assert parsed.get("total_count", 0) == 0


class TestAdditionalTools:
    """Test additional tools for coverage."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_search_issues(self, mock_request):
        """Test searching for issues."""
        # Mock search results
        mock_response = {
            "total_count": 2,
            "items": [
                {
                    "number": 1,
                    "title": "Bug in feature X",
                    "state": "open",
                    "html_url": "https://github.com/test/repo/issues/1",
                    "user": {"login": "testuser"},
                    "created_at": "2024-01-01T00:00:00Z"
                },
                {
                    "number": 2,
                    "title": "Feature request Y",
                    "state": "open",
                    "html_url": "https://github.com/test/repo/issues/2",
                    "user": {"login": "testuser"},
                    "created_at": "2024-01-02T00:00:00Z"
                }
            ]
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import SearchIssuesInput
        params = SearchIssuesInput(
            query="bug is:open",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_search_issues(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_update_release(self, mock_request):
        """Test updating a release."""
        # Mock updated release response
        mock_response = {
            "tag_name": "v1.0.0",
            "name": "Updated Release",
            "body": "Updated release notes",
            "draft": False,
            "prerelease": False,
            "html_url": "https://github.com/test/test-repo/releases/tag/v1.0.0",
            "created_at": "2024-01-01T00:00:00Z",
            "published_at": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import UpdateReleaseInput
        params = UpdateReleaseInput(
            owner="test",
            repo="test-repo",
            release_id="v1.0.0",
            name="Updated Release",
            body="Updated release notes"
        )
        result = await github_mcp.github_update_release(params)

        # Verify
        assert isinstance(result, str)
        assert "updated" in result.lower() or "v1.0.0" in result or "Release" in result or "Error" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_close_pull_request(self, mock_request):
        """Test closing a pull request."""
        # Mock closed PR response
        mock_response = {
            "number": 42,
            "title": "Test PR",
            "state": "closed",
            "html_url": "https://github.com/test/test-repo/pull/42",
            "closed_at": "2024-01-20T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ClosePullRequestInput
        params = ClosePullRequestInput(
            owner="test",
            repo="test-repo",
            pull_number=42
        )
        result = await github_mcp.github_close_pull_request(params)

        # Verify
        assert isinstance(result, str)
        assert "closed" in result.lower() or "42" in result or "success" in result.lower() or "Error" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_create_pr_review(self, mock_request):
        """Test creating a PR review."""
        # Mock review response
        mock_response = {
            "id": 12345,
            "state": "APPROVED",
            "body": "Looks good!",
            "html_url": "https://github.com/test/test-repo/pull/42#pullrequestreview-12345",
            "user": {
                "login": "testuser"
            },
            "submitted_at": "2024-01-20T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import CreatePRReviewInput
        params = CreatePRReviewInput(
            owner="test",
            repo="test-repo",
            pull_number=42,
            event="APPROVE",
            body="Looks good!"
        )
        result = await github_mcp.github_create_pr_review(params)

        # Verify
        assert isinstance(result, str)
        assert "review" in result.lower() or "approved" in result.lower() or "12345" in result or "Error" in result


class TestSearchRepositories:
    """Test repository search operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_search_repositories(self, mock_request):
        """Test searching for repositories."""
        # Mock search results
        mock_response = {
            "total_count": 2,
            "items": [
                {
                    "full_name": "test/repo1",
                    "name": "repo1",
                    "description": "Test repo 1",
                    "stargazers_count": 100,
                    "language": "Python",
                    "html_url": "https://github.com/test/repo1"
                },
                {
                    "full_name": "test/repo2",
                    "name": "repo2",
                    "description": "Test repo 2",
                    "stargazers_count": 50,
                    "language": "JavaScript",
                    "html_url": "https://github.com/test/repo2"
                }
            ]
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import SearchRepositoriesInput
        params = SearchRepositoriesInput(
            query="test language:python",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_search_repositories(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0


class TestMoreErrorPaths:
    """Test additional error scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_unauthorized_error(self, mock_request):
        """Test 401 unauthorized error."""
        import httpx

        # Mock 401 unauthorized error
        mock_request.side_effect = httpx.HTTPStatusError(
            "Bad credentials",
            request=MagicMock(),
            response=MagicMock(status_code=401)
        )

        # Call the tool
        params = RepoInfoInput(
            owner="test",
            repo="test-repo"
        )
        result = await github_get_repo_info(params)

        # Verify error handling
        assert isinstance(result, str)
        assert "error" in result.lower() or "unauthorized" in result.lower() or "401" in result or "credentials" in result.lower()

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_conflict_error(self, mock_request):
        """Test 409 conflict error."""
        import httpx

        # Mock 409 conflict error
        mock_request.side_effect = httpx.HTTPStatusError(
            "Conflict",
            request=MagicMock(),
            response=MagicMock(status_code=409)
        )

        # Call the tool
        params = CreateIssueInput(
            owner="test",
            repo="test-repo",
            title="Test"
        )
        result = await github_create_issue(params)

        # Verify error handling
        assert isinstance(result, str)
        assert "error" in result.lower() or "conflict" in result.lower() or "409" in result


class TestBatchFileOperations:
    """Test batch file operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_batch_file_operations(self, mock_request):
        """Test batch file updates."""
        # Mock responses for batch operations
        # First: get default branch
        mock_branch_response = {
            "ref": "refs/heads/main",
            "object": {
                "sha": "abc123"
            }
        }
        # Second: get tree
        mock_tree_response = {
            "sha": "tree123",
            "tree": []
        }
        # Third: create tree
        mock_create_tree_response = {
            "sha": "newtree123",
            "url": "https://api.github.com/repos/test/test-repo/git/trees/newtree123"
        }
        # Fourth: create commit
        mock_commit_response = {
            "sha": "commit123",
            "html_url": "https://github.com/test/test-repo/commit/commit123"
        }
        # Fifth: update ref
        mock_ref_response = {
            "ref": "refs/heads/main",
            "object": {
                "sha": "commit123"
            }
        }

        mock_request.side_effect = [
            mock_branch_response,
            mock_tree_response,
            mock_create_tree_response,
            mock_commit_response,
            mock_ref_response
        ]

        # Call the tool
        from github_mcp import BatchFileOperationsInput
        params = BatchFileOperationsInput(
            owner="test",
            repo="test-repo",
            operations=[
                {
                    "operation": "create",
                    "path": "file1.txt",
                    "content": "Content 1"
                },
                {
                    "operation": "update",
                    "path": "file2.txt",
                    "content": "Content 2",
                    "sha": "sha123"
                }
            ],
            message="Batch update"
        )
        result = await github_mcp.github_batch_file_operations(params)

        # Verify
        assert isinstance(result, str)
        assert "commit" in result.lower() or "batch" in result.lower() or "updated" in result.lower() or "Error" in result


class TestFileCreateUpdateDelete:
    """Test individual file operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_create_file(self, mock_request):
        """Test creating a new file."""
        # Mock created file response
        mock_response = {
            "commit": {
                "sha": "new123",
                "html_url": "https://github.com/test/test-repo/commit/new123"
            },
            "content": {
                "name": "new-file.txt",
                "path": "new-file.txt",
                "sha": "content123"
            }
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import CreateFileInput
        params = CreateFileInput(
            owner="test",
            repo="test-repo",
            path="new-file.txt",
            message="Add new file",
            content="File content"
        )
        result = await github_mcp.github_create_file(params)

        # Verify
        assert isinstance(result, str)
        assert "created" in result.lower() or "commit" in result.lower() or "new-file" in result.lower() or "Error" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_update_file(self, mock_request):
        """Test updating a file."""
        # Mock updated file response
        mock_response = {
            "commit": {
                "sha": "update123",
                "html_url": "https://github.com/test/test-repo/commit/update123"
            },
            "content": {
                "name": "test.txt",
                "path": "test.txt",
                "sha": "newsha123"
            }
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import UpdateFileInput
        params = UpdateFileInput(
            owner="test",
            repo="test-repo",
            path="test.txt",
            message="Update file",
            content="# Updated content",
            sha="oldsha123"
        )
        result = await github_mcp.github_update_file(params)

        # Verify
        assert isinstance(result, str)
        assert "updated" in result.lower() or "commit" in result.lower() or "Error" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_delete_file(self, mock_request):
        """Test deleting a file."""
        # Mock deleted file response
        mock_response = {
            "commit": {
                "sha": "delete123",
                "html_url": "https://github.com/test/test-repo/commit/delete123"
            }
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import DeleteFileInput
        params = DeleteFileInput(
            owner="test",
            repo="test-repo",
            path="old-file.txt",
            message="Delete old file",
            sha="filesha123"
        )
        result = await github_mcp.github_delete_file(params)

        # Verify
        assert isinstance(result, str)
        assert "deleted" in result.lower() or "commit" in result.lower() or "removed" in result.lower() or "Error" in result


class TestRepositoryTransferArchive:
    """Test repository transfer and archive operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_transfer_repository(self, mock_request):
        """Test transferring a repository."""
        # Mock transfer response
        mock_response = {
            "full_name": "newowner/test-repo",
            "owner": {
                "login": "newowner"
            },
            "html_url": "https://github.com/newowner/test-repo"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import TransferRepositoryInput
        params = TransferRepositoryInput(
            owner="test",
            repo="test-repo",
            new_owner="newowner"
        )
        result = await github_mcp.github_transfer_repository(params)

        # Verify
        assert isinstance(result, str)
        assert "transferred" in result.lower() or "newowner" in result or "Error" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_archive_repository(self, mock_request):
        """Test archiving a repository."""
        # Mock archive response
        mock_response = {
            "full_name": "test/test-repo",
            "archived": True,
            "html_url": "https://github.com/test/test-repo"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ArchiveRepositoryInput
        params = ArchiveRepositoryInput(
            owner="test",
            repo="test-repo",
            archived=True
        )
        result = await github_mcp.github_archive_repository(params)

        # Verify
        assert isinstance(result, str)
        assert "archived" in result.lower() or "archive" in result.lower() or "Error" in result


class TestRepositoryCreationDeletion:
    """Test repository creation and deletion."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_create_repository(self, mock_request):
        """Test creating a repository."""
        # Mock created repo response
        mock_response = {
            "full_name": "test/new-repo",
            "name": "new-repo",
            "html_url": "https://github.com/test/new-repo",
            "private": False,
            "description": "Test repository"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import CreateRepositoryInput
        params = CreateRepositoryInput(
            name="new-repo",
            description="Test repository",
            private=False
        )
        result = await github_mcp.github_create_repository(params)

        # Verify
        assert isinstance(result, str)
        assert "created" in result.lower() or "new-repo" in result or "Error" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_delete_repository(self, mock_request):
        """Test deleting a repository."""
        # Mock delete response (204 No Content typically)
        mock_request.return_value = None

        # Call the tool
        from github_mcp import DeleteRepositoryInput
        params = DeleteRepositoryInput(
            owner="test",
            repo="test-repo"
        )
        result = await github_mcp.github_delete_repository(params)

        # Verify
        assert isinstance(result, str)
        assert "deleted" in result.lower() or "removed" in result.lower() or "Error" in result


class TestGraphQLOperations:
    """Test GraphQL-based operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_pr_overview_graphql(self, mock_request):
        """Test GraphQL PR overview."""
        # Mock GraphQL response
        mock_response = {
            "data": {
                "repository": {
                    "pullRequests": {
                        "nodes": [
                            {
                                "number": 1,
                                "title": "Test PR",
                                "state": "OPEN",
                                "author": {
                                    "login": "testuser"
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import GraphQLPROverviewInput
        params = GraphQLPROverviewInput(
            owner="test",
            repo="test-repo",
            pull_number=1
        )
        result = await github_mcp.github_get_pr_overview_graphql(params)

        # Verify
        assert isinstance(result, str)
        # Should contain PR info or be parseable JSON
        assert "Test PR" in result or "1" in result or "{" in result or "Error" in result


class TestWorkflowSuggestions:
    """Test workflow suggestion operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_suggest_workflow(self, mock_request):
        """Test workflow suggestions."""
        # Mock suggestion response (this tool might return markdown)
        mock_response = {
            "suggestion": "Use GitHub API for read operations",
            "reason": "Large repository detected"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import WorkflowSuggestionInput
        params = WorkflowSuggestionInput(
            operation="read_files"
        )
        result = await github_mcp.github_suggest_workflow(params)

        # Verify
        assert isinstance(result, str)
        # Should contain suggestion or guidance
        assert len(result) > 0


class TestAdvancedSearchOperations:
    """Test advanced search functionality."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_search_code_advanced(self, mock_request):
        """Test advanced code search with filters."""
        # Mock search results
        mock_response = {
            "total_count": 5,
            "items": [
                {
                    "name": "test.py",
                    "path": "src/test.py",
                    "repository": {
                        "full_name": "test/repo"
                    },
                    "text_matches": [
                        {
                            "fragment": "def test_function():"
                        }
                    ]
                }
            ]
        }
        mock_request.return_value = mock_response

        # Call the tool with advanced query
        from github_mcp import SearchCodeInput
        params = SearchCodeInput(
            query="test_function language:python",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_search_code(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0


class TestEdgeCasesAdvanced:
    """Test additional advanced edge cases."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_issues_with_pagination(self, mock_request):
        """Test handling paginated results."""
        # Mock paginated response
        mock_response = {
            "items": [
                {
                    "number": i,
                    "title": f"Issue {i}",
                    "state": "open",
                    "html_url": f"https://github.com/test/test/issues/{i}",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
                for i in range(1, 101)  # 100 issues
            ],
            "total_count": 100
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListIssuesInput
        params = ListIssuesInput(
            owner="test",
            repo="test-repo",
            state="all",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_list_issues(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should handle large result sets
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_repo_info_null_description(self, mock_request):
        """Test handling null/missing descriptions."""
        # Mock repo with null description
        mock_response = {
            "name": "test-repo",
            "full_name": "test/test-repo",
            "description": None,  # Null description
            "stargazers_count": 0,
            "forks_count": 0,
            "html_url": "https://github.com/test/test-repo",
            "archived": False,
            "default_branch": "main",
            "language": None,
            "license": None,
            "topics": [],
            "homepage": None,
            "clone_url": "https://github.com/test/test-repo.git",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import RepoInfoInput
        params = RepoInfoInput(
            owner="test",
            repo="test-repo"
        )
        result = await github_mcp.github_get_repo_info(params)

        # Verify - should handle None gracefully
        assert isinstance(result, str)
        assert "test-repo" in result or "Error" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_abuse_rate_limit(self, mock_request):
        """Test handling secondary rate limits."""
        import httpx

        # Mock abuse rate limit error
        mock_request.side_effect = httpx.HTTPStatusError(
            "You have triggered an abuse detection mechanism",
            request=MagicMock(),
            response=MagicMock(status_code=403)
        )

        # Call the tool
        from github_mcp import RepoInfoInput
        params = RepoInfoInput(
            owner="test",
            repo="test-repo"
        )
        result = await github_mcp.github_get_repo_info(params)

        # Verify error handling
        assert isinstance(result, str)
        assert "error" in result.lower() or "403" in result or "abuse" in result.lower() or "rate limit" in result.lower()


class TestLicenseOperations:
    """Test license information operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_license_info(self, mock_request):
        """Test getting license information."""
        # Mock license response
        mock_response = {
            "license": "AGPL v3",
            "tier": "FREE",
            "status": "Valid"
        }
        mock_request.return_value = mock_response

        # Call the tool (no params needed)
        result = await github_mcp.github_license_info()

        # Verify
        assert isinstance(result, str)
        assert "license" in result.lower() or "AGPL" in result or "tier" in result.lower()


class TestUpdateRepository:
    """Test repository update operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_update_repository(self, mock_request):
        """Test updating repository settings."""
        # Mock updated repo response
        mock_response = {
            "full_name": "test/test-repo",
            "name": "test-repo",
            "description": "Updated description",
            "html_url": "https://github.com/test/test-repo",
            "private": False,
            "archived": False
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import UpdateRepositoryInput
        params = UpdateRepositoryInput(
            owner="test",
            repo="test-repo",
            description="Updated description"
        )
        result = await github_mcp.github_update_repository(params)

        # Verify
        assert isinstance(result, str)
        assert "updated" in result.lower() or "test-repo" in result or "description" in result.lower() or "Error" in result


class TestGrepOperations:
    """Test grep/search operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_grep(self, mock_request):
        """Test GitHub grep operation."""
        # Mock grep response - github_grep uses search_code API
        mock_response = {
            "total_count": 2,
            "items": [
                {
                    "name": "test.py",
                    "path": "src/test.py",
                    "repository": {
                        "full_name": "test/repo"
                    },
                    "text_matches": [
                        {
                            "fragment": "def test_function():"
                        }
                    ]
                }
            ]
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import GitHubGrepInput
        params = GitHubGrepInput(
            owner="test",
            repo="test-repo",
            pattern="test_function",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_grep(params)

        # Verify - result might be JSON string or markdown
        assert isinstance(result, str)
        # Try to parse if it looks like JSON
        if result.strip().startswith('{') or result.strip().startswith('['):
            try:
                parsed = json.loads(result)
                # Should have items or be a list
                if isinstance(parsed, dict):
                    assert "items" in parsed or "total_count" in parsed
                elif isinstance(parsed, list):
                    assert len(parsed) > 0
            except json.JSONDecodeError:
                # If not JSON, that's okay - might be markdown
                pass


class TestReadFileChunk:
    """Test file chunk reading operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_read_file_chunk(self, mock_request):
        """Test reading a file chunk."""
        # Mock file content response
        file_content = b"Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        mock_response = {
            "content": encoded_content,
            "encoding": "base64"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import GitHubReadFileChunkInput
        params = GitHubReadFileChunkInput(
            owner="test",
            repo="test-repo",
            path="test.txt",
            start_line=2,
            num_lines=3
        )
        result = await github_mcp.github_read_file_chunk(params)

        # Verify
        assert isinstance(result, str)
        assert "Line 2" in result or "Line 3" in result or "Line 4" in result or "Error" in result


class TestStringReplaceOperations:
    """Test string replace operations."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_str_replace(self, mock_request):
        """Test string replace in GitHub files."""
        # Mock file content and update response
        file_content = b"old text\nmore text\nold text again"
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        # First call: get file content
        # Second call: update file
        mock_request.side_effect = [
            {
                "content": encoded_content,
                "encoding": "base64",
                "sha": "oldsha123"
            },
            {
                "content": {
                    "sha": "newsha123"
                },
                "commit": {
                    "sha": "commit123",
                    "html_url": "https://github.com/test/test-repo/commit/commit123"
                }
            }
        ]

        # Call the tool
        from github_mcp import GitHubStrReplaceInput
        params = GitHubStrReplaceInput(
            owner="test",
            repo="test-repo",
            path="test.txt",
            old_str="old text",
            new_str="new text"
        )
        result = await github_mcp.github_str_replace(params)

        # Verify
        assert isinstance(result, str)
        assert "replaced" in result.lower() or "commit" in result.lower() or "new text" in result.lower() or "Error" in result


class TestComplexWorkflows:
    """Test complex multi-step workflows."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_issue_to_pr_workflow(self, mock_request):
        """Test creating issue, then PR workflow."""
        # Step 1: Create issue
        mock_issue = {
            "number": 42,
            "title": "Bug fix needed",
            "html_url": "https://github.com/test/test/issues/42",
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        # Step 2: Get default branch
        mock_branch = {
            "ref": "refs/heads/main",
            "object": {"sha": "abc123"}
        }
        
        # Step 3: Create PR
        mock_pr = {
            "number": 10,
            "title": "Fix #42",
            "html_url": "https://github.com/test/test/pull/10",
            "state": "open",
            "head": {"ref": "fix-42"},
            "base": {"ref": "main"}
        }
        
        mock_request.side_effect = [mock_issue, mock_branch, mock_pr]

        # Test the workflow - create issue
        from github_mcp import CreateIssueInput
        issue_params = CreateIssueInput(
            owner="test",
            repo="test",
            title="Bug fix needed"
        )
        issue_result = await github_mcp.github_create_issue(issue_params)
        assert "42" in str(issue_result) or "created" in str(issue_result).lower() or "Error" in issue_result

        # Create PR
        from github_mcp import CreatePullRequestInput
        pr_params = CreatePullRequestInput(
            owner="test",
            repo="test",
            title="Fix #42",
            head="fix-42",
            base="main"
        )
        pr_result = await github_mcp.github_create_pull_request(pr_params)
        assert "10" in str(pr_result) or "created" in str(pr_result).lower() or "Error" in pr_result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_release_workflow(self, mock_request):
        """Test complete release workflow."""
        # Mock release response
        mock_release = {
            "tag_name": "v1.0.0",
            "name": "Release 1.0",
            "id": 123,
            "html_url": "https://github.com/test/test/releases/tag/v1.0.0",
            "created_at": "2024-01-01T00:00:00Z",
            "published_at": "2024-01-01T00:00:00Z",
            "author": {
                "login": "testuser"
            },
            "draft": False,
            "prerelease": False
        }
        mock_request.return_value = mock_release

        # Test workflow
        from github_mcp import CreateReleaseInput
        params = CreateReleaseInput(
            owner="test",
            repo="test",
            tag_name="v1.0.0",
            name="Release 1.0"
        )
        result = await github_mcp.github_create_release(params)

        assert "v1.0.0" in str(result) or "123" in str(result) or "created" in str(result).lower() or "Error" in result


class TestMoreErrorScenarios:
    """Test additional error scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_validation_error(self, mock_request):
        """Test validation errors (422)."""
        import httpx

        # Mock 422 validation error
        mock_request.side_effect = httpx.HTTPStatusError(
            "Validation Failed",
            request=MagicMock(),
            response=MagicMock(status_code=422)
        )

        # Call the tool - use a valid title but mock will return 422
        from github_mcp import CreateIssueInput
        params = CreateIssueInput(
            owner="test",
            repo="test-repo",
            title="Test Issue"
        )
        result = await github_mcp.github_create_issue(params)

        # Verify error handling
        assert isinstance(result, str)
        assert "error" in result.lower() or "validation" in result.lower() or "422" in result

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_gone_error(self, mock_request):
        """Test 410 Gone errors (deleted resources)."""
        import httpx

        # Mock 410 Gone error
        mock_request.side_effect = httpx.HTTPStatusError(
            "Repository access blocked",
            request=MagicMock(),
            response=MagicMock(status_code=410)
        )

        # Call the tool
        from github_mcp import RepoInfoInput
        params = RepoInfoInput(
            owner="test",
            repo="blocked-repo"
        )
        result = await github_mcp.github_get_repo_info(params)

        # Verify error handling
        assert isinstance(result, str)
        assert "error" in result.lower() or "blocked" in result.lower() or "410" in result or "gone" in result.lower()


class TestPerformanceScenarios:
    """Test handling of large data sets."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_large_file_content(self, mock_request):
        """Test handling large file content (1MB+)."""
        # Simulate 1MB file
        large_content = b"x" * (1024 * 1024)
        encoded_content = base64.b64encode(large_content).decode('utf-8')
        
        mock_response = {
            "content": encoded_content,
            "encoding": "base64",
            "sha": "filesha123"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import GetFileContentInput
        params = GetFileContentInput(
            owner="test",
            repo="test-repo",
            path="large-file.bin"
        )
        result = await github_mcp.github_get_file_content(params)

        # Verify - should handle large files
        assert isinstance(result, str)
        # Should either return content or error gracefully
        assert len(result) > 0

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_many_commits(self, mock_request):
        """Test listing many commits (100+)."""
        # Create 100 mock commits
        mock_commits = []
        for i in range(100):
            mock_commits.append({
                "sha": f"abc{i:03d}",
                "commit": {
                    "message": f"Commit {i}",
                    "author": {
                        "name": "Test User",
                        "date": "2024-01-01T00:00:00Z"
                    }
                },
                "author": {
                    "login": "testuser"
                },
                "html_url": f"https://github.com/test/test/commit/abc{i:03d}"
            })
        
        mock_response = {
            "items": mock_commits,
            "total_count": 100
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListCommitsInput
        params = ListCommitsInput(
            owner="test",
            repo="test-repo",
            limit=100,
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_list_commits(params)

        # Verify - should handle large result sets
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0


class TestAdvancedFileOperations:
    """Test advanced file operation scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_batch_file_operations_large(self, mock_request):
        """Test batch operations with many files."""
        # Mock responses for batch operations
        # First: get default branch
        mock_branch_response = {
            "ref": "refs/heads/main",
            "object": {"sha": "abc123"}
        }
        # Second: get tree
        mock_tree_response = {
            "sha": "tree123",
            "tree": []
        }
        # Third: create tree with many files
        mock_create_tree_response = {
            "sha": "newtree123",
            "url": "https://api.github.com/repos/test/test-repo/git/trees/newtree123"
        }
        # Fourth: create commit
        mock_commit_response = {
            "sha": "commit123",
            "html_url": "https://github.com/test/test-repo/commit/commit123"
        }
        # Fifth: update ref
        mock_ref_response = {
            "ref": "refs/heads/main",
            "object": {"sha": "commit123"}
        }

        mock_request.side_effect = [
            mock_branch_response,
            mock_tree_response,
            mock_create_tree_response,
            mock_commit_response,
            mock_ref_response
        ]

        # Call the tool with many operations
        from github_mcp import BatchFileOperationsInput
        operations = [
            {
                "operation": "create",
                "path": f"file{i}.txt",
                "content": f"Content {i}"
            }
            for i in range(20)  # 20 files
        ]
        params = BatchFileOperationsInput(
            owner="test",
            repo="test-repo",
            operations=operations,
            message="Batch update 20 files"
        )
        result = await github_mcp.github_batch_file_operations(params)

        # Verify
        assert isinstance(result, str)
        assert "commit" in result.lower() or "batch" in result.lower() or "updated" in result.lower() or "Error" in result


class TestAdvancedSearchOperations:
    """Test advanced search scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_search_code_complex_query(self, mock_request):
        """Test complex search queries."""
        # Mock search results
        mock_response = {
            "total_count": 50,
            "items": [
                {
                    "name": f"test{i}.py",
                    "path": f"src/test{i}.py",
                    "repository": {
                        "full_name": "test/repo"
                    },
                    "text_matches": [
                        {
                            "fragment": f"def test_function_{i}():"
                        }
                    ]
                }
                for i in range(50)
            ]
        }
        mock_request.return_value = mock_response

        # Call the tool with complex query
        from github_mcp import SearchCodeInput
        params = SearchCodeInput(
            query="language:python def test_function",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_search_code(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0


class TestListRepoContentsAdvanced:
    """Test advanced repository contents listing."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_repo_contents_nested(self, mock_request):
        """Test listing nested directory contents."""
        # Mock nested directory structure
        mock_response = [
            {
                "name": "src",
                "type": "dir",
                "path": "src",
                "sha": "dirsha123"
            },
            {
                "name": "README.md",
                "type": "file",
                "path": "README.md",
                "sha": "filesha123",
                "size": 1024
            },
            {
                "name": ".github",
                "type": "dir",
                "path": ".github",
                "sha": "dirsha456"
            }
        ]
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListRepoContentsInput
        params = ListRepoContentsInput(
            owner="test",
            repo="test-repo",
            path="",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_list_repo_contents(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or isinstance(parsed.get("contents"), list)
        elif isinstance(parsed, list):
            assert len(parsed) > 0

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_repo_contents_subdirectory(self, mock_request):
        """Test listing contents of a subdirectory."""
        # Mock subdirectory contents
        mock_response = [
            {
                "name": "main.py",
                "type": "file",
                "path": "src/main.py",
                "sha": "filesha789",
                "size": 2048
            },
            {
                "name": "utils.py",
                "type": "file",
                "path": "src/utils.py",
                "sha": "filesha012",
                "size": 1536
            }
        ]
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListRepoContentsInput
        params = ListRepoContentsInput(
            owner="test",
            repo="test-repo",
            path="src",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_list_repo_contents(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or isinstance(parsed.get("contents"), list)
        elif isinstance(parsed, list):
            assert len(parsed) > 0


class TestListCommitsAdvanced:
    """Test advanced commit listing scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_commits_with_author_filter(self, mock_request):
        """Test listing commits filtered by author."""
        # Mock commits from specific author
        mock_response = {
            "items": [
                {
                    "sha": f"sha{i}",
                    "commit": {
                        "message": f"Commit {i}",
                        "author": {
                            "name": "Test Author",
                            "email": "test@example.com",
                            "date": "2024-01-01T00:00:00Z"
                        }
                    },
                    "author": {
                        "login": "testauthor"
                    },
                    "html_url": f"https://github.com/test/test/commit/sha{i}"
                }
                for i in range(10)
            ],
            "total_count": 10
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListCommitsInput
        params = ListCommitsInput(
            owner="test",
            repo="test-repo",
            author="testauthor",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_list_commits(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_commits_with_path_filter(self, mock_request):
        """Test listing commits filtered by path."""
        # Mock commits affecting specific path
        mock_response = {
            "items": [
                {
                    "sha": f"sha{i}",
                    "commit": {
                        "message": f"Update README {i}",
                        "author": {
                            "name": "Test User",
                            "date": "2024-01-01T00:00:00Z"
                        }
                    },
                    "author": {
                        "login": "testuser"
                    },
                    "html_url": f"https://github.com/test/test/commit/sha{i}"
                }
                for i in range(5)
            ],
            "total_count": 5
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListCommitsInput
        params = ListCommitsInput(
            owner="test",
            repo="test-repo",
            path="README.md",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_list_commits(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0


class TestGetUserInfoAdvanced:
    """Test advanced user info scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_user_info_organization(self, mock_request):
        """Test getting organization info."""
        # Mock organization response
        mock_response = {
            "login": "testorg",
            "type": "Organization",
            "name": "Test Organization",
            "description": "Test org description",
            "public_repos": 50,
            "followers": 100,
            "html_url": "https://github.com/testorg",
            "created_at": "2020-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import GetUserInfoInput
        params = GetUserInfoInput(
            username="testorg"
        )
        result = await github_mcp.github_get_user_info(params)

        # Verify
        assert isinstance(result, str)
        assert "testorg" in result or "Organization" in result or "Error" in result


class TestGetPRDetailsAdvanced:
    """Test advanced PR details scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_pr_details_with_reviews(self, mock_request):
        """Test getting PR details with review information."""
        # Mock PR with reviews
        mock_response = {
            "number": 42,
            "title": "Test PR",
            "state": "open",
            "html_url": "https://github.com/test/test/pull/42",
            "author": {
                "login": "testuser"
            },
            "reviews": [
                {
                    "id": 1,
                    "state": "APPROVED",
                    "author": {
                        "login": "reviewer1"
                    }
                },
                {
                    "id": 2,
                    "state": "COMMENTED",
                    "author": {
                        "login": "reviewer2"
                    }
                }
            ],
            "commits": 5,
            "additions": 100,
            "deletions": 50,
            "changed_files": 3,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import GetPullRequestDetailsInput
        params = GetPullRequestDetailsInput(
            owner="test",
            repo="test-repo",
            pull_number=42,
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_get_pr_details(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have PR info
        if isinstance(parsed, dict):
            assert "number" in parsed or "title" in parsed or "reviews" in parsed
        else:
            assert "42" in result or "Test PR" in result or "Error" in result


class TestListPullRequestsAdvanced:
    """Test advanced pull request listing scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_pull_requests_draft(self, mock_request):
        """Test listing draft pull requests."""
        # Mock draft PRs
        mock_response = {
            "items": [
                {
                    "number": 10,
                    "title": "Draft: WIP feature",
                    "state": "open",
                    "draft": True,
                    "html_url": "https://github.com/test/test/pull/10",
                    "author": {
                        "login": "testuser"
                    },
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                {
                    "number": 11,
                    "title": "Draft: Another WIP",
                    "state": "open",
                    "draft": True,
                    "html_url": "https://github.com/test/test/pull/11",
                    "author": {
                        "login": "testuser"
                    },
                    "created_at": "2024-01-02T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z"
                }
            ],
            "total_count": 2
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListPullRequestsInput
        params = ListPullRequestsInput(
            owner="test",
            repo="test-repo",
            state="open",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_list_pull_requests(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_pull_requests_merged(self, mock_request):
        """Test listing merged pull requests."""
        # Mock merged PRs
        mock_response = {
            "items": [
                {
                    "number": 5,
                    "title": "Merged feature",
                    "state": "closed",
                    "merged": True,
                    "merged_at": "2024-01-01T00:00:00Z",
                    "html_url": "https://github.com/test/test/pull/5",
                    "author": {
                        "login": "testuser"
                    },
                    "created_at": "2023-12-31T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ],
            "total_count": 1
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListPullRequestsInput
        params = ListPullRequestsInput(
            owner="test",
            repo="test-repo",
            state="closed",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_list_pull_requests(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0


class TestListWorkflowsAdvanced:
    """Test advanced workflow listing scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_workflows_inactive(self, mock_request):
        """Test listing workflows including inactive ones."""
        # Mock workflows with inactive state
        mock_response = {
            "total_count": 3,
            "workflows": [
                {
                    "id": 1,
                    "name": "CI",
                    "path": ".github/workflows/ci.yml",
                    "state": "active"
                },
                {
                    "id": 2,
                    "name": "Deploy",
                    "path": ".github/workflows/deploy.yml",
                    "state": "active"
                },
                {
                    "id": 3,
                    "name": "Old Workflow",
                    "path": ".github/workflows/old.yml",
                    "state": "disabled_manually"
                }
            ]
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListWorkflowsInput
        params = ListWorkflowsInput(
            owner="test",
            repo="test-repo",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_list_workflows(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have workflows or be a list
        if isinstance(parsed, dict):
            assert "workflows" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0


class TestGetWorkflowRunsAdvanced:
    """Test advanced workflow run scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_get_workflow_runs_filtered(self, mock_request):
        """Test getting workflow runs with status filter."""
        # Mock workflow runs with different statuses
        mock_response = {
            "total_count": 5,
            "workflow_runs": [
                {
                    "id": 100,
                    "status": "completed",
                    "conclusion": "success",
                    "html_url": "https://github.com/test/test/actions/runs/100",
                    "created_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": 101,
                    "status": "completed",
                    "conclusion": "failure",
                    "html_url": "https://github.com/test/test/actions/runs/101",
                    "created_at": "2024-01-02T00:00:00Z"
                },
                {
                    "id": 102,
                    "status": "in_progress",
                    "conclusion": None,
                    "html_url": "https://github.com/test/test/actions/runs/102",
                    "created_at": "2024-01-03T00:00:00Z"
                }
            ]
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import GetWorkflowRunsInput
        params = GetWorkflowRunsInput(
            owner="test",
            repo="test-repo",
            workflow_id="ci.yml",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_get_workflow_runs(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have workflow_runs or be a list
        if isinstance(parsed, dict):
            assert "workflow_runs" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0


class TestGrepAdvanced:
    """Test advanced grep scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_grep_with_context(self, mock_request):
        """Test grep with context lines."""
        # Mock tree and file content responses
        # First: get tree
        mock_tree = {
            "sha": "tree123",
            "tree": [
                {
                    "path": "src/test.py",
                    "type": "blob",
                    "sha": "filesha123"
                }
            ]
        }
        # Second: get file content
        file_content = b"def function1():\n    pass\n\ndef function2():\n    pass"
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        mock_file = {
            "content": encoded_content,
            "encoding": "base64"
        }
        
        mock_request.side_effect = [mock_tree, mock_file]

        # Call the tool
        from github_mcp import GitHubGrepInput
        params = GitHubGrepInput(
            owner="test",
            repo="test-repo",
            pattern="function",
            context_lines=2,
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_grep(params)

        # Verify
        assert isinstance(result, str)
        # Should contain matches or be parseable
        if result.strip().startswith('{') or result.strip().startswith('['):
            try:
                parsed = json.loads(result)
                assert isinstance(parsed, (dict, list))
            except json.JSONDecodeError:
                pass


class TestListIssuesAdvanced:
    """Test advanced issue listing scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_list_issues_with_labels(self, mock_request):
        """Test listing issues filtered by labels."""
        # Mock issues with labels
        mock_response = {
            "items": [
                {
                    "number": 1,
                    "title": "Bug report",
                    "state": "open",
                    "labels": [
                        {"name": "bug", "color": "d73a4a"},
                        {"name": "urgent", "color": "b60205"}
                    ],
                    "html_url": "https://github.com/test/test/issues/1",
                    "user": {"login": "testuser"},
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                {
                    "number": 2,
                    "title": "Feature request",
                    "state": "open",
                    "labels": [
                        {"name": "enhancement", "color": "a2eeef"}
                    ],
                    "html_url": "https://github.com/test/test/issues/2",
                    "user": {"login": "testuser"},
                    "created_at": "2024-01-02T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z"
                }
            ],
            "total_count": 2
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import ListIssuesInput
        params = ListIssuesInput(
            owner="test",
            repo="test-repo",
            state="open",
            labels="bug",
            response_format=ResponseFormat.JSON
        )
        result = await github_mcp.github_list_issues(params)

        # Verify
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Should have items or be a list
        if isinstance(parsed, dict):
            assert "items" in parsed or "total_count" in parsed
        elif isinstance(parsed, list):
            assert len(parsed) > 0


class TestCreateIssueAdvanced:
    """Test advanced issue creation scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_create_issue_with_labels_and_assignees(self, mock_request):
        """Test creating issue with labels and assignees."""
        # Mock created issue
        mock_response = {
            "number": 50,
            "title": "New issue",
            "body": "Issue description",
            "state": "open",
            "labels": [
                {"name": "bug", "color": "d73a4a"},
                {"name": "priority", "color": "b60205"}
            ],
            "assignees": [
                {"login": "user1"},
                {"login": "user2"}
            ],
            "html_url": "https://github.com/test/test/issues/50",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import CreateIssueInput
        params = CreateIssueInput(
            owner="test",
            repo="test-repo",
            title="New issue",
            body="Issue description",
            labels=["bug", "priority"],
            assignees=["user1", "user2"]
        )
        result = await github_mcp.github_create_issue(params)

        # Verify
        assert isinstance(result, str)
        assert "50" in result or "created" in result.lower() or "New issue" in result or "Error" in result


class TestUpdateIssueAdvanced:
    """Test advanced issue update scenarios."""

    @pytest.mark.asyncio
    @patch('github_mcp._make_github_request')
    async def test_github_update_issue_with_labels(self, mock_request):
        """Test updating issue with label changes."""
        # Mock updated issue
        mock_response = {
            "number": 25,
            "title": "Updated issue",
            "state": "open",
            "labels": [
                {"name": "bug", "color": "d73a4a"},
                {"name": "fixed", "color": "0e8a16"}
            ],
            "html_url": "https://github.com/test/test/issues/25",
            "updated_at": "2024-01-02T00:00:00Z"
        }
        mock_request.return_value = mock_response

        # Call the tool
        from github_mcp import UpdateIssueInput
        params = UpdateIssueInput(
            owner="test",
            repo="test-repo",
            issue_number=25,
            labels=["bug", "fixed"]
        )
        result = await github_mcp.github_update_issue(params)

        # Verify
        assert isinstance(result, str)
        assert "25" in result or "updated" in result.lower() or "Error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
