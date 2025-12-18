"""Security tools for GitHub MCP Server."""

import json
from typing import Any, Dict, List, cast

from ..models.inputs import (
    GetCodeScanningAlertInput,
    GetDependabotAlertInput,
    GetSecretScanningAlertInput,
    GetSecurityAdvisoryInput,
    ListCodeScanningAlertsInput,
    ListCodeScanningAnalysesInput,
    ListDependabotAlertsInput,
    ListOrgDependabotAlertsInput,
    ListRepoSecurityAdvisoriesInput,
    ListSecretScanningAlertsInput,
    UpdateCodeScanningAlertInput,
    UpdateDependabotAlertInput,
    UpdateSecretScanningAlertInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response
from ..utils.compact_format import format_response


async def github_list_dependabot_alerts(params: ListDependabotAlertsInput) -> str:
    """
    List Dependabot security alerts for a repository.

    Retrieves alerts about vulnerable dependencies detected by Dependabot.
    Supports filtering by state, severity, and ecosystem.

    Args:
        params (ListDependabotAlertsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - state (Optional[str]): Filter by state
            - severity (Optional[str]): Filter by severity
            - ecosystem (Optional[str]): Filter by ecosystem
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of Dependabot alerts with details

    Examples:
        - Use when: "Show me all Dependabot alerts"
        - Use when: "List critical security vulnerabilities"
    """
    try:
        params_dict: Dict[str, Any] = {"per_page": params.limit, "page": params.page}
        if params.state:
            params_dict["state"] = params.state
        if params.severity:
            params_dict["severity"] = params.severity
        if params.ecosystem:
            params_dict["ecosystem"] = params.ecosystem

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/dependabot/alerts",
            token=params.token,
            params=params_dict,
        )
        alerts: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(alerts, indent=2)
            return _truncate_response(result, len(alerts))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                alerts, ResponseFormat.COMPACT.value, "alert"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(alerts))

        markdown = f"# Dependabot Alerts for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Alerts:** {len(alerts)}\n\n"

        if not alerts:
            markdown += "No Dependabot alerts found.\n"
        else:
            for alert in alerts:
                severity_emoji = (
                    "🔴"
                    if alert["security_vulnerability"]["severity"] == "critical"
                    else "🟠"
                    if alert["security_vulnerability"]["severity"] == "high"
                    else "🟡"
                    if alert["security_vulnerability"]["severity"] == "medium"
                    else "🟢"
                )

                markdown += f"## {severity_emoji} Alert #{alert['number']}: {alert['dependency']['package']['name']}\n"
                markdown += f"- **State:** {alert['state']}\n"
                markdown += (
                    f"- **Severity:** {alert['security_vulnerability']['severity']}\n"
                )
                markdown += (
                    f"- **Ecosystem:** {alert['dependency']['package']['ecosystem']}\n"
                )
                markdown += f"- **Vulnerable Version:** {alert['security_vulnerability']['vulnerable_version_range']}\n"
                markdown += f"- **Patched Version:** {alert['security_vulnerability']['first_patched_version'].get('identifier', 'N/A')}\n"
                markdown += f"- **Created:** {_format_timestamp(alert['created_at'])}\n"
                markdown += f"- **URL:** {alert['html_url']}\n\n"

        return _truncate_response(markdown, len(data))

    except Exception as e:
        return _handle_api_error(e)


