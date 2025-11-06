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
- Pull request operations (list, create, detailed view, merge, review)
- GitHub Actions workflow monitoring
- Advanced search (code and issues across GitHub)
- File content retrieval
- **File management (create, update, delete files, batch operations)**
- **Commit history and tracking**
- Workflow advisor (suggest API vs local vs hybrid)
- Repository management (create, update, delete, transfer, archive)
- User and organization information
"""

from typing import Optional, List, Dict, Any
from enum import Enum
import json
import os
import httpx
from datetime import datetime
import base64
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP
from license_manager import check_license_on_startup, get_license_manager
from github_client import GhClient
from auth.github_app import get_installation_token_from_env
from graphql_client import GraphQLClient

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
    Reusable function for all GitHub API calls using a shared pooled client.

    Returns parsed JSON. For 304, returns a marker dict {"_from_cache": True}.
    """
    headers = kwargs.pop("headers", None)
    params = kwargs.pop("params", None)
    json_body = kwargs.pop("json", None)
    data_body = kwargs.pop("data", None)

    # If no token provided, optionally use GitHub App installation token when configured
    if token is None and os.getenv("GITHUB_AUTH_MODE", "pat").lower() == "app":
        app_token = await get_installation_token_from_env()
        if app_token:
            token = app_token

    client = GhClient.instance()
    response = await client.request(
        method=method,
        path=f"/{endpoint}",
        token=token,
        params=params,
        headers=headers,
        json=json_body,
        data=data_body,
    )
    # Raise for non-2xx (except we allow 304 to fall through as cache marker)
    if response.status_code == 304:
        return {"_from_cache": True}
    response.raise_for_status()
    # Some endpoints (DELETE) may return empty body
    if response.content is None or len(response.content) == 0:
        return {"success": True}
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
        # Avoid echoing full response text to prevent leaking sensitive data
        safe_excerpt = ""
        try:
            txt = e.response.text or ""
            safe_excerpt = (txt[:200] + "...") if len(txt) > 200 else txt
        except Exception:
            safe_excerpt = ""

        if status_code == 401:
            return (
                "Error: Authentication required. Provide a valid token.\n"
                "Hint: Set GITHUB_TOKEN or enable GitHub App auth (GITHUB_APP_ID, PRIVATE_KEY, INSTALLATION_ID)."
            )
        if status_code == 403:
            return (
                "Error: Permission denied.\n"
                "Hint: Check token scopes/installation permissions. Common needs: contents:write for file ops; pull_requests:write for PR ops."
            )
        if status_code == 404:
            return (
                "Error: Resource not found.\n"
                "Hint: Verify owner/repo/number and token access to private repos."
            )
        if status_code == 409:
            return (
                "Error: Conflict.\n"
                "Hint: For file updates, ensure SHA matches current head; for merges, resolve conflicts first."
            )
        if status_code == 422:
            return (
                "Error: Validation failed.\n"
                "Hint: Check required fields and enum values; see API docs for this endpoint."
            )
        if status_code == 429:
            retry_after = e.response.headers.get("Retry-After")
            retry_hint = f"retry after {retry_after}s" if retry_after else "retry later"
            return f"Error: Rate limit exceeded, {retry_hint}. Consider enabling conditional requests and backoff."
        if 500 <= status_code < 600:
            return "Error: GitHub service error. Hint: Retry shortly (transient)."
        return f"Error: GitHub API request failed with status {status_code}. {safe_excerpt}"
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
    labels: Optional[List[str]] = Field(default=None, description="List of label names to apply", max_length=20)
    assignees: Optional[List[str]] = Field(default=None, description="List of usernames to assign", max_length=10)
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

class ListCommitsInput(BaseModel):
    """Input model for listing repository commits."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    sha: Optional[str] = Field(default=None, description="Branch name, tag, or commit SHA (defaults to default branch)")
    path: Optional[str] = Field(default=None, description="Only commits containing this file path")
    author: Optional[str] = Field(default=None, description="Filter by commit author (username or email)")
    since: Optional[str] = Field(default=None, description="Only commits after this date (ISO 8601 format)")
    until: Optional[str] = Field(default=None, description="Only commits before this date (ISO 8601 format)")
    limit: Optional[int] = Field(default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100)
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

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

class GraphQLPROverviewInput(BaseModel):
    """Input for GraphQL PR overview query (batch read)."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')

    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    pull_number: int = Field(..., description="Pull request number", ge=1)
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

class CreateReleaseInput(BaseModel):
    """Input model for creating GitHub releases."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    tag_name: str = Field(..., description="Git tag name for the release (e.g., 'v1.2.0')", min_length=1, max_length=100)
    name: Optional[str] = Field(default=None, description="Release title (defaults to tag_name if not provided)")
    body: Optional[str] = Field(default=None, description="Release notes/description in Markdown format")
    draft: Optional[bool] = Field(default=False, description="Create as draft release (not visible publicly)")
    prerelease: Optional[bool] = Field(default=False, description="Mark as pre-release (not production ready)")
    target_commitish: Optional[str] = Field(default=None, description="Commit SHA, branch, or tag to create release from (defaults to default branch)")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")

class UpdateReleaseInput(BaseModel):
    """Input model for updating GitHub releases."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    release_id: str = Field(..., description="Release ID or tag name (e.g., 'v1.2.0')")
    tag_name: Optional[str] = Field(default=None, description="New tag name (use carefully!)")
    name: Optional[str] = Field(default=None, description="New release title")
    body: Optional[str] = Field(default=None, description="New release notes/description in Markdown format")
    draft: Optional[bool] = Field(default=None, description="Set draft status")
    prerelease: Optional[bool] = Field(default=None, description="Set pre-release status")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")

