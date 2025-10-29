#!/usr/bin/env python3
"""
GitHub MCP Server - A comprehensive Model Context Protocol server for GitHub integration.

Copyright (C) 2025 MCP Labs
https://github.com/crypto-ninja/github-mcp-server

This software is available under a dual licensing model:

1. AGPL v3 License - For open source projects and personal use
   See LICENSE file for full terms
   https://www.gnu.org/licenses/agpl-3.0.html

2. Commercial License - For commercial/proprietary use
   See LICENSE-COMMERCIAL file for full terms
   Contact: licensing@mcplabs.co.uk

Key AGPL v3 Requirements:
- Source code must be made available to users
- Modifications must be released under AGPL v3
- Network use is considered distribution
- Commercial use allowed IF source code is shared

For proprietary/commercial use WITHOUT sharing source code,
a commercial license is required.

For licensing inquiries:
Email: licensing@mcplabs.co.uk
Website: https://mcplabs.co.uk
GitHub: https://github.com/crypto-ninja/github-mcp-server/issues/new?title=Commercial+License+Inquiry

---

This server provides tools to interact with GitHub repositories, issues, pull requests,
and more. It enables AI assistants to seamlessly integrate with GitHub workflows.

Features:
- Repository management and exploration
- Issue creation, search, and management
- Pull request operations (list, create, detailed view)
- GitHub Actions workflow monitoring
- Advanced search (code and issues across GitHub)
- File content retrieval
- User and organization information
"""

from typing import Optional, List, Dict, Any
from enum import Enum
import json
import httpx
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("github_mcp")

# Constants
API_BASE_URL = "https://api.github.com"
CHARACTER_LIMIT = 25000  # Maximum response size in characters
DEFAULT_LIMIT = 20

# Enums
class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"

class IssueState(str, Enum):
    """GitHub issue state."""
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"

class PullRequestState(str, Enum):
    """GitHub pull request state."""
    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"

class SortOrder(str, Enum):
    """Sort order for results."""
    ASC = "asc"
    DESC = "desc"

class WorkflowRunStatus(str, Enum):
    """GitHub workflow run status."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    REQUESTED = "requested"
    PENDING = "pending"

class WorkflowRunConclusion(str, Enum):
    """GitHub workflow run conclusion."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"

class PRMergeMethod(str, Enum):
    """GitHub pull request merge method."""
    MERGE = "merge"
    SQUASH = "squash"
    REBASE = "rebase"

class PRReviewState(str, Enum):
    """GitHub pull request review state."""
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"
    DISMISSED = "DISMISSED"
    PENDING = "PENDING"

# Shared Utilities
async def _make_github_request(
    endpoint: str,
    method: str = "GET",
    token: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Reusable function for all GitHub API calls.
    
    Args:
        endpoint: API endpoint (without base URL)
        method: HTTP method (GET, POST, PATCH, etc.)
        token: Optional GitHub personal access token
        **kwargs: Additional arguments for httpx request
    
    Returns:
        Dict containing the API response
    
    Raises:
        httpx.HTTPStatusError: For HTTP errors
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if "headers" in kwargs:
        headers.update(kwargs.pop("headers"))
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{API_BASE_URL}/{endpoint}",
            headers=headers,
            timeout=30.0,
            **kwargs
        )
        response.raise_for_status()
        return response.json()

def _handle_api_error(e: Exception) -> str:
    """
    Consistent error formatting across all tools.
    
    Args:
        e: The exception that occurred
    
    Returns:
        User-friendly error message
    """
    if isinstance(e, httpx.HTTPStatusError):
        status_code = e.response.status_code
        if status_code == 404:
            return "Error: Resource not found. Please verify the repository, issue, or user exists."
        elif status_code == 403:
            return "Error: Permission denied. You may need authentication or lack access to this resource."
        elif status_code == 401:
            return "Error: Authentication required. Please provide a valid GitHub token."
        elif status_code == 422:
            return "Error: Invalid request. Please check your input parameters."
        elif status_code == 429:
            return "Error: Rate limit exceeded. Please wait before making more requests."
        return f"Error: GitHub API request failed with status {status_code}. {e.response.text}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    elif isinstance(e, httpx.NetworkError):
        return "Error: Network error occurred. Please check your connection."
    return f"Error: Unexpected error occurred: {str(e)}"

def _format_timestamp(timestamp: str) -> str:
    """Convert ISO timestamp to human-readable format."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        return timestamp

def _truncate_response(response: str, data_count: Optional[int] = None) -> str:
    """
    Truncate response if it exceeds CHARACTER_LIMIT.
    
    Args:
        response: The response string to check
        data_count: Optional count of items in the response
    
    Returns:
        Original or truncated response with notice
    """
    if len(response) <= CHARACTER_LIMIT:
        return response
    
    truncated = response[:CHARACTER_LIMIT]
    truncation_notice = (
        f"\n\n[Response truncated at {CHARACTER_LIMIT} characters"
    )
    
    if data_count:
        truncation_notice += f" - showing partial results. Use pagination or filters to see more."
    else:
        truncation_notice += ". Use filters or pagination to reduce result size."
    
    truncation_notice += "]"
    
    return truncated + truncation_notice

# Pydantic Models for Input Validation

class RepoInfoInput(BaseModel):
    """Input model for repository information retrieval."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner username or organization (e.g., 'octocat', 'github')", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name (e.g., 'hello-world', 'docs')", min_length=1, max_length=100)
    token: Optional[str] = Field(default=None, description="Optional GitHub personal access token for authenticated requests")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for human-readable or 'json' for machine-readable")

class ListIssuesInput(BaseModel):
    """Input model for listing repository issues."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner username", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: IssueState = Field(default=IssueState.OPEN, description="Issue state filter: 'open', 'closed', or 'all'")
    limit: Optional[int] = Field(default=DEFAULT_LIMIT, description="Maximum results to return (1-100)", ge=1, le=100)
    page: Optional[int] = Field(default=1, description="Page number for pagination", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class CreateIssueInput(BaseModel):
    """Input model for creating GitHub issues."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner username", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    title: str = Field(..., description="Issue title", min_length=1, max_length=256)
    body: Optional[str] = Field(default=None, description="Issue description/body in Markdown format")
    labels: Optional[List[str]] = Field(default=None, description="List of label names to apply", max_items=20)
    assignees: Optional[List[str]] = Field(default=None, description="List of usernames to assign", max_items=10)
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")