async def github_get_dependabot_alert(params: GetDependabotAlertInput) -> str:
    """
    Get details about a specific Dependabot alert.

    Retrieves complete alert information including vulnerability details,
    affected versions, and remediation guidance.

    Args:
        params (GetDependabotAlertInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - alert_number (int): Alert number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed alert information

    Examples:
        - Use when: "Show me details about Dependabot alert 123"
        - Use when: "Get information about security alert 456"
    """
    try:
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/dependabot/alerts/{params.alert_number}",
            token=params.token,
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(data, ResponseFormat.COMPACT.value, "alert")
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        severity_emoji = (
            "🔴"
            if data["security_vulnerability"]["severity"] == "critical"
            else "🟠"
            if data["security_vulnerability"]["severity"] == "high"
            else "🟡"
            if data["security_vulnerability"]["severity"] == "medium"
            else "🟢"
        )

        markdown = f"# {severity_emoji} Dependabot Alert #{data['number']}\n\n"
        markdown += f"- **State:** {data['state']}\n"
        markdown += f"- **Severity:** {data['security_vulnerability']['severity']}\n"
        markdown += f"- **Package:** {data['dependency']['package']['name']}\n"
        markdown += f"- **Ecosystem:** {data['dependency']['package']['ecosystem']}\n"
        markdown += f"- **Vulnerable Version:** {data['security_vulnerability']['vulnerable_version_range']}\n"
        markdown += f"- **Patched Version:** {data['security_vulnerability']['first_patched_version'].get('identifier', 'N/A')}\n"

        if data.get("dismissed_at"):
            markdown += f"- **Dismissed:** {_format_timestamp(data['dismissed_at'])}\n"
            if data.get("dismissed_reason"):
                markdown += f"- **Dismissal Reason:** {data['dismissed_reason']}\n"

        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **URL:** {data['html_url']}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_update_dependabot_alert(params: UpdateDependabotAlertInput) -> str:
    """
    Update a Dependabot alert (dismiss or reopen).

    Allows dismissing alerts with a reason and optional comment, or
    reopening dismissed alerts.

    Args:
        params (UpdateDependabotAlertInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - alert_number (int): Alert number
            - state (str): 'dismissed' or 'open'
            - dismissed_reason (Optional[str]): Reason for dismissal
            - dismissed_comment (Optional[str]): Optional comment
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Updated alert details

    Examples:
        - Use when: "Dismiss Dependabot alert 123 as false positive"
        - Use when: "Reopen dismissed alert 456"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for updating Dependabot alerts.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload = {"state": params.state}
        if params.state == "dismissed":
            if params.dismissed_reason:
                payload["dismissed_reason"] = params.dismissed_reason
            if params.dismissed_comment:
                payload["dismissed_comment"] = params.dismissed_comment

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/dependabot/alerts/{params.alert_number}",
            method="PATCH",
            token=auth_token,
            json=payload,
        )

        return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


async def github_list_org_dependabot_alerts(
    params: ListOrgDependabotAlertsInput,
) -> str:
    """
    List Dependabot alerts across an organization.

    Retrieves alerts from all repositories in an organization. Requires
    organization admin permissions.

    Args:
        params (ListOrgDependabotAlertsInput): Validated input parameters containing:
            - org (str): Organization name
            - state (Optional[str]): Filter by state
            - severity (Optional[str]): Filter by severity
            - ecosystem (Optional[str]): Filter by ecosystem
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of organization-wide Dependabot alerts

    Examples:
        - Use when: "Show me all critical alerts in the organization"
        - Use when: "List all open Dependabot alerts across our repos"
    """
    try:
        params_dict: Dict[str, Any] = {"per_page": params.limit, "page": params.page}
        if params.state:
            params_dict["state"] = params.state
        if params.severity:
            params_dict["severity"] = params.severity
        if params.ecosystem:
            params_dict["ecosystem"] = params.ecosystem

        data = await _make_github_request(
            f"orgs/{params.org}/dependabot/alerts",
            token=params.token,
            params=params_dict,
        )
        alerts: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(alerts, indent=2)
            return _truncate_response(result, len(alerts))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                alerts, ResponseFormat.COMPACT.value, "alert"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(alerts))

        markdown = f"# Dependabot Alerts for Organization: {params.org}\n\n"
        markdown += f"**Total Alerts:** {len(alerts)}\n\n"

        if not alerts:
            markdown += "No Dependabot alerts found.\n"
        else:
            for alert in alerts:
                severity_emoji = (
                    "🔴"
                    if alert["security_vulnerability"]["severity"] == "critical"
                    else "🟠"
                    if alert["security_vulnerability"]["severity"] == "high"
                    else "🟡"
                    if alert["security_vulnerability"]["severity"] == "medium"
                    else "🟢"
                )

                markdown += f"## {severity_emoji} {alert['repository']['full_name']} - Alert #{alert['number']}\n"
                markdown += f"- **Package:** {alert['dependency']['package']['name']}\n"
                markdown += (
                    f"- **Severity:** {alert['security_vulnerability']['severity']}\n"
                )
                markdown += f"- **State:** {alert['state']}\n"
                markdown += f"- **URL:** {alert['html_url']}\n\n"

        return _truncate_response(markdown, len(data))

    except Exception as e:
        return _handle_api_error(e)


# Code Scanning Tools


async def github_list_code_scanning_alerts(params: ListCodeScanningAlertsInput) -> str:
    """
    List code scanning alerts for a repository.

    Retrieves alerts from CodeQL and other code scanning tools. Supports
    filtering by state, severity, and tool name.

    Args:
        params (ListCodeScanningAlertsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - state (Optional[str]): Filter by state
            - severity (Optional[str]): Filter by severity
            - tool_name (Optional[str]): Filter by tool name
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of code scanning alerts with details

    Examples:
        - Use when: "Show me all CodeQL alerts"
        - Use when: "List critical code scanning issues"
    """
    try:
        params_dict: Dict[str, Any] = {"per_page": params.limit, "page": params.page}
        if params.state:
            params_dict["state"] = params.state
        if params.severity:
            params_dict["severity"] = params.severity
        if params.tool_name:
            params_dict["tool_name"] = params.tool_name

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/code-scanning/alerts",
            token=params.token,
            params=params_dict,
        )
        alerts: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(alerts, indent=2)
            return _truncate_response(result, len(alerts))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                alerts, ResponseFormat.COMPACT.value, "alert"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(alerts))

        markdown = f"# Code Scanning Alerts for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Alerts:** {len(alerts)}\n\n"

        if not alerts:
            markdown += "No code scanning alerts found.\n"
        else:
            for alert in alerts:
                severity_emoji = (
                    "🔴"
                    if alert.get("rule", {}).get("severity") == "error"
                    else "🟠"
                    if alert.get("rule", {}).get("severity") == "warning"
                    else "🟡"
                )

                markdown += f"## {severity_emoji} Alert #{alert['number']}: {alert['rule']['name']}\n"
                markdown += f"- **State:** {alert['state']}\n"
                markdown += f"- **Severity:** {alert['rule'].get('severity', 'N/A')}\n"
                markdown += f"- **Tool:** {alert['tool']['name']}\n"
                markdown += f"- **Created:** {_format_timestamp(alert['created_at'])}\n"
                markdown += f"- **URL:** {alert['html_url']}\n\n"

        return _truncate_response(markdown, len(data))

    except Exception as e:
        return _handle_api_error(e)


async def github_get_code_scanning_alert(params: GetCodeScanningAlertInput) -> str:
    """
    Get details about a specific code scanning alert.

    Retrieves complete alert information including rule details, location,
    and remediation guidance.

    Args:
        params (GetCodeScanningAlertInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - alert_number (int): Alert number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed alert information

    Examples:
        - Use when: "Show me details about code scanning alert 123"
        - Use when: "Get information about CodeQL alert 456"
    """
    try:
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/code-scanning/alerts/{params.alert_number}",
            token=params.token,
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(data, ResponseFormat.COMPACT.value, "alert")
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        severity_emoji = (
            "🔴"
            if data.get("rule", {}).get("severity") == "error"
            else "🟠"
            if data.get("rule", {}).get("severity") == "warning"
            else "🟡"
        )

        markdown = f"# {severity_emoji} Code Scanning Alert #{data['number']}\n\n"
        markdown += f"- **State:** {data['state']}\n"
        markdown += f"- **Rule:** {data['rule']['name']}\n"
        markdown += f"- **Severity:** {data['rule'].get('severity', 'N/A')}\n"
        markdown += f"- **Tool:** {data['tool']['name']}\n"

        if data.get("most_recent_instance"):
            instance = data["most_recent_instance"]
            markdown += f"- **Location:** {instance.get('location', {}).get('path', 'N/A')}:{instance.get('location', {}).get('start_line', 'N/A')}\n"

        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **URL:** {data['html_url']}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_update_code_scanning_alert(
    params: UpdateCodeScanningAlertInput,
) -> str:
    """
    Update a code scanning alert (dismiss or reopen).

    Allows dismissing alerts with a reason and optional comment, or
    reopening dismissed alerts.

    Args:
        params (UpdateCodeScanningAlertInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - alert_number (int): Alert number
            - state (str): 'dismissed' or 'open'
            - dismissed_reason (Optional[str]): Reason for dismissal
            - dismissed_comment (Optional[str]): Optional comment
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Updated alert details

    Examples:
        - Use when: "Dismiss code scanning alert 123 as false positive"
        - Use when: "Reopen dismissed CodeQL alert 456"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for updating code scanning alerts.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload = {"state": params.state}
        if params.state == "dismissed":
            if params.dismissed_reason:
                payload["dismissed_reason"] = params.dismissed_reason
            if params.dismissed_comment:
                payload["dismissed_comment"] = params.dismissed_comment

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/code-scanning/alerts/{params.alert_number}",
            method="PATCH",
            token=auth_token,
            json=payload,
        )

        return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


async def github_list_code_scanning_analyses(
    params: ListCodeScanningAnalysesInput,
) -> str:
    """
    List code scanning analyses for a repository.

    Retrieves analysis runs from code scanning tools, including their
    status, tool, and commit information.

    Args:
        params (ListCodeScanningAnalysesInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - tool_name (Optional[str]): Filter by tool name
            - ref (Optional[str]): Filter by branch/tag/commit
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of code scanning analyses

    Examples:
        - Use when: "Show me all CodeQL analyses"
        - Use when: "List recent code scanning runs"
    """
    try:
        params_dict: Dict[str, Any] = {"per_page": params.limit, "page": params.page}
        if params.tool_name:
            params_dict["tool_name"] = params.tool_name
        if params.ref:
            params_dict["ref"] = params.ref

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/code-scanning/analyses",
            token=params.token,
            params=params_dict,
        )
        analyses: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(analyses, indent=2)
            return _truncate_response(result, len(analyses))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                analyses, ResponseFormat.COMPACT.value, "alert"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(analyses))

        markdown = f"# Code Scanning Analyses for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Analyses:** {len(analyses)}\n\n"

        if not analyses:
            markdown += "No code scanning analyses found.\n"
        else:
            for analysis in analyses:
                markdown += (
                    f"## Analysis: {analysis.get('tool', {}).get('name', 'N/A')}\n"
                )
                markdown += f"- **Ref:** {analysis.get('ref', 'N/A')}\n"
                markdown += (
                    f"- **Commit SHA:** {analysis.get('commit_sha', 'N/A')[:8]}\n"
                )
                markdown += (
                    f"- **Created:** {_format_timestamp(analysis['created_at'])}\n"
                )
                markdown += f"- **URL:** {analysis.get('url', 'N/A')}\n\n"

        return _truncate_response(markdown, len(analyses))

    except Exception as e:
        return _handle_api_error(e)