# Workflow Optimization Model
class WorkflowSuggestionInput(BaseModel):
    """Input model for workflow optimization suggestions."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    operation: str = Field(..., description="Operation type (e.g., 'update_readme', 'create_release', 'multiple_file_edits')", min_length=1, max_length=200)
    file_size: Optional[int] = Field(default=None, description="Estimated file size in bytes", ge=0)
    num_edits: Optional[int] = Field(default=1, description="Number of separate edit operations", ge=1)
    file_count: Optional[int] = Field(default=1, description="Number of files being modified", ge=1)
    description: Optional[str] = Field(default=None, description="Additional context about the task")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

# Phase 2.2: Repository Management Models

class CreateRepositoryInput(BaseModel):
    """Input model for creating repositories (user or org)."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    owner: Optional[str] = Field(default=None, description="Organization owner (if creating in an org); omit for user repo")
    name: str = Field(..., description="Repository name", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="Repository description")
    private: Optional[bool] = Field(default=False, description="Create as private repository")
    auto_init: Optional[bool] = Field(default=True, description="Initialize with README")
    gitignore_template: Optional[str] = Field(default=None, description="Gitignore template name (e.g., 'Python')")
    license_template: Optional[str] = Field(default=None, description="License template (e.g., 'mit')")
    token: Optional[str] = Field(default=None, description="GitHub personal access token")

class PRReviewComment(BaseModel):
    """Single review comment on a PR."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    path: str = Field(..., description="File path in the PR", min_length=1, max_length=500)
    position: Optional[int] = Field(default=None, description="Line position in the diff (deprecated, use line)")
    line: Optional[int] = Field(default=None, description="Line number in the file")
    side: Optional[str] = Field(default="RIGHT", description="Side of diff: 'LEFT' (old) or 'RIGHT' (new)")
    body: str = Field(..., description="Comment text in Markdown", min_length=1, max_length=65536)
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        if v not in ['LEFT', 'RIGHT']:
            raise ValueError("side must be 'LEFT' or 'RIGHT'")
        return v

class CreatePRReviewInput(BaseModel):
    """Input model for creating pull request reviews."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    pull_number: int = Field(..., description="Pull request number", ge=1)
    event: str = Field(default="COMMENT", description="Review action: 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'")
    body: Optional[str] = Field(default=None, description="General review comment (Markdown)")
    comments: Optional[List[PRReviewComment]] = Field(default=None, description="Line-specific comments", max_length=100)
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")
    
    @field_validator('event')
    @classmethod
    def validate_event(cls, v):
        if v not in ['APPROVE', 'REQUEST_CHANGES', 'COMMENT']:
            raise ValueError("event must be 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'")
        return v
    
    @field_validator('body')
    @classmethod
    def validate_body(cls, v, info):
        event = info.data.get('event')
        comments = info.data.get('comments')
        if event in ['APPROVE', 'REQUEST_CHANGES']:
            if not v and not comments:
                raise ValueError(f"{event} requires either body or comments")
        return v

class DeleteRepositoryInput(BaseModel):
    """Input model for deleting a repository."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    token: Optional[str] = Field(default=None, description="GitHub personal access token")

class UpdateRepositoryInput(BaseModel):
    """Input model for updating repository settings."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    name: Optional[str] = Field(default=None, description="New repository name")
    description: Optional[str] = Field(default=None, description="New description")
    homepage: Optional[str] = Field(default=None, description="Homepage URL")
    private: Optional[bool] = Field(default=None, description="Set repository visibility")
    has_issues: Optional[bool] = Field(default=None, description="Enable issues")
    has_projects: Optional[bool] = Field(default=None, description="Enable projects")
    has_wiki: Optional[bool] = Field(default=None, description="Enable wiki")
    default_branch: Optional[str] = Field(default=None, description="Set default branch")
    archived: Optional[bool] = Field(default=None, description="Archive/unarchive repository")
    token: Optional[str] = Field(default=None, description="GitHub personal access token")

class TransferRepositoryInput(BaseModel):
    """Input model for transferring repository ownership."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    owner: str = Field(..., description="Current repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    new_owner: str = Field(..., description="New owner (user or org)", min_length=1, max_length=100)
    team_ids: Optional[List[int]] = Field(default=None, description="IDs of teams to add to the repository (org only)")
    token: Optional[str] = Field(default=None, description="GitHub personal access token")

class ArchiveRepositoryInput(BaseModel):
    """Input model for archiving or unarchiving repositories."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    archived: bool = Field(..., description="True to archive, False to unarchive")
    token: Optional[str] = Field(default=None, description="GitHub personal access token")

class MergePullRequestInput(BaseModel):
    """Input model for merging pull requests."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    pull_number: int = Field(..., description="Pull request number", ge=1)
    merge_method: Optional[str] = Field(default="squash", description="Merge method: 'merge', 'squash', or 'rebase'")
    commit_title: Optional[str] = Field(default=None, description="Custom commit title for merge commit")
    commit_message: Optional[str] = Field(default=None, description="Custom commit message for merge commit")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")
# Phase 2.1: File Management Models


class CreateFileInput(BaseModel):
    """Input model for creating files in a repository."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(..., description="File path (e.g., 'docs/README.md', 'src/main.py')", min_length=1, max_length=500)
    content: str = Field(..., description="File content (will be base64 encoded automatically)")
    message: str = Field(..., description="Commit message", min_length=1, max_length=500)
    branch: Optional[str] = Field(default=None, description="Branch name (defaults to repository's default branch)")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class UpdateFileInput(BaseModel):
    """Input model for updating files in a repository."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(..., description="File path to update", min_length=1, max_length=500)
    content: str = Field(..., description="New file content")
    message: str = Field(..., description="Commit message", min_length=1, max_length=500)
    sha: str = Field(..., description="SHA of the file being replaced (get from github_get_file_content)")
    branch: Optional[str] = Field(default=None, description="Branch name (defaults to repository's default branch)")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class DeleteFileInput(BaseModel):
    """Input model for deleting files from a repository."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(..., description="File path to delete", min_length=1, max_length=500)
    message: str = Field(..., description="Commit message", min_length=1, max_length=500)
    sha: str = Field(..., description="SHA of the file being deleted (get from github_get_file_content)")
    branch: Optional[str] = Field(default=None, description="Branch name (defaults to repository's default branch)")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")

