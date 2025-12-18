"""Actions tools for GitHub MCP Server."""

import json
from typing import Dict, Any, List, cast

from ..models.inputs import (
    CancelWorkflowRunInput,
    DeleteArtifactInput,
    GetArtifactInput,
    GetJobInput,
    GetJobLogsInput,
    GetWorkflowInput,
    GetWorkflowRunInput,
    GetWorkflowRunsInput,
    ListWorkflowRunArtifactsInput,
    ListWorkflowRunJobsInput,
    ListWorkflowsInput,
    RerunFailedJobsInput,
    RerunWorkflowInput,
    TriggerWorkflowInput,
    WorkflowSuggestionInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response
from ..utils.compact_format import format_response


async def github_list_workflows(params: ListWorkflowsInput) -> str:
    """
    List GitHub Actions workflows for a repository.

    Retrieves all workflows configured in a repository, including their status,
    trigger events, and basic metadata. Essential for CI/CD monitoring.

    Args:
        params (ListWorkflowsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of workflows with their configuration and status

    Examples:
        - Use when: "Show me all GitHub Actions workflows"
        - Use when: "What CI/CD workflows are configured?"
        - Use when: "List the workflows in microsoft/vscode"

    Error Handling:
        - Returns error if repository not found
        - Handles private repository access requirements
        - Provides clear status for each workflow
    """
    try:
        query: Dict[str, Any] = {
            "per_page": params.limit,
            "page": params.page,
        }
        data: Dict[str, Any] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/workflows",
            token=params.token,
            params=query,
        )

        # Ensure data is a dict with expected structure
        total_count: int = data.get("total_count", 0) if isinstance(data, dict) else 0
        workflows: List[Dict[str, Any]] = (
            data.get("workflows", []) if isinstance(data, dict) else []
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                workflows, ResponseFormat.COMPACT.value, "workflow"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, total_count)

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, total_count)

        # Markdown format
        markdown = f"# GitHub Actions Workflows for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Workflows:** {total_count}\n\n"

        if not workflows:
            markdown += "No workflows found in this repository.\n"
        else:
            for workflow in workflows:
                markdown += f"## {workflow['name']}\n"
                markdown += f"- **ID:** {workflow['id']}\n"
                markdown += f"- **State:** {workflow['state']}\n"
                markdown += (
                    f"- **Created:** {_format_timestamp(workflow['created_at'])}\n"
                )
                markdown += (
                    f"- **Updated:** {_format_timestamp(workflow['updated_at'])}\n"
                )
                markdown += f"- **Path:** `{workflow['path']}`\n"
                markdown += f"- **URL:** {workflow['html_url']}\n\n"

                if workflow.get("badge_url"):
                    markdown += (
                        f"- **Badge:** ![Workflow Status]({workflow['badge_url']})\n\n"
                    )

                markdown += "---\n\n"

        return _truncate_response(markdown, total_count)

    except Exception as e:
        return _handle_api_error(e)


