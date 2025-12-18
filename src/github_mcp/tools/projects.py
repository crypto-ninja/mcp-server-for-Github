"""Projects tools for GitHub MCP Server."""

import json

from ..models.inputs import (
    CreateOrgProjectInput,
    CreateProjectColumnInput,
    CreateRepoProjectInput,
    DeleteProjectInput,
    GetProjectInput,
    ListOrgProjectsInput,
    ListProjectColumnsInput,
    ListRepoProjectsInput,
    UpdateProjectInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response
from ..utils.compact_format import format_response


async def github_list_repo_projects(params: ListRepoProjectsInput) -> str:
    """
    List projects for a repository.

    Retrieves all projects (classic) associated with a repository.
    Supports filtering by state (open/closed/all).

    Args:
        params (ListRepoProjectsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - state (str): Filter by state (default: 'open')
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of projects with details

    Examples:
        - Use when: "Show me all projects for this repo"
        - Use when: "List open projects"
    """
    try:
        params_dict = {
            "state": params.state,
            "per_page": params.limit,
            "page": params.page,
        }

        # Projects API requires preview header
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/projects",
            token=params.token,
            params=params_dict,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "project"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(data))

        markdown = f"# Projects for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Projects:** {len(data)}\n\n"

        if not data:
            markdown += "No projects found.\n"
        else:
            for project in data:
                markdown += f"## {project['name']}\n"
                markdown += f"- **ID:** {project['id']}\n"
                markdown += f"- **State:** {project['state']}\n"
                if project.get("body"):
                    markdown += f"- **Description:** {project['body'][:100]}{'...' if len(project.get('body', '')) > 100 else ''}\n"
                markdown += (
                    f"- **Created:** {_format_timestamp(project['created_at'])}\n"
                )
                markdown += (
                    f"- **Updated:** {_format_timestamp(project['updated_at'])}\n"
                )
                markdown += f"- **URL:** {project['html_url']}\n\n"

        return _truncate_response(markdown, len(data))

    except Exception as e:
        return _handle_api_error(e)


async def github_list_org_projects(params: ListOrgProjectsInput) -> str:
    """
    List projects for an organization.

    Retrieves all projects (classic) associated with an organization.
    Requires organization read access.

    Args:
        params (ListOrgProjectsInput): Validated input parameters containing:
            - org (str): Organization name
            - state (str): Filter by state (default: 'open')
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of organization projects

    Examples:
        - Use when: "Show me all organization projects"
        - Use when: "List open projects for myorg"
    """
    try:
        params_dict = {
            "state": params.state,
            "per_page": params.limit,
            "page": params.page,
        }

        data = await _make_github_request(
            f"orgs/{params.org}/projects",
            token=params.token,
            params=params_dict,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "project"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(data))

        markdown = f"# Projects for Organization: {params.org}\n\n"
        markdown += f"**Total Projects:** {len(data)}\n\n"

        if not data:
            markdown += "No projects found.\n"
        else:
            for project in data:
                markdown += f"## {project['name']}\n"
                markdown += f"- **ID:** {project['id']}\n"
                markdown += f"- **State:** {project['state']}\n"
                if project.get("body"):
                    markdown += f"- **Description:** {project['body'][:100]}{'...' if len(project.get('body', '')) > 100 else ''}\n"
                markdown += f"- **URL:** {project['html_url']}\n\n"

        return _truncate_response(markdown, len(data))

    except Exception as e:
        return _handle_api_error(e)


async def github_get_project(params: GetProjectInput) -> str:
    """
    Get details about a specific project.

    Retrieves complete project information including name, description,
    state, and metadata.

    Args:
        params (GetProjectInput): Validated input parameters containing:
            - project_id (int): Project ID
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed project information

    Examples:
        - Use when: "Show me details about project 12345"
        - Use when: "Get information about project 67890"
    """
    try:
        data = await _make_github_request(
            f"projects/{params.project_id}",
            token=params.token,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "project"
            )
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        markdown = f"# Project: {data['name']}\n\n"
        markdown += f"- **ID:** {data['id']}\n"
        markdown += f"- **State:** {data['state']}\n"
        if data.get("body"):
            markdown += f"- **Description:** {data['body']}\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **Updated:** {_format_timestamp(data['updated_at'])}\n"
        markdown += f"- **URL:** {data['html_url']}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_create_repo_project(params: CreateRepoProjectInput) -> str:
    """
    Create a new project for a repository.

    Creates a classic project board for organizing issues and pull requests.

    Args:
        params (CreateRepoProjectInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - name (str): Project name
            - body (Optional[str]): Project description
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Created project details

    Examples:
        - Use when: "Create a new project called 'Sprint Planning'"
        - Use when: "Add a project board for this repo"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating projects.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload = {"name": params.name}
        if params.body:
            payload["body"] = params.body

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/projects",
            method="POST",
            token=auth_token,
            json=payload,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )

        return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


async def github_create_org_project(params: CreateOrgProjectInput) -> str:
    """
    Create a new project for an organization.

    Creates a classic project board at the organization level.
    Requires organization admin permissions.

    Args:
        params (CreateOrgProjectInput): Validated input parameters containing:
            - org (str): Organization name
            - name (str): Project name
            - body (Optional[str]): Project description
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Created project details

    Examples:
        - Use when: "Create an organization project called 'Q1 Goals'"
        - Use when: "Add a project board for the org"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating projects.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload = {"name": params.name}
        if params.body:
            payload["body"] = params.body

        data = await _make_github_request(
            f"orgs/{params.org}/projects",
            method="POST",
            token=auth_token,
            json=payload,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )

        return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