class FileOperation(BaseModel):
    """Single file operation within a batch."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    operation: str = Field(..., description="Operation type: 'create', 'update', or 'delete'")
    path: str = Field(..., description="File path in repository", min_length=1, max_length=500)
    content: Optional[str] = Field(default=None, description="File content (required for create/update)")
    sha: Optional[str] = Field(default=None, description="Current file SHA (required for update/delete)")
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v):
        if v not in ['create', 'update', 'delete']:
            raise ValueError("operation must be 'create', 'update', or 'delete'")
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v, info):
        operation = info.data.get('operation')
        if operation in ['create', 'update'] and not v:
            raise ValueError(f"content is required for {operation} operations")
        return v
    
    @field_validator('sha')
    @classmethod
    def validate_sha(cls, v, info):
        operation = info.data.get('operation')
        if operation in ['update', 'delete'] and not v:
            raise ValueError(f"sha is required for {operation} operations")
        return v

class BatchFileOperationsInput(BaseModel):
    """Input model for batch file operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    operations: List[FileOperation] = Field(..., description="List of file operations to perform", min_length=1, max_length=50)
    message: str = Field(..., description="Commit message for all operations", min_length=1, max_length=500)
    branch: Optional[str] = Field(default=None, description="Target branch (defaults to default branch)")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")