# Secret Scanning Tools


async def github_list_secret_scanning_alerts(
    params: ListSecretScanningAlertsInput,
) -> str:
    """
    List secret scanning alerts for a repository.

    Retrieves alerts about exposed secrets (API keys, tokens, etc.)
    detected by GitHub's secret scanning.

    Args:
        params (ListSecretScanningAlertsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - state (Optional[str]): Filter by state
            - secret_type (Optional[str]): Filter by secret type
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of secret scanning alerts with details

    Examples:
        - Use when: "Show me all secret scanning alerts"
        - Use when: "List exposed API keys"
    """
    try:
        params_dict: Dict[str, Any] = {"per_page": params.limit, "page": params.page}
        if params.state:
            params_dict["state"] = params.state
        if params.secret_type:
            params_dict["secret_type"] = params.secret_type

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/secret-scanning/alerts",
            token=params.token,
            params=params_dict,
        )
        alerts: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(alerts, indent=2)
            return _truncate_response(result, len(alerts))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                alerts, ResponseFormat.COMPACT.value, "alert"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(alerts))

        markdown = f"# Secret Scanning Alerts for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Alerts:** {len(alerts)}\n\n"

        if not alerts:
            markdown += "No secret scanning alerts found.\n"
        else:
            for alert in alerts:
                markdown += f"## 🔐 Alert #{alert['number']}\n"
                markdown += f"- **State:** {alert['state']}\n"
                markdown += f"- **Secret Type:** {alert.get('secret_type', 'N/A')}\n"
                markdown += f"- **Created:** {_format_timestamp(alert['created_at'])}\n"
                markdown += f"- **URL:** {alert['html_url']}\n\n"

        return _truncate_response(markdown, len(alerts))

    except Exception as e:
        return _handle_api_error(e)