async def github_update_project(params: UpdateProjectInput) -> str:
    """
    Update a project.

    Allows updating project name, description, and state (open/closed).

    Args:
        params (UpdateProjectInput): Validated input parameters containing:
            - project_id (int): Project ID
            - name (Optional[str]): New project name
            - body (Optional[str]): New project description
            - state (Optional[str]): New state ('open' or 'closed')
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Updated project details

    Examples:
        - Use when: "Rename project 12345 to 'New Name'"
        - Use when: "Close project 67890"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for updating projects.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload = {}
        if params.name:
            payload["name"] = params.name
        if params.body is not None:
            payload["body"] = params.body
        if params.state:
            payload["state"] = params.state

        data = await _make_github_request(
            f"projects/{params.project_id}",
            method="PATCH",
            token=auth_token,
            json=payload,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )

        return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


async def github_delete_project(params: DeleteProjectInput) -> str:
    """
    Delete a project.

    Permanently deletes a project. This action cannot be undone.

    Args:
        params (DeleteProjectInput): Validated input parameters containing:
            - project_id (int): Project ID
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Success confirmation

    Examples:
        - Use when: "Delete project 12345"
        - Use when: "Remove the old project board"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for deleting projects.",
                "success": False,
            },
            indent=2,
        )

    try:
        await _make_github_request(
            f"projects/{params.project_id}",
            method="DELETE",
            token=auth_token,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )

        return json.dumps(
            {
                "success": True,
                "message": f"Project {params.project_id} deleted successfully",
                "project_id": params.project_id,
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_list_project_columns(params: ListProjectColumnsInput) -> str:
    """
    List columns in a project.

    Retrieves all columns (e.g., "To Do", "In Progress", "Done") in a project board.

    Args:
        params (ListProjectColumnsInput): Validated input parameters containing:
            - project_id (int): Project ID
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of project columns

    Examples:
        - Use when: "Show me all columns in project 12345"
        - Use when: "List the project board columns"
    """
    try:
        params_dict = {"per_page": params.limit, "page": params.page}

        data = await _make_github_request(
            f"projects/{params.project_id}/columns",
            token=params.token,
            params=params_dict,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))

        markdown = f"# Columns for Project #{params.project_id}\n\n"
        markdown += f"**Total Columns:** {len(data)}\n\n"

        if not data:
            markdown += "No columns found.\n"
        else:
            for column in data:
                markdown += f"## {column['name']}\n"
                markdown += f"- **ID:** {column['id']}\n"
                markdown += (
                    f"- **Created:** {_format_timestamp(column['created_at'])}\n"
                )
                markdown += (
                    f"- **Updated:** {_format_timestamp(column['updated_at'])}\n\n"
                )

        return _truncate_response(markdown, len(data))

    except Exception as e:
        return _handle_api_error(e)


async def github_create_project_column(params: CreateProjectColumnInput) -> str:
    """
    Create a new column in a project.

    Adds a new column (e.g., "Review", "Testing") to a project board.

    Args:
        params (CreateProjectColumnInput): Validated input parameters containing:
            - project_id (int): Project ID
            - name (str): Column name
            - token (Optional[str]): GitHub token (required)

    Returns:
        str: Created column details

    Examples:
        - Use when: "Add a 'Review' column to project 12345"
        - Use when: "Create a new column called 'Testing'"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating project columns.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload = {"name": params.name}

        data = await _make_github_request(
            f"projects/{params.project_id}/columns",
            method="POST",
            token=auth_token,
            json=payload,
            headers={"Accept": "application/vnd.github.inertia-preview+json"},
        )

        return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# GitHub Discussions Tools (Phase 2 - Batch 4)
# ============================================================================