# Safe local file chunk reading
class ReadFileChunkInput(BaseModel):
    """Input model for reading a chunk of a local file (repo-root constrained)."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    path: str = Field(..., description="Relative path under the server's repository root", min_length=1, max_length=500)
    start_line: int = Field(default=1, description="1-based starting line number", ge=1)
    num_lines: int = Field(default=200, description="Number of lines to read (max 500)", ge=1, le=500)

# Tool Implementations

@mcp.tool(
    name="repo_read_file_chunk",
    annotations={
        "title": "Read Local File Chunk (Safe)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def repo_read_file_chunk(params: ReadFileChunkInput) -> str:
    """
    Read a specific range of lines from a local file under the server's repo root.

    Security:
    - Normalizes path
    - Denies parent traversal (..)
    - Enforces repo-root constraint
    - Caps lines read
    """
    try:
        base_dir = os.path.abspath(os.getcwd())
        norm_path = os.path.normpath(params.path)

        if norm_path.startswith("..") or os.path.isabs(norm_path):
            return "Error: Path traversal is not allowed."

        abs_path = os.path.abspath(os.path.join(base_dir, norm_path))
        if not abs_path.startswith(base_dir + os.sep) and abs_path != base_dir:
            return "Error: Access outside repository root is not allowed."

        if not os.path.exists(abs_path):
            return "Error: File does not exist."
        if os.path.isdir(abs_path):
            return "Error: Path is a directory."

        start = max(1, params.start_line)
        end = start + params.num_lines - 1

        lines: List[str] = []
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            for current_idx, line in enumerate(f, start=1):
                if current_idx < start:
                    continue
                if current_idx > end:
                    break
                lines.append(line.rstrip("\n"))

        header = f"# {norm_path}\n\nLines {start}-{end} (max {params.num_lines})\n\n"
        content = "\n".join(lines) if lines else "(no content in range)"
        return _truncate_response(header + "```\n" + content + "\n```")
    except Exception as e:
        return _handle_api_error(e)

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

@mcp.tool()
async def github_license_info() -> str:
    """
    Display current license information and status for the GitHub MCP Server.
    
    Returns:
        Formatted license information including tier, expiration, and status
    """
    license_manager = get_license_manager()
    license_info = await license_manager.verify_license()
    
    if license_info.get('valid'):
        tier = license_info.get('tier', 'free')
        tier_info = license_manager.get_tier_info(tier)
        
        response = f'''# GitHub MCP Server License


**Status:** ✅ Valid
**Tier:** {tier_info['name']}
**License Type:** {tier.upper()}
'''
        if tier != 'free':
            response += f'''
**Expires:** {license_info.get('expires_at', 'N/A').split('T')[0]}
**Max Developers:** {license_info.get('max_developers') or 'Unlimited'}
**Status:** {license_info.get('status', 'unknown').upper()}
'''
        else:
            response += '''
**License:** AGPL v3 (Open Source)
**Commercial Use:** Requires commercial license
**Purchase:** https://mcplabs.co.uk/pricing
**Contact:** licensing@mcplabs.co.uk
'''
        return response
    else:
        return f'''# License Verification Failed


**Error:** {license_info.get('error', 'Unknown')}
**Message:** {license_info.get('message', '')}


**Options:**
1. Get free AGPL license: https://github.com/crypto-ninja/github-mcp-server
2. Purchase commercial license: https://mcplabs.co.uk/pricing
3. Contact support: licensing@mcplabs.co.uk
'''

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
    name="github_list_commits",
    annotations={
        "title": "List Repository Commits",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_commits(params: ListCommitsInput) -> str:
    """
    List commits from a GitHub repository.
    
    Retrieves commit history with optional filtering by branch, author, path, and date range.
    Shows commit SHA, author, date, message, and statistics.
    
    Args:
        params (ListCommitsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - sha (Optional[str]): Branch, tag, or commit SHA
            - path (Optional[str]): File path filter
            - author (Optional[str]): Author filter
            - since (Optional[str]): Start date (ISO 8601)
            - until (Optional[str]): End date (ISO 8601)
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: List of commits with details
    
    Examples:
        - Use when: "Show me recent commits in the main branch"
        - Use when: "List commits by user octocat"
        - Use when: "Get commits that modified README.md"
    
    Error Handling:
        - Returns error if repository not found (404)
        - Returns error if branch/SHA doesn't exist (404)
        - Handles pagination for large histories
    """
    try:
        token = params.token or os.getenv("GITHUB_TOKEN")
        query_params = {
            "per_page": params.limit,
            "page": params.page
        }
        if params.sha:
            query_params["sha"] = params.sha
        if params.path:
            query_params["path"] = params.path
        if params.author:
            query_params["author"] = params.author
        if params.since:
            query_params["since"] = params.since
        if params.until:
            query_params["until"] = params.until
        
        commits = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/commits",
            token=token,
            params=query_params
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(commits, indent=2)
        
        response = f"# Commits for {params.owner}/{params.repo}\n\n"
        if params.sha:
            response += f"**Branch/SHA:** {params.sha}\n"
        if params.path:
            response += f"**Path:** {params.path}\n"
        if params.author:
            response += f"**Author:** {params.author}\n"
        if params.since or params.until:
            response += f"**Date Range:** {params.since or 'beginning'} to {params.until or 'now'}\n"
        
        response += f"\n**Page:** {params.page} | **Showing:** {len(commits)} commits\n\n"
        response += "---\n\n"
        
        for commit in commits:
            sha_short = commit['sha'][:7]
            author_name = commit['commit']['author']['name']
            author_email = commit['commit']['author']['email']
            date = _format_timestamp(commit['commit']['author']['date'])
            message_first = commit['commit']['message'].split('\n')[0]
            
            stats = ""
            if 'stats' in commit:
                additions = commit['stats'].get('additions', 0)
                deletions = commit['stats'].get('deletions', 0)
                stats = f" (+{additions}/-{deletions})"
            
            response += f"### {sha_short} - {message_first}{stats}\n\n"
            response += f"**Author:** {author_name} <{author_email}>  \n"
            response += f"**Date:** {date}  \n"
            response += f"**Full SHA:** `{commit['sha']}`  \n"
            
            if commit.get('parents'):
                parent_shas = [p['sha'][:7] for p in commit['parents']]
                response += f"**Parents:** {', '.join(parent_shas)}  \n"
            
            response += f"**URL:** {commit['html_url']}\n\n"
            
            full_message = commit['commit']['message']
            if '\n' in full_message:
                response += f"**Full message:**\n```\n{full_message}\n```\n\n"
            
            response += "---\n\n"
        
        if len(commits) == params.limit:
            response += f"\n*More commits may be available. Use `page={params.page + 1}` to see the next page.*\n"
        
        return _truncate_response(response, len(commits))
        
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
    name="github_get_pr_overview_graphql",
    annotations={
        "title": "Get PR Overview (GraphQL)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_pr_overview_graphql(params: GraphQLPROverviewInput) -> str:
    """
    Fetch PR title, author, review states, commits count, and files changed in one GraphQL query.
    """
    try:
        token = params.token or os.getenv("GITHUB_TOKEN")
        if token is None and os.getenv("GITHUB_AUTH_MODE", "pat").lower() == "app":
            app_token = await get_installation_token_from_env()
            if app_token:
                token = app_token
        if not token:
            return "Error: Authentication required for GraphQL. Set GITHUB_TOKEN or GitHub App env vars."

        gql = GraphQLClient()
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              number
              title
              author { login }
              state
              additions
              deletions
              changedFiles
              reviews(last: 20) { nodes { author { login } state submittedAt } }
              commits(last: 1) { totalCount }
              files(first: 20) { totalCount nodes { path additions deletions } }
              url
              createdAt
              merged
            }
          }
        }
        """
        variables = {"owner": params.owner, "repo": params.repo, "number": params.pull_number}
        data = await gql.query(token, query, variables)
        pr = (((data or {}).get("data") or {}).get("repository") or {}).get("pullRequest")
        if not pr:
            return "Error: PR not found."

        if params.response_format == ResponseFormat.JSON:
            return _truncate_response(json.dumps(pr, indent=2))

        md = [
            f"# PR #{pr['number']}: {pr['title']}",
            f"Author: @{pr['author']['login']} | State: {pr['state']}",
            f"Additions: +{pr['additions']} | Deletions: -{pr['deletions']} | Files: {pr['changedFiles']}",
            f"Commits: {pr['commits']['totalCount']} | URL: {pr['url']}",
            "",
            "## Recent Reviews",
        ]
        reviews = (pr.get("reviews") or {}).get("nodes") or []
        if not reviews:
            md.append("(no reviews)")
        else:
            for rv in reviews:
                md.append(f"- {rv['state']} by @{rv['author']['login']} at {rv.get('submittedAt','')} ")
        files = (pr.get("files") or {}).get("nodes") or []
        if files:
            md.append("\n## Changed Files (first 20)")
            for f in files:
                md.append(f"- {f['path']} (+{f['additions']}, -{f['deletions']})")
        return _truncate_response("\n".join(md))
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

@mcp.tool(
    name="github_create_release",
    annotations={
        "title": "Create GitHub Release",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_create_release(params: CreateReleaseInput) -> str:
    """
    Create a new release in a GitHub repository.
    
    This tool creates a GitHub release with a tag, title, and release notes.
    Can create draft or pre-release versions. Requires write access to the repository.
    
    Args:
        params (CreateReleaseInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - tag_name (str): Git tag for the release (e.g., 'v1.2.0')
            - name (Optional[str]): Release title
            - body (Optional[str]): Release notes in Markdown
            - draft (Optional[bool]): Create as draft
            - prerelease (Optional[bool]): Mark as pre-release
            - target_commitish (Optional[str]): Commit/branch to release from
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Confirmation message with release details and URL
    
    Examples:
        - Use when: "Create a v1.2.0 release"
        - Use when: "Tag and release the current version"
        - Use when: "Create a pre-release for testing"
    
    Error Handling:
        - Returns error if tag already exists (422)
        - Returns error if authentication fails (401/403)
        - Returns error if invalid parameters (422)
    """
    auth_token = params.token or os.getenv('GITHUB_TOKEN')

    try:
        endpoint = f"repos/{params.owner}/{params.repo}/releases"
        
        # Build request body
        body_data = {
            "tag_name": params.tag_name,
            "name": params.name or params.tag_name,
            "draft": params.draft or False,
            "prerelease": params.prerelease or False
        }
        
        # Add optional fields
        if params.body:
            body_data["body"] = params.body
        if params.target_commitish:
            body_data["target_commitish"] = params.target_commitish
        
        # Create the release
        data = await _make_github_request(
            endpoint,
            method="POST",
            token=auth_token,
            json=body_data
        )
        
        # Format response
        response = [
            "✅ **Release Created Successfully!**\n",
            f"🏷️ **Tag:** {data['tag_name']}",
            f"📦 **Name:** {data['name']}",
            f"🔗 **URL:** {data['html_url']}",
            f"📅 **Created:** {_format_timestamp(data['created_at'])}",
            f"👤 **Author:** @{data['author']['login']}",
        ]
        
        if data.get('draft'):
            response.append("📝 **Status:** Draft (not publicly visible)")
        elif data.get('prerelease'):
            response.append("🚧 **Status:** Pre-release")
        else:
            response.append("✅ **Status:** Published")
        
        if data.get('body'):
            response.append(f"\n**Release Notes:**\n{data['body'][:500]}{'...' if len(data['body']) > 500 else ''}")
        
        return "\n".join(response)
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_update_release",
    annotations={
        "title": "Update GitHub Release",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_update_release(params: UpdateReleaseInput) -> str:
    """
    Update an existing GitHub release.
    
    This tool modifies release information including title, notes, and status.
    Only provided fields will be updated - others remain unchanged.
    
    Args:
        params (UpdateReleaseInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - release_id (str): Release ID or tag name
            - tag_name (Optional[str]): New tag name
            - name (Optional[str]): New title
            - body (Optional[str]): New release notes
            - draft (Optional[bool]): Draft status
            - prerelease (Optional[bool]): Pre-release status
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Confirmation message with updated release details
    
    Examples:
        - Use when: "Update the v1.2.0 release notes"
        - Use when: "Change release from draft to published"
        - Use when: "Add more details to the latest release"
    
    Error Handling:
        - Returns error if release not found (404)
        - Returns error if authentication fails (401/403)
        - Returns error if invalid parameters (422)
    """
    auth_token = params.token or os.getenv('GITHUB_TOKEN')
    
    try:
        # First, get the release to find its ID if tag name was provided
        if params.release_id.startswith('v') or '.' in params.release_id:
            # Looks like a tag name, need to get release ID
            get_endpoint = f"repos/{params.owner}/{params.repo}/releases/tags/{params.release_id}"
            release_data = await _make_github_request(
                get_endpoint,
                method="GET",
                token=auth_token
            )
            release_id = release_data['id']
        else:
            release_id = params.release_id
        
        endpoint = f"repos/{params.owner}/{params.repo}/releases/{release_id}"
        
        # Build request body with only provided fields
        body_data = {}
        
        if params.tag_name is not None:
            body_data["tag_name"] = params.tag_name
        if params.name is not None:
            body_data["name"] = params.name
        if params.body is not None:
            body_data["body"] = params.body
        if params.draft is not None:
            body_data["draft"] = params.draft
        if params.prerelease is not None:
            body_data["prerelease"] = params.prerelease
        
        # Update the release
        data = await _make_github_request(
            endpoint,
            method="PATCH",
            token=auth_token,
            json=body_data
        )
        
        # Format response
        response = [
            "✅ **Release Updated Successfully!**\n",
            f"🏷️ **Tag:** {data['tag_name']}",
            f"📦 **Name:** {data['name']}",
            f"🔗 **URL:** {data['html_url']}",
            f"📅 **Updated:** {_format_timestamp(data.get('published_at', data['created_at']))}",
        ]
        
        if data.get('draft'):
            response.append("📝 **Status:** Draft")
        elif data.get('prerelease'):
            response.append("🚧 **Status:** Pre-release")
        else:
            response.append("✅ **Status:** Published")
        
        if params.body:
            response.append(f"\n**Updated Release Notes Preview:**\n{params.body[:300]}{'...' if len(params.body) > 300 else ''}")
        
        return "\n".join(response)
        
    except Exception as e:
        return _handle_api_error(e)

# Phase 2.1: File Management Tools


@mcp.tool(
    name="github_create_file",
    annotations={
        "title": "Create File in Repository",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def github_create_file(params: CreateFileInput) -> str:
    """
    Create a new file in a GitHub repository.
    
    This tool creates a new file with the specified content and commits it to the repository.
    If the file already exists, this will fail - use github_update_file instead.
    
    Args:
        params (CreateFileInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - path (str): File path in repository
            - content (str): File content
            - message (str): Commit message
            - branch (Optional[str]): Target branch
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Confirmation message with commit details
    
    Examples:
        - Use when: "Create a new README.md file"
        - Use when: "Add a LICENSE file to the repository"
        - Use when: "Create docs/API.md with content..."
    
    Error Handling:
        - Returns error if file already exists (422)
        - Returns error if authentication fails (401/403)
        - Returns error if branch doesn't exist (404)
    """
    auth_token = params.token or os.getenv('GITHUB_TOKEN')

    try:
        # Encode content to base64
        content_bytes = params.content.encode('utf-8')
        content_base64 = base64.b64encode(content_bytes).decode('utf-8')
        
        # Prepare request body
        body = {
            "message": params.message,
            "content": content_base64
        }
        
        if params.branch:
            body["branch"] = params.branch
        
        # Make API request
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            method="PUT",
            token=auth_token,
            json=body
        )
        
        # Format success response
        result = f"""✅ **File Created Successfully!**


**Repository:** {params.owner}/{params.repo}
**File:** {params.path}
**Branch:** {params.branch or 'default'}
**Commit Message:** {params.message}


**Commit Details:**
- SHA: {data['commit']['sha']}
- Author: {data['commit']['author']['name']}
- Date: {data['commit']['author']['date']}


**File URL:** {data['content']['html_url']}
"""
        
        return result
        
    except Exception as e:
        error_msg = _handle_api_error(e)
        
        # Add helpful context for common errors
        if "422" in error_msg or "already exists" in error_msg.lower():
            error_msg += "\n\n💡 Tip: This file already exists. Use 'github_update_file' to modify it, or 'github_delete_file' to remove it first."
        
        return error_msg


@mcp.tool(
    name="github_update_file",
    annotations={
        "title": "Update File in Repository",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def github_update_file(params: UpdateFileInput) -> str:
    """
    Update an existing file in a GitHub repository.
    
    This tool modifies the content of an existing file and commits the changes.
    Requires the current SHA of the file (get it from github_get_file_content first).
    
    Args:
        params (UpdateFileInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - path (str): File path in repository
            - content (str): New file content
            - message (str): Commit message
            - sha (str): Current file SHA (required)
            - branch (Optional[str]): Target branch
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Confirmation message with commit details
    
    Examples:
        - Use when: "Update the README.md file"
        - Use when: "Modify src/config.py"
        - Use when: "Change the content of docs/API.md"
    
    Error Handling:
        - Returns error if file doesn't exist (404)
        - Returns error if SHA doesn't match (409 conflict)
        - Returns error if authentication fails (401/403)
    """
    auth_token = params.token or os.getenv('GITHUB_TOKEN')

    try:
        # Encode content to base64
        content_bytes = params.content.encode('utf-8')
        content_base64 = base64.b64encode(content_bytes).decode('utf-8')
        
        # Prepare request body
        body = {
            "message": params.message,
            "content": content_base64,
            "sha": params.sha
        }
        
        if params.branch:
            body["branch"] = params.branch
        
        # Make API request
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            method="PUT",
            token=auth_token,
            json=body
        )
        
        # Format success response
        result = f"""✅ **File Updated Successfully!**


**Repository:** {params.owner}/{params.repo}
**File:** {params.path}
**Branch:** {params.branch or 'default'}
**Commit Message:** {params.message}


**Commit Details:**
- SHA: {data['commit']['sha']}
- Author: {data['commit']['author']['name']}
- Date: {data['commit']['author']['date']}


**File URL:** {data['content']['html_url']}
"""
        
        return result
        
    except Exception as e:
        error_msg = _handle_api_error(e)
        
        # Add helpful context for common errors
        if "409" in error_msg or "does not match" in error_msg.lower():
            error_msg += "\n\n💡 Tip: The file SHA doesn't match. The file may have been modified. Get the current SHA with 'github_get_file_content' and try again."
        elif "404" in error_msg:
            error_msg += "\n\n💡 Tip: File not found. Use 'github_create_file' to create it first."
        
        return error_msg


@mcp.tool(
    name="github_delete_file",
    annotations={
        "title": "Delete File from Repository",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def github_delete_file(params: DeleteFileInput) -> str:
    """
    Delete a file from a GitHub repository.
    
    ⚠️ DESTRUCTIVE OPERATION: This permanently deletes the file from the repository.
    Requires the current SHA of the file (get it from github_get_file_content first).
    
    Args:
        params (DeleteFileInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - path (str): File path to delete
            - message (str): Commit message explaining deletion
            - sha (str): Current file SHA (required for safety)
            - branch (Optional[str]): Target branch
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Confirmation message with commit details
    
    Examples:
        - Use when: "Delete the old config file"
        - Use when: "Remove docs/deprecated.md"
        - Use when: "Clean up temporary files"
    
    Error Handling:
        - Returns error if file doesn't exist (404)
        - Returns error if SHA doesn't match (409 conflict)
        - Returns error if authentication fails (401/403)
        
    Safety Notes:
        - Requires explicit SHA to prevent accidental deletions
        - Creates a commit that can be reverted if needed
        - File history is preserved in Git
    """
    auth_token = params.token or os.getenv('GITHUB_TOKEN')

    try:
        # Prepare request body
        body = {
            "message": params.message,
            "sha": params.sha
        }
        
        if params.branch:
            body["branch"] = params.branch
        
        # Make API request
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            method="DELETE",
            token=auth_token,
            json=body
        )
        
        # Format success response
        result = f"""✅ **File Deleted Successfully!**


**Repository:** {params.owner}/{params.repo}
**File:** {params.path}
**Branch:** {params.branch or 'default'}
**Commit Message:** {params.message}


**Commit Details:**
- SHA: {data['commit']['sha']}
- Author: {data['commit']['author']['name']}
- Date: {data['commit']['author']['date']}


⚠️ **Note:** File has been removed from the repository but remains in Git history.
You can restore it by reverting this commit if needed.
"""
        
        return result
        
    except Exception as e:
        error_msg = _handle_api_error(e)
        
        # Add helpful context for common errors
        if "409" in error_msg or "does not match" in error_msg.lower():
            error_msg += "\n\n💡 Tip: The file SHA doesn't match. The file may have been modified. Get the current SHA with 'github_get_file_content' and try again."
        elif "404" in error_msg:
            error_msg += "\n\n💡 Tip: File not found. It may have already been deleted or the path is incorrect."
        
        return error_msg

@mcp.tool(
    name="github_batch_file_operations",
    annotations={
        "title": "Batch File Operations (Single Commit)",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def github_batch_file_operations(params: BatchFileOperationsInput) -> str:
    """
    Perform multiple file operations (create/update/delete) in a single commit.
    
    This is much more efficient than individual file operations. All changes are committed
    together atomically - either all succeed or all fail.
    
    Args:
        params (BatchFileOperationsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - operations (List[FileOperation]): List of file operations
            - message (str): Commit message
            - branch (Optional[str]): Target branch
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Confirmation message with commit details
    
    Examples:
        - Use when: "Update README.md and LICENSE in one commit"
        - Use when: "Create multiple documentation files"
        - Use when: "Refactor: delete old files and create new ones"
    
    Error Handling:
        - Returns error if any file operation is invalid
        - Returns error if branch doesn't exist (404)
        - Validates all operations before making changes
    """
    try:
        token = params.token or os.getenv("GITHUB_TOKEN")
        if not token:
            return "Error: GitHub token required for batch file operations. Set GITHUB_TOKEN environment variable or provide token parameter."
        
        branch_name = params.branch or "main"
        if not params.branch:
            repo_info = await _make_github_request(
                f"repos/{params.owner}/{params.repo}",
                token=token
            )
            branch_name = repo_info['default_branch']
        
        branch_data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/git/ref/heads/{branch_name}",
            token=token
        )
        latest_commit_sha = branch_data['object']['sha']
        
        commit_data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/git/commits/{latest_commit_sha}",
            token=token
        )
        base_tree_sha = commit_data['tree']['sha']
        
        tree: List[Dict[str, Any]] = []
        for op in params.operations:
            if op.operation == 'delete':
                tree.append({
                    "path": op.path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": None
                })
            else:
                content_bytes = op.content.encode('utf-8')
                encoded_content = base64.b64encode(content_bytes).decode('utf-8')
                blob_data = await _make_github_request(
                    f"repos/{params.owner}/{params.repo}/git/blobs",
                    method="POST",
                    token=token,
                    json={
                        "content": encoded_content,
                        "encoding": "base64"
                    }
                )
                tree.append({
                    "path": op.path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_data['sha']
                })
        
        new_tree = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/git/trees",
            method="POST",
            token=token,
            json={
                "base_tree": base_tree_sha,
                "tree": tree
            }
        )
        
        new_commit = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/git/commits",
            method="POST",
            token=token,
            json={
                "message": params.message,
                "tree": new_tree['sha'],
                "parents": [latest_commit_sha]
            }
        )
        
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/git/refs/heads/{branch_name}",
            method="PATCH",
            token=token,
            json={
                "sha": new_commit['sha']
            }
        )
        
        response = f"# Batch File Operations Complete! ✅\n\n"
        response += f"**Repository:** {params.owner}/{params.repo}  \n"
        response += f"**Branch:** {branch_name}  \n"
        response += f"**Commit Message:** {params.message}  \n"
        response += f"**Commit SHA:** `{new_commit['sha']}`  \n"
        response += f"**Operations:** {len(params.operations)} files modified  \n\n"
        response += "## Changes:\n\n"
        for op in params.operations:
            emoji = "📝" if op.operation == "update" else "✨" if op.operation == "create" else "🗑️"
            response += f"- {emoji} **{op.operation.upper()}**: `{op.path}`\n"
        response += f"\n**View Commit:** https://github.com/{params.owner}/{params.repo}/commit/{new_commit['sha']}\n"
        return response
        
    except Exception as e:
        return _handle_api_error(e)

# Workflow Optimization Tool

@mcp.tool(
    name="github_suggest_workflow",
    annotations={
        "title": "Suggest Optimal Workflow (API vs Local vs Hybrid)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
        rationale = "Operation requires GitHub API (releases cannot be done locally only)."
    # Dogfooding detection
    elif any(x in operation for x in ["dogfood", "dogfooding", "test"]) or any(x in description for x in ["dogfood", "test", "github_", "mcp"]):
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
        rationale = "Mix approaches: structure changes locally, finalize small pieces via API."

    # Simple token cost model
    api_tokens = bytes_to_tokens(file_size) * max(1, num_edits)
    local_tokens = bytes_to_tokens(min(file_size, 1024))  # local coordination minimal
    savings_tokens = max(0, api_tokens - local_tokens)

    if params.response_format == ResponseFormat.JSON:
        return _truncate_response(json.dumps({
            "recommendation": recommendation,
            "rationale": rationale,
            "estimates": {
                "api_tokens": api_tokens,
                "local_tokens": local_tokens,
                "potential_savings_tokens": savings_tokens
            },
            "meta": {
                "dogfooding": recommendation == "api" and ("dogfood" in operation or "test" in operation or "dogfood" in description or "test" in description)
            }
        }, indent=2))

    # Markdown output
    lines = [
        f"# Workflow Suggestion",
        f"**Recommendation:** {recommendation.upper()}",
        f"**Rationale:** {rationale}",
        "",
        "## Estimates",
        f"- API tokens (rough): {api_tokens}",
        f"- Local tokens (rough): {local_tokens}",
        f"- Potential savings: {savings_tokens} tokens",
    ]

    if recommendation == "api" and ("dogfood" in operation or "test" in operation or "dogfood" in description or "test" in description):
        lines.append("\n🐕🍖 Dogfooding detected: Use API tools to validate new features end-to-end.")

    lines.append("\n## Next Steps")
    if recommendation == "api":
        lines.append("- Use targeted API tools for atomic changes (e.g., github_update_file, github_create_release)")
    elif recommendation == "local":
        lines.append("- Make edits locally, commit logically, and push a PR for review")
    else:
        lines.append("- Do bulk changes locally, then use API tools for final small edits")

    return _truncate_response("\n".join(lines))

# Phase 2.2: Repository Management Tools

@mcp.tool(
    name="github_create_repository",
    annotations={
        "title": "Create Repository",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_create_repository(params: CreateRepositoryInput) -> str:
    """
    Create a new repository for the authenticated user or in an organization.
    """
    auth_token = params.token or os.getenv("GITHUB_TOKEN")
    try:
        body = {
            "name": params.name,
            "description": params.description,
            "private": params.private,
            "auto_init": params.auto_init,
        }
        if params.gitignore_template:
            body["gitignore_template"] = params.gitignore_template
        if params.license_template:
            body["license_template"] = params.license_template

        if params.owner:
            endpoint = f"orgs/{params.owner}/repos"
        else:
            endpoint = "user/repos"

        data = await _make_github_request(endpoint, method="POST", token=auth_token, json=body)
        return f"✅ Repository created: {data['full_name']}\nURL: {data['html_url']}"
    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="github_delete_repository",
    annotations={
        "title": "Delete Repository",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def github_delete_repository(params: DeleteRepositoryInput) -> str:
    """
    Delete a repository. Destructive; requires appropriate permissions.
    """
    auth_token = params.token or os.getenv("GITHUB_TOKEN")
    try:
        await _make_github_request(f"repos/{params.owner}/{params.repo}", method="DELETE", token=auth_token)
        return f"✅ Repository deleted: {params.owner}/{params.repo}"
    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="github_update_repository",
    annotations={
        "title": "Update Repository Settings",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_update_repository(params: UpdateRepositoryInput) -> str:
    """
    Update repository settings such as description, visibility, and features.
    """
    auth_token = params.token or os.getenv("GITHUB_TOKEN")
    try:
        body: Dict[str, Any] = {}
        for field in ["name", "description", "homepage", "private", "has_issues", "has_projects", "has_wiki", "default_branch", "archived"]:
            value = getattr(params, field)
            if value is not None:
                body[field] = value
        data = await _make_github_request(f"repos/{params.owner}/{params.repo}", method="PATCH", token=auth_token, json=body)
        return f"✅ Repository updated: {data['full_name']}\nURL: {data['html_url']}"
    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="github_transfer_repository",
    annotations={
        "title": "Transfer Repository Ownership",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def github_transfer_repository(params: TransferRepositoryInput) -> str:
    """
    Transfer a repository to a new owner (user or organization).
    """
    auth_token = params.token or os.getenv("GITHUB_TOKEN")
    try:
        body: Dict[str, Any] = {"new_owner": params.new_owner}
        if params.team_ids:
            body["team_ids"] = params.team_ids
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/transfer",
            method="POST",
            token=auth_token,
            json=body
        )
        return f"✅ Transfer initiated: {data['full_name']} -> {params.new_owner}\nURL: {data['html_url']}"
    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="github_archive_repository",
    annotations={
        "title": "Archive/Unarchive Repository",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_archive_repository(params: ArchiveRepositoryInput) -> str:
    """
    Archive or unarchive a repository by toggling the archived flag.
    """
    auth_token = params.token or os.getenv("GITHUB_TOKEN")
    try:
        body = {"archived": params.archived}
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}",
            method="PATCH",
            token=auth_token,
            json=body
        )
        state = "archived" if data.get("archived") else "active"
        return f"✅ Repository state updated: {data['full_name']} is now {state}"
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_merge_pull_request",
    annotations={
        "title": "Merge Pull Request",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_merge_pull_request(params: MergePullRequestInput) -> str:
    """
    Merge a pull request using the specified merge method.
    
    This tool merges an open pull request into its base branch. Supports
    merge commits, squash merging, and rebase merging.
    
    Args:
        params (MergePullRequestInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pull_number (int): Pull request number
            - merge_method (Optional[str]): 'merge', 'squash', or 'rebase' (default: squash)
            - commit_title (Optional[str]): Custom commit title
            - commit_message (Optional[str]): Custom commit message
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Merge confirmation with commit details
    
    Examples:
        - Use when: "Merge PR #8"
        - Use when: "Squash and merge this pull request"
        - Use when: "Merge the feature branch"
    
    Error Handling:
        - Returns error if PR not found (404)
        - Returns error if not mergeable (405)
        - Returns error if insufficient permissions (403)
        - Returns error if conflicts exist (409)
    """
    try:
        # Get token from env if not provided
        token = params.token or os.environ.get("GITHUB_TOKEN")
        
        # Build merge data
        merge_data = {
            "merge_method": params.merge_method or "squash"
        }
        
        if params.commit_title:
            merge_data["commit_title"] = params.commit_title
        if params.commit_message:
            merge_data["commit_message"] = params.commit_message
        
        # Merge the pull request
        result = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/merge",
            method="PUT",
            token=token,
            json=merge_data
        )
        
        response = f"""✅ **Pull Request Merged Successfully!**


📦 **Repository:** {params.owner}/{params.repo}
🔀 **PR:** #{params.pull_number}
✅ **Status:** {result.get('message', 'Merged')}


**Merge Details:**

- 📝 **Commit SHA:** {result.get('sha', 'N/A')}
- 🔀 **Method:** {params.merge_method or 'squash'}
- ✅ **Merged:** {result.get('merged', False)}


The pull request has been successfully merged! 🎉

"""
        
        return response
        
    except Exception as e:
        return _handle_api_error(e)

@mcp.tool(
    name="github_create_pr_review",
    annotations={
        "title": "Create Pull Request Review",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_create_pr_review(params: CreatePRReviewInput) -> str:
    """
    Create a review on a pull request with optional line-specific comments.
    
    This tool allows you to review pull requests by:
    - Adding general review comments
    - Adding line-specific comments to code
    - Approving the PR
    - Requesting changes to the PR
    
    Args:
        params (CreatePRReviewInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pull_number (int): Pull request number
            - event (str): 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'
            - body (Optional[str]): General review comment
            - comments (Optional[List[PRReviewComment]]): Line-specific comments
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Confirmation with review details
    
    Examples:
        - Use when: "Approve PR #42"
        - Use when: "Request changes on line 15 of main.py"
        - Use when: "Add review comment suggesting improvements"
    
    Error Handling:
        - Returns error if PR not found (404)
        - Returns error if already reviewed (422)
        - Returns error if insufficient permissions (403)
    """
    try:
        token = params.token or os.getenv("GITHUB_TOKEN")
        if not token:
            return "Error: GitHub token required for creating PR reviews. Set GITHUB_TOKEN environment variable or provide token parameter."
        
        review_data: Dict[str, Any] = {
            "event": params.event
        }
        if params.body:
            review_data["body"] = params.body
        if params.comments:
            review_data["comments"] = []
            for comment in params.comments:
                comment_data: Dict[str, Any] = {
                    "path": comment.path,
                    "body": comment.body,
                    "side": comment.side
                }
                if comment.line:
                    comment_data["line"] = comment.line
                elif comment.position:
                    comment_data["position"] = comment.position
                else:
                    return f"Error: Comment on {comment.path} must specify either 'line' or 'position'"
                review_data["comments"].append(comment_data)
        
        review = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/reviews",
            method="POST",
            token=token,
            json=review_data
        )
        
        response = f"# Pull Request Review Created! ✅\n\n"
        response += f"**Repository:** {params.owner}/{params.repo}  \n"
        response += f"**Pull Request:** #{params.pull_number}  \n"
        response += f"**Review ID:** {review['id']}  \n"
        response += f"**State:** {review['state']}  \n"
        if review.get('user'):
            response += f"**Reviewer:** {review['user']['login']}  \n"
        if review.get('submitted_at'):
            response += f"**Submitted:** {_format_timestamp(review['submitted_at'])}  \n\n"
        if params.body:
            response += f"## Review Comment:\n\n{params.body}\n\n"
        if params.comments:
            response += f"## Line Comments: {len(params.comments)}\n\n"
            for comment in params.comments:
                line_info = f"line {comment.line}" if comment.line else f"position {comment.position}"
                response += f"- **{comment.path}** ({line_info}, {comment.side}): {comment.body[:100]}...\n"
        if review.get('html_url'):
            response += f"\n**View Review:** {review['html_url']}\n"
        return response
        
    except Exception as e:
        return _handle_api_error(e)
# Entry point
if __name__ == "__main__":
    import asyncio
    import argparse
    import os as _os

    parser = argparse.ArgumentParser(description="GitHub MCP Server")
    parser.add_argument("--auth", choices=["pat", "app"], default=None, help="Authentication mode: pat (default) or app")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"], default=None, help="Transport type")
    parser.add_argument("--port", type=int, default=None, help="Port for HTTP/SSE transport")
    args, unknown = parser.parse_known_args()

    if args.auth:
        _os.environ["GITHUB_AUTH_MODE"] = args.auth

    # Run license check first on its own event loop, then start MCP server
    asyncio.run(check_license_on_startup())
    if args.transport in ("http", "sse"):
        mcp.run(transport=args.transport, port=(args.port or 8080))
    else:
        mcp.run()