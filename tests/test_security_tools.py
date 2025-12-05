"""
Tests for Security Suite tools (Phase 2).
"""

import pytest
import json
from unittest.mock import AsyncMock, patch

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from github_mcp import (  # noqa: E402
    # Dependabot
    github_list_dependabot_alerts,
    github_get_dependabot_alert,
    github_update_dependabot_alert,
    github_list_org_dependabot_alerts,
    # Code Scanning
    github_list_code_scanning_alerts,
    github_get_code_scanning_alert,
    github_update_code_scanning_alert,
    github_list_code_scanning_analyses,
    # Secret Scanning
    github_list_secret_scanning_alerts,
    github_get_secret_scanning_alert,
    github_update_secret_scanning_alert,
    # Security Advisories
    github_list_repo_security_advisories,
    github_get_security_advisory,
    # Input models
    ListDependabotAlertsInput,
    GetDependabotAlertInput,
    UpdateDependabotAlertInput,
    ListOrgDependabotAlertsInput,
    ListCodeScanningAlertsInput,
    GetCodeScanningAlertInput,
    UpdateCodeScanningAlertInput,
    ListCodeScanningAnalysesInput,
    ListSecretScanningAlertsInput,
    GetSecretScanningAlertInput,
    UpdateSecretScanningAlertInput,
    ListRepoSecurityAdvisoriesInput,
    GetSecurityAdvisoryInput,
    ResponseFormat,
)


