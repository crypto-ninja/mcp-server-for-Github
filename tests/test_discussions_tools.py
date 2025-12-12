"""
Tests for GitHub Discussions tools (Phase 2).
"""

import pytest
from unittest.mock import patch

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.github_mcp.tools import (  # noqa: E402
    github_get_discussion,
    github_list_discussions,
    github_list_discussion_categories,
    github_list_discussion_comments,
)
from src.github_mcp.models import (
    ListDiscussionsInput,
    GetDiscussionInput,
    ListDiscussionCategoriesInput,
    ListDiscussionCommentsInput,
)  # noqa: E402


class TestDiscussionsTools:
    """Test suite for GitHub Discussions tools."""

    @pytest.mark.asyncio
    @patch("src.github_mcp.utils.requests._get_auth_token_fallback")
    @patch("src.github_mcp.tools.discussions._make_github_request")
    async def test_list_discussions(self, mock_github_request, mock_auth_token):
        """Test listing discussions."""
        mock_auth_token.return_value = "test-token"
        mock_github_request.return_value = [
            {"number": 1, "title": "Welcome!", "category": {"name": "General"}}
        ]

        params = ListDiscussionsInput(owner="test-owner", repo="test-repo")

        await github_list_discussions(params)

        mock_github_request.assert_called_once()
        assert "/discussions" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    @patch("src.github_mcp.utils.requests._get_auth_token_fallback")
    @patch("src.github_mcp.tools.discussions._make_github_request")
    async def test_list_discussions_with_category(
        self, mock_github_request, mock_auth_token
    ):
        """Test listing discussions with category filter."""
        mock_auth_token.return_value = "test-token"
        mock_github_request.return_value = []

        params = ListDiscussionsInput(
            owner="test-owner", repo="test-repo", category="qa"
        )

        await github_list_discussions(params)

        call_args = mock_github_request.call_args
        params_dict = call_args[1].get("params", {})
        assert params_dict.get("category") == "qa"

    @pytest.mark.asyncio
    @patch("src.github_mcp.utils.requests._get_auth_token_fallback")
    @patch("src.github_mcp.tools.discussions._make_github_request")
    async def test_get_discussion(self, mock_github_request, mock_auth_token):
        """Test getting a specific discussion."""
        mock_auth_token.return_value = "test-token"
        mock_github_request.return_value = {
            "number": 1,
            "title": "Welcome!",
            "body": "Welcome to discussions",
        }

        params = GetDiscussionInput(
            owner="test-owner", repo="test-repo", discussion_number=1
        )

        await github_get_discussion(params)

        mock_github_request.assert_called_once()
        assert "/discussions/1" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    @patch("src.github_mcp.utils.requests._get_auth_token_fallback")
    @patch("src.github_mcp.tools.discussions._make_github_request")
    async def test_list_discussion_categories(
        self, mock_github_request, mock_auth_token
    ):
        """Test listing discussion categories."""
        mock_auth_token.return_value = "test-token"
        mock_github_request.return_value = [
            {"id": "1", "name": "Announcements"},
            {"id": "2", "name": "Q&A"},
        ]

        params = ListDiscussionCategoriesInput(owner="test-owner", repo="test-repo")

        await github_list_discussion_categories(params)

        mock_github_request.assert_called_once()
        assert "/discussions/categories" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    @patch("src.github_mcp.utils.requests._get_auth_token_fallback")
    @patch("src.github_mcp.tools.discussions._make_github_request")
    async def test_list_discussion_comments(self, mock_github_request, mock_auth_token):
        """Test listing discussion comments."""
        mock_auth_token.return_value = "test-token"
        mock_github_request.return_value = [
            {"id": 1, "body": "First comment"},
            {"id": 2, "body": "Second comment"},
        ]

        params = ListDiscussionCommentsInput(
            owner="test-owner", repo="test-repo", discussion_number=1
        )

        await github_list_discussion_comments(params)

        mock_github_request.assert_called_once()
        assert "/discussions/1/comments" in mock_github_request.call_args[0][0]
