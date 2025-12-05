"""
Tests for GitHub Actions tools (Phase 2).
"""

import pytest
import json
from unittest.mock import AsyncMock, patch

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from github_mcp import (  # noqa: E402
    github_get_workflow,
    github_trigger_workflow,
    github_get_workflow_run,
    github_list_workflow_run_jobs,
    github_get_job,
    github_get_job_logs,
    github_rerun_workflow,
    github_rerun_failed_jobs,
    github_cancel_workflow_run,
    github_list_workflow_run_artifacts,
    github_get_artifact,
    github_delete_artifact,
    GetWorkflowInput,
    TriggerWorkflowInput,
    GetWorkflowRunInput,
    ListWorkflowRunJobsInput,
    GetJobInput,
    GetJobLogsInput,
    RerunWorkflowInput,
    RerunFailedJobsInput,
    CancelWorkflowRunInput,
    ListWorkflowRunArtifactsInput,
    GetArtifactInput,
    DeleteArtifactInput,
    ResponseFormat,
)


class TestActionsTools:
    """Test suite for GitHub Actions tools."""

    @pytest.fixture
    def mock_github_request(self):
        """Mock the GitHub API request function."""
        with patch('github_mcp._make_github_request') as mock:
            yield mock

    @pytest.fixture
    def mock_auth_token(self):
        """Mock authentication token resolution."""
        with patch('github_mcp._get_auth_token_fallback') as mock:
            mock.return_value = "test-token"
            yield mock

    # github_get_workflow tests
    @pytest.mark.asyncio
    async def test_get_workflow_by_id(self, mock_github_request, mock_auth_token):
        """Test getting a workflow by ID."""
        mock_github_request.return_value = {
            "id": 12345,
            "name": "CI",
            "path": ".github/workflows/ci.yml",
            "state": "active"
        }
        
        params = GetWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            workflow_id="12345"
        )
        
        result = await github_get_workflow(params)
        
        mock_github_request.assert_called_once()
        call_args = mock_github_request.call_args
        assert "/actions/workflows/12345" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_workflow_by_filename(self, mock_github_request, mock_auth_token):
        """Test getting a workflow by filename."""
        mock_github_request.return_value = {
            "id": 12345,
            "name": "CI",
            "path": ".github/workflows/ci.yml"
        }
        
        params = GetWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            workflow_id="ci.yml"
        )
        
        result = await github_get_workflow(params)
        
        mock_github_request.assert_called_once()
        assert "/actions/workflows/ci.yml" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_workflow_json_format(self, mock_github_request, mock_auth_token):
        """Test getting workflow with JSON format."""
        mock_github_request.return_value = {
            "id": 12345,
            "name": "CI",
            "state": "active"
        }
        
        params = GetWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            workflow_id="12345",
            response_format=ResponseFormat.JSON
        )
        
        result = await github_get_workflow(params)
        data = json.loads(result)
        assert data["id"] == 12345

    # github_trigger_workflow tests
    @pytest.mark.asyncio
    async def test_trigger_workflow(self, mock_github_request, mock_auth_token):
        """Test triggering a workflow dispatch."""
        mock_github_request.return_value = {}
        
        params = TriggerWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            workflow_id="ci.yml",
            ref="main"
        )
        
        result = await github_trigger_workflow(params)
        
        mock_github_request.assert_called_once()
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/dispatches" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_trigger_workflow_with_inputs(self, mock_github_request, mock_auth_token):
        """Test triggering a workflow with inputs."""
        mock_github_request.return_value = {}
        
        params = TriggerWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            workflow_id="ci.yml",
            ref="main",
            inputs={"environment": "production", "debug": "true"}
        )
        
        result = await github_trigger_workflow(params)
        
        call_args = mock_github_request.call_args
        body = call_args[1].get("json", {})
        assert body.get("inputs") == {"environment": "production", "debug": "true"}

    # github_get_workflow_run tests
    @pytest.mark.asyncio
    async def test_get_workflow_run(self, mock_github_request, mock_auth_token):
        """Test getting a specific workflow run."""
        mock_github_request.return_value = {
            "id": 98765,
            "status": "completed",
            "conclusion": "success"
        }
        
        params = GetWorkflowRunInput(
            owner="test-owner",
            repo="test-repo",
            run_id=98765
        )
        
        result = await github_get_workflow_run(params)
        
        mock_github_request.assert_called_once()
        assert "/actions/runs/98765" in mock_github_request.call_args[0][0]

    # github_list_workflow_run_jobs tests
    @pytest.mark.asyncio
    async def test_list_workflow_run_jobs(self, mock_github_request, mock_auth_token):
        """Test listing jobs for a workflow run."""
        mock_github_request.return_value = {
            "total_count": 2,
            "jobs": [
                {"id": 1, "name": "build", "status": "completed"},
                {"id": 2, "name": "test", "status": "completed"}
            ]
        }
        
        params = ListWorkflowRunJobsInput(
            owner="test-owner",
            repo="test-repo",
            run_id=98765
        )
        
        result = await github_list_workflow_run_jobs(params)
        
        mock_github_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_workflow_run_jobs_with_filter(self, mock_github_request, mock_auth_token):
        """Test listing jobs with filter."""
        mock_github_request.return_value = {
            "total_count": 1,
            "jobs": [{"id": 1, "name": "build"}]
        }
        
        params = ListWorkflowRunJobsInput(
            owner="test-owner",
            repo="test-repo",
            run_id=98765,
            filter="latest"
        )
        
        result = await github_list_workflow_run_jobs(params)
        
        call_args = mock_github_request.call_args
        params_dict = call_args[1].get("params", {})
        assert params_dict.get("filter") == "latest"

    # github_get_job tests
    @pytest.mark.asyncio
    async def test_get_job(self, mock_github_request, mock_auth_token):
        """Test getting a specific job."""
        mock_github_request.return_value = {
            "id": 123,
            "name": "build",
            "status": "completed",
            "conclusion": "success"
        }
        
        params = GetJobInput(
            owner="test-owner",
            repo="test-repo",
            job_id=123
        )
        
        result = await github_get_job(params)
        
        mock_github_request.assert_called_once()
        assert "/actions/jobs/123" in mock_github_request.call_args[0][0]

    # github_get_job_logs tests
    @pytest.mark.asyncio
    async def test_get_job_logs(self, mock_auth_token):
        """Test getting job logs - verifies function structure."""
        # This function uses GhClient directly which is complex to mock
        # We'll just verify it handles missing auth correctly
        mock_auth_token.return_value = None
        
        params = GetJobLogsInput(
            owner="test-owner",
            repo="test-repo",
            job_id=123
        )
        
        result = await github_get_job_logs(params)
        
        # Should return error JSON when no auth
        assert isinstance(result, str)
        if result.strip().startswith('{'):
            data = json.loads(result)
            assert data.get("error") == "Authentication required"
        else:
            # Might return markdown or other format
            assert "error" in result.lower() or "authentication" in result.lower()

    # github_cancel_workflow_run tests
    @pytest.mark.asyncio
    async def test_cancel_workflow_run(self, mock_github_request, mock_auth_token):
        """Test cancelling a workflow run."""
        mock_github_request.return_value = {}
        
        params = CancelWorkflowRunInput(
            owner="test-owner",
            repo="test-repo",
            run_id=98765
        )
        
        result = await github_cancel_workflow_run(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/cancel" in call_args[0][0]

    # github_rerun_workflow tests
    @pytest.mark.asyncio
    async def test_rerun_workflow(self, mock_github_request, mock_auth_token):
        """Test rerunning a workflow."""
        mock_github_request.return_value = {}
        
        params = RerunWorkflowInput(
            owner="test-owner",
            repo="test-repo",
            run_id=98765
        )
        
        result = await github_rerun_workflow(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/rerun" in call_args[0][0]

    # github_rerun_failed_jobs tests
    @pytest.mark.asyncio
    async def test_rerun_failed_jobs(self, mock_github_request, mock_auth_token):
        """Test rerunning only failed jobs."""
        mock_github_request.return_value = {}
        
        params = RerunFailedJobsInput(
            owner="test-owner",
            repo="test-repo",
            run_id=98765
        )
        
        result = await github_rerun_failed_jobs(params)
        
        call_args = mock_github_request.call_args
        assert "/rerun-failed-jobs" in call_args[0][0]

    # Artifact tests
    @pytest.mark.asyncio
    async def test_list_workflow_run_artifacts(self, mock_github_request, mock_auth_token):
        """Test listing artifacts for a workflow run."""
        mock_github_request.return_value = {
            "total_count": 1,
            "artifacts": [
                {"id": 123, "name": "build-output", "size_in_bytes": 1024}
            ]
        }
        
        params = ListWorkflowRunArtifactsInput(
            owner="test-owner",
            repo="test-repo",
            run_id=98765
        )
        
        result = await github_list_workflow_run_artifacts(params)
        
        mock_github_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_artifact(self, mock_github_request, mock_auth_token):
        """Test getting artifact details."""
        mock_github_request.return_value = {
            "id": 123,
            "name": "build-output",
            "size_in_bytes": 1024,
            "archive_download_url": "https://api.github.com/..."
        }
        
        params = GetArtifactInput(
            owner="test-owner",
            repo="test-repo",
            artifact_id=123
        )
        
        result = await github_get_artifact(params)
        
        mock_github_request.assert_called_once()
        assert "/actions/artifacts/123" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_artifact(self, mock_github_request, mock_auth_token):
        """Test deleting an artifact."""
        mock_github_request.return_value = {}
        
        params = DeleteArtifactInput(
            owner="test-owner",
            repo="test-repo",
            artifact_id=123
        )
        
        result = await github_delete_artifact(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "DELETE"