async def github_get_workflow(params: GetWorkflowInput) -> str:
    """
    Get details about a specific GitHub Actions workflow.

    Retrieves workflow configuration, state, and metadata including path,
    created/updated timestamps, and current status.

    Args:
        params (GetWorkflowInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - workflow_id (str): Workflow ID (numeric) or workflow file name
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Workflow details including configuration and status

    Examples:
        - Use when: "Show me the CI workflow details"
        - Use when: "Get information about workflow 12345"
    """
    try:
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/workflows/{params.workflow_id}",
            token=params.token,
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "workflow"
            )
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        markdown = f"# Workflow: {data['name']}\n\n"
        markdown += f"- **ID:** {data['id']}\n"
        markdown += f"- **State:** {data['state']}\n"
        markdown += f"- **Path:** `{data['path']}`\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **Updated:** {_format_timestamp(data['updated_at'])}\n"
        markdown += f"- **URL:** {data['html_url']}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_get_workflow_runs(params: GetWorkflowRunsInput) -> str:
    """
    Get GitHub Actions workflow run history and status.

    Retrieves recent workflow runs with detailed status, conclusions, and timing.
    Supports filtering by workflow, status, and conclusion. Critical for CI/CD monitoring.

    Args:
        params (GetWorkflowRunsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - workflow_id (Optional[str]): Specific workflow ID or name
            - status (Optional[WorkflowRunStatus]): Filter by run status
            - conclusion (Optional[WorkflowRunConclusion]): Filter by conclusion
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of workflow runs with status, timing, and results

    Examples:
        - Use when: "Show me recent workflow runs"
        - Use when: "Check if my deployment workflow passed"
        - Use when: "Show me failed test runs from last week"
        - Use when: "Get runs for the 'CI' workflow"

    Error Handling:
        - Returns error if repository not accessible
        - Handles workflow not found scenarios
        - Provides clear status indicators for each run
    """
    try:
        params_dict: Dict[str, Any] = {"per_page": params.limit, "page": params.page}

        if params.status:
            params_dict["status"] = params.status.value
        if params.conclusion:
            params_dict["conclusion"] = params.conclusion.value

        # Build endpoint
        if params.workflow_id:
            endpoint = f"repos/{params.owner}/{params.repo}/actions/workflows/{params.workflow_id}/runs"
        else:
            endpoint = f"repos/{params.owner}/{params.repo}/actions/runs"

        data = await _make_github_request(
            endpoint, token=params.token, params=params_dict
        )

        runs: List[Dict[str, Any]] = data.get("workflow_runs", [])
        total_count = data.get("total_count", len(runs))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                runs, ResponseFormat.COMPACT.value, "workflow_run"
            )
            result = json.dumps(
                {"total_count": total_count, "workflow_runs": compact_data},
                indent=2,
            )
            return _truncate_response(result, total_count)

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, total_count)

        # Markdown format
        workflow_name = params.workflow_id or "All Workflows"
        markdown = f"# Workflow Runs for {params.owner}/{params.repo}\n\n"
        markdown += f"**Workflow:** {workflow_name}\n"
        markdown += f"**Total Runs:** {total_count:,}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(runs)} runs\n\n"

        if not runs:
            markdown += "No workflow runs found matching your criteria.\n"
        else:
            for run in runs:
                # Status emoji
                status_emoji = (
                    "🔄"
                    if run["status"] == "in_progress"
                    else "✅"
                    if run["conclusion"] == "success"
                    else "❌"
                    if run["conclusion"] == "failure"
                    else "⏸️"
                    if run["status"] == "queued"
                    else "⚠️"
                )

                markdown += (
                    f"## {status_emoji} Run #{run['run_number']}: {run['name']}\n"
                )
                markdown += f"- **Status:** {run['status']}\n"
                markdown += f"- **Conclusion:** {run['conclusion'] or 'N/A'}\n"
                markdown += f"- **Triggered By:** {run['triggering_actor']['login']}\n"
                markdown += f"- **Branch:** `{run['head_branch']}`\n"
                markdown += f"- **Commit:** {run['head_sha'][:8]}\n"
                markdown += f"- **Created:** {_format_timestamp(run['created_at'])}\n"
                markdown += f"- **Updated:** {_format_timestamp(run['updated_at'])}\n"

                if run.get("run_started_at"):
                    markdown += (
                        f"- **Started:** {_format_timestamp(run['run_started_at'])}\n"
                    )

                if run.get("jobs_url"):
                    markdown += f"- **Jobs:** {run['jobs_url']}\n"

                markdown += f"- **URL:** {run['html_url']}\n\n"

                # Show workflow info
                if run.get("workflow_id"):
                    markdown += f"- **Workflow ID:** {run['workflow_id']}\n"

                markdown += "---\n\n"

        return _truncate_response(markdown, total_count)

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# GitHub Actions Expansion Tools (Phase 2 - Batch 1)
# ============================================================================