class SearchRepositoriesInput(BaseModel):
    """Input model for searching GitHub repositories."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    query: str = Field(..., description="Search query (e.g., 'language:python stars:>1000', 'machine learning')", min_length=1, max_length=256)
    sort: Optional[str] = Field(default=None, description="Sort field: 'stars', 'forks', 'updated', 'help-wanted-issues'")
    order: Optional[SortOrder] = Field(default=SortOrder.DESC, description="Sort order: 'asc' or 'desc'")
    limit: Optional[int] = Field(default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100)
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetFileContentInput(BaseModel):
    """Input model for retrieving file content from a repository."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(..., description="File path in the repository (e.g., 'src/main.py', 'README.md')", min_length=1, max_length=500)
    ref: Optional[str] = Field(default=None, description="Branch, tag, or commit SHA (defaults to repository's default branch)")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")

class ListPullRequestsInput(BaseModel):
    """Input model for listing pull requests."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: PullRequestState = Field(default=PullRequestState.OPEN, description="PR state: 'open', 'closed', or 'all'")
    limit: Optional[int] = Field(default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100)
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetUserInfoInput(BaseModel):
    """Input model for retrieving user information."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    username: str = Field(..., description="GitHub username (e.g., 'octocat')", min_length=1, max_length=100)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class ListRepoContentsInput(BaseModel):
    """Input model for listing repository contents."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: Optional[str] = Field(default="", description="Directory path (empty for root directory)")
    ref: Optional[str] = Field(default=None, description="Branch, tag, or commit")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class ListWorkflowsInput(BaseModel):
    """Input model for listing GitHub Actions workflows."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetWorkflowRunsInput(BaseModel):
    """Input model for getting GitHub Actions workflow runs."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    workflow_id: Optional[str] = Field(default=None, description="Workflow ID or name (optional - gets all workflows if not specified)")
    status: Optional[WorkflowRunStatus] = Field(default=None, description="Filter by run status")
    conclusion: Optional[WorkflowRunConclusion] = Field(default=None, description="Filter by run conclusion")
    limit: Optional[int] = Field(default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100)
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class CreatePullRequestInput(BaseModel):
    """Input model for creating GitHub pull requests."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    title: str = Field(..., description="Pull request title", min_length=1, max_length=256)
    head: str = Field(..., description="Source branch name", min_length=1, max_length=100)
    base: str = Field(..., description="Target branch name (default: main)", min_length=1, max_length=100)
    body: Optional[str] = Field(default=None, description="Pull request description in Markdown format")
    draft: Optional[bool] = Field(default=False, description="Create as draft pull request")
    maintainer_can_modify: Optional[bool] = Field(default=True, description="Allow maintainers to modify the PR")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")

class GetPullRequestDetailsInput(BaseModel):
    """Input model for getting detailed pull request information."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    pull_number: int = Field(..., description="Pull request number", ge=1)
    include_reviews: Optional[bool] = Field(default=True, description="Include review information")
    include_commits: Optional[bool] = Field(default=True, description="Include commit information")
    include_files: Optional[bool] = Field(default=False, description="Include changed files (can be large)")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class SearchCodeInput(BaseModel):
    """Input model for searching code across GitHub."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    query: str = Field(..., description="Code search query (e.g., 'TODO language:python', 'function authenticate')", min_length=1, max_length=256)
    sort: Optional[str] = Field(default=None, description="Sort field: 'indexed' (default)")
    order: Optional[SortOrder] = Field(default=SortOrder.DESC, description="Sort order: 'asc' or 'desc'")
    limit: Optional[int] = Field(default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100)
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class SearchIssuesInput(BaseModel):
    """Input model for searching issues across GitHub."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    query: str = Field(..., description="Issue search query (e.g., 'bug language:python', 'security in:title')", min_length=1, max_length=256)
    sort: Optional[str] = Field(default=None, description="Sort field: 'created', 'updated', 'comments'")
    order: Optional[SortOrder] = Field(default=SortOrder.DESC, description="Sort order: 'asc' or 'desc'")
    limit: Optional[int] = Field(default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100)
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class ListReleasesInput(BaseModel):
    """Input model for listing repository releases."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    limit: Optional[int] = Field(default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100)
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class GetReleaseInput(BaseModel):
    """Input model for getting a specific release or latest release."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    tag: Optional[str] = Field(default="latest", description="Release tag (e.g., 'v1.1.0') or 'latest' for most recent")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

# Tool Implementations

@mcp.tool(
    name="github_get_repo_info",
    annotations={
        "title": "Get Repository Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_repo_info(params: RepoInfoInput) -> str:
    """
    Retrieve detailed information about a GitHub repository.
    
    This tool fetches comprehensive metadata about a repository including description,
    statistics, languages, and ownership information. It does NOT modify the repository.
    
    Args:
        params (RepoInfoInput): Validated input parameters containing:
            - owner (str): Repository owner username or organization
            - repo (str): Repository name
            - token (Optional[str]): GitHub token for authenticated requests
            - response_format (ResponseFormat): Output format preference
    
    Returns:
        str: Repository information in requested format (JSON or Markdown)
    
    Examples:
        - Use when: "Tell me about the tensorflow repository"
        - Use when: "What's the license for facebook/react?"
        - Use when: "Get details on microsoft/vscode"
    
    Error Handling:
        - Returns error if repository doesn't exist (404)
        - Returns error if authentication required but not provided (403)
        - Includes actionable suggestions for resolving errors
    """
    try:
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}",
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result)
        
        # Markdown format
        markdown = f"""# {data['full_name']}

**Description:** {data['description'] or 'No description provided'}

## Statistics
- ⭐ Stars: {data['stargazers_count']:,}
- 🍴 Forks: {data['forks_count']:,}
- 👁️ Watchers: {data['watchers_count']:,}
- 🐛 Open Issues: {data['open_issues_count']:,}

## Details
- **Owner:** {data['owner']['login']} ({data['owner']['type']})
- **Created:** {_format_timestamp(data['created_at'])}
- **Last Updated:** {_format_timestamp(data['updated_at'])}
- **Default Branch:** {data['default_branch']}
- **Language:** {data['language'] or 'Not specified'}
- **License:** {data['license']['name'] if data.get('license') else 'No license'}
- **Topics:** {', '.join(data.get('topics', [])) or 'None'}

## URLs
- **Homepage:** {data['homepage'] or 'None'}
- **Clone URL:** {data['clone_url']}
- **Repository:** {data['html_url']}

