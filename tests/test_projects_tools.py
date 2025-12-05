"""
Tests for GitHub Projects tools (Phase 2).
"""

import pytest
import json
from unittest.mock import AsyncMock, patch

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from github_mcp import (  # noqa: E402
    github_list_repo_projects,
    github_list_org_projects,
    github_get_project,
    github_create_repo_project,
    github_create_org_project,
    github_update_project,
    github_delete_project,
    github_list_project_columns,
    github_create_project_column,
    ListRepoProjectsInput,
    ListOrgProjectsInput,
    GetProjectInput,
    CreateRepoProjectInput,
    CreateOrgProjectInput,
    UpdateProjectInput,
    DeleteProjectInput,
    ListProjectColumnsInput,
    CreateProjectColumnInput,
    ResponseFormat,
)


class TestProjectsTools:
    """Test suite for GitHub Projects tools."""

    @pytest.fixture
    def mock_github_request(self):
        with patch('github_mcp._make_github_request') as mock:
            yield mock

    @pytest.fixture
    def mock_auth_token(self):
        with patch('github_mcp._get_auth_token_fallback') as mock:
            mock.return_value = "test-token"
            yield mock

    @pytest.mark.asyncio
    async def test_list_repo_projects(self, mock_github_request, mock_auth_token):
        """Test listing repository projects."""
        mock_github_request.return_value = [
            {"id": 1, "name": "Sprint 1", "state": "open"}
        ]
        
        params = ListRepoProjectsInput(
            owner="test-owner",
            repo="test-repo"
        )
        
        result = await github_list_repo_projects(params)
        
        mock_github_request.assert_called_once()
        # Should include preview header for Projects API
        call_args = mock_github_request.call_args
        headers = call_args[1].get("headers", {})
        assert "inertia-preview" in str(headers.get("Accept", ""))

    @pytest.mark.asyncio
    async def test_list_org_projects(self, mock_github_request, mock_auth_token):
        """Test listing organization projects."""
        mock_github_request.return_value = [
            {"id": 1, "name": "Roadmap", "state": "open"}
        ]
        
        params = ListOrgProjectsInput(org="test-org")
        
        result = await github_list_org_projects(params)
        
        mock_github_request.assert_called_once()
        assert "orgs/test-org/projects" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_project(self, mock_github_request, mock_auth_token):
        """Test getting a specific project."""
        mock_github_request.return_value = {
            "id": 123,
            "name": "Test Project",
            "state": "open"
        }
        
        params = GetProjectInput(project_id=123)
        
        result = await github_get_project(params)
        
        mock_github_request.assert_called_once()
        assert "projects/123" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_repo_project(self, mock_github_request, mock_auth_token):
        """Test creating a repository project."""
        mock_github_request.return_value = {
            "id": 123,
            "name": "New Project",
            "html_url": "https://github.com/..."
        }
        
        params = CreateRepoProjectInput(
            owner="test-owner",
            repo="test-repo",
            name="New Project",
            body="Project description"
        )
        
        result = await github_create_repo_project(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "POST"

    @pytest.mark.asyncio
    async def test_create_org_project(self, mock_github_request, mock_auth_token):
        """Test creating an organization project."""
        mock_github_request.return_value = {
            "id": 124,
            "name": "Org Project"
        }
        
        params = CreateOrgProjectInput(
            org="test-org",
            name="Org Project"
        )
        
        result = await github_create_org_project(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "POST"
        assert "orgs/test-org/projects" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_project(self, mock_github_request, mock_auth_token):
        """Test updating a project."""
        mock_github_request.return_value = {
            "id": 123,
            "name": "Updated Name",
            "state": "closed"
        }
        
        params = UpdateProjectInput(
            project_id=123,
            name="Updated Name",
            state="closed"
        )
        
        result = await github_update_project(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "PATCH"

    @pytest.mark.asyncio
    async def test_delete_project(self, mock_github_request, mock_auth_token):
        """Test deleting a project."""
        mock_github_request.return_value = {}
        
        params = DeleteProjectInput(project_id=123)
        
        result = await github_delete_project(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "DELETE"

    @pytest.mark.asyncio
    async def test_list_project_columns(self, mock_github_request, mock_auth_token):
        """Test listing project columns."""
        mock_github_request.return_value = [
            {"id": 1, "name": "To Do"},
            {"id": 2, "name": "In Progress"},
            {"id": 3, "name": "Done"}
        ]
        
        params = ListProjectColumnsInput(project_id=123)
        
        result = await github_list_project_columns(params)
        
        assert "projects/123/columns" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_project_column(self, mock_github_request, mock_auth_token):
        """Test creating a project column."""
        mock_github_request.return_value = {
            "id": 4,
            "name": "Review"
        }
        
        params = CreateProjectColumnInput(
            project_id=123,
            name="Review"
        )
        
        result = await github_create_project_column(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "POST"