async def github_trigger_workflow(params: TriggerWorkflowInput) -> str:
    """
    Trigger a workflow dispatch event (manually run a workflow).

    Triggers a workflow that has workflow_dispatch enabled. Can pass
    input parameters to the workflow.

    Args:
        params (TriggerWorkflowInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - workflow_id (str): Workflow ID or file name
            - ref (str): Branch, tag, or commit SHA
            - inputs (Optional[Dict[str, str]]): Input parameters
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Success confirmation (202 Accepted)

    Examples:
        - Use when: "Trigger the deployment workflow on main branch"
        - Use when: "Run the CI workflow with custom inputs"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for triggering workflows.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload: Dict[str, Any] = {"ref": params.ref}
        if params.inputs:
            payload["inputs"] = params.inputs

        # 202 Accepted is expected for workflow dispatch
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/workflows/{params.workflow_id}/dispatches",
            method="POST",
            token=auth_token,
            json=payload,
        )

        return json.dumps(
            {
                "success": True,
                "message": f"Workflow {params.workflow_id} triggered successfully on {params.ref}",
                "workflow_id": params.workflow_id,
                "ref": params.ref,
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_get_workflow_run(params: GetWorkflowRunInput) -> str:
    """
    Get detailed information about a specific workflow run.

    Retrieves complete run details including status, conclusion, timing,
    triggering actor, branch, commit, and jobs.

    Args:
        params (GetWorkflowRunInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - run_id (int): Workflow run ID
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed workflow run information

    Examples:
        - Use when: "Show me details about run 12345"
        - Use when: "Check the status of workflow run 67890"
    """
    try:
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}",
            token=params.token,
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "workflow_run"
            )
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        status_emoji = (
            "🔄"
            if data["status"] == "in_progress"
            else "✅"
            if data["conclusion"] == "success"
            else "❌"
            if data["conclusion"] == "failure"
            else "⏸️"
            if data["status"] == "queued"
            else "⚠️"
        )

        markdown = (
            f"# {status_emoji} Workflow Run #{data['run_number']}: {data['name']}\n\n"
        )
        markdown += f"- **Status:** {data['status']}\n"
        markdown += f"- **Conclusion:** {data['conclusion'] or 'N/A'}\n"
        markdown += f"- **Triggered By:** {data['triggering_actor']['login']}\n"
        markdown += f"- **Branch:** `{data['head_branch']}`\n"
        markdown += f"- **Commit:** {data['head_sha'][:8]} - {data['head_commit']['message'][:60]}\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **Updated:** {_format_timestamp(data['updated_at'])}\n"

        if data.get("run_started_at"):
            markdown += f"- **Started:** {_format_timestamp(data['run_started_at'])}\n"
        if data.get("run_attempt"):
            markdown += f"- **Attempt:** {data['run_attempt']}\n"

        markdown += f"- **URL:** {data['html_url']}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_list_workflow_run_jobs(params: ListWorkflowRunJobsInput) -> str:
    """
    List all jobs in a workflow run.

    Retrieves jobs with their status, conclusion, steps, and timing.
    Supports filtering by latest or all jobs.

    Args:
        params (ListWorkflowRunJobsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - run_id (int): Workflow run ID
            - filter (Optional[str]): 'latest' or 'all'
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of jobs with status and details

    Examples:
        - Use when: "Show me all jobs in run 12345"
        - Use when: "List the latest jobs for this workflow run"
    """
    try:
        params_dict: Dict[str, Any] = {"per_page": params.limit, "page": params.page}
        if params.filter:
            params_dict["filter"] = params.filter

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}/jobs",
            token=params.token,
            params=params_dict,
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, data["total_count"])

        if params.response_format == ResponseFormat.COMPACT:
            jobs_list: List[Dict[str, Any]] = cast(
                List[Dict[str, Any]], data.get("jobs", [])
            )
            compact_data = format_response(
                jobs_list, ResponseFormat.COMPACT.value, "job"
            )
            result = json.dumps(
                {
                    "total_count": data.get("total_count", len(jobs_list)),
                    "jobs": compact_data,
                },
                indent=2,
            )
            return _truncate_response(result, data.get("total_count", len(jobs_list)))

        markdown = f"# Jobs for Workflow Run #{params.run_id}\n\n"
        markdown += f"**Total Jobs:** {data['total_count']}\n"
        markdown += (
            f"**Page:** {params.page} | **Showing:** {len(data['jobs'])} jobs\n\n"
        )

        if not data["jobs"]:
            markdown += "No jobs found.\n"
        else:
            for job in data["jobs"]:
                status_emoji = (
                    "🔄"
                    if job["status"] == "in_progress"
                    else "✅"
                    if job["conclusion"] == "success"
                    else "❌"
                    if job["conclusion"] == "failure"
                    else "⏸️"
                    if job["status"] == "queued"
                    else "⚠️"
                )

                markdown += f"## {status_emoji} {job['name']}\n"
                markdown += f"- **ID:** {job['id']}\n"
                markdown += f"- **Status:** {job['status']}\n"
                markdown += f"- **Conclusion:** {job['conclusion'] or 'N/A'}\n"
                markdown += f"- **Runner:** {job.get('runner_name', 'N/A')}\n"
                markdown += f"- **Started:** {_format_timestamp(job['started_at']) if job.get('started_at') else 'N/A'}\n"
                markdown += f"- **Completed:** {_format_timestamp(job['completed_at']) if job.get('completed_at') else 'N/A'}\n"
                markdown += f"- **URL:** {job['html_url']}\n\n"

        return _truncate_response(markdown, data["total_count"])

    except Exception as e:
        return _handle_api_error(e)


async def github_get_job(params: GetJobInput) -> str:
    """
    Get detailed information about a specific job.

    Retrieves job details including status, conclusion, steps, logs URL,
    and runner information.

    Args:
        params (GetJobInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - job_id (int): Job ID
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed job information

    Examples:
        - Use when: "Show me details about job 12345"
        - Use when: "Check the status of job 67890"
    """
    try:
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/jobs/{params.job_id}",
            token=params.token,
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(data, ResponseFormat.COMPACT.value, "job")
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        status_emoji = (
            "🔄"
            if data["status"] == "in_progress"
            else "✅"
            if data["conclusion"] == "success"
            else "❌"
            if data["conclusion"] == "failure"
            else "⏸️"
            if data["status"] == "queued"
            else "⚠️"
        )

        markdown = f"# {status_emoji} Job: {data['name']}\n\n"
        markdown += f"- **ID:** {data['id']}\n"
        markdown += f"- **Status:** {data['status']}\n"
        markdown += f"- **Conclusion:** {data['conclusion'] or 'N/A'}\n"
        markdown += f"- **Runner:** {data.get('runner_name', 'N/A')}\n"
        markdown += f"- **Workflow:** {data.get('workflow_name', 'N/A')}\n"
        markdown += f"- **Started:** {_format_timestamp(data['started_at']) if data.get('started_at') else 'N/A'}\n"
        markdown += f"- **Completed:** {_format_timestamp(data['completed_at']) if data.get('completed_at') else 'N/A'}\n"

        if data.get("steps"):
            markdown += f"\n### Steps ({len(data['steps'])}):\n"
            for step in data["steps"]:
                step_emoji = (
                    "✅"
                    if step["conclusion"] == "success"
                    else "❌"
                    if step["conclusion"] == "failure"
                    else "🔄"
                    if step["status"] == "in_progress"
                    else "⏸️"
                )
                markdown += f"- {step_emoji} {step['name']}: {step['status']} / {step['conclusion'] or 'N/A'}\n"

        markdown += f"\n- **URL:** {data['html_url']}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_get_job_logs(params: GetJobLogsInput) -> str:
    """
    Get logs for a specific job.

    Retrieves the raw log output from a job execution. Logs are returned
    as plain text and may be large for long-running jobs.

    Args:
        params (GetJobLogsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - job_id (int): Job ID
            - token (Optional[str]): GitHub token

    Returns:
        str: Job logs as plain text

    Examples:
        - Use when: "Show me the logs for job 12345"
        - Use when: "Get the error output from failed job 67890"
    """
    try:
        # Job logs endpoint returns plain text, not JSON
        from ..utils.github_client import GhClient

        auth_token = await _get_auth_token_fallback(params.token)
        if not auth_token:
            return json.dumps(
                {
                    "error": "Authentication required",
                    "message": "GitHub token required for accessing job logs.",
                    "success": False,
                },
                indent=2,
            )

        client = GhClient.instance()
        response = await client.request(
            "GET",
            f"repos/{params.owner}/{params.repo}/actions/jobs/{params.job_id}/logs",
            token=auth_token,
            headers={"Accept": "application/vnd.github.v3+json"},
        )

        # Logs are returned as plain text
        logs_text = response.text if hasattr(response, "text") else str(response)

        # Truncate if too long (GitHub API may return very large logs)
        max_length = 50000  # ~50KB
        if len(logs_text) > max_length:
            truncated = logs_text[:max_length]
            if params.response_format == ResponseFormat.JSON:
                return json.dumps(
                    {
                        "job_id": params.job_id,
                        "logs": truncated,
                        "truncated": True,
                        "max_length": max_length,
                    },
                    indent=2,
                )
            if params.response_format == ResponseFormat.COMPACT:
                return json.dumps(
                    {
                        "job_id": params.job_id,
                        "snippet": truncated[:1000],
                        "truncated": True,
                    },
                    indent=2,
                )
            return f"# Job Logs (Truncated - showing first {max_length} characters)\n\n```\n{truncated}\n...\n```\n\n*Logs truncated. Full logs available at job URL.*"

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"job_id": params.job_id, "logs": logs_text}, indent=2)

        if params.response_format == ResponseFormat.COMPACT:
            return json.dumps(
                {
                    "job_id": params.job_id,
                    "snippet": logs_text[:1000],
                    "truncated": len(logs_text) > 1000,
                },
                indent=2,
            )

        # markdown (default)
        return f"# Job Logs\n\n```\n{logs_text}\n```"

    except Exception as e:
        return _handle_api_error(e)


async def github_rerun_workflow(params: RerunWorkflowInput) -> str:
    """
    Rerun a workflow run.

    Re-runs all jobs in a workflow run. Useful for retrying failed or
    cancelled workflows.

    Args:
        params (RerunWorkflowInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - run_id (int): Workflow run ID
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Success confirmation

    Examples:
        - Use when: "Rerun workflow run 12345"
        - Use when: "Retry the failed workflow"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for rerunning workflows.",
                "success": False,
            },
            indent=2,
        )

    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}/rerun",
            method="POST",
            token=auth_token,
        )

        return json.dumps(
            {
                "success": True,
                "message": f"Workflow run {params.run_id} rerun initiated",
                "run_id": params.run_id,
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_rerun_failed_jobs(params: RerunFailedJobsInput) -> str:
    """
    Rerun only the failed jobs in a workflow run.

    Re-runs only jobs that failed, skipping successful ones. More efficient
    than rerunning the entire workflow.

    Args:
        params (RerunFailedJobsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - run_id (int): Workflow run ID
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Success confirmation

    Examples:
        - Use when: "Rerun only the failed jobs in run 12345"
        - Use when: "Retry failed tests without rerunning successful ones"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for rerunning workflows.",
                "success": False,
            },
            indent=2,
        )

    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}/rerun-failed-jobs",
            method="POST",
            token=auth_token,
        )

        return json.dumps(
            {
                "success": True,
                "message": f"Failed jobs in workflow run {params.run_id} rerun initiated",
                "run_id": params.run_id,
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_cancel_workflow_run(params: CancelWorkflowRunInput) -> str:
    """
    Cancel a workflow run.

    Cancels an in-progress or queued workflow run. Cannot cancel completed runs.

    Args:
        params (CancelWorkflowRunInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - run_id (int): Workflow run ID
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Success confirmation

    Examples:
        - Use when: "Cancel workflow run 12345"
        - Use when: "Stop the running deployment workflow"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for canceling workflows.",
                "success": False,
            },
            indent=2,
        )

    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}/cancel",
            method="POST",
            token=auth_token,
        )

        return json.dumps(
            {
                "success": True,
                "message": f"Workflow run {params.run_id} cancellation requested",
                "run_id": params.run_id,
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_list_workflow_run_artifacts(
    params: ListWorkflowRunArtifactsInput,
) -> str:
    """
    List artifacts from a workflow run.

    Retrieves all artifacts produced by a workflow run, including their
    names, sizes, and download URLs.

    Args:
        params (ListWorkflowRunArtifactsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - run_id (int): Workflow run ID
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of artifacts with details

    Examples:
        - Use when: "Show me artifacts from run 12345"
        - Use when: "List all build artifacts for this workflow"
    """
    try:
        params_dict = {"per_page": params.limit, "page": params.page}

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}/artifacts",
            token=params.token,
            params=params_dict,
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, data["total_count"])

        if params.response_format == ResponseFormat.COMPACT:
            artifacts_list: List[Dict[str, Any]] = cast(
                List[Dict[str, Any]], data.get("artifacts", [])
            )
            compact_data = format_response(
                artifacts_list, ResponseFormat.COMPACT.value, "artifact"
            )
            result = json.dumps(
                {
                    "total_count": data.get("total_count", len(artifacts_list)),
                    "artifacts": compact_data,
                },
                indent=2,
            )
            return _truncate_response(
                result, data.get("total_count", len(artifacts_list))
            )

        markdown = f"# Artifacts for Workflow Run #{params.run_id}\n\n"
        markdown += f"**Total Artifacts:** {data['total_count']}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(data['artifacts'])} artifacts\n\n"

        if not data["artifacts"]:
            markdown += "No artifacts found.\n"
        else:
            for artifact in data["artifacts"]:
                size_mb = artifact["size_in_bytes"] / (1024 * 1024)
                markdown += f"## {artifact['name']}\n"
                markdown += f"- **ID:** {artifact['id']}\n"
                markdown += f"- **Size:** {size_mb:.2f} MB ({artifact['size_in_bytes']:,} bytes)\n"
                markdown += (
                    f"- **Created:** {_format_timestamp(artifact['created_at'])}\n"
                )
                markdown += (
                    f"- **Expires:** {_format_timestamp(artifact['expires_at'])}\n"
                )
                markdown += f"- **URL:** {artifact['archive_download_url']}\n\n"

        return _truncate_response(markdown, data["total_count"])

    except Exception as e:
        return _handle_api_error(e)


