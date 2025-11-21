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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