class TestDependabotTools:
    """Test suite for Dependabot tools."""

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
    async def test_list_dependabot_alerts(self, mock_github_request, mock_auth_token):
        """Test listing Dependabot alerts."""
        mock_github_request.return_value = [
            {"number": 1, "state": "open", "severity": "high"},
            {"number": 2, "state": "open", "severity": "medium"}
        ]
        
        params = ListDependabotAlertsInput(
            owner="test-owner",
            repo="test-repo"
        )
        
        result = await github_list_dependabot_alerts(params)
        
        mock_github_request.assert_called_once()
        assert "/dependabot/alerts" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_dependabot_alerts_with_filters(self, mock_github_request, mock_auth_token):
        """Test listing Dependabot alerts with state filter."""
        mock_github_request.return_value = []
        
        params = ListDependabotAlertsInput(
            owner="test-owner",
            repo="test-repo",
            state="dismissed",
            severity="critical"
        )
        
        result = await github_list_dependabot_alerts(params)
        
        call_args = mock_github_request.call_args
        params_dict = call_args[1].get("params", {})
        assert params_dict.get("state") == "dismissed" or params_dict.get("severity") == "critical"

    @pytest.mark.asyncio
    async def test_get_dependabot_alert(self, mock_github_request, mock_auth_token):
        """Test getting a specific Dependabot alert."""
        mock_github_request.return_value = {
            "number": 1,
            "state": "open",
            "dependency": {"package": {"name": "lodash"}}
        }
        
        params = GetDependabotAlertInput(
            owner="test-owner",
            repo="test-repo",
            alert_number=1
        )
        
        result = await github_get_dependabot_alert(params)
        
        assert "/dependabot/alerts/1" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_dependabot_alert(self, mock_github_request, mock_auth_token):
        """Test dismissing a Dependabot alert."""
        mock_github_request.return_value = {"number": 1, "state": "dismissed"}
        
        params = UpdateDependabotAlertInput(
            owner="test-owner",
            repo="test-repo",
            alert_number=1,
            state="dismissed",
            dismissed_reason="tolerable_risk"
        )
        
        result = await github_update_dependabot_alert(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "PATCH"

    @pytest.mark.asyncio
    async def test_list_org_dependabot_alerts(self, mock_github_request, mock_auth_token):
        """Test listing organization Dependabot alerts."""
        mock_github_request.return_value = []
        
        params = ListOrgDependabotAlertsInput(
            org="test-org"
        )
        
        result = await github_list_org_dependabot_alerts(params)
        
        assert "orgs/test-org/dependabot/alerts" in mock_github_request.call_args[0][0]


class TestCodeScanningTools:
    """Test suite for Code Scanning tools."""

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
    async def test_list_code_scanning_alerts(self, mock_github_request, mock_auth_token):
        """Test listing code scanning alerts."""
        mock_github_request.return_value = [
            {"number": 1, "rule": {"id": "js/xss"}, "state": "open"}
        ]
        
        params = ListCodeScanningAlertsInput(
            owner="test-owner",
            repo="test-repo"
        )
        
        result = await github_list_code_scanning_alerts(params)
        
        assert "/code-scanning/alerts" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_code_scanning_alert(self, mock_github_request, mock_auth_token):
        """Test getting a specific code scanning alert."""
        mock_github_request.return_value = {
            "number": 1,
            "rule": {"id": "js/xss", "severity": "error"},
            "most_recent_instance": {"location": {"path": "src/index.js"}}
        }
        
        params = GetCodeScanningAlertInput(
            owner="test-owner",
            repo="test-repo",
            alert_number=1
        )
        
        result = await github_get_code_scanning_alert(params)
        
        mock_github_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_code_scanning_alert(self, mock_github_request, mock_auth_token):
        """Test updating a code scanning alert."""
        mock_github_request.return_value = {"number": 1, "state": "dismissed"}
        
        params = UpdateCodeScanningAlertInput(
            owner="test-owner",
            repo="test-repo",
            alert_number=1,
            state="dismissed",
            dismissed_reason="false_positive"
        )
        
        result = await github_update_code_scanning_alert(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "PATCH"

    @pytest.mark.asyncio
    async def test_list_code_scanning_analyses(self, mock_github_request, mock_auth_token):
        """Test listing code scanning analyses."""
        mock_github_request.return_value = [
            {"ref": "refs/heads/main", "analysis_key": "test"}
        ]
        
        params = ListCodeScanningAnalysesInput(
            owner="test-owner",
            repo="test-repo"
        )
        
        result = await github_list_code_scanning_analyses(params)
        
        assert "/code-scanning/analyses" in mock_github_request.call_args[0][0]


class TestSecretScanningTools:
    """Test suite for Secret Scanning tools."""

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
    async def test_list_secret_scanning_alerts(self, mock_github_request, mock_auth_token):
        """Test listing secret scanning alerts."""
        mock_github_request.return_value = [
            {"number": 1, "secret_type": "github_token", "state": "open"}
        ]
        
        params = ListSecretScanningAlertsInput(
            owner="test-owner",
            repo="test-repo"
        )
        
        result = await github_list_secret_scanning_alerts(params)
        
        assert "/secret-scanning/alerts" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_secret_scanning_alert(self, mock_github_request, mock_auth_token):
        """Test getting a specific secret scanning alert."""
        mock_github_request.return_value = {
            "number": 1,
            "secret_type": "github_token",
            "state": "open"
        }
        
        params = GetSecretScanningAlertInput(
            owner="test-owner",
            repo="test-repo",
            alert_number=1
        )
        
        result = await github_get_secret_scanning_alert(params)
        
        mock_github_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_secret_scanning_alert(self, mock_github_request, mock_auth_token):
        """Test updating a secret scanning alert."""
        mock_github_request.return_value = {"number": 1, "state": "resolved"}
        
        params = UpdateSecretScanningAlertInput(
            owner="test-owner",
            repo="test-repo",
            alert_number=1,
            state="resolved"
        )
        
        result = await github_update_secret_scanning_alert(params)
        
        call_args = mock_github_request.call_args
        assert call_args[1]["method"] == "PATCH"


class TestSecurityAdvisoryTools:
    """Test suite for Security Advisory tools."""

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
    async def test_list_security_advisories(self, mock_github_request, mock_auth_token):
        """Test listing security advisories."""
        mock_github_request.return_value = [
            {"ghsa_id": "GHSA-xxxx-xxxx-xxxx", "severity": "high"}
        ]
        
        params = ListRepoSecurityAdvisoriesInput(
            owner="test-owner",
            repo="test-repo"
        )
        
        result = await github_list_repo_security_advisories(params)
        
        assert "/security-advisories" in mock_github_request.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_security_advisory(self, mock_github_request, mock_auth_token):
        """Test getting a specific security advisory."""
        mock_github_request.return_value = {
            "ghsa_id": "GHSA-xxxx-xxxx-xxxx",
            "severity": "high",
            "summary": "Security vulnerability"
        }
        
        params = GetSecurityAdvisoryInput(
            owner="test-owner",
            repo="test-repo",
            ghsa_id="GHSA-xxxx-xxxx-xxxx"
        )
        
        result = await github_get_security_advisory(params)
        
        assert "/security-advisories/GHSA-xxxx-xxxx-xxxx" in mock_github_request.call_args[0][0]