async def github_get_artifact(params: GetArtifactInput) -> str:
    """
    Get details about a specific artifact.

    Retrieves artifact metadata including name, size, creation date,
    expiration date, and download URL.

    Args:
        params (GetArtifactInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - artifact_id (int): Artifact ID
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Artifact details

    Examples:
        - Use when: "Show me details about artifact 12345"
        - Use when: "Get information about build artifact 67890"
    """
    try:
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/artifacts/{params.artifact_id}",
            token=params.token,
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "artifact"
            )
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        size_mb = data["size_in_bytes"] / (1024 * 1024)
        markdown = f"# Artifact: {data['name']}\n\n"
        markdown += f"- **ID:** {data['id']}\n"
        markdown += f"- **Size:** {size_mb:.2f} MB ({data['size_in_bytes']:,} bytes)\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **Expires:** {_format_timestamp(data['expires_at'])}\n"
        markdown += f"- **Download URL:** {data['archive_download_url']}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_delete_artifact(params: DeleteArtifactInput) -> str:
    """
    Delete an artifact.

    Permanently deletes an artifact. This action cannot be undone.

    Args:
        params (DeleteArtifactInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - artifact_id (int): Artifact ID
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Success confirmation

    Examples:
        - Use when: "Delete artifact 12345"
        - Use when: "Remove old build artifacts"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for deleting artifacts.",
                "success": False,
            },
            indent=2,
        )

    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/artifacts/{params.artifact_id}",
            method="DELETE",
            token=auth_token,
        )

        return json.dumps(
            {
                "success": True,
                "message": f"Artifact {params.artifact_id} deleted successfully",
                "artifact_id": params.artifact_id,
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_suggest_workflow(params: WorkflowSuggestionInput) -> str:
    """
    Recommend whether to use API tools, local git, or a hybrid approach.

    Heuristics consider operation type, file size, number of edits, and file count.
    Includes meta-level dogfooding detection and rough token cost estimates.
    """
    operation = (params.operation or "").lower()
    description = (params.description or "").lower()
    file_size = params.file_size or 0
    num_edits = params.num_edits or 1
    file_count = params.file_count or 1

    # Token estimate: ~4 bytes per token (very rough)
    def bytes_to_tokens(b: int) -> int:
        return max(1, b // 4)

    # Detect cases where API is required
    api_only_ops = {"create_release", "github_release", "publish_release"}
    if operation in api_only_ops or "create_release" in operation:
        recommendation = "api"
        rationale = (
            "Operation requires GitHub API (releases cannot be done locally only)."
        )
    # Dogfooding detection
    elif any(x in operation for x in ["dogfood", "dogfooding", "test"]) or any(
        x in description for x in ["dogfood", "test", "github_", "mcp"]
    ):
        recommendation = "api"
        rationale = "Dogfooding detected. Use API tools to test features end-to-end."
    # Single small edit → API
    elif file_count == 1 and num_edits == 1 and file_size <= 10_000:
        recommendation = "api"
        rationale = "Single small edit is fastest via API with minimal overhead."
    # Large/bulk changes → Local
    elif file_count > 1 or num_edits >= 3 or file_size >= 40_000:
        recommendation = "local"
        rationale = "Multiple edits or large files are more efficient with local git."
    # Otherwise → Hybrid
    else:
        recommendation = "hybrid"
        rationale = (
            "Mix approaches: structure changes locally, finalize small pieces via API."
        )

    # Simple token cost model
    api_tokens = bytes_to_tokens(file_size) * max(1, num_edits)
    local_tokens = bytes_to_tokens(min(file_size, 1024))  # local coordination minimal
    savings_tokens = max(0, api_tokens - local_tokens)

    if params.response_format == ResponseFormat.JSON:
        return _truncate_response(
            json.dumps(
                {
                    "recommendation": recommendation,
                    "rationale": rationale,
                    "estimates": {
                        "api_tokens": api_tokens,
                        "local_tokens": local_tokens,
                        "potential_savings_tokens": savings_tokens,
                    },
                    "meta": {
                        "dogfooding": recommendation == "api"
                        and (
                            "dogfood" in operation
                            or "test" in operation
                            or "dogfood" in description
                            or "test" in description
                        )
                    },
                },
                indent=2,
            )
        )

    # Markdown output
    lines = [
        "# Workflow Suggestion",
        f"**Recommendation:** {recommendation.upper()}",
        f"**Rationale:** {rationale}",
        "",
        "## Estimates",
        f"- API tokens (rough): {api_tokens}",
        f"- Local tokens (rough): {local_tokens}",
        f"- Potential savings: {savings_tokens} tokens",
    ]

    if recommendation == "api" and (
        "dogfood" in operation
        or "test" in operation
        or "dogfood" in description
        or "test" in description
    ):
        lines.append(
            "\n🐕🍖 Dogfooding detected: Use API tools to validate new features end-to-end."
        )

    lines.append("\n## Next Steps")
    if recommendation == "api":
        lines.append(
            "- Use targeted API tools for atomic changes (e.g., github_update_file, github_create_release)"
        )
    elif recommendation == "local":
        lines.append("- Make edits locally, commit logically, and push a PR for review")
    else:
        lines.append(
            "- Do bulk changes locally, then use API tools for final small edits"
        )

    return _truncate_response("\n".join(lines))