## Status
- Archived: {'Yes' if data['archived'] else 'No'}
- Disabled: {'Yes' if data['disabled'] else 'No'}
- Private: {'Yes' if data['private'] else 'No'}
- Fork: {'Yes' if data['fork'] else 'No'}
"""
        
        return _truncate_response(markdown)
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_list_issues",
    annotations={
        "title": "List Repository Issues",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_issues(params: ListIssuesInput) -> str:
    """
    List issues from a GitHub repository with filtering options.
    
    This tool retrieves issues from a repository, supporting state filtering and
    pagination. It does NOT create or modify issues.
    
    Args:
        params (ListIssuesInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - state (IssueState): Filter by state ('open', 'closed', 'all')
            - limit (int): Maximum results per page (1-100, default 20)
            - page (int): Page number for pagination (default 1)
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: List of issues in requested format with pagination info
    
    Examples:
        - Use when: "Show me open issues in react repository"
        - Use when: "List all closed issues for tensorflow/tensorflow"
        - Use when: "Get the first 50 issues from microsoft/vscode"
    
    Error Handling:
        - Returns error if repository not found
        - Handles rate limiting with clear guidance
        - Provides pagination info for continued browsing
    """
    try:
        params_dict = {
            "state": params.state.value,
            "per_page": params.limit,
            "page": params.page
        }
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/issues",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))
        
        # Markdown format
        markdown = f"# Issues for {params.owner}/{params.repo}\n\n"
        markdown += f"**State:** {params.state.value} | **Page:** {params.page} | **Showing:** {len(data)} issues\n\n"
        
        if not data:
            markdown += f"No {params.state.value} issues found.\n"
        else:
            for issue in data:
                # Skip pull requests (they appear in issues endpoint)
                if 'pull_request' in issue:
                    continue
                
                markdown += f"## #{issue['number']}: {issue['title']}\n"
                markdown += f"- **State:** {issue['state']}\n"
                markdown += f"- **Author:** @{issue['user']['login']}\n"
                markdown += f"- **Created:** {_format_timestamp(issue['created_at'])}\n"
                markdown += f"- **Updated:** {_format_timestamp(issue['updated_at'])}\n"
                
                if issue.get('labels'):
                    labels = ', '.join([f"`{l['name']}`" for l in issue['labels']])
                    markdown += f"- **Labels:** {labels}\n"
                
                if issue.get('assignees'):
                    assignees = ', '.join([f"@{a['login']}" for a in issue['assignees']])
                    markdown += f"- **Assignees:** {assignees}\n"
                
                markdown += f"- **Comments:** {issue['comments']}\n"
                markdown += f"- **URL:** {issue['html_url']}\n\n"
                
                if issue.get('body'):
                    body_preview = issue['body'][:200] + "..." if len(issue['body']) > 200 else issue['body']
                    markdown += f"**Preview:** {body_preview}\n\n"
                
                markdown += "---\n\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_create_issue",
    annotations={
        "title": "Create GitHub Issue",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_create_issue(params: CreateIssueInput) -> str:
    """
    Create a new issue in a GitHub repository.
    
    This tool creates a new issue with specified title, body, labels, and assignees.
    Requires authentication with a GitHub token that has repository access.
    
    Args:
        params (CreateIssueInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - title (str): Issue title (required)
            - body (Optional[str]): Issue description in Markdown
            - labels (Optional[List[str]]): Label names to apply
            - assignees (Optional[List[str]]): Usernames to assign
            - token (Optional[str]): GitHub token (optional - uses GITHUB_TOKEN env var if not provided)
    
    Returns:
        str: Created issue details including issue number and URL
    
    Examples:
        - Use when: "Create a bug report in myrepo"
        - Use when: "Open a new feature request issue"
        - Use when: "File an issue about the documentation"
    
    Error Handling:
        - Returns error if authentication fails (401)
        - Returns error if insufficient permissions (403)
        - Returns error if labels/assignees don't exist (422)
    """
    import os
    
    # Get token from parameter or environment
    auth_token = params.token or os.getenv("GITHUB_TOKEN")
    
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for creating issues. Set GITHUB_TOKEN environment variable or pass token parameter.",
            "success": False
        }, indent=2)
    
    try:
        payload = {
            "title": params.title,
        }
        
        if params.body:
            payload["body"] = params.body
        if params.labels:
            payload["labels"] = params.labels
        if params.assignees:
            payload["assignees"] = params.assignees
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/issues",
            method="POST",
            token=auth_token,
            json=payload
        )
        
        result = f"""✅ Issue Created Successfully!

**Issue:** #{data['number']} - {data['title']}
**State:** {data['state']}
**URL:** {data['html_url']}
**Created:** {_format_timestamp(data['created_at'])}
**Author:** @{data['user']['login']}

"""
        
        if data.get('labels'):
            labels = ', '.join([f"`{l['name']}`" for l in data['labels']])
            result += f"**Labels:** {labels}\n"
        
        if data.get('assignees'):
            assignees = ', '.join([f"@{a['login']}" for a in data['assignees']])
            result += f"**Assignees:** {assignees}\n"
        
        return result
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_search_repositories",
    annotations={
        "title": "Search GitHub Repositories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_search_repositories(params: SearchRepositoriesInput) -> str:
    """
    Search for repositories on GitHub with advanced filtering.
    
    Supports GitHub's full search syntax including language, stars, topics, and more.
    Returns sorted and paginated results.
    
    Args:
        params (SearchRepositoriesInput): Validated input parameters containing:
            - query (str): Search query with optional qualifiers
            - sort (Optional[str]): Sort by 'stars', 'forks', 'updated', etc.
            - order (SortOrder): Sort order ('asc' or 'desc')
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Search results with repository details and pagination info
    
    Examples:
        - Use when: "Find Python machine learning repositories"
          query="machine learning language:python"
        - Use when: "Search for React repositories with >10k stars"
          query="react stars:>10000"
        - Use when: "Find trending JavaScript projects"
          query="language:javascript" sort="stars"
    
    Query Qualifiers:
        - language:python - Repositories in Python
        - stars:>1000 - More than 1000 stars
        - topics:machine-learning - Tagged with topic
        - created:>2023-01-01 - Created after date
        - fork:false - Exclude forks
    
    Error Handling:
        - Returns error if query syntax is invalid
        - Handles rate limiting for search API
        - Provides clear error messages for all failures
    """
    try:
        params_dict = {
            "q": params.query,
            "per_page": params.limit,
            "page": params.page,
            "order": params.order.value
        }
        
        if params.sort:
            params_dict["sort"] = params.sort
        
        data = await _make_github_request(
            "search/repositories",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, data['total_count'])
        
        # Markdown format
        markdown = f"# Repository Search Results\n\n"
        markdown += f"**Query:** {params.query}\n"
        markdown += f"**Total Results:** {data['total_count']:,}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(data['items'])} repositories\n\n"
        
        if not data['items']:
            markdown += "No repositories found matching your query.\n"
        else:
            for repo in data['items']:
                markdown += f"## {repo['full_name']}\n"
                markdown += f"{repo['description'] or 'No description'}\n\n"
                markdown += f"- ⭐ **Stars:** {repo['stargazers_count']:,}\n"
                markdown += f"- 🍴 **Forks:** {repo['forks_count']:,}\n"
                markdown += f"- **Language:** {repo['language'] or 'Not specified'}\n"
                markdown += f"- **Updated:** {_format_timestamp(repo['updated_at'])}\n"
                
                if repo.get('topics'):
                    topics = ', '.join([f"`{t}`" for t in repo['topics'][:5]])
                    markdown += f"- **Topics:** {topics}\n"
                
                markdown += f"- **URL:** {repo['html_url']}\n\n"
                markdown += "---\n\n"
        
        return _truncate_response(markdown, data['total_count'])
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_get_file_content",
    annotations={
        "title": "Get File Content",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_file_content(params: GetFileContentInput) -> str:
    """
    Retrieve the content of a file from a GitHub repository.
    
    Fetches file content from a specific branch, tag, or commit. Automatically
    decodes base64-encoded content for text files.
    
    Args:
        params (GetFileContentInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - path (str): File path in repository
            - ref (Optional[str]): Branch, tag, or commit SHA
            - token (Optional[str]): GitHub token
    
    Returns:
        str: File content with metadata (name, size, encoding, etc.)
    
    Examples:
        - Use when: "Show me the README from tensorflow/tensorflow"
        - Use when: "Get the content of src/main.py"
        - Use when: "Fetch package.json from the main branch"
    
    Error Handling:
        - Returns error if file not found (404)
        - Returns error if file is too large for API
        - Handles binary files appropriately
    """
    try:
        params_dict = {}
        if params.ref:
            params_dict["ref"] = params.ref
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            token=params.token,
            params=params_dict
        )
        
        # Handle file content
        if data.get('encoding') == 'base64':
            import base64
            content = base64.b64decode(data['content']).decode('utf-8', errors='replace')
        else:
            content = data.get('content', '')
        
        result = f"""# File: {data['name']}

**Path:** {data['path']}
**Size:** {data['size']:,} bytes
**Type:** {data['type']}
**Encoding:** {data.get('encoding', 'none')}
**SHA:** {data['sha']}
**URL:** {data['html_url']}

---

**Content:**

```
{content}
```
"""
        
        return _truncate_response(result)
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_list_pull_requests",
    annotations={
        "title": "List Pull Requests",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_pull_requests(params: ListPullRequestsInput) -> str:
    """
    List pull requests from a GitHub repository.
    
    Retrieves pull requests with state filtering and pagination support.
    Shows PR metadata including author, status, and review information.
    
    Args:
        params (ListPullRequestsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - state (PullRequestState): Filter by 'open', 'closed', or 'all'
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: List of pull requests with details and pagination info
    
    Examples:
        - Use when: "Show open PRs in react repository"
        - Use when: "List all merged pull requests"
        - Use when: "Get recent PRs for microsoft/typescript"
    
    Error Handling:
        - Returns error if repository not accessible
        - Handles pagination for large result sets
        - Provides clear status for each PR
    """
    try:
        params_dict = {
            "state": params.state.value,
            "per_page": params.limit,
            "page": params.page
        }
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))
        
        # Markdown format
        markdown = f"# Pull Requests for {params.owner}/{params.repo}\n\n"
        markdown += f"**State:** {params.state.value} | **Page:** {params.page} | **Showing:** {len(data)} PRs\n\n"
        
        if not data:
            markdown += f"No {params.state.value} pull requests found.\n"
        else:
            for pr in data:
                markdown += f"## #{pr['number']}: {pr['title']}\n"
                markdown += f"- **State:** {pr['state']}\n"
                markdown += f"- **Author:** @{pr['user']['login']}\n"
                markdown += f"- **Created:** {_format_timestamp(pr['created_at'])}\n"
                markdown += f"- **Updated:** {_format_timestamp(pr['updated_at'])}\n"
                markdown += f"- **Base:** `{pr['base']['ref']}` ← **Head:** `{pr['head']['ref']}`\n"
                
                if pr.get('draft'):
                    markdown += f"- **Draft:** Yes\n"
                
                if pr.get('merged'):
                    markdown += f"- **Merged:** Yes\n"
                    if pr.get('merged_at'):
                        markdown += f"- **Merged At:** {_format_timestamp(pr['merged_at'])}\n"
                
                markdown += f"- **URL:** {pr['html_url']}\n\n"
                
                if pr.get('body'):
                    body_preview = pr['body'][:200] + "..." if len(pr['body']) > 200 else pr['body']
                    markdown += f"**Preview:** {body_preview}\n\n"
                
                markdown += "---\n\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_get_user_info",
    annotations={
        "title": "Get User Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_user_info(params: GetUserInfoInput) -> str:
    """
    Retrieve information about a GitHub user or organization.
    
    Fetches profile information including bio, location, public repos,
    followers, and activity statistics.
    
    Args:
        params (GetUserInfoInput): Validated input parameters containing:
            - username (str): GitHub username
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: User profile information in requested format
    
    Examples:
        - Use when: "Get info about user torvalds"
        - Use when: "Show me the profile for facebook organization"
        - Use when: "Look up GitHub user details"
    
    Error Handling:
        - Returns error if user not found (404)
        - Handles both users and organizations
        - Returns appropriate data for account type
    """
    try:
        data = await _make_github_request(
            f"users/{params.username}",
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result)
        
        # Markdown format
        markdown = f"# {data['name'] or data['login']}\n\n"
        
        if data.get('bio'):
            markdown += f"**Bio:** {data['bio']}\n\n"
        
        markdown += f"**Username:** @{data['login']}\n"
        markdown += f"**Type:** {data['type']}\n"
        
        if data.get('company'):
            markdown += f"**Company:** {data['company']}\n"
        
        if data.get('location'):
            markdown += f"**Location:** {data['location']}\n"
        
        if data.get('email'):
            markdown += f"**Email:** {data['email']}\n"
        
        if data.get('blog'):
            markdown += f"**Website:** {data['blog']}\n"
        
        if data.get('twitter_username'):
            markdown += f"**Twitter:** @{data['twitter_username']}\n"
        
        markdown += f"\n## Statistics\n"
        markdown += f"- 📦 **Public Repos:** {data['public_repos']:,}\n"
        markdown += f"- 👥 **Followers:** {data['followers']:,}\n"
        markdown += f"- 👤 **Following:** {data['following']:,}\n"
        
        if data.get('public_gists') is not None:
            markdown += f"- 📝 **Public Gists:** {data['public_gists']:,}\n"
        
        markdown += f"\n**Joined:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"**Last Updated:** {_format_timestamp(data['updated_at'])}\n"
        markdown += f"**Profile URL:** {data['html_url']}\n"
        
        return _truncate_response(markdown)
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_list_repo_contents",
    annotations={
        "title": "List Repository Contents",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_repo_contents(params: ListRepoContentsInput) -> str:
    """
    List files and directories in a repository path.
    
    Browse repository structure by listing contents of directories.
    Returns file/folder names, types, sizes, and paths.
    
    Args:
        params (ListRepoContentsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - path (str): Directory path (empty string for root)
            - ref (Optional[str]): Branch, tag, or commit
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Directory listing with file/folder information
    
    Examples:
        - Use when: "List files in the src directory"
        - Use when: "Show me what's in the root of the repo"
        - Use when: "Browse the docs folder"
    
    Error Handling:
        - Returns error if path doesn't exist (404)
        - Handles both files and directories
        - Indicates if path points to a file vs directory
    """
    try:
        params_dict = {}
        if params.ref:
            params_dict["ref"] = params.ref
        
        path = params.path.strip('/') if params.path else ''
        endpoint = f"repos/{params.owner}/{params.repo}/contents/{path}"
        
        data = await _make_github_request(
            endpoint,
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data) if isinstance(data, list) else 1)
        
        # Markdown format
        if isinstance(data, dict):
            # Single file returned
            return f"""# Single File

This path points to a file, not a directory.

**Name:** {data['name']}
**Path:** {data['path']}
**Size:** {data['size']:,} bytes
**Type:** {data['type']}
**URL:** {data['html_url']}

Use `github_get_file_content` to retrieve the file content.
"""
        
        # Directory listing
        display_path = path or "(root)"
        markdown = f"# Contents of /{display_path}\n\n"
        markdown += f"**Repository:** {params.owner}/{params.repo}\n"
        if params.ref:
            markdown += f"**Branch/Ref:** {params.ref}\n"
        markdown += f"**Items:** {len(data)}\n\n"
        
        # Separate directories and files
        directories = [item for item in data if item['type'] == 'dir']
        files = [item for item in data if item['type'] == 'file']
        
        if directories:
            markdown += "## 📁 Directories\n"
            for item in directories:
                markdown += f"- `{item['name']}/`\n"
            markdown += "\n"
        
        if files:
            markdown += "## 📄 Files\n"
            for item in files:
                size_kb = item['size'] / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb >= 1 else f"{item['size']} bytes"
                markdown += f"- `{item['name']}` ({size_str})\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_list_workflows",
    annotations={
        "title": "List GitHub Actions Workflows",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/workflows",
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, data['total_count'])
        
        # Markdown format
        markdown = f"# GitHub Actions Workflows for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Workflows:** {data['total_count']}\n\n"
        
        if not data['workflows']:
            markdown += "No workflows found in this repository.\n"
        else:
            for workflow in data['workflows']:
                markdown += f"## {workflow['name']}\n"
                markdown += f"- **ID:** {workflow['id']}\n"
                markdown += f"- **State:** {workflow['state']}\n"
                markdown += f"- **Created:** {_format_timestamp(workflow['created_at'])}\n"
                markdown += f"- **Updated:** {_format_timestamp(workflow['updated_at'])}\n"
                markdown += f"- **Path:** `{workflow['path']}`\n"
                markdown += f"- **URL:** {workflow['html_url']}\n\n"
                
                if workflow.get('badge_url'):
                    markdown += f"- **Badge:** ![Workflow Status]({workflow['badge_url']})\n\n"
                
                markdown += "---\n\n"
        
        return _truncate_response(markdown, data['total_count'])
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_get_workflow_runs",
    annotations={
        "title": "Get GitHub Actions Workflow Runs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
        params_dict = {
            "per_page": params.limit,
            "page": params.page
        }
        
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
            endpoint,
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, data['total_count'])
        
        # Markdown format
        workflow_name = params.workflow_id or "All Workflows"
        markdown = f"# Workflow Runs for {params.owner}/{params.repo}\n\n"
        markdown += f"**Workflow:** {workflow_name}\n"
        markdown += f"**Total Runs:** {data['total_count']:,}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(data['workflow_runs'])} runs\n\n"
        
        if not data['workflow_runs']:
            markdown += "No workflow runs found matching your criteria.\n"
        else:
            for run in data['workflow_runs']:
                # Status emoji
                status_emoji = "🔄" if run['status'] == "in_progress" else "✅" if run['conclusion'] == "success" else "❌" if run['conclusion'] == "failure" else "⏸️" if run['status'] == "queued" else "⚠️"
                
                markdown += f"## {status_emoji} Run #{run['run_number']}: {run['name']}\n"
                markdown += f"- **Status:** {run['status']}\n"
                markdown += f"- **Conclusion:** {run['conclusion'] or 'N/A'}\n"
                markdown += f"- **Triggered By:** {run['triggering_actor']['login']}\n"
                markdown += f"- **Branch:** `{run['head_branch']}`\n"
                markdown += f"- **Commit:** {run['head_sha'][:8]}\n"
                markdown += f"- **Created:** {_format_timestamp(run['created_at'])}\n"
                markdown += f"- **Updated:** {_format_timestamp(run['updated_at'])}\n"
                
                if run.get('run_started_at'):
                    markdown += f"- **Started:** {_format_timestamp(run['run_started_at'])}\n"
                
                if run.get('jobs_url'):
                    markdown += f"- **Jobs:** {run['jobs_url']}\n"
                
                markdown += f"- **URL:** {run['html_url']}\n\n"
                
                # Show workflow info
                if run.get('workflow_id'):
                    markdown += f"- **Workflow ID:** {run['workflow_id']}\n"
                
                markdown += "---\n\n"
        
        return _truncate_response(markdown, data['total_count'])
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_create_pull_request",
    annotations={
        "title": "Create Pull Request",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_create_pull_request(params: CreatePullRequestInput) -> str:
    """
    Create a new pull request in a GitHub repository.
    
    Creates a pull request from a source branch to a target branch with optional
    draft status, description, and maintainer modification permissions.
    
    Args:
        params (CreatePullRequestInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - title (str): Pull request title (required)
            - head (str): Source branch name (required)
            - base (str): Target branch name (required)
            - body (Optional[str]): PR description in Markdown
            - draft (bool): Create as draft PR (default: False)
            - maintainer_can_modify (bool): Allow maintainer modifications (default: True)
            - token (Optional[str]): GitHub token (optional - uses GITHUB_TOKEN env var if not provided)
    
    Returns:
        str: Created pull request details including number and URL
    
    Examples:
        - Use when: "Create a PR from feature-branch to main"
        - Use when: "Open a draft PR for review"
        - Use when: "Create a pull request for this feature"
    
    Error Handling:
        - Returns error if branches don't exist
        - Returns error if authentication fails
        - Returns error if insufficient permissions
        - Validates branch names and repository access
    """
    import os
    
    # Get token from parameter or environment
    auth_token = params.token or os.getenv("GITHUB_TOKEN")
    
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for creating pull requests. Set GITHUB_TOKEN environment variable or pass token parameter.",
            "success": False
        }, indent=2)
    
    try:
        payload = {
            "title": params.title,
            "head": params.head,
            "base": params.base,
            "draft": params.draft,
            "maintainer_can_modify": params.maintainer_can_modify
        }
        
        if params.body:
            payload["body"] = params.body
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls",
            method="POST",
            token=auth_token,
            json=payload
        )
        
        # Status emoji based on draft status
        status_emoji = "📝" if params.draft else "🔀"
        
        result = f"""✅ Pull Request Created Successfully!

{status_emoji} **PR:** #{data['number']} - {data['title']}
**State:** {data['state']}
**Draft:** {'Yes' if data['draft'] else 'No'}
**Base:** `{data['base']['ref']}` ← **Head:** `{data['head']['ref']}`
**URL:** {data['html_url']}
**Created:** {_format_timestamp(data['created_at'])}
**Author:** @{data['user']['login']}

"""
        
        if data.get('body'):
            body_preview = data['body'][:200] + "..." if len(data['body']) > 200 else data['body']
            result += f"**Description:** {body_preview}\n\n"
        
        result += f"**Mergeable:** {data.get('mergeable', 'Unknown')}\n"
        result += f"**Maintainer Can Modify:** {'Yes' if data.get('maintainer_can_modify') else 'No'}\n"
        
        return result
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_get_pr_details",
    annotations={
        "title": "Get Pull Request Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_pr_details(params: GetPullRequestDetailsInput) -> str:
    """
    Get comprehensive details about a specific pull request.
    
    Retrieves detailed information including reviews, commits, status checks,
    and optionally changed files. Essential for PR review workflows.
    
    Args:
        params (GetPullRequestDetailsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pull_number (int): Pull request number
            - include_reviews (bool): Include review information (default: True)
            - include_commits (bool): Include commit information (default: True)
            - include_files (bool): Include changed files (default: False)
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Comprehensive PR details with reviews, commits, and status
    
    Examples:
        - Use when: "Show me details for PR #42"
        - Use when: "What's blocking PR #123?"
        - Use when: "Get review status for this pull request"
        - Use when: "Show me all commits in PR #456"
    
    Error Handling:
        - Returns error if PR not found (404)
        - Handles private repository access requirements
        - Provides clear status for merge conflicts and checks
    """
    try:
        # Get PR details
        pr_data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}",
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = {"pr": pr_data}
            
            # Add additional data if requested
            if params.include_reviews:
                try:
                    reviews = await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/reviews",
                        token=params.token
                    )
                    result["reviews"] = reviews
                except:
                    result["reviews"] = "Error fetching reviews"
            
            if params.include_commits:
                try:
                    commits = await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/commits",
                        token=params.token
                    )
                    result["commits"] = commits
                except:
                    result["commits"] = "Error fetching commits"
            
            if params.include_files:
                try:
                    files = await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/files",
                        token=params.token
                    )
                    result["files"] = files
                except:
                    result["files"] = "Error fetching files"
            
            return json.dumps(result, indent=2)
        
        # Markdown format
        status_emoji = "🔀" if not pr_data['draft'] else "📝"
        merge_emoji = "✅" if pr_data.get('mergeable') else "❌" if pr_data.get('mergeable') is False else "⏳"
        
        markdown = f"""# {status_emoji} Pull Request #{pr_data['number']}: {pr_data['title']}

**State:** {pr_data['state']} | **Draft:** {'Yes' if pr_data['draft'] else 'No'}
**Base:** `{pr_data['base']['ref']}` ← **Head:** `{pr_data['head']['ref']}`
**Mergeable:** {merge_emoji} {pr_data.get('mergeable', 'Unknown')}
**Created:** {_format_timestamp(pr_data['created_at'])}
**Updated:** {_format_timestamp(pr_data['updated_at'])}
**Author:** @{pr_data['user']['login']}
**URL:** {pr_data['html_url']}

"""
        
        if pr_data.get('body'):
            body_preview = pr_data['body'][:300] + "..." if len(pr_data['body']) > 300 else pr_data['body']
            markdown += f"## Description\n\n{body_preview}\n\n"
        
        # Additions/Deletions
        markdown += f"## Changes\n"
        markdown += f"- **Additions:** +{pr_data['additions']:,} lines\n"
        markdown += f"- **Deletions:** -{pr_data['deletions']:,} lines\n"
        markdown += f"- **Changed Files:** {pr_data['changed_files']:,}\n\n"
        
        # Reviews section
        if params.include_reviews:
            try:
                reviews = await _make_github_request(
                    f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/reviews",
                    token=params.token
                )
                
                markdown += f"## Reviews ({len(reviews)})\n\n"
                
                if not reviews:
                    markdown += "No reviews yet.\n\n"
                else:
                    for review in reviews:
                        review_emoji = "✅" if review['state'] == "APPROVED" else "❌" if review['state'] == "CHANGES_REQUESTED" else "💬"
                        markdown += f"- {review_emoji} **@{review['user']['login']}** - {review['state']}\n"
                        if review.get('body'):
                            body_preview = review['body'][:100] + "..." if len(review['body']) > 100 else review['body']
                            markdown += f"  _{body_preview}_\n"
                        markdown += f"  _{_format_timestamp(review['submitted_at'])}_\n\n"
            except:
                markdown += "## Reviews\n\nError fetching reviews.\n\n"
        
        # Commits section
        if params.include_commits:
            try:
                commits = await _make_github_request(
                    f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/commits",
                    token=params.token
                )
                
                markdown += f"## Commits ({len(commits)})\n\n"
                
                for commit in commits[:10]:  # Limit to first 10 commits
                    commit_msg = commit['commit']['message'].split('\n')[0]  # First line only
                    markdown += f"- **{commit['sha'][:8]}** - {commit_msg}\n"
                    markdown += f"  _by @{commit['author']['login']} on {_format_timestamp(commit['commit']['author']['date'])}_\n"
                
                if len(commits) > 10:
                    markdown += f"\n... and {len(commits) - 10} more commits\n"
                
                markdown += "\n"
            except:
                markdown += "## Commits\n\nError fetching commits.\n\n"
        
        # Files section (optional, can be large)
        if params.include_files:
            try:
                files = await _make_github_request(
                    f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/files",
                    token=params.token
                )
                
                markdown += f"## Changed Files ({len(files)})\n\n"
                
                for file in files[:20]:  # Limit to first 20 files
                    status_icon = "📝" if file['status'] == "modified" else "➕" if file['status'] == "added" else "➖" if file['status'] == "removed" else "🔄"
                    markdown += f"- {status_icon} `{file['filename']}` (+{file['additions']}, -{file['deletions']})\n"
                
                if len(files) > 20:
                    markdown += f"\n... and {len(files) - 20} more files\n"
                
                markdown += "\n"
            except:
                markdown += "## Changed Files\n\nError fetching files.\n\n"
        
        return _truncate_response(markdown)
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_search_code",
    annotations={
        "title": "Search Code Across GitHub",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_search_code(params: SearchCodeInput) -> str:
    """
    Search for code snippets across GitHub repositories.
    
    Powerful code search with language filtering, repository targeting, and
    advanced qualifiers. Essential for finding patterns, TODOs, and specific functions.
    
    Args:
        params (SearchCodeInput): Validated input parameters containing:
            - query (str): Code search query with optional qualifiers
            - sort (Optional[str]): Sort by 'indexed' (default)
            - order (SortOrder): Sort order ('asc' or 'desc')
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Code search results with file locations and context
    
    Examples:
        - Use when: "Find all TODOs in Python repositories"
          query="TODO language:python"
        - Use when: "Search for authentication functions"
          query="function authenticate"
        - Use when: "Find security vulnerabilities"
          query="password language:javascript"
        - Use when: "Find API endpoints in specific repo"
          query="@RequestMapping repo:spring-projects/spring-framework"
    
    Query Qualifiers:
        - language:python - Code in Python
        - repo:owner/repo - Search specific repository
        - user:username - Search user's repositories
        - org:organization - Search organization's repositories
        - path:src/main - Search specific path
        - extension:js - Files with specific extension
        - size:>1000 - Files larger than 1000 bytes
    
    Error Handling:
        - Returns error if query syntax is invalid
        - Handles rate limiting for search API
        - Provides clear guidance for complex queries
    """
    try:
        params_dict = {
            "q": params.query,
            "per_page": params.limit,
            "page": params.page,
            "order": params.order.value
        }
        
        if params.sort:
            params_dict["sort"] = params.sort
        
        data = await _make_github_request(
            "search/code",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, data['total_count'])
        
        # Markdown format
        markdown = f"# Code Search Results\n\n"
        markdown += f"**Query:** `{params.query}`\n"
        markdown += f"**Total Results:** {data['total_count']:,}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(data['items'])} files\n\n"
        
        if not data['items']:
            markdown += "No code found matching your query.\n"
        else:
            for item in data['items']:
                # Extract repository info
                repo_name = item['repository']['full_name']
                file_path = item['path']
                file_name = file_path.split('/')[-1]
                
                markdown += f"## 📄 {file_name}\n"
                markdown += f"**Repository:** [{repo_name}]({item['repository']['html_url']})\n"
                markdown += f"**Path:** `{file_path}`\n"
                markdown += f"**Language:** {item.get('language', 'Unknown')}\n"
                markdown += f"**Size:** {item['size']:,} bytes\n"
                markdown += f"**URL:** [{item['html_url']}]({item['html_url']})\n\n"
                
                # Show code snippets if available
                if 'text_matches' in item and item['text_matches']:
                    markdown += "**Code Snippets:**\n"
                    for match in item['text_matches'][:3]:  # Limit to first 3 matches
                        if match.get('fragment'):
                            # Clean up the fragment
                            fragment = match['fragment'].replace('\n', ' ').strip()
                            if len(fragment) > 200:
                                fragment = fragment[:200] + "..."
                            markdown += f"```\n{fragment}\n```\n"
                    markdown += "\n"
                
                markdown += "---\n\n"
        
        return _truncate_response(markdown, data['total_count'])
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_search_issues",
    annotations={
        "title": "Search Issues Across GitHub",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_search_issues(params: SearchIssuesInput) -> str:
    """
    Search for issues across GitHub repositories with advanced filtering.
    
    Powerful issue search with state, label, author, and repository filtering.
    Essential for finding specific problems, feature requests, and security issues.
    
    Args:
        params (SearchIssuesInput): Validated input parameters containing:
            - query (str): Issue search query with optional qualifiers
            - sort (Optional[str]): Sort by 'created', 'updated', 'comments'
            - order (SortOrder): Sort order ('asc' or 'desc')
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Issue search results with details and pagination info
    
    Examples:
        - Use when: "Find security issues in Python projects"
          query="security language:python"
        - Use when: "Search for bug reports"
          query="bug label:bug"
        - Use when: "Find feature requests in specific repo"
          query="feature request repo:microsoft/vscode"
        - Use when: "Find issues by specific user"
          query="author:torvalds"
    
    Query Qualifiers:
        - state:open - Open issues only
        - state:closed - Closed issues only
        - label:bug - Issues with specific label
        - author:username - Issues by specific author
        - assignee:username - Issues assigned to user
        - repo:owner/repo - Issues in specific repository
        - user:username - Issues in user's repositories
        - org:organization - Issues in organization's repositories
        - language:python - Issues in Python repositories
        - created:>2023-01-01 - Issues created after date
        - updated:>2023-01-01 - Issues updated after date
        - comments:>10 - Issues with more than 10 comments
        - in:title - Search in issue titles only
        - in:body - Search in issue bodies only
    
    Error Handling:
        - Returns error if query syntax is invalid
        - Handles rate limiting for search API
        - Provides clear guidance for complex queries
    """
    try:
        params_dict = {
            "q": params.query,
            "per_page": params.limit,
            "page": params.page,
            "order": params.order.value
        }
        
        if params.sort:
            params_dict["sort"] = params.sort
        
        data = await _make_github_request(
            "search/issues",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, data['total_count'])
        
        # Markdown format
        markdown = f"# Issue Search Results\n\n"
        markdown += f"**Query:** `{params.query}`\n"
        markdown += f"**Total Results:** {data['total_count']:,}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(data['items'])} issues\n\n"
        
        if not data['items']:
            markdown += "No issues found matching your query.\n"
        else:
            for issue in data['items']:
                # Status emoji
                status_emoji = "🟢" if issue['state'] == "open" else "🔴"
                
                markdown += f"## {status_emoji} #{issue['number']}: {issue['title']}\n"
                markdown += f"**Repository:** [{issue['repository_url'].split('/')[-2]}/{issue['repository_url'].split('/')[-1]}]({issue['html_url']})\n"
                markdown += f"**State:** {issue['state']}\n"
                markdown += f"**Author:** @{issue['user']['login']}\n"
                markdown += f"**Created:** {_format_timestamp(issue['created_at'])}\n"
                markdown += f"**Updated:** {_format_timestamp(issue['updated_at'])}\n"
                
                if issue.get('closed_at'):
                    markdown += f"**Closed:** {_format_timestamp(issue['closed_at'])}\n"
                
                if issue.get('labels'):
                    labels = ', '.join([f"`{l['name']}`" for l in issue['labels'][:5]])
                    markdown += f"**Labels:** {labels}\n"
                
                if issue.get('assignees'):
                    assignees = ', '.join([f"@{a['login']}" for a in issue['assignees']])
                    markdown += f"**Assignees:** {assignees}\n"
                
                markdown += f"**Comments:** {issue['comments']}\n"
                markdown += f"**URL:** {issue['html_url']}\n\n"
                
                if issue.get('body'):
                    body_preview = issue['body'][:300] + "..." if len(issue['body']) > 300 else issue['body']
                    markdown += f"**Description:** {body_preview}\n\n"
                
                markdown += "---\n\n"
        
        return _truncate_response(markdown, data['total_count'])
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_list_releases",
    annotations={
        "title": "List Repository Releases",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_releases(params: ListReleasesInput) -> str:
    """
    List all releases from a GitHub repository.
    """
    try:
        params_dict = {
            "per_page": params.limit,
            "page": params.page
        }
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/releases",
            token=params.token,
            params=params_dict
        )
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))
        markdown = f"# Releases for {params.owner}/{params.repo}\n\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(data)} releases\n\n"
        if not data:
            markdown += "No releases found.\n"
        else:
            for release in data:
                status = []
                if release.get('draft'):
                    status.append("🚧 Draft")
                if release.get('prerelease'):
                    status.append("🔬 Pre-release")
                status_str = " | ".join(status) if status else "📦 Release"
                markdown += f"## {release['name'] or release['tag_name']} {status_str}\n\n"
                markdown += f"- **Tag:** `{release['tag_name']}`\n"
                markdown += f"- **Published:** {_format_timestamp(release['published_at']) if release.get('published_at') else 'Draft'}\n"
                markdown += f"- **Author:** {release['author']['login']}\n"
                asset_count = len(release.get('assets', []))
                if asset_count > 0:
                    markdown += f"- **Assets:** {asset_count} file(s)\n"
                if release.get('assets'):
                    total_downloads = sum(asset.get('download_count', 0) for asset in release['assets'])
                    if total_downloads > 0:
                        markdown += f"- **Downloads:** {total_downloads:,}\n"
                markdown += f"- **URL:** {release['html_url']}\n\n"
                if release.get('body'):
                    body_preview = release['body'][:300]
                    if len(release['body']) > 300:
                        body_preview += "..."
                    markdown += f"{body_preview}\n\n"
                markdown += "---\n\n"
            if len(data) == params.limit:
                markdown += f"*Showing page {params.page}. Use `page: {params.page + 1}` to see more.*\n"
        return _truncate_response(markdown, len(data))
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_get_release",
    annotations={
        "title": "Get Release Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_release(params: GetReleaseInput) -> str:
    """
    Get detailed information about a specific release or the latest release.
    """
    try:
        if params.tag == "latest":
            endpoint = f"repos/{params.owner}/{params.repo}/releases/latest"
        else:
            endpoint = f"repos/{params.owner}/{params.repo}/releases/tags/{params.tag}"
        data = await _make_github_request(
            endpoint,
            token=params.token
        )
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result)
        status = []
        if data.get('draft'):
            status.append("🚧 Draft")
        if data.get('prerelease'):
            status.append("🔬 Pre-release")
        status_str = " | ".join(status) if status else "📦 Release"
        markdown = f"# {data['name'] or data['tag_name']}\n\n"
        markdown += f"**Status:** {status_str}\n\n"
        markdown += "## Release Information\n\n"
        markdown += f"- **Tag:** `{data['tag_name']}`\n"
        markdown += f"- **Published:** {_format_timestamp(data['published_at']) if data.get('published_at') else 'Draft (not published)'}\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **Author:** {data['author']['login']}\n"
        markdown += f"- **URL:** {data['html_url']}\n\n"
        if data.get('assets'):
            markdown += "## Assets\n\n"
            total_downloads = 0
            for asset in data['assets']:
                downloads = asset.get('download_count', 0)
                total_downloads += downloads
                size_mb = asset['size'] / (1024 * 1024)
                markdown += f"- **{asset['name']}**\n"
                markdown += f"  - Size: {size_mb:.2f} MB\n"
                markdown += f"  - Downloads: {downloads:,}\n"
                markdown += f"  - [Download]({asset['browser_download_url']})\n\n"
            markdown += f"**Total Downloads:** {total_downloads:,}\n\n"
        if data.get('body'):
            markdown += "## Release Notes\n\n"
            markdown += data['body']
            markdown += "\n\n"
        if data.get('target_commitish'):
            markdown += f"**Target:** `{data['target_commitish']}`\n"
        return _truncate_response(markdown)
    except Exception as e:
        return _handle_api_error(e)

# Entry point
if __name__ == "__main__":
    mcp.run()