async def github_get_secret_scanning_alert(params: GetSecretScanningAlertInput) -> str:
    """
    Get details about a specific secret scanning alert.

    Retrieves complete alert information including secret type, location,
    and resolution status.

    Args:
        params (GetSecretScanningAlertInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - alert_number (int): Alert number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed alert information

    Examples:
        - Use when: "Show me details about secret scanning alert 123"
        - Use when: "Get information about exposed token alert 456"
    """
    try:
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/secret-scanning/alerts/{params.alert_number}",
            token=params.token,
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(data, ResponseFormat.COMPACT.value, "alert")
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        markdown = f"# 🔐 Secret Scanning Alert #{data['number']}\n\n"
        markdown += f"- **State:** {data['state']}\n"
        markdown += f"- **Secret Type:** {data.get('secret_type', 'N/A')}\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"

        if data.get("resolution"):
            markdown += f"- **Resolution:** {data['resolution']}\n"

        markdown += f"- **URL:** {data['html_url']}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_update_secret_scanning_alert(
    params: UpdateSecretScanningAlertInput,
) -> str:
    """
    Update a secret scanning alert (resolve or reopen).

    Allows resolving alerts with a resolution reason, or reopening
    resolved alerts.

    Args:
        params (UpdateSecretScanningAlertInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - alert_number (int): Alert number
            - state (str): 'resolved' or 'open'
            - resolution (Optional[str]): Resolution reason
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Updated alert details

    Examples:
        - Use when: "Resolve secret scanning alert 123 as revoked"
        - Use when: "Reopen resolved alert 456"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for updating secret scanning alerts.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload = {"state": params.state}
        if params.state == "resolved" and params.resolution:
            payload["resolution"] = params.resolution

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/secret-scanning/alerts/{params.alert_number}",
            method="PATCH",
            token=auth_token,
            json=payload,
        )

        return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


# Security Advisories Tools


async def github_list_repo_security_advisories(
    params: ListRepoSecurityAdvisoriesInput,
) -> str:
    """
    List security advisories for a repository.

    Retrieves published security advisories (GHSA) for vulnerabilities
    in the repository.

    Args:
        params (ListRepoSecurityAdvisoriesInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - state (Optional[str]): Filter by state
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of security advisories

    Examples:
        - Use when: "Show me all security advisories"
        - Use when: "List published GHSA advisories"
    """
    try:
        params_dict: Dict[str, Any] = {"per_page": params.limit, "page": params.page}
        if params.state:
            params_dict["state"] = params.state

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/security-advisories",
            token=params.token,
            params=params_dict,
        )
        advisories: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(advisories, indent=2)
            return _truncate_response(result, len(advisories))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                advisories, ResponseFormat.COMPACT.value, "alert"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(advisories))

        markdown = f"# Security Advisories for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Advisories:** {len(advisories)}\n\n"

        if not advisories:
            markdown += "No security advisories found.\n"
        else:
            for advisory in advisories:
                markdown += f"## {advisory.get('ghsa_id', 'N/A')}: {advisory.get('summary', 'N/A')}\n"
                markdown += f"- **State:** {advisory.get('state', 'N/A')}\n"
                markdown += f"- **Severity:** {advisory.get('severity', 'N/A')}\n"
                markdown += f"- **Published:** {_format_timestamp(advisory['published_at']) if advisory.get('published_at') else 'Not published'}\n"
                markdown += f"- **URL:** {advisory.get('html_url', 'N/A')}\n\n"

        return _truncate_response(markdown, len(advisories))

    except Exception as e:
        return _handle_api_error(e)


async def github_get_security_advisory(params: GetSecurityAdvisoryInput) -> str:
    """
    Get details about a specific security advisory.

    Retrieves complete advisory information including description,
    severity, affected versions, and remediation guidance.

    Args:
        params (GetSecurityAdvisoryInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - ghsa_id (str): GitHub Security Advisory ID (e.g., 'GHSA-xxxx-xxxx-xxxx')
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed advisory information

    Examples:
        - Use when: "Show me details about GHSA-xxxx-xxxx-xxxx"
        - Use when: "Get information about security advisory GHSA-1234-5678-9012"
    """
    try:
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/security-advisories/{params.ghsa_id}",
            token=params.token,
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "advisory"
            )
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        markdown = f"# Security Advisory: {data.get('ghsa_id', 'N/A')}\n\n"
        markdown += f"- **Summary:** {data.get('summary', 'N/A')}\n"
        markdown += f"- **State:** {data.get('state', 'N/A')}\n"
        markdown += f"- **Severity:** {data.get('severity', 'N/A')}\n"
        markdown += f"- **Published:** {_format_timestamp(data['published_at']) if data.get('published_at') else 'Not published'}\n"

        if data.get("description"):
            markdown += f"\n### Description\n{data['description'][:500]}{'...' if len(data.get('description', '')) > 500 else ''}\n"

        markdown += f"\n- **URL:** {data.get('html_url', 'N/A')}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# GitHub Projects Tools (Phase 2 - Batch 3)
# ============================================================================
