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
import sys
import httpx
from datetime import datetime
import base64
import subprocess
import re
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from license_manager import check_license_on_startup, get_license_manager
from github_client import GhClient
from auth.github_app import get_auth_token, clear_token_cache
from graphql_client import GraphQLClient

# Get the directory where THIS script is located
SCRIPT_DIR = Path(__file__).parent

# Load .env file from the same directory as the script
# This ensures .env is found regardless of where the server is started from
env_path = SCRIPT_DIR / ".env"
load_dotenv(env_path)

# Debug: Log if token was loaded (only if DEBUG_AUTH is enabled)
if os.getenv("GITHUB_MCP_DEBUG_AUTH", "false").lower() == "true":
    token_loaded = os.getenv("GITHUB_TOKEN") is not None
    print(f"[DEBUG] .env loaded from: {env_path}", file=sys.stderr)
    print(f"[DEBUG] GITHUB_TOKEN loaded: {token_loaded}", file=sys.stderr)

# Validate Deno installation at startup
def check_deno_installed():
    """Check if Deno is installed and accessible."""
    try:
        result = subprocess.run(
            ["deno", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            return True, version
        else:
            return False, "Deno command failed"
    except FileNotFoundError:
        return False, "Deno not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "Deno version check timed out"
    except Exception as e:
        return False, f"Error checking Deno: {str(e)}"

# Check Deno at startup
deno_available, deno_info = check_deno_installed()
if not deno_available:
    print("=" * 60, file=sys.stderr)
    print("❌ DENO NOT FOUND", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Error: {deno_info}", file=sys.stderr)
    print("\nGitHub MCP Server requires Deno to execute TypeScript code.", file=sys.stderr)
    print("\nInstallation:", file=sys.stderr)
    print("  Windows: irm https://deno.land/install.ps1 | iex", file=sys.stderr)
    print("  macOS:    brew install deno", file=sys.stderr)
    print("  Linux:    curl -fsSL https://deno.land/install.sh | sh", file=sys.stderr)
    print("\nOr visit: https://deno.land", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    sys.exit(1)

# Code-First Mode: Expose only execute_code to Claude Desktop for token efficiency
# Deno runtime will connect with CODE_FIRST_MODE=false to access all tools internally
CODE_FIRST_MODE = os.getenv("MCP_CODE_FIRST_MODE", "true").lower() == "true"

# Initialize the MCP server
mcp = FastMCP("github_mcp")

# Print startup message based on mode
if CODE_FIRST_MODE:
    print(">> GitHub MCP Server v2.4.0 - Code-First Mode (execute_code only)")
    print(">> Token usage: ~800 tokens (98% savings!)")
    print(f">> Deno: {deno_info}")
else:
    print(">> GitHub MCP Server v2.4.0 - Internal Mode (all internal tools)")
    print(">> Used by Deno runtime for tool execution")
    print(f">> Deno: {deno_info}")

# Conditional tool registration decorator
def conditional_tool(*args, **kwargs):
    """
    Only register tool if not in code-first mode.
    In code-first mode, only execute_code is exposed to Claude Desktop.
    """
    if CODE_FIRST_MODE:
        # Return a no-op decorator that doesn't register the tool
        def noop_decorator(func):
            return func
        return noop_decorator
    else:
        # Return the actual mcp.tool decorator
        return mcp.tool(*args, **kwargs)

# Constants
API_BASE_URL = "https://api.github.com"
CHARACTER_LIMIT = 25000  # Maximum response size in characters
DEFAULT_LIMIT = 20

# Workspace Configuration - supports user projects!
# Set MCP_WORKSPACE_ROOT env var to your project root, or defaults to current directory
WORKSPACE_ROOT = Path(os.getenv("MCP_WORKSPACE_ROOT", Path.cwd()))
REPO_ROOT = WORKSPACE_ROOT  # Backward compatibility alias

def validate_workspace_path(path: Path) -> bool:
    """
    Ensure path is within workspace for security.
    
    Args:
        path: Path to validate
    
    Returns:
        True if path is within WORKSPACE_ROOT, False otherwise
    """
    try:
        resolved = path.resolve()
        workspace = WORKSPACE_ROOT.resolve()
        resolved.relative_to(workspace)  # Raises ValueError if outside workspace
        return True
    except (ValueError, OSError):
        return False

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
async def _get_auth_token_fallback(param_token: Optional[str] = None) -> Optional[str]:
    """
    Get authentication token with fallback logic.
    
    Priority:
    1. Parameter token (if provided)
    2. GitHub App token (if configured)
    3. Personal Access Token (if configured)
    
    Args:
        param_token: Token from function parameter
        
    Returns:
        Token string or None
    """
    if param_token:
        return param_token
    return await get_auth_token()


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

    # If no token provided, try GitHub App first, then fall back to PAT
    if token is None:
        token = await get_auth_token()

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
    except Exception:
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
        truncation_notice += " - showing partial results. Use pagination or filters to see more."
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

class UpdateIssueInput(BaseModel):
    """Input model for updating GitHub issues."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., min_length=1, max_length=100, description="Repository owner username or organization")
    repo: str = Field(..., min_length=1, max_length=100, description="Repository name")
    issue_number: int = Field(..., ge=1, description="Issue number to update")
    state: Optional[str] = Field(None, description="Issue state: 'open' or 'closed'")
    title: Optional[str] = Field(None, min_length=1, max_length=256, description="New issue title")
    body: Optional[str] = Field(None, description="New issue body/description in Markdown format")
    labels: Optional[List[str]] = Field(None, max_length=20, description="List of label names to apply (replaces existing)")
    assignees: Optional[List[str]] = Field(None, max_length=10, description="List of usernames to assign (replaces existing)")
    milestone: Optional[int] = Field(None, description="Milestone number (use null to remove milestone)")
    token: Optional[str] = Field(None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")

class AddIssueCommentInput(BaseModel):
    """Input model for adding a comment to an existing issue."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., min_length=1, max_length=100, description="Repository owner username or organization")
    repo: str = Field(..., min_length=1, max_length=100, description="Repository name")
    issue_number: int = Field(..., ge=1, description="Issue number to comment on")
    body: str = Field(..., min_length=1, max_length=65535, description="Comment content in Markdown format")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class ListGistsInput(BaseModel):
    """Input model for listing gists for a user or the authenticated user."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    username: Optional[str] = Field(default=None, description="GitHub username to list gists for (omit for authenticated user)")
    since: Optional[str] = Field(default=None, description="Only gists updated at or after this time (ISO 8601)")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page (1-100, default 30)")
    page: Optional[int] = Field(default=1, ge=1, description="Page number for pagination")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - required when username is omitted)")


class GetGistInput(BaseModel):
    """Input model for retrieving a single gist by ID."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    gist_id: str = Field(..., min_length=1, max_length=200, description="ID of the gist to retrieve")
    token: Optional[str] = Field(default=None, description="Optional GitHub token (for private gists)")


class CreateGistFileInput(BaseModel):
    """Input model for a single file in a gist create/update request."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    content: str = Field(..., description="File content")


class CreateGistInput(BaseModel):
    """Input model for creating a new gist."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    description: Optional[str] = Field(default=None, description="Description of the gist")
    public: Optional[bool] = Field(default=False, description="Whether the gist is public (default: false)")
    files: Dict[str, CreateGistFileInput] = Field(..., description="Mapping of filename to file content")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class UpdateGistInput(BaseModel):
    """Input model for updating an existing gist."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    gist_id: str = Field(..., min_length=1, max_length=200, description="ID of the gist to update")
    description: Optional[str] = Field(default=None, description="New description for the gist")
    files: Optional[Dict[str, Optional[CreateGistFileInput]]] = Field(
        default=None,
        description="Files to add/update/delete. To delete a file, set its value to null."
    )
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

class ListBranchesInput(BaseModel):
    """Input model for listing repository branches."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    protected: Optional[bool] = Field(default=None, description="Filter by protected status")
    per_page: Optional[int] = Field(default=30, description="Results per page", ge=1, le=100)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Response format")

class CreateBranchInput(BaseModel):
    """Input model for creating a new branch."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    branch: str = Field(..., description="New branch name", min_length=1, max_length=250)
    from_ref: str = Field(default="main", description="Branch, tag, or commit SHA to branch from")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")

class GetBranchInput(BaseModel):
    """Input model for getting branch details."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    branch: str = Field(..., description="Branch name", min_length=1, max_length=250)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Response format")

class DeleteBranchInput(BaseModel):
    """Input model for deleting a branch."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    branch: str = Field(..., description="Branch name to delete", min_length=1, max_length=250)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")

class CompareBranchesInput(BaseModel):
    """Input model for comparing two branches."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    base: str = Field(..., description="Base branch name", min_length=1, max_length=250)
    head: str = Field(..., description="Head branch name to compare", min_length=1, max_length=250)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Response format")

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


class ListLabelsInput(BaseModel):
    """Input model for listing labels in a repository."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page (1-100, default 30)")
    page: Optional[int] = Field(default=1, ge=1, description="Page number for pagination")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


class CreateLabelInput(BaseModel):
    """Input model for creating a label in a repository."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=50, description="Label name")
    color: str = Field(..., min_length=3, max_length=10, description="6-character hex color code without '#' (GitHub accepts up to 10 chars including alpha)")
    description: Optional[str] = Field(default=None, max_length=255, description="Label description")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class DeleteLabelInput(BaseModel):
    """Input model for deleting a label from a repository."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=50, description="Label name to delete")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class ListStargazersInput(BaseModel):
    """Input model for listing stargazers on a repository."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page (1-100, default 30)")
    page: Optional[int] = Field(default=1, ge=1, description="Page number for pagination")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


class StarRepositoryInput(BaseModel):
    """Input model for starring a repository."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class UnstarRepositoryInput(BaseModel):
    """Input model for unstarring a repository."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class GetAuthenticatedUserInput(BaseModel):
    """Input model for getting the authenticated user's profile."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class ListUserReposInput(BaseModel):
    """Input model for listing repositories for a user."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    username: Optional[str] = Field(default=None, description="GitHub username to list repositories for (omit for authenticated user)")
    type: Optional[str] = Field(default="owner", description="Repository type: 'all', 'owner', 'member' (default: 'owner')")
    sort: Optional[str] = Field(default="full_name", description="Sort field: 'created', 'updated', 'pushed', 'full_name' (default: 'full_name')")
    direction: Optional[str] = Field(default="asc", description="Sort direction: 'asc' or 'desc' (default: 'asc')")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page (1-100, default 30)")
    page: Optional[int] = Field(default=1, ge=1, description="Page number for pagination")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class ListOrgReposInput(BaseModel):
    """Input model for listing repositories for an organization."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    org: str = Field(..., description="Organization name", min_length=1, max_length=100)
    type: Optional[str] = Field(default="all", description="Repository type: 'all', 'public', 'private', 'forks', 'sources', 'member'")
    sort: Optional[str] = Field(default="full_name", description="Sort field: 'created', 'updated', 'pushed', 'full_name' (default: 'full_name')")
    direction: Optional[str] = Field(default="asc", description="Sort direction: 'asc' or 'desc' (default: 'asc')")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page (1-100, default 30)")
    page: Optional[int] = Field(default=1, ge=1, description="Page number for pagination")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")


class SearchUsersInput(BaseModel):
    """Input model for searching GitHub users."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    query: str = Field(..., min_length=1, max_length=256, description="Search query (supports qualifiers like 'location:', 'language:', 'followers:>100')")
    sort: Optional[str] = Field(default=None, description="Sort field: 'followers', 'repositories', or 'joined'")
    order: Optional[SortOrder] = Field(default=SortOrder.DESC, description="Sort order: 'asc' or 'desc'")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page (1-100, default 30)")
    page: Optional[int] = Field(default=1, ge=1, description="Page number for pagination")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


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

class ClosePullRequestInput(BaseModel):
    """Input model for closing pull requests."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., min_length=1, max_length=100, description="Repository owner")
    repo: str = Field(..., min_length=1, max_length=100, description="Repository name")
    pull_number: int = Field(..., ge=1, description="Pull request number to close")
    comment: Optional[str] = Field(None, description="Optional comment to add when closing")
    token: Optional[str] = Field(None, description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)")

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

class WorkspaceGrepInput(BaseModel):
    """Input model for workspace grep search."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    pattern: str = Field(..., description="Regex pattern to search for", min_length=1, max_length=500)
    repo_path: str = Field(default="", description="Optional subdirectory to search within (relative to repo root)", max_length=500)
    context_lines: int = Field(default=2, description="Number of lines before/after match to include (0-5)", ge=0, le=5)
    max_results: int = Field(default=100, description="Maximum matches to return (1-500)", ge=1, le=500)
    file_pattern: str = Field(default="*", description="Glob pattern for files to search (e.g., '*.py', '*.md')", max_length=100)
    case_sensitive: bool = Field(default=True, description="Whether search is case-sensitive")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format (markdown or json)")

class StrReplaceInput(BaseModel):
    """Input model for string replacement in files."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    path: str = Field(..., description="Relative path to file under repository root", min_length=1, max_length=500)
    old_str: str = Field(..., description="Exact string to find and replace (must be unique match)", min_length=1)
    new_str: str = Field(..., description="Replacement string", min_length=0)
    description: Optional[str] = Field(default=None, description="Optional description of the change", max_length=200)

class GitHubGrepInput(BaseModel):
    """Input model for GitHub repository grep search."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    pattern: str = Field(..., description="Regex pattern to search for", min_length=1, max_length=500)
    ref: Optional[str] = Field(default=None, description="Branch, tag, or commit SHA (defaults to default branch)")
    file_pattern: Optional[str] = Field(default="*", description="Glob pattern for files (e.g., '*.py', '*.md')", max_length=100)
    path: Optional[str] = Field(default="", description="Optional subdirectory to search within", max_length=500)
    case_sensitive: Optional[bool] = Field(default=True, description="Whether search is case-sensitive")
    context_lines: Optional[int] = Field(default=2, description="Number of lines before/after match to include (0-5)", ge=0, le=5)
    max_results: Optional[int] = Field(default=100, description="Maximum matches to return (1-500)", ge=1, le=500)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format (markdown or json)")

class GitHubReadFileChunkInput(BaseModel):
    """Input model for reading chunks from GitHub files."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(..., description="File path in repository", min_length=1, max_length=500)
    start_line: int = Field(default=1, description="1-based starting line number", ge=1)
    num_lines: int = Field(default=200, description="Number of lines to read (max 500)", ge=1, le=500)
    ref: Optional[str] = Field(default=None, description="Branch, tag, or commit SHA (defaults to default branch)")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")

class GitHubStrReplaceInput(BaseModel):
    """Input model for string replacement in GitHub files."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(..., description="File path in repository", min_length=1, max_length=500)
    old_str: str = Field(..., description="Exact string to find and replace (must be unique match)", min_length=1)
    new_str: str = Field(..., description="Replacement string", min_length=0)
    ref: Optional[str] = Field(default=None, description="Branch, tag, or commit SHA (defaults to default branch)")
    commit_message: Optional[str] = Field(default=None, description="Custom commit message (auto-generated if not provided)", max_length=500)
    description: Optional[str] = Field(default=None, description="Optional description of the change", max_length=200)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")

# ============================================================================
# GITHUB TOOLS (Internal Use Only - Called by execute_code via Deno runtime)
# ============================================================================
# Note: Claude Desktop only sees execute_code tool (exposed below)
# These 46 tools are registered for internal use by the Deno runtime
# This architecture provides 98% token savings vs traditional MCP
# ============================================================================

# Tool Implementations

@conditional_tool(
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
    Read a specific range of lines from a local file under the workspace root.

    **Workspace Configuration**: Set MCP_WORKSPACE_ROOT environment variable
    to your project directory. Defaults to current working directory.

    Security:
    - Normalizes path
    - Denies parent traversal (..)
    - Enforces repo-root constraint
    - Caps lines read
    """
    try:
        base_dir = WORKSPACE_ROOT.resolve()  # Use configurable workspace
        norm_path = os.path.normpath(params.path)

        if norm_path.startswith("..") or os.path.isabs(norm_path):
            return "Error: Path traversal is not allowed."

        abs_path = os.path.abspath(os.path.join(str(base_dir), norm_path))
        if not abs_path.startswith(str(base_dir) + os.sep) and abs_path != str(base_dir):
            return "Error: Access outside workspace root is not allowed."

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

def _validate_search_path(repo_path: str) -> Path:
    """Validate and normalize search path, ensuring it's within workspace."""
    base_dir = WORKSPACE_ROOT  # Use configurable workspace, not hardcoded REPO_ROOT
    norm_path = Path(repo_path).as_posix() if repo_path else ""
    
    # Normalize path
    if norm_path:
        # Remove leading slashes
        norm_path = norm_path.lstrip('/')
        # Check for parent traversal
        if '..' in norm_path or norm_path.startswith('..'):
            raise ValueError("Path traversal detected: parent directory access not allowed")
        search_path = (base_dir / norm_path).resolve()
    else:
        search_path = base_dir
    
    # Ensure it's within repo root
    try:
        search_path.relative_to(base_dir)
    except ValueError:
        raise ValueError(f"Path outside workspace root: {repo_path}")
    
    if not search_path.exists():
        raise ValueError(f"Search path does not exist: {repo_path}")
    
    return search_path

def _is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary."""
    # Check by extension
    binary_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin', 
                        '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.tar',
                        '.gz', '.bz2', '.xz', '.ico', '.woff', '.woff2', '.ttf',
                        '.eot', '.otf', '.mp3', '.mp4', '.avi', '.mov', '.wmv'}
    if file_path.suffix.lower() in binary_extensions:
        return True
    
    # Check by content (first 512 bytes)
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(512)
            # Check for null bytes (common in binary files)
            if b'\x00' in chunk:
                return True
            # Check if it's valid UTF-8
            try:
                chunk.decode('utf-8')
            except UnicodeDecodeError:
                return True
    except Exception:
        return True
    
    return False

def _load_gitignore(base_dir: Path) -> List[re.Pattern]:
    """Load and parse .gitignore patterns."""
    gitignore_path = base_dir / '.gitignore'
    patterns = []
    
    # Always ignore .git directory
    patterns.append(re.compile(r'^\.git(/|$)'))
    
    if not gitignore_path.exists():
        return patterns
    
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Convert gitignore pattern to regex
                pattern = line.replace('.', r'\.').replace('*', '.*').replace('?', '.')
                if pattern.startswith('/'):
                    pattern = pattern[1:]
                else:
                    pattern = f'.*{pattern}'
                patterns.append(re.compile(pattern))
    except Exception:
        pass
    
    return patterns

def _should_ignore_file(file_path: Path, base_dir: Path, gitignore_patterns: List[re.Pattern]) -> bool:
    """Check if a file should be ignored based on .gitignore patterns."""
    rel_path = file_path.relative_to(base_dir).as_posix()
    
    for pattern in gitignore_patterns:
        if pattern.search(rel_path):
            return True
    
    return False

def _python_grep_search(search_path: Path, pattern: str, file_pattern: str, 
                       case_sensitive: bool, max_results: int, context_lines: int,
                       gitignore_patterns: List[re.Pattern], base_dir: Path) -> List[Dict[str, Any]]:
    """Python-based grep search as fallback."""
    matches = []
    compiled_pattern = re.compile(pattern, re.IGNORECASE if not case_sensitive else 0)
    
    # Convert file_pattern glob to regex
    if file_pattern == "*":
        file_regex = re.compile(r'.*')
    else:
        # Simple glob to regex conversion
        file_regex_str = file_pattern.replace('.', r'\.').replace('*', '.*').replace('?', '.')
        file_regex = re.compile(file_regex_str, re.IGNORECASE)
    
    try:
        for root, dirs, files in os.walk(search_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            for file_name in files:
                file_path = Path(root) / file_name
                
                # Check if file matches pattern
                if not file_regex.search(file_name):
                    continue
                
                # Check if binary
                if _is_binary_file(file_path):
                    continue
                
                # Check gitignore
                if _should_ignore_file(file_path, base_dir, gitignore_patterns):
                    continue
                
                if len(matches) >= max_results:
                    break
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                        for line_num, line in enumerate(lines, start=1):
                            if len(matches) >= max_results:
                                break
                            if compiled_pattern.search(line):
                                # Get context
                                start_line = max(1, line_num - context_lines)
                                end_line = min(len(lines), line_num + context_lines)
                                context_before = [line.rstrip('\n\r') for line in lines[start_line-1:line_num-1]]
                                context_after = [line.rstrip('\n\r') for line in lines[line_num:end_line]]
                                
                                matches.append({
                                    'file': str(file_path.relative_to(base_dir)),
                                    'line_number': line_num,
                                    'line': line.rstrip('\n\r'),
                                    'context_before': context_before,
                                    'context_after': context_after
                                })
                except Exception:
                    continue
    except Exception:
        pass
    
    return matches

@conditional_tool(
    name="workspace_grep",
    annotations={
        "title": "Search Workspace Files with Grep",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def workspace_grep(params: WorkspaceGrepInput) -> str:
    """
    Search for patterns in workspace files using grep.
    
    **Workspace Configuration**: Set MCP_WORKSPACE_ROOT environment variable 
    to your project directory. Defaults to current working directory.
    
    This tool efficiently searches through files in the repository,
    returning only matching lines with context instead of full files.
    Ideal for finding functions, errors, TODOs, or any code pattern.
    
    Security: Repository-rooted, no parent traversal allowed.
    
    Args:
        params (WorkspaceGrepInput): Validated input parameters containing:
            - pattern (str): Regex pattern to search for
            - repo_path (str): Optional subdirectory to search within
            - context_lines (int): Number of lines before/after match (0-5)
            - max_results (int): Maximum matches to return (1-500)
            - file_pattern (str): Glob pattern for files (e.g., '*.py', '*.md')
            - case_sensitive (bool): Whether search is case-sensitive
            - response_format (ResponseFormat): Output format (markdown or json)
    
    Returns:
        str: Formatted search results with file paths, line numbers, and matches
    
    Examples:
        - Use when: "Find all KeyError occurrences"
        - Use when: "Search for function definitions matching github_*"
        - Use when: "Find all TODOs in Python files"
        - Use when: "Search for import statements in src directory"
    
    Error Handling:
        - Returns error if pattern is invalid
        - Returns error if path traversal detected
        - Handles binary files gracefully
        - Respects .gitignore patterns
    """
    try:
        # Validate inputs
        if not params.pattern:
            return "Error: Pattern cannot be empty"
        
        # Validate and get search path
        try:
            search_path = _validate_search_path(params.repo_path)
            base_dir = WORKSPACE_ROOT  # Use configurable workspace
        except ValueError as e:
            return f"Error: {str(e)}"
        
        # Load gitignore patterns
        gitignore_patterns = _load_gitignore(base_dir)
        
        # Try ripgrep first, then grep, then Python fallback
        matches = []
        files_searched = 0
        
        # Try ripgrep
        try:
            cmd = ['rg', '--json', '--no-heading', '--with-filename', '--line-number']
            if params.context_lines > 0:
                cmd.extend(['-C', str(params.context_lines)])
            if not params.case_sensitive:
                cmd.append('--ignore-case')
            if params.file_pattern != '*':
                cmd.extend(['--glob', params.file_pattern])
            cmd.extend([params.pattern, str(search_path)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse ripgrep JSON output
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'match':
                            file_path_str = data['data']['path']['text']
                            file_path = Path(file_path_str)
                            line_num = data['data']['line_number']
                            line_text = data['data']['lines']['text'].rstrip('\n\r')
                            
                            # Convert to relative path if absolute
                            try:
                                rel_path = file_path.relative_to(base_dir)
                            except ValueError:
                                # If it's already relative or outside base_dir, use as-is
                                rel_path = file_path
                            
                            # Get context - ripgrep JSON doesn't include context directly
                            # We'll read it from the file if needed
                            context_before = []
                            context_after = []
                            if params.context_lines > 0:
                                try:
                                    full_path = base_dir / rel_path if not rel_path.is_absolute() else rel_path
                                    if full_path.exists() and full_path.is_file():
                                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                                            all_lines = f.readlines()
                                            if line_num <= len(all_lines):
                                                start_idx = max(0, line_num - 1 - params.context_lines)
                                                end_idx = min(len(all_lines), line_num + params.context_lines)
                                                context_before = [line.rstrip('\n\r') for line in all_lines[start_idx:line_num-1]]
                                                context_after = [line.rstrip('\n\r') for line in all_lines[line_num:end_idx]]
                                except Exception:
                                    pass
                            
                            matches.append({
                                'file': str(rel_path),
                                'line_number': line_num,
                                'line': line_text,
                                'context_before': context_before,
                                'context_after': context_after
                            })
                        elif data.get('type') == 'summary':
                            files_searched = data.get('data', {}).get('stats', {}).get('searched', 0)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # Fallback to Python-based search
            matches = _python_grep_search(
                search_path, params.pattern, params.file_pattern,
                params.case_sensitive, params.max_results, params.context_lines,
                gitignore_patterns, base_dir
            )
            files_searched = len(set(m['file'] for m in matches))
        
        # Limit results
        matches = matches[:params.max_results]
        
        # Format response
        if params.response_format == ResponseFormat.JSON:
            result = {
                'pattern': params.pattern,
                'files_searched': files_searched or len(set(m['file'] for m in matches)),
                'total_matches': len(matches),
                'matches': matches,
                'truncated': len(matches) >= params.max_results
            }
            return json.dumps(result, indent=2)
        
        # Markdown format
        markdown = "# Grep Results\n\n"
        markdown += f"**Pattern:** `{params.pattern}`\n"
        markdown += f"**Files Searched:** {files_searched or len(set(m['file'] for m in matches))}\n"
        markdown += f"**Total Matches:** {len(matches)}\n"
        markdown += f"**Showing:** {len(matches)} matches\n\n"
        
        if not matches:
            markdown += "No matches found.\n"
        else:
            # Group by file
            by_file: Dict[str, List[Dict[str, Any]]] = {}
            for match in matches:
                file_path = match['file']
                if file_path not in by_file:
                    by_file[file_path] = []
                by_file[file_path].append(match)
            
            for file_path, file_matches in by_file.items():
                markdown += f"## {file_path}\n\n"
                for match in file_matches:
                    line_num = match['line_number']
                    line_text = match['line']
                    context_before = match.get('context_before', [])
                    context_after = match.get('context_after', [])
                    
                    markdown += f"**Line {line_num}:**\n"
                    markdown += "```\n"
                    
                    # Show context before
                    for i, ctx_line in enumerate(context_before):
                        ctx_line_num = line_num - len(context_before) + i
                        markdown += f"{ctx_line_num}: {ctx_line}\n"
                    
                    # Show matching line
                    markdown += f"{line_num}: {line_text}\n"
                    
                    # Show context after
                    for i, ctx_line in enumerate(context_after):
                        ctx_line_num = line_num + 1 + i
                        markdown += f"{ctx_line_num}: {ctx_line}\n"
                    
                    markdown += "```\n\n"
                
                markdown += "---\n\n"
        
        markdown += "\n**Summary:**\n"
        if matches:
            by_file = {match['file'] for match in matches}
            markdown += f"- {len(by_file)} files with matches\n"
        else:
            markdown += "- 0 files with matches\n"
        markdown += f"- {len(matches)} total occurrences\n"
        markdown += f"- Pattern: `{params.pattern}`\n"
        
        return _truncate_response(markdown, len(matches))
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="str_replace",
    annotations={
        "title": "Replace String in File",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def str_replace(params: StrReplaceInput) -> str:
    """
    Replace an exact string match in a file with a new string.
    
    **Workspace Configuration**: Set MCP_WORKSPACE_ROOT environment variable
    to your project directory. Defaults to current working directory.
    
    This tool finds an exact match of old_str in the file and replaces it with new_str.
    The match must be unique (exactly one occurrence) to prevent accidental replacements.
    
    Security: Repository-rooted, no parent traversal allowed.
    
    Args:
        params (StrReplaceInput): Validated input parameters containing:
            - path (str): Relative path to file under repository root
            - old_str (str): Exact string to find and replace (must be unique)
            - new_str (str): Replacement string
            - description (Optional[str]): Optional description of the change
    
    Returns:
        str: Confirmation message with details of the replacement
    
    Examples:
        - Use when: "Replace function name in file"
        - Use when: "Update configuration value"
        - Use when: "Fix typo in documentation"
        - Use when: "Update version number"
    
    Error Handling:
        - Returns error if file not found
        - Returns error if old_str not found
        - Returns error if multiple matches found (must be unique)
        - Returns error if path traversal detected
    """
    try:
        # Validate and normalize path
        base_dir = WORKSPACE_ROOT  # Use configurable workspace
        norm_path = Path(params.path).as_posix()
        
        # Check for path traversal
        if '..' in norm_path or norm_path.startswith('..') or os.path.isabs(norm_path):
            return "Error: Path traversal is not allowed."
        
        abs_path = (base_dir / norm_path).resolve()
        
        # Ensure it's within repo root
        try:
            abs_path.relative_to(base_dir)
        except ValueError:
            return f"Error: Access outside workspace root ({WORKSPACE_ROOT}) is not allowed."
        
        if not abs_path.exists():
            return f"Error: File does not exist: {params.path}"
        
        if abs_path.is_dir():
            return f"Error: Path is a directory, not a file: {params.path}"
        
        # Read file content
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            return f"Error: Could not read file: {str(e)}"
        
        # Count occurrences
        count = content.count(params.old_str)
        
        if count == 0:
            return f"Error: String not found in file '{params.path}'. The exact string '{params.old_str[:50]}{'...' if len(params.old_str) > 50 else ''}' was not found."
        
        if count > 1:
            return f"Error: Multiple matches found ({count} occurrences). The string must appear exactly once for safety. Found at {count} locations in '{params.path}'."
        
        # Perform replacement
        new_content = content.replace(params.old_str, params.new_str, 1)
        
        # Write back to file
        try:
            with open(abs_path, 'w', encoding='utf-8', newline='') as f:
                f.write(new_content)
        except Exception as e:
            return f"Error: Could not write to file: {str(e)}"
        
        # Build confirmation message
        result = "✅ String replacement successful!\n\n"
        result += f"**File:** `{params.path}`\n"
        if params.description:
            result += f"**Description:** {params.description}\n"
        result += "**Occurrences:** 1 (unique match)\n"
        result += f"**Replaced:** `{params.old_str[:100]}{'...' if len(params.old_str) > 100 else ''}`\n"
        result += f"**With:** `{params.new_str[:100]}{'...' if len(params.new_str) > 100 else ''}`\n"
        
        return result
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_grep",
    annotations={
        "title": "Search GitHub Repository Files with Grep",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_grep(params: GitHubGrepInput) -> str:
    """
    Search for patterns in GitHub repository files using grep-like functionality.
    
    This tool efficiently searches through files in a GitHub repository,
    returning only matching lines with context instead of full files.
    Ideal for finding functions, errors, TODOs, or any code pattern in remote repos.
    
    **Use Cases:**
    - Verify code exists after pushing changes
    - Search across branches or specific commits
    - Find patterns in remote repositories without cloning
    - Efficient token usage (returns only matches, not full files)
    
    Args:
        params (GitHubGrepInput): Search parameters including:
            - owner/repo: Repository identification
            - pattern: Regex pattern to search for
            - ref: Optional branch/tag/commit
            - file_pattern: File filter (e.g., '*.py')
            - path: Subdirectory to search
            - context_lines: Lines before/after match
            - max_results: Maximum matches
    
    Returns:
        str: Formatted search results with file paths, line numbers, and matches
    
    Examples:
        - "Find all TODOs in Python files"
        - "Search for 'async def' in main branch"
        - "Find error handling patterns after my last push"
    
    Security:
        - Respects GitHub repository permissions
        - Rate limited by GitHub API
        - No local file system access
    """
    import fnmatch
    import re
    
    try:
        # Get repository tree to list files
        ref = params.ref or "HEAD"
        tree_endpoint = f"repos/{params.owner}/{params.repo}/git/trees/{ref}"
        tree_params = {"recursive": "1"}
        
        tree_response = await _make_github_request(
            tree_endpoint,
            params=tree_params,
            token=params.token
        )
        
        if isinstance(tree_response, dict) and tree_response.get("_from_cache"):
            # Retry without conditional request if cached
            tree_response = await _make_github_request(
                tree_endpoint,
                params=tree_params,
                token=params.token
            )
        
        tree_data = tree_response.get("tree", [])
        
        # Filter files by pattern and path
        files_to_search = []
        for item in tree_data:
            if item.get("type") != "blob":  # Only files, not directories
                continue
            
            file_path = item.get("path", "")
            
            # Apply path filter
            if params.path and not file_path.startswith(params.path):
                continue
            
            # Apply file pattern filter
            if params.file_pattern != "*":
                if not fnmatch.fnmatch(file_path, params.file_pattern) and not fnmatch.fnmatch(os.path.basename(file_path), params.file_pattern):
                    continue
            
            files_to_search.append(file_path)
        
        if not files_to_search:
            return f"No files matching pattern '{params.file_pattern}' in path '{params.path or 'repository'}'"
        
        # Compile regex pattern
        flags = 0 if params.case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(params.pattern, flags)
        except re.error as e:
            return f"Error: Invalid regex pattern: {str(e)}"
        
        # Search through files (limit to 100 to avoid rate limits)
        matches = []
        files_searched = 0
        
        for file_path in files_to_search[:100]:
            files_searched += 1
            
            try:
                # Get file content
                content_params = {}
                if params.ref:
                    content_params["ref"] = params.ref
                
                content_response = await _make_github_request(
                    f"repos/{params.owner}/{params.repo}/contents/{file_path}",
                    params=content_params if content_params else None,
                    token=params.token
                )
                
                if isinstance(content_response, dict) and content_response.get("_from_cache"):
                    content_response = await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/contents/{file_path}",
                        params=content_params if content_params else None,
                        token=params.token
                    )
                
                # Decode content
                if content_response.get("encoding") == "base64":
                    content = base64.b64decode(content_response["content"]).decode("utf-8", errors="ignore")
                else:
                    content = content_response.get("content", "")
                
                lines = content.split("\n")
                
                # Search for pattern
                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        # Get context lines
                        start_line = max(1, line_num - params.context_lines)
                        end_line = min(len(lines), line_num + params.context_lines)
                        
                        context_before = []
                        context_after = []
                        for i in range(start_line, line_num):
                            if 1 <= i <= len(lines):
                                context_before.append(lines[i-1].rstrip('\n\r'))
                        for i in range(line_num + 1, end_line + 1):
                            if 1 <= i <= len(lines):
                                context_after.append(lines[i-1].rstrip('\n\r'))
                        
                        matches.append({
                            "file": file_path,
                            "line_number": line_num,
                            "line": line.rstrip('\n\r'),
                            "context_before": context_before,
                            "context_after": context_after
                        })
                        
                        if len(matches) >= params.max_results:
                            break
                
                if len(matches) >= params.max_results:
                    break
                    
            except Exception:
                # Skip files that can't be read (binary, too large, etc.)
                continue
        
        # Limit results
        matches = matches[:params.max_results]
        
        # Format results
        if params.response_format == ResponseFormat.JSON:
            result = {
                "pattern": params.pattern,
                "repository": f"{params.owner}/{params.repo}",
                "ref": params.ref or "default branch",
                "matches": len(matches),
                "files_searched": files_searched,
                "results": matches
            }
            return json.dumps(result, indent=2)
        else:
            # Markdown format
            result = f"# Search Results: '{params.pattern}'\n\n"
            result += f"**Repository:** {params.owner}/{params.repo}\n"
            result += f"**Ref:** {params.ref or 'default branch'}\n"
            result += f"**Matches:** {len(matches)} in {files_searched} files searched\n\n"
            
            if not matches:
                result += "No matches found.\n"
            else:
                # Group by file
                by_file: Dict[str, List[Dict[str, Any]]] = {}
                for match in matches:
                    file_path = match["file"]
                    if file_path not in by_file:
                        by_file[file_path] = []
                    by_file[file_path].append(match)
                
                for file_path, file_matches in by_file.items():
                    result += f"\n## {file_path}\n\n"
                    for match in file_matches:
                        result += f"**Line {match['line_number']}:** `{match['line']}`\n\n"
                        if match.get('context_before') or match.get('context_after'):
                            result += "```\n"
                            for ctx_line in match.get('context_before', []):
                                result += f"  {ctx_line}\n"
                            result += f"> {match['line']}\n"
                            for ctx_line in match.get('context_after', []):
                                result += f"  {ctx_line}\n"
                            result += "```\n\n"
            
            return _truncate_response(result, len(matches))
    
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_read_file_chunk",
    annotations={
        "title": "Read GitHub File Chunk",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_read_file_chunk(params: GitHubReadFileChunkInput) -> str:
    """
    Read a specific range of lines from a GitHub repository file.
    
    This tool efficiently reads just the lines you need from a GitHub file,
    avoiding loading entire large files into memory. Perfect for:
    - Reading specific functions or sections
    - Checking code after pushing changes
    - Reviewing specific parts of documentation
    - Token-efficient file reading (90%+ savings vs full file)
    
    Args:
        params (GitHubReadFileChunkInput): Parameters including:
            - owner/repo: Repository identification
            - path: File path in repository
            - start_line: Starting line (1-based)
            - num_lines: Number of lines to read (max 500)
            - ref: Optional branch/tag/commit
    
    Returns:
        str: Numbered lines from the file with metadata
    
    Examples:
        - "Read lines 50-100 of main.py from main branch"
        - "Show me the first 20 lines of README.md"
        - "Read the function starting at line 150"
    
    Security:
        - Respects GitHub repository permissions
        - No local file system access
        - Rate limited by GitHub API
    """
    try:
        # Get file content from GitHub
        content_params = {}
        if params.ref:
            content_params["ref"] = params.ref
        
        content_response = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            params=content_params if content_params else None,
            token=params.token
        )
        
        if isinstance(content_response, dict) and content_response.get("_from_cache"):
            # Retry without conditional request if cached
            content_response = await _make_github_request(
                f"repos/{params.owner}/{params.repo}/contents/{params.path}",
                params=content_params if content_params else None,
                token=params.token
            )
        
        # Decode content
        if content_response.get("encoding") == "base64":
            content = base64.b64decode(content_response["content"]).decode("utf-8", errors="ignore")
        else:
            content = content_response.get("content", "")
        
        lines = content.split("\n")
        total_lines = len(lines)
        
        # Calculate line range
        start_idx = params.start_line - 1  # Convert to 0-based
        end_idx = min(start_idx + params.num_lines, total_lines)
        
        if start_idx >= total_lines:
            return f"Error: start_line {params.start_line} exceeds file length ({total_lines} lines)"
        
        if start_idx < 0:
            return "Error: start_line must be >= 1"
        
        # Extract requested lines
        chunk_lines = lines[start_idx:end_idx]
        
        # Format output with line numbers
        result = f"# File: {params.path}\n\n"
        result += f"**Repository:** {params.owner}/{params.repo}\n"
        result += f"**Ref:** {params.ref or 'default branch'}\n"
        result += f"**Lines:** {params.start_line}-{params.start_line + len(chunk_lines) - 1} of {total_lines}\n"
        result += f"**Size:** {content_response.get('size', 0)} bytes\n\n"
        result += "```\n"
        
        for i, line in enumerate(chunk_lines, start=params.start_line):
            result += f"{i:4d}: {line}\n"
        
        result += "```\n"
        
        if end_idx < total_lines:
            result += f"\n*({total_lines - end_idx} more lines not shown)*\n"
        
        return result
    
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_str_replace",
    annotations={
        "title": "Replace String in GitHub File",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_str_replace(params: GitHubStrReplaceInput) -> str:
    """
    Replace an exact string match in a GitHub repository file with a new string.
    
    This tool finds an exact match of old_str in the GitHub file and replaces it with new_str.
    The match must be unique (exactly one occurrence) to prevent accidental replacements.
    Updates the file via GitHub API with a commit.
    
    **Use Cases:**
    - Make surgical edits to GitHub files without cloning
    - Update configuration values in remote repos
    - Fix typos or update documentation on GitHub
    - Token-efficient file updates (only changes what's needed)
    
    Args:
        params (GitHubStrReplaceInput): Parameters including:
            - owner/repo: Repository identification
            - path: File path in repository
            - old_str: Exact string to find and replace (must be unique)
            - new_str: Replacement string
            - ref: Optional branch (defaults to default branch)
            - commit_message: Optional commit message
            - description: Optional description of the change
    
    Returns:
        str: Confirmation message with commit details
    
    Examples:
        - "Replace version number in README.md on GitHub"
        - "Update configuration value in remote file"
        - "Fix typo in GitHub documentation"
    
    Security:
        - Respects GitHub repository permissions
        - Requires write access to repository
        - No local file system access
    """
    
    try:
        # Get token (try param, then GitHub App, then PAT)
        token = await _get_auth_token_fallback(params.token)
        if not token:
            return json.dumps({
                "error": "Authentication required",
                "message": "GitHub token required for updating files. Set GITHUB_TOKEN environment variable or pass token parameter.",
                "success": False
            }, indent=2)
        
        # Get current file content and SHA
        content_params = {}
        if params.ref:
            content_params["ref"] = params.ref
        
        file_response = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            params=content_params if content_params else None,
            token=token
        )
        
        if isinstance(file_response, dict) and file_response.get("_from_cache"):
            file_response = await _make_github_request(
                f"repos/{params.owner}/{params.repo}/contents/{params.path}",
                params=content_params if content_params else None,
                token=token
            )
        
        # Decode content
        if file_response.get("encoding") == "base64":
            content = base64.b64decode(file_response["content"]).decode("utf-8", errors="replace")
        else:
            content = file_response.get("content", "")
        
        current_sha = file_response.get("sha")
        if not current_sha:
            return "Error: Could not get file SHA. File may not exist or you may not have access."
        
        # Count occurrences
        count = content.count(params.old_str)
        
        if count == 0:
            return f"Error: String not found in file '{params.path}'. The exact string '{params.old_str[:50]}{'...' if len(params.old_str) > 50 else ''}' was not found."
        
        if count > 1:
            return f"Error: Multiple matches found ({count} occurrences). The string must appear exactly once for safety. Found at {count} locations in '{params.path}'."
        
        # Perform replacement
        new_content = content.replace(params.old_str, params.new_str, 1)
        
        # Encode new content
        new_content_bytes = new_content.encode('utf-8')
        new_content_b64 = base64.b64encode(new_content_bytes).decode('utf-8')
        
        # Generate commit message if not provided
        commit_msg = params.commit_message
        if not commit_msg:
            commit_msg = f"Update {params.path}"
            if params.description:
                commit_msg += f": {params.description}"
            else:
                commit_msg += f" (replace '{params.old_str[:30]}{'...' if len(params.old_str) > 30 else ''}')"
        
        # Update file via GitHub API
        update_data = {
            "message": commit_msg,
            "content": new_content_b64,
            "sha": current_sha
        }
        
        if params.ref:
            update_data["branch"] = params.ref
        
        update_response = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            method="PUT",
            token=token,
            json=update_data
        )
        
        # Format confirmation
        result = "✅ String replacement successful on GitHub!\n\n"
        result += f"**Repository:** {params.owner}/{params.repo}\n"
        result += f"**File:** {params.path}\n"
        result += f"**Branch:** {params.ref or 'default branch'}\n"
        if params.description:
            result += f"**Description:** {params.description}\n"
        result += f"**Commit:** {update_response.get('commit', {}).get('sha', 'N/A')[:7]}\n"
        result += f"**Commit Message:** {commit_msg}\n"
        result += f"**URL:** {update_response.get('content', {}).get('html_url', 'N/A')}\n\n"
        result += f"**Replaced:** `{params.old_str[:100]}{'...' if len(params.old_str) > 100 else ''}`\n"
        result += f"**With:** `{params.new_str[:100]}{'...' if len(params.new_str) > 100 else ''}`\n"
        
        return result
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
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

@conditional_tool()
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

@conditional_tool(
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
                    labels = ', '.join([f"`{label['name']}`" for label in issue['labels']])
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

@conditional_tool(
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
    # Get token (try param, then GitHub App, then PAT)
    auth_token = await _get_auth_token_fallback(params.token)
    
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for creating issues. Set GITHUB_TOKEN or configure GitHub App authentication.",
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
        
        # Return the FULL GitHub API response as JSON
        return json.dumps(data, indent=2)
        
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)

@conditional_tool(
    name="github_update_issue",
    annotations={
        "title": "Update GitHub Issue",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_update_issue(params: UpdateIssueInput) -> str:
    """
    Update an existing GitHub issue.
    
    This tool modifies issue properties including state (open/closed),
    title, body, labels, assignees, and milestone. Only provided fields
    will be updated - others remain unchanged.
    
    Args:
        params (UpdateIssueInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - issue_number (int): Issue number to update
            - state (Optional[str]): 'open' or 'closed'
            - title (Optional[str]): New title
            - body (Optional[str]): New description
            - labels (Optional[List[str]]): Label names
            - assignees (Optional[List[str]]): Usernames to assign
            - milestone (Optional[int]): Milestone number
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Updated issue details with confirmation message
    
    Examples:
        - Use when: "Close issue #28"
        - Use when: "Update issue #29 labels"
        - Use when: "Reassign issue #30 to user"
    
    Error Handling:
        - Returns error if issue not found (404)
        - Returns error if authentication fails (401/403)
        - Returns error if invalid parameters (422)
    """
    
    # Get token (try param, then GitHub App, then PAT)
    token = await _get_auth_token_fallback(params.token)
    if not token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for updating issues. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    # Validate state if provided
    if params.state and params.state not in ["open", "closed"]:
        return f"Error: Invalid state '{params.state}'. Must be 'open' or 'closed'."
    
    try:
        # Build update payload
        update_data = {}
        if params.state is not None:
            update_data["state"] = params.state
        if params.title is not None:
            update_data["title"] = params.title
        if params.body is not None:
            update_data["body"] = params.body
        if params.labels is not None:
            update_data["labels"] = params.labels
        if params.assignees is not None:
            update_data["assignees"] = params.assignees
        if params.milestone is not None:
            update_data["milestone"] = params.milestone
        
        # Make request
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/issues/{params.issue_number}",
            method="PATCH",
            token=token,
            json=update_data
        )
        
        # Format response
        changes = []
        if params.state:
            changes.append(f"State: {params.state}")
        if params.title:
            changes.append("Title updated")
        if params.body:
            changes.append("Description updated")
        if params.labels:
            changes.append(f"Labels: {', '.join(params.labels)}")
        if params.assignees:
            changes.append(f"Assignees: {', '.join(params.assignees)}")
        if params.milestone:
            changes.append(f"Milestone: #{params.milestone}")
        
        result = f"""✅ Issue Updated Successfully!

**Issue:** #{data['number']} - {data['title']}
**Repository:** {params.owner}/{params.repo}
**URL:** {data['html_url']}

**Changes Applied:**
{chr(10).join(f'- {change}' for change in changes)}

**Current State:** {data['state']}
**Updated:** {_format_timestamp(data['updated_at'])}
"""
        
        return result
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
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
        markdown = "# Repository Search Results\n\n"
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

@conditional_tool(
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
        
        # Handle cache marker (304 Not Modified response)
        if isinstance(data, dict) and data.get('_from_cache'):
            # For 304 responses, we need to make a fresh request without conditional headers
            # This is a workaround - ideally we'd cache the actual response data
            # For now, retry without cache to get the actual data
            client = GhClient.instance()
            response = await client.request(
                method="GET",
                path=f"/repos/{params.owner}/{params.repo}/contents/{params.path}",
                token=params.token,
                params=params_dict,
                headers={"Cache-Control": "no-cache"}  # Force fresh request
            )
            response.raise_for_status()
            data = response.json()
        
        # Validate that we have the expected structure
        if not isinstance(data, dict) or 'name' not in data:
            return f"Error: Unexpected response format from GitHub API. Expected file data, got: {type(data).__name__}"
        
        # Handle file content
        if data.get('encoding') == 'base64':
            import base64
            content = base64.b64decode(data['content']).decode('utf-8', errors='replace')
        else:
            content = data.get('content', '')
        
        result = f"""# File: {data.get('name', 'unknown')}

**Path:** {data.get('path', 'unknown')}
**Size:** {data.get('size', 0):,} bytes
**Type:** {data.get('type', 'unknown')}
**Encoding:** {data.get('encoding', 'none')}
**SHA:** {data.get('sha', 'unknown')}
**URL:** {data.get('html_url', 'unknown')}

---

**Content:**

```
{content}
```
"""
        
        return _truncate_response(result)
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
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
        token = await _get_auth_token_fallback(params.token)
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

@conditional_tool(
    name="github_list_branches",
    annotations={
        "title": "List Repository Branches",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_branches(params: ListBranchesInput) -> str:
    """
    List all branches in a GitHub repository.
    
    Returns branch names, latest commit SHA, protection status, and whether
    it's the default branch. Essential for branch management workflows.
    
    Args:
        params (ListBranchesInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - protected (Optional[bool]): Filter by protected status
            - per_page (Optional[int]): Results per page (1-100, default 30)
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: List of branches with details
    
    Examples:
        - Use when: "List all branches in my repository"
        - Use when: "Show me only protected branches"
        - Use when: "What branches exist in this repo?"
    
    Error Handling:
        - Returns error if repository not found (404)
        - Returns error if authentication fails (401/403)
    """
    try:
        auth_token = await _get_auth_token_fallback(params.token)
        
        if not auth_token:
            return json.dumps({
                "error": "Authentication required",
                "message": "GitHub token required for listing branches. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False
            }, indent=2)
        
        endpoint = f"repos/{params.owner}/{params.repo}/branches"
        query_params = {"per_page": params.per_page}
        
        if params.protected is not None:
            query_params["protected"] = "true" if params.protected else "false"
        
        data = await _make_github_request(
            endpoint,
            method="GET",
            token=auth_token,
            params=query_params
        )
        
        repo_info = await _make_github_request(
            f"repos/{params.owner}/{params.repo}",
            method="GET",
            token=auth_token
        )
        default_branch = repo_info.get("default_branch", "main")
        
        branches = data if isinstance(data, list) else []
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "owner": params.owner,
                "repo": params.repo,
                "default_branch": default_branch,
                "total_branches": len(branches),
                "branches": [
                    {
                        "name": b["name"],
                        "commit_sha": b["commit"]["sha"],
                        "protected": b.get("protected", False),
                        "is_default": b["name"] == default_branch
                    }
                    for b in branches
                ]
            }, indent=2)
        else:
            result = f"# Branches: {params.owner}/{params.repo}\n\n"
            result += f"**Default Branch:** {default_branch}\n"
            result += f"**Total Branches:** {len(branches)}\n\n"
            
            if branches:
                result += "| Branch | Commit | Protected | Default |\n"
                result += "|--------|--------|-----------|----------|\n"
                for b in branches:
                    sha = b["commit"]["sha"][:7]
                    protected = "🔒" if b.get("protected", False) else "🔓"
                    is_default = "⭐" if b["name"] == default_branch else ""
                    result += f"| {b['name']} | {sha} | {protected} | {is_default} |\n"
            else:
                result += "*No branches found*\n"
            
            return result
            
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_create_branch",
    annotations={
        "title": "Create Branch",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_create_branch(params: CreateBranchInput) -> str:
    """
    Create a new branch in a GitHub repository.
    
    Creates a new branch from a specified ref (branch, tag, or commit).
    Uses Git References API for reliability.
    
    Args:
        params (CreateBranchInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - branch (str): New branch name
            - from_ref (str): Branch, tag, or commit SHA to branch from (default: "main")
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Confirmation message with branch details
    
    Examples:
        - Use when: "Create a new feature branch from main"
        - Use when: "Create branch from specific commit"
        - Use when: "Branch off from tag v1.0.0"
    
    Error Handling:
        - Returns error if branch already exists (422)
        - Returns error if from_ref doesn't exist (404)
        - Returns error if authentication fails (401/403)
    """
    try:
        auth_token = await _get_auth_token_fallback(params.token)
        
        if not auth_token:
            return json.dumps({
                "error": "Authentication required",
                "message": "GitHub token required for creating branches.",
                "success": False
            }, indent=2)
        
        ref_endpoint = f"repos/{params.owner}/{params.repo}/git/ref/heads/{params.from_ref}"
        try:
            ref_data = await _make_github_request(
                ref_endpoint,
                method="GET",
                token=auth_token
            )
            sha = ref_data["object"]["sha"]
        except Exception:
            commit_endpoint = f"repos/{params.owner}/{params.repo}/commits/{params.from_ref}"
            commit_data = await _make_github_request(
                commit_endpoint,
                method="GET",
                token=auth_token
            )
            sha = commit_data["sha"]
        
        create_endpoint = f"repos/{params.owner}/{params.repo}/git/refs"
        await _make_github_request(
            create_endpoint,
            method="POST",
            token=auth_token,
            json={
                "ref": f"refs/heads/{params.branch}",
                "sha": sha
            }
        )
        
        return json.dumps({
            "success": True,
            "branch": params.branch,
            "sha": sha,
            "from_ref": params.from_ref,
            "url": f"https://github.com/{params.owner}/{params.repo}/tree/{params.branch}",
            "message": f"Branch '{params.branch}' created successfully from '{params.from_ref}'"
        }, indent=2)
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_get_branch",
    annotations={
        "title": "Get Branch Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_branch(params: GetBranchInput) -> str:
    """
    Get detailed information about a branch including protection status,
    latest commit, and whether it's ahead/behind the default branch.
    
    Args:
        params (GetBranchInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - branch (str): Branch name
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Detailed branch information
    
    Examples:
        - Use when: "Get details about the feature branch"
        - Use when: "Check if branch is protected"
        - Use when: "Show me the latest commit on this branch"
    
    Error Handling:
        - Returns error if branch not found (404)
        - Returns error if authentication fails (401/403)
    """
    try:
        auth_token = await _get_auth_token_fallback(params.token)
        
        if not auth_token:
            return json.dumps({
                "error": "Authentication required",
                "success": False
            }, indent=2)
        
        endpoint = f"repos/{params.owner}/{params.repo}/branches/{params.branch}"
        data = await _make_github_request(
            endpoint,
            method="GET",
            token=auth_token
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "branch": data["name"],
                "protected": data.get("protected", False),
                "commit": {
                    "sha": data["commit"]["sha"],
                    "message": data["commit"]["commit"]["message"].split('\n')[0],
                    "author": data["commit"]["commit"]["author"]["name"],
                    "date": data["commit"]["commit"]["author"]["date"]
                },
                "url": f"https://github.com/{params.owner}/{params.repo}/tree/{params.branch}"
            }, indent=2)
        else:
            result = f"# Branch: {data['name']}\n\n"
            result += f"**Repository:** {params.owner}/{params.repo}\n"
            result += f"**Protected:** {'🔒 Yes' if data.get('protected', False) else '🔓 No'}\n\n"
            result += "## Latest Commit\n\n"
            result += f"**SHA:** {data['commit']['sha'][:7]}\n"
            result += f"**Message:** {data['commit']['commit']['message'].split(chr(10))[0]}\n"
            result += f"**Author:** {data['commit']['commit']['author']['name']}\n"
            result += f"**Date:** {_format_timestamp(data['commit']['commit']['author']['date'])}\n\n"
            result += f"**URL:** https://github.com/{params.owner}/{params.repo}/tree/{params.branch}\n"
            
            return result
            
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_delete_branch",
    annotations={
        "title": "Delete Branch",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_delete_branch(params: DeleteBranchInput) -> str:
    """
    Delete a branch from a GitHub repository.
    
    Safety: Cannot delete the default branch or protected branches.
    Use with caution - this is permanent!
    
    Args:
        params (DeleteBranchInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - branch (str): Branch name to delete
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Confirmation message
    
    Examples:
        - Use when: "Delete the old feature branch"
        - Use when: "Clean up merged branches"
        - Use when: "Remove test branch"
    
    Error Handling:
        - Returns error if trying to delete default branch
        - Returns error if trying to delete protected branch
        - Returns error if branch not found (404)
    """
    try:
        auth_token = await _get_auth_token_fallback(params.token)
        
        if not auth_token:
            return json.dumps({
                "error": "Authentication required",
                "success": False
            }, indent=2)
        
        repo_info = await _make_github_request(
            f"repos/{params.owner}/{params.repo}",
            method="GET",
            token=auth_token
        )
        
        if params.branch == repo_info.get("default_branch"):
            return json.dumps({
                "error": "Cannot delete default branch",
                "message": f"'{params.branch}' is the default branch and cannot be deleted.",
                "success": False
            }, indent=2)
        
        try:
            branch_data = await _make_github_request(
                f"repos/{params.owner}/{params.repo}/branches/{params.branch}",
                method="GET",
                token=auth_token
            )
            if branch_data.get("protected", False):
                return json.dumps({
                    "error": "Cannot delete protected branch",
                    "message": f"'{params.branch}' is protected and cannot be deleted.",
                    "success": False
                }, indent=2)
        except Exception:
            pass
        
        endpoint = f"repos/{params.owner}/{params.repo}/git/refs/heads/{params.branch}"
        await _make_github_request(
            endpoint,
            method="DELETE",
            token=auth_token
        )
        
        return json.dumps({
            "success": True,
            "branch": params.branch,
            "message": f"Branch '{params.branch}' deleted successfully"
        }, indent=2)
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_compare_branches",
    annotations={
        "title": "Compare Branches",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_compare_branches(params: CompareBranchesInput) -> str:
    """
    Compare two branches to see commits ahead/behind and files changed.
    
    Useful before merging to understand what will change.
    
    Args:
        params (CompareBranchesInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - base (str): Base branch name
            - head (str): Head branch name to compare
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Comparison results with commits and files changed
    
    Examples:
        - Use when: "Compare feature branch to main"
        - Use when: "See what's different between branches"
        - Use when: "Check if branch is ready to merge"
    
    Error Handling:
        - Returns error if branches not found (404)
        - Returns error if authentication fails (401/403)
    """
    try:
        auth_token = await _get_auth_token_fallback(params.token)
        
        if not auth_token:
            return json.dumps({
                "error": "Authentication required",
                "success": False
            }, indent=2)
        
        endpoint = f"repos/{params.owner}/{params.repo}/compare/{params.base}...{params.head}"
        data = await _make_github_request(
            endpoint,
            method="GET",
            token=auth_token
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "base": params.base,
                "head": params.head,
                "status": data["status"],
                "ahead_by": data["ahead_by"],
                "behind_by": data["behind_by"],
                "total_commits": data["total_commits"],
                "files_changed": len(data.get("files", [])),
                "commits": [
                    {
                        "sha": c["sha"][:7],
                        "message": c["commit"]["message"].split('\n')[0],
                        "author": c["commit"]["author"]["name"]
                    }
                    for c in data["commits"][:10]
                ]
            }, indent=2)
        else:
            result = "# Branch Comparison\n\n"
            result += f"**Base:** {params.base} → **Head:** {params.head}\n\n"
            result += f"**Status:** {data['status']}\n"
            result += f"**Commits Ahead:** {data['ahead_by']}\n"
            result += f"**Commits Behind:** {data['behind_by']}\n"
            result += f"**Files Changed:** {len(data.get('files', []))}\n\n"
            
            if data["ahead_by"] > 0:
                result += f"## Commits in {params.head} (not in {params.base})\n\n"
                for commit in data["commits"][:5]:
                    sha = commit["sha"][:7]
                    msg = commit["commit"]["message"].split('\n')[0]
                    result += f"- {sha}: {msg}\n"
                if data["total_commits"] > 5:
                    result += f"\n*...and {data['total_commits'] - 5} more commits*\n"
            
            return result
            
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
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
                    markdown += "- **Draft:** Yes\n"
                
                if pr.get('merged'):
                    markdown += "- **Merged:** Yes\n"
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

@conditional_tool(
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
        
        markdown += "\n## Statistics\n"
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

@conditional_tool(
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
        
        # Handle cache marker (304 Not Modified response)
        if isinstance(data, dict) and data.get('_from_cache'):
            # For 304 responses, we need to make a fresh request without conditional headers
            # This is a workaround - ideally we'd cache the actual response data
            # For now, retry without cache to get the actual data
            client = GhClient.instance()
            response = await client.request(
                method="GET",
                path=f"/{endpoint}",
                token=params.token,
                params=params_dict,
                headers={"Cache-Control": "no-cache"}  # Force fresh request
            )
            response.raise_for_status()
            data = response.json()
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data) if isinstance(data, list) else 1)
        
        # Markdown format
        if isinstance(data, dict):
            # Single file returned
            # Validate structure before accessing keys
            if 'name' not in data:
                return f"Error: Unexpected response format from GitHub API. Expected file data, got: {type(data).__name__}"
            
            return f"""# Single File

This path points to a file, not a directory.

**Name:** {data.get('name', 'unknown')}
**Path:** {data.get('path', 'unknown')}
**Size:** {data.get('size', 0):,} bytes
**Type:** {data.get('type', 'unknown')}
**URL:** {data.get('html_url', 'unknown')}

Use `github_get_file_content` to retrieve the file content.
"""
        
        # Directory listing - validate it's a list
        if not isinstance(data, list):
            return f"Error: Unexpected response format from GitHub API. Expected list of items, got: {type(data).__name__}"
        
        display_path = path or "(root)"
        markdown = f"# Contents of /{display_path}\n\n"
        markdown += f"**Repository:** {params.owner}/{params.repo}\n"
        if params.ref:
            markdown += f"**Branch/Ref:** {params.ref}\n"
        markdown += f"**Items:** {len(data)}\n\n"
        
        # Separate directories and files
        directories = [item for item in data if isinstance(item, dict) and item.get('type') == 'dir']
        files = [item for item in data if isinstance(item, dict) and item.get('type') == 'file']
        
        if directories:
            markdown += "## 📁 Directories\n"
            for item in directories:
                name = item.get('name', 'unknown')
                markdown += f"- `{name}/`\n"
            markdown += "\n"
        
        if files:
            markdown += "## 📄 Files\n"
            for item in files:
                name = item.get('name', 'unknown')
                size = item.get('size', 0)
                size_kb = size / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb >= 1 else f"{size} bytes"
                markdown += f"- `{name}` ({size_str})\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
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

@conditional_tool(
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

# ============================================================================
# GitHub Actions Expansion Tools (Phase 2 - Batch 1)
# ============================================================================

class GetWorkflowInput(BaseModel):
    """Input model for getting a specific workflow."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    workflow_id: str = Field(..., description="Workflow ID (numeric) or workflow file name (e.g., 'ci.yml')", min_length=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class TriggerWorkflowInput(BaseModel):
    """Input model for triggering a workflow dispatch."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    workflow_id: str = Field(..., description="Workflow ID (numeric) or workflow file name (e.g., 'ci.yml')", min_length=1)
    ref: str = Field(..., description="Branch, tag, or commit SHA to trigger workflow on", min_length=1)
    inputs: Optional[Dict[str, str]] = Field(default=None, description="Input parameters for workflow (key-value pairs)")
    token: Optional[str] = Field(default=None, description="GitHub token (required for triggering workflows)")

class GetWorkflowRunInput(BaseModel):
    """Input model for getting a specific workflow run."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class ListWorkflowRunJobsInput(BaseModel):
    """Input model for listing jobs in a workflow run."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    filter: Optional[str] = Field(default=None, description="Filter jobs: 'latest' or 'all'")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetJobInput(BaseModel):
    """Input model for getting a specific job."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    job_id: int = Field(..., description="Job ID", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetJobLogsInput(BaseModel):
    """Input model for getting job logs."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    job_id: int = Field(..., description="Job ID", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")

class RerunWorkflowInput(BaseModel):
    """Input model for rerunning a workflow."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    token: Optional[str] = Field(default=None, description="GitHub token (required for rerunning workflows)")

class RerunFailedJobsInput(BaseModel):
    """Input model for rerunning failed jobs in a workflow run."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    token: Optional[str] = Field(default=None, description="GitHub token (required for rerunning workflows)")

class CancelWorkflowRunInput(BaseModel):
    """Input model for canceling a workflow run."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    token: Optional[str] = Field(default=None, description="GitHub token (required for canceling workflows)")

class ListWorkflowRunArtifactsInput(BaseModel):
    """Input model for listing artifacts from a workflow run."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetArtifactInput(BaseModel):
    """Input model for getting artifact details."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    artifact_id: int = Field(..., description="Artifact ID", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class DeleteArtifactInput(BaseModel):
    """Input model for deleting an artifact."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    artifact_id: int = Field(..., description="Artifact ID", ge=1)
    token: Optional[str] = Field(default=None, description="GitHub token (required for deleting artifacts)")

@conditional_tool(
    name="github_get_workflow",
    annotations={
        "title": "Get GitHub Actions Workflow",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
            token=params.token
        )
        
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

@conditional_tool(
    name="github_trigger_workflow",
    annotations={
        "title": "Trigger GitHub Actions Workflow",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
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
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for triggering workflows.",
            "success": False
        }, indent=2)
    
    try:
        payload = {
            "ref": params.ref
        }
        if params.inputs:
            payload["inputs"] = params.inputs
        
        # 202 Accepted is expected for workflow dispatch
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/workflows/{params.workflow_id}/dispatches",
            method="POST",
            token=auth_token,
            json=payload
        )
        
        return json.dumps({
            "success": True,
            "message": f"Workflow {params.workflow_id} triggered successfully on {params.ref}",
            "workflow_id": params.workflow_id,
            "ref": params.ref
        }, indent=2)
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_get_workflow_run",
    annotations={
        "title": "Get GitHub Actions Workflow Run",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        status_emoji = "🔄" if data['status'] == "in_progress" else "✅" if data['conclusion'] == "success" else "❌" if data['conclusion'] == "failure" else "⏸️" if data['status'] == "queued" else "⚠️"
        
        markdown = f"# {status_emoji} Workflow Run #{data['run_number']}: {data['name']}\n\n"
        markdown += f"- **Status:** {data['status']}\n"
        markdown += f"- **Conclusion:** {data['conclusion'] or 'N/A'}\n"
        markdown += f"- **Triggered By:** {data['triggering_actor']['login']}\n"
        markdown += f"- **Branch:** `{data['head_branch']}`\n"
        markdown += f"- **Commit:** {data['head_sha'][:8]} - {data['head_commit']['message'][:60]}\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **Updated:** {_format_timestamp(data['updated_at'])}\n"
        
        if data.get('run_started_at'):
            markdown += f"- **Started:** {_format_timestamp(data['run_started_at'])}\n"
        if data.get('run_attempt'):
            markdown += f"- **Attempt:** {data['run_attempt']}\n"
        
        markdown += f"- **URL:** {data['html_url']}\n"
        
        return markdown
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_list_workflow_run_jobs",
    annotations={
        "title": "List GitHub Actions Workflow Run Jobs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
        params_dict = {
            "per_page": params.per_page,
            "page": params.page
        }
        if params.filter:
            params_dict["filter"] = params.filter
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}/jobs",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, data['total_count'])
        
        markdown = f"# Jobs for Workflow Run #{params.run_id}\n\n"
        markdown += f"**Total Jobs:** {data['total_count']}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(data['jobs'])} jobs\n\n"
        
        if not data['jobs']:
            markdown += "No jobs found.\n"
        else:
            for job in data['jobs']:
                status_emoji = "🔄" if job['status'] == "in_progress" else "✅" if job['conclusion'] == "success" else "❌" if job['conclusion'] == "failure" else "⏸️" if job['status'] == "queued" else "⚠️"
                
                markdown += f"## {status_emoji} {job['name']}\n"
                markdown += f"- **ID:** {job['id']}\n"
                markdown += f"- **Status:** {job['status']}\n"
                markdown += f"- **Conclusion:** {job['conclusion'] or 'N/A'}\n"
                markdown += f"- **Runner:** {job.get('runner_name', 'N/A')}\n"
                markdown += f"- **Started:** {_format_timestamp(job['started_at']) if job.get('started_at') else 'N/A'}\n"
                markdown += f"- **Completed:** {_format_timestamp(job['completed_at']) if job.get('completed_at') else 'N/A'}\n"
                markdown += f"- **URL:** {job['html_url']}\n\n"
        
        return _truncate_response(markdown, data['total_count'])
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_get_job",
    annotations={
        "title": "Get GitHub Actions Job",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        status_emoji = "🔄" if data['status'] == "in_progress" else "✅" if data['conclusion'] == "success" else "❌" if data['conclusion'] == "failure" else "⏸️" if data['status'] == "queued" else "⚠️"
        
        markdown = f"# {status_emoji} Job: {data['name']}\n\n"
        markdown += f"- **ID:** {data['id']}\n"
        markdown += f"- **Status:** {data['status']}\n"
        markdown += f"- **Conclusion:** {data['conclusion'] or 'N/A'}\n"
        markdown += f"- **Runner:** {data.get('runner_name', 'N/A')}\n"
        markdown += f"- **Workflow:** {data.get('workflow_name', 'N/A')}\n"
        markdown += f"- **Started:** {_format_timestamp(data['started_at']) if data.get('started_at') else 'N/A'}\n"
        markdown += f"- **Completed:** {_format_timestamp(data['completed_at']) if data.get('completed_at') else 'N/A'}\n"
        
        if data.get('steps'):
            markdown += f"\n### Steps ({len(data['steps'])}):\n"
            for step in data['steps']:
                step_emoji = "✅" if step['conclusion'] == "success" else "❌" if step['conclusion'] == "failure" else "🔄" if step['status'] == "in_progress" else "⏸️"
                markdown += f"- {step_emoji} {step['name']}: {step['status']} / {step['conclusion'] or 'N/A'}\n"
        
        markdown += f"\n- **URL:** {data['html_url']}\n"
        
        return markdown
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_get_job_logs",
    annotations={
        "title": "Get GitHub Actions Job Logs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
        from src.github_mcp.github_client import GhClient
        
        auth_token = await _get_auth_token_fallback(params.token)
        if not auth_token:
            return json.dumps({
                "error": "Authentication required",
                "message": "GitHub token required for accessing job logs.",
                "success": False
            }, indent=2)
        
        client = GhClient.instance()
        response = await client.request(
            "GET",
            f"repos/{params.owner}/{params.repo}/actions/jobs/{params.job_id}/logs",
            token=auth_token,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        
        # Logs are returned as plain text
        logs_text = response.text if hasattr(response, 'text') else str(response)
        
        # Truncate if too long (GitHub API may return very large logs)
        max_length = 50000  # ~50KB
        if len(logs_text) > max_length:
            truncated = logs_text[:max_length]
            return f"# Job Logs (Truncated - showing first {max_length} characters)\n\n```\n{truncated}\n...\n```\n\n*Logs truncated. Full logs available at job URL.*"
        
        return f"# Job Logs\n\n```\n{logs_text}\n```"
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_rerun_workflow",
    annotations={
        "title": "Rerun GitHub Actions Workflow",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
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
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for rerunning workflows.",
            "success": False
        }, indent=2)
    
    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}/rerun",
            method="POST",
            token=auth_token
        )
        
        return json.dumps({
            "success": True,
            "message": f"Workflow run {params.run_id} rerun initiated",
            "run_id": params.run_id
        }, indent=2)
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_rerun_failed_jobs",
    annotations={
        "title": "Rerun Failed Jobs in Workflow",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
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
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for rerunning workflows.",
            "success": False
        }, indent=2)
    
    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}/rerun-failed-jobs",
            method="POST",
            token=auth_token
        )
        
        return json.dumps({
            "success": True,
            "message": f"Failed jobs in workflow run {params.run_id} rerun initiated",
            "run_id": params.run_id
        }, indent=2)
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_cancel_workflow_run",
    annotations={
        "title": "Cancel GitHub Actions Workflow Run",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
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
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for canceling workflows.",
            "success": False
        }, indent=2)
    
    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}/cancel",
            method="POST",
            token=auth_token
        )
        
        return json.dumps({
            "success": True,
            "message": f"Workflow run {params.run_id} cancellation requested",
            "run_id": params.run_id
        }, indent=2)
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_list_workflow_run_artifacts",
    annotations={
        "title": "List GitHub Actions Workflow Run Artifacts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_workflow_run_artifacts(params: ListWorkflowRunArtifactsInput) -> str:
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
        params_dict = {
            "per_page": params.per_page,
            "page": params.page
        }
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/runs/{params.run_id}/artifacts",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, data['total_count'])
        
        markdown = f"# Artifacts for Workflow Run #{params.run_id}\n\n"
        markdown += f"**Total Artifacts:** {data['total_count']}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(data['artifacts'])} artifacts\n\n"
        
        if not data['artifacts']:
            markdown += "No artifacts found.\n"
        else:
            for artifact in data['artifacts']:
                size_mb = artifact['size_in_bytes'] / (1024 * 1024)
                markdown += f"## {artifact['name']}\n"
                markdown += f"- **ID:** {artifact['id']}\n"
                markdown += f"- **Size:** {size_mb:.2f} MB ({artifact['size_in_bytes']:,} bytes)\n"
                markdown += f"- **Created:** {_format_timestamp(artifact['created_at'])}\n"
                markdown += f"- **Expires:** {_format_timestamp(artifact['expires_at'])}\n"
                markdown += f"- **URL:** {artifact['archive_download_url']}\n\n"
        
        return _truncate_response(markdown, data['total_count'])
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_get_artifact",
    annotations={
        "title": "Get GitHub Actions Artifact",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        size_mb = data['size_in_bytes'] / (1024 * 1024)
        markdown = f"# Artifact: {data['name']}\n\n"
        markdown += f"- **ID:** {data['id']}\n"
        markdown += f"- **Size:** {size_mb:.2f} MB ({data['size_in_bytes']:,} bytes)\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **Expires:** {_format_timestamp(data['expires_at'])}\n"
        markdown += f"- **Download URL:** {data['archive_download_url']}\n"
        
        return markdown
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_delete_artifact",
    annotations={
        "title": "Delete GitHub Actions Artifact",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
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
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for deleting artifacts.",
            "success": False
        }, indent=2)
    
    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/actions/artifacts/{params.artifact_id}",
            method="DELETE",
            token=auth_token
        )
        
        return json.dumps({
            "success": True,
            "message": f"Artifact {params.artifact_id} deleted successfully",
            "artifact_id": params.artifact_id
        }, indent=2)
        
    except Exception as e:
        return _handle_api_error(e)

# ============================================================================
# Security Suite Tools (Phase 2 - Batch 2)
# ============================================================================

# Dependabot Input Models
class ListDependabotAlertsInput(BaseModel):
    """Input model for listing Dependabot alerts."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, description="Filter by state: 'open', 'dismissed', 'fixed'")
    severity: Optional[str] = Field(default=None, description="Filter by severity: 'low', 'medium', 'high', 'critical'")
    ecosystem: Optional[str] = Field(default=None, description="Filter by ecosystem (e.g., 'npm', 'pip', 'maven')")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetDependabotAlertInput(BaseModel):
    """Input model for getting a specific Dependabot alert."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class UpdateDependabotAlertInput(BaseModel):
    """Input model for updating a Dependabot alert."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    state: str = Field(..., description="New state: 'dismissed' or 'open'")
    dismissed_reason: Optional[str] = Field(default=None, description="Reason for dismissal: 'fix_started', 'inaccurate', 'no_bandwidth', 'not_used', 'tolerable_risk'")
    dismissed_comment: Optional[str] = Field(default=None, max_length=280, description="Optional comment when dismissing")
    token: Optional[str] = Field(default=None, description="GitHub token (required for updating alerts)")

class ListOrgDependabotAlertsInput(BaseModel):
    """Input model for listing organization Dependabot alerts."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    org: str = Field(..., description="Organization name", min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, description="Filter by state: 'open', 'dismissed', 'fixed'")
    severity: Optional[str] = Field(default=None, description="Filter by severity: 'low', 'medium', 'high', 'critical'")
    ecosystem: Optional[str] = Field(default=None, description="Filter by ecosystem")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

# Code Scanning Input Models
class ListCodeScanningAlertsInput(BaseModel):
    """Input model for listing code scanning alerts."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, description="Filter by state: 'open', 'dismissed', 'fixed'")
    severity: Optional[str] = Field(default=None, description="Filter by severity: 'critical', 'high', 'medium', 'low', 'warning', 'note'")
    tool_name: Optional[str] = Field(default=None, description="Filter by tool name (e.g., 'CodeQL', 'ESLint')")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetCodeScanningAlertInput(BaseModel):
    """Input model for getting a specific code scanning alert."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class UpdateCodeScanningAlertInput(BaseModel):
    """Input model for updating a code scanning alert."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    state: str = Field(..., description="New state: 'dismissed' or 'open'")
    dismissed_reason: Optional[str] = Field(default=None, description="Reason for dismissal: 'false_positive', 'wont_fix', 'used_in_tests'")
    dismissed_comment: Optional[str] = Field(default=None, max_length=280, description="Optional comment when dismissing")
    token: Optional[str] = Field(default=None, description="GitHub token (required for updating alerts)")

class ListCodeScanningAnalysesInput(BaseModel):
    """Input model for listing code scanning analyses."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    tool_name: Optional[str] = Field(default=None, description="Filter by tool name")
    ref: Optional[str] = Field(default=None, description="Filter by branch/tag/commit")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

# Secret Scanning Input Models
class ListSecretScanningAlertsInput(BaseModel):
    """Input model for listing secret scanning alerts."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, description="Filter by state: 'open', 'resolved'")
    secret_type: Optional[str] = Field(default=None, description="Filter by secret type (e.g., 'github_personal_access_token')")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetSecretScanningAlertInput(BaseModel):
    """Input model for getting a specific secret scanning alert."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class UpdateSecretScanningAlertInput(BaseModel):
    """Input model for updating a secret scanning alert."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    state: str = Field(..., description="New state: 'resolved' or 'open'")
    resolution: Optional[str] = Field(default=None, description="Resolution: 'false_positive', 'wont_fix', 'revoked', 'used_in_tests'")
    token: Optional[str] = Field(default=None, description="GitHub token (required for updating alerts)")

# Security Advisories Input Models
class ListRepoSecurityAdvisoriesInput(BaseModel):
    """Input model for listing repository security advisories."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, description="Filter by state: 'triage', 'draft', 'published', 'closed'")
    per_page: Optional[int] = Field(default=30, ge=1, le=100, description="Results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetSecurityAdvisoryInput(BaseModel):
    """Input model for getting a specific security advisory."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1, max_length=100)
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    ghsa_id: str = Field(..., description="GitHub Security Advisory ID (e.g., 'GHSA-xxxx-xxxx-xxxx')", min_length=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

# Dependabot Tools
@conditional_tool(
    name="github_list_dependabot_alerts",
    annotations={
        "title": "List Dependabot Alerts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
        params_dict = {
            "per_page": params.per_page,
            "page": params.page
        }
        if params.state:
            params_dict["state"] = params.state
        if params.severity:
            params_dict["severity"] = params.severity
        if params.ecosystem:
            params_dict["ecosystem"] = params.ecosystem
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/dependabot/alerts",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))
        
        markdown = f"# Dependabot Alerts for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Alerts:** {len(data)}\n\n"
        
        if not data:
            markdown += "No Dependabot alerts found.\n"
        else:
            for alert in data:
                severity_emoji = "🔴" if alert['security_vulnerability']['severity'] == "critical" else "🟠" if alert['security_vulnerability']['severity'] == "high" else "🟡" if alert['security_vulnerability']['severity'] == "medium" else "🟢"
                
                markdown += f"## {severity_emoji} Alert #{alert['number']}: {alert['dependency']['package']['name']}\n"
                markdown += f"- **State:** {alert['state']}\n"
                markdown += f"- **Severity:** {alert['security_vulnerability']['severity']}\n"
                markdown += f"- **Ecosystem:** {alert['dependency']['package']['ecosystem']}\n"
                markdown += f"- **Vulnerable Version:** {alert['security_vulnerability']['vulnerable_version_range']}\n"
                markdown += f"- **Patched Version:** {alert['security_vulnerability']['first_patched_version'].get('identifier', 'N/A')}\n"
                markdown += f"- **Created:** {_format_timestamp(alert['created_at'])}\n"
                markdown += f"- **URL:** {alert['html_url']}\n\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_get_dependabot_alert",
    annotations={
        "title": "Get Dependabot Alert",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        severity_emoji = "🔴" if data['security_vulnerability']['severity'] == "critical" else "🟠" if data['security_vulnerability']['severity'] == "high" else "🟡" if data['security_vulnerability']['severity'] == "medium" else "🟢"
        
        markdown = f"# {severity_emoji} Dependabot Alert #{data['number']}\n\n"
        markdown += f"- **State:** {data['state']}\n"
        markdown += f"- **Severity:** {data['security_vulnerability']['severity']}\n"
        markdown += f"- **Package:** {data['dependency']['package']['name']}\n"
        markdown += f"- **Ecosystem:** {data['dependency']['package']['ecosystem']}\n"
        markdown += f"- **Vulnerable Version:** {data['security_vulnerability']['vulnerable_version_range']}\n"
        markdown += f"- **Patched Version:** {data['security_vulnerability']['first_patched_version'].get('identifier', 'N/A')}\n"
        
        if data.get('dismissed_at'):
            markdown += f"- **Dismissed:** {_format_timestamp(data['dismissed_at'])}\n"
            if data.get('dismissed_reason'):
                markdown += f"- **Dismissal Reason:** {data['dismissed_reason']}\n"
        
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **URL:** {data['html_url']}\n"
        
        return markdown
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_update_dependabot_alert",
    annotations={
        "title": "Update Dependabot Alert",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
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
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for updating Dependabot alerts.",
            "success": False
        }, indent=2)
    
    try:
        payload = {
            "state": params.state
        }
        if params.state == "dismissed":
            if params.dismissed_reason:
                payload["dismissed_reason"] = params.dismissed_reason
            if params.dismissed_comment:
                payload["dismissed_comment"] = params.dismissed_comment
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/dependabot/alerts/{params.alert_number}",
            method="PATCH",
            token=auth_token,
            json=payload
        )
        
        return json.dumps(data, indent=2)
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_list_org_dependabot_alerts",
    annotations={
        "title": "List Organization Dependabot Alerts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_org_dependabot_alerts(params: ListOrgDependabotAlertsInput) -> str:
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
        params_dict = {
            "per_page": params.per_page,
            "page": params.page
        }
        if params.state:
            params_dict["state"] = params.state
        if params.severity:
            params_dict["severity"] = params.severity
        if params.ecosystem:
            params_dict["ecosystem"] = params.ecosystem
        
        data = await _make_github_request(
            f"orgs/{params.org}/dependabot/alerts",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))
        
        markdown = f"# Dependabot Alerts for Organization: {params.org}\n\n"
        markdown += f"**Total Alerts:** {len(data)}\n\n"
        
        if not data:
            markdown += "No Dependabot alerts found.\n"
        else:
            for alert in data:
                severity_emoji = "🔴" if alert['security_vulnerability']['severity'] == "critical" else "🟠" if alert['security_vulnerability']['severity'] == "high" else "🟡" if alert['security_vulnerability']['severity'] == "medium" else "🟢"
                
                markdown += f"## {severity_emoji} {alert['repository']['full_name']} - Alert #{alert['number']}\n"
                markdown += f"- **Package:** {alert['dependency']['package']['name']}\n"
                markdown += f"- **Severity:** {alert['security_vulnerability']['severity']}\n"
                markdown += f"- **State:** {alert['state']}\n"
                markdown += f"- **URL:** {alert['html_url']}\n\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

# Code Scanning Tools
@conditional_tool(
    name="github_list_code_scanning_alerts",
    annotations={
        "title": "List Code Scanning Alerts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
        params_dict = {
            "per_page": params.per_page,
            "page": params.page
        }
        if params.state:
            params_dict["state"] = params.state
        if params.severity:
            params_dict["severity"] = params.severity
        if params.tool_name:
            params_dict["tool_name"] = params.tool_name
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/code-scanning/alerts",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))
        
        markdown = f"# Code Scanning Alerts for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Alerts:** {len(data)}\n\n"
        
        if not data:
            markdown += "No code scanning alerts found.\n"
        else:
            for alert in data:
                severity_emoji = "🔴" if alert.get('rule', {}).get('severity') == "error" else "🟠" if alert.get('rule', {}).get('severity') == "warning" else "🟡"
                
                markdown += f"## {severity_emoji} Alert #{alert['number']}: {alert['rule']['name']}\n"
                markdown += f"- **State:** {alert['state']}\n"
                markdown += f"- **Severity:** {alert['rule'].get('severity', 'N/A')}\n"
                markdown += f"- **Tool:** {alert['tool']['name']}\n"
                markdown += f"- **Created:** {_format_timestamp(alert['created_at'])}\n"
                markdown += f"- **URL:** {alert['html_url']}\n\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_get_code_scanning_alert",
    annotations={
        "title": "Get Code Scanning Alert",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        severity_emoji = "🔴" if data.get('rule', {}).get('severity') == "error" else "🟠" if data.get('rule', {}).get('severity') == "warning" else "🟡"
        
        markdown = f"# {severity_emoji} Code Scanning Alert #{data['number']}\n\n"
        markdown += f"- **State:** {data['state']}\n"
        markdown += f"- **Rule:** {data['rule']['name']}\n"
        markdown += f"- **Severity:** {data['rule'].get('severity', 'N/A')}\n"
        markdown += f"- **Tool:** {data['tool']['name']}\n"
        
        if data.get('most_recent_instance'):
            instance = data['most_recent_instance']
            markdown += f"- **Location:** {instance.get('location', {}).get('path', 'N/A')}:{instance.get('location', {}).get('start_line', 'N/A')}\n"
        
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **URL:** {data['html_url']}\n"
        
        return markdown
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_update_code_scanning_alert",
    annotations={
        "title": "Update Code Scanning Alert",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_update_code_scanning_alert(params: UpdateCodeScanningAlertInput) -> str:
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
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for updating code scanning alerts.",
            "success": False
        }, indent=2)
    
    try:
        payload = {
            "state": params.state
        }
        if params.state == "dismissed":
            if params.dismissed_reason:
                payload["dismissed_reason"] = params.dismissed_reason
            if params.dismissed_comment:
                payload["dismissed_comment"] = params.dismissed_comment
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/code-scanning/alerts/{params.alert_number}",
            method="PATCH",
            token=auth_token,
            json=payload
        )
        
        return json.dumps(data, indent=2)
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_list_code_scanning_analyses",
    annotations={
        "title": "List Code Scanning Analyses",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_code_scanning_analyses(params: ListCodeScanningAnalysesInput) -> str:
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
        params_dict = {
            "per_page": params.per_page,
            "page": params.page
        }
        if params.tool_name:
            params_dict["tool_name"] = params.tool_name
        if params.ref:
            params_dict["ref"] = params.ref
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/code-scanning/analyses",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))
        
        markdown = f"# Code Scanning Analyses for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Analyses:** {len(data)}\n\n"
        
        if not data:
            markdown += "No code scanning analyses found.\n"
        else:
            for analysis in data:
                markdown += f"## Analysis: {analysis.get('tool', {}).get('name', 'N/A')}\n"
                markdown += f"- **Ref:** {analysis.get('ref', 'N/A')}\n"
                markdown += f"- **Commit SHA:** {analysis.get('commit_sha', 'N/A')[:8]}\n"
                markdown += f"- **Created:** {_format_timestamp(analysis['created_at'])}\n"
                markdown += f"- **URL:** {analysis.get('url', 'N/A')}\n\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

# Secret Scanning Tools
@conditional_tool(
    name="github_list_secret_scanning_alerts",
    annotations={
        "title": "List Secret Scanning Alerts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_secret_scanning_alerts(params: ListSecretScanningAlertsInput) -> str:
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
        params_dict = {
            "per_page": params.per_page,
            "page": params.page
        }
        if params.state:
            params_dict["state"] = params.state
        if params.secret_type:
            params_dict["secret_type"] = params.secret_type
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/secret-scanning/alerts",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))
        
        markdown = f"# Secret Scanning Alerts for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Alerts:** {len(data)}\n\n"
        
        if not data:
            markdown += "No secret scanning alerts found.\n"
        else:
            for alert in data:
                markdown += f"## 🔐 Alert #{alert['number']}\n"
                markdown += f"- **State:** {alert['state']}\n"
                markdown += f"- **Secret Type:** {alert.get('secret_type', 'N/A')}\n"
                markdown += f"- **Created:** {_format_timestamp(alert['created_at'])}\n"
                markdown += f"- **URL:** {alert['html_url']}\n\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_get_secret_scanning_alert",
    annotations={
        "title": "Get Secret Scanning Alert",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        markdown = f"# 🔐 Secret Scanning Alert #{data['number']}\n\n"
        markdown += f"- **State:** {data['state']}\n"
        markdown += f"- **Secret Type:** {data.get('secret_type', 'N/A')}\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        
        if data.get('resolution'):
            markdown += f"- **Resolution:** {data['resolution']}\n"
        
        markdown += f"- **URL:** {data['html_url']}\n"
        
        return markdown
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_update_secret_scanning_alert",
    annotations={
        "title": "Update Secret Scanning Alert",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_update_secret_scanning_alert(params: UpdateSecretScanningAlertInput) -> str:
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
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for updating secret scanning alerts.",
            "success": False
        }, indent=2)
    
    try:
        payload = {
            "state": params.state
        }
        if params.state == "resolved" and params.resolution:
            payload["resolution"] = params.resolution
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/secret-scanning/alerts/{params.alert_number}",
            method="PATCH",
            token=auth_token,
            json=payload
        )
        
        return json.dumps(data, indent=2)
        
    except Exception as e:
        return _handle_api_error(e)

# Security Advisories Tools
@conditional_tool(
    name="github_list_repo_security_advisories",
    annotations={
        "title": "List Repository Security Advisories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_repo_security_advisories(params: ListRepoSecurityAdvisoriesInput) -> str:
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
        params_dict = {
            "per_page": params.per_page,
            "page": params.page
        }
        if params.state:
            params_dict["state"] = params.state
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/security-advisories",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))
        
        markdown = f"# Security Advisories for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Advisories:** {len(data)}\n\n"
        
        if not data:
            markdown += "No security advisories found.\n"
        else:
            for advisory in data:
                markdown += f"## {advisory.get('ghsa_id', 'N/A')}: {advisory.get('summary', 'N/A')}\n"
                markdown += f"- **State:** {advisory.get('state', 'N/A')}\n"
                markdown += f"- **Severity:** {advisory.get('severity', 'N/A')}\n"
                markdown += f"- **Published:** {_format_timestamp(advisory['published_at']) if advisory.get('published_at') else 'Not published'}\n"
                markdown += f"- **URL:** {advisory.get('html_url', 'N/A')}\n\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
    name="github_get_security_advisory",
    annotations={
        "title": "Get Security Advisory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
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
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        markdown = f"# Security Advisory: {data.get('ghsa_id', 'N/A')}\n\n"
        markdown += f"- **Summary:** {data.get('summary', 'N/A')}\n"
        markdown += f"- **State:** {data.get('state', 'N/A')}\n"
        markdown += f"- **Severity:** {data.get('severity', 'N/A')}\n"
        markdown += f"- **Published:** {_format_timestamp(data['published_at']) if data.get('published_at') else 'Not published'}\n"
        
        if data.get('description'):
            markdown += f"\n### Description\n{data['description'][:500]}{'...' if len(data.get('description', '')) > 500 else ''}\n"
        
        markdown += f"\n- **URL:** {data.get('html_url', 'N/A')}\n"
        
        return markdown
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
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
    
    # Get token (try param, then GitHub App, then PAT)
    auth_token = await _get_auth_token_fallback(params.token)
    
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for creating pull requests. Set GITHUB_TOKEN or configure GitHub App authentication.",
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
        
        # Return a wrapper that includes a stable "created" marker while preserving the full API response
        # This includes all fields: number, html_url, state, title, etc.
        # This makes it easy for programmatic use (e.g., TypeScript code)
        response = {
            "success": True,
            "created": True,
            "pr": data
        }
        return json.dumps(response, indent=2)
        
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = _handle_api_error(e)
        
        return json.dumps(error_info, indent=2)


@conditional_tool(
    name="github_add_issue_comment",
    annotations={
        "title": "Add Issue Comment",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_add_issue_comment(params: AddIssueCommentInput) -> str:
    """
    Add a comment to an existing GitHub issue.
    
    This tool posts a new comment to the specified issue using the
    authenticated user's identity.
    
    Args:
        params (AddIssueCommentInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - issue_number (int): Issue number to comment on
            - body (str): Comment content in Markdown format
            - token (Optional[str]): GitHub token (optional - uses GITHUB_TOKEN env var if not provided)
    
    Returns:
        str: JSON string with the created comment details including id, URL, and body.
    """
    # Get token (try param, then GitHub App, then PAT)
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for adding issue comments. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        payload = {
            "body": params.body,
        }
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/issues/{params.issue_number}/comments",
            method="POST",
            token=auth_token,
            json=payload
        )
        
        # Return the FULL GitHub API response as JSON for programmatic use
        return json.dumps(data, indent=2)
    
    except Exception as e:
        # Reuse generic error handler for consistent error surfaces
        return _handle_api_error(e)


@conditional_tool(
    name="github_list_gists",
    annotations={
        "title": "List Gists",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_gists(params: ListGistsInput) -> str:
    """
    List gists for the authenticated user or a specified user.
    
    If a username is provided, public gists for that user are returned and
    authentication is optional. If username is omitted, the authenticated
    user's gists are listed and a token is required.
    """
    # Only require auth when listing for the authenticated user
    auth_token: Optional[str] = None
    if params.username is None:
        auth_token = await _get_auth_token_fallback(params.token)
        if not auth_token:
            return json.dumps({
                "error": "Authentication required",
                "message": "GitHub token required for listing your own gists. Set GITHUB_TOKEN or pass a token parameter, or provide a username to list public gists.",
                "success": False
            }, indent=2)
    else:
        # Allow anonymous listing of another user's public gists
        auth_token = params.token
    
    try:
        query: Dict[str, Any] = {}
        if params.since:
            query["since"] = params.since
        if params.per_page:
            query["per_page"] = params.per_page
        if params.page:
            query["page"] = params.page
        
        if params.username:
            endpoint = f"users/{params.username}/gists"
        else:
            endpoint = "gists"
        
        data = await _make_github_request(
            endpoint,
            token=auth_token,
            params=query
        )
        
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_get_gist",
    annotations={
        "title": "Get Gist",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_gist(params: GetGistInput) -> str:
    """
    Get detailed information about a specific gist including files and metadata.
    """
    try:
        data = await _make_github_request(
            f"gists/{params.gist_id}",
            token=params.token
        )
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_create_gist",
    annotations={
        "title": "Create Gist",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_create_gist(params: CreateGistInput) -> str:
    """
    Create a new gist with one or more files.
    
    Requires authentication with a token that has gist scope.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for creating gists. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        files_payload: Dict[str, Dict[str, str]] = {}
        for filename, file_def in params.files.items():
            files_payload[filename] = {"content": file_def.content}
        
        payload: Dict[str, Any] = {
            "files": files_payload,
            "public": bool(params.public),
        }
        if params.description is not None:
            payload["description"] = params.description
        
        data = await _make_github_request(
            "gists",
            method="POST",
            token=auth_token,
            json=payload
        )
        
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_update_gist",
    annotations={
        "title": "Update Gist",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_update_gist(params: UpdateGistInput) -> str:
    """
    Update an existing gist's description and files.
    
    To delete a file, set its value to null in the files mapping.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for updating gists. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        payload: Dict[str, Any] = {}
        if params.description is not None:
            payload["description"] = params.description
        
        if params.files is not None:
            files_payload: Dict[str, Any] = {}
            for filename, file_def in params.files.items():
                if file_def is None:
                    # Delete this file from the gist
                    files_payload[filename] = None
                else:
                    files_payload[filename] = {"content": file_def.content}
            payload["files"] = files_payload
        
        data = await _make_github_request(
            f"gists/{params.gist_id}",
            method="PATCH",
            token=auth_token,
            json=payload
        )
        
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_list_labels",
    annotations={
        "title": "List Labels",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_labels(params: ListLabelsInput) -> str:
    """
    List all labels in a repository.
    """
    try:
        query: Dict[str, Any] = {}
        if params.per_page:
            query["per_page"] = params.per_page
        if params.page:
            query["page"] = params.page
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/labels",
            token=params.token,
            params=query
        )
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_create_label",
    annotations={
        "title": "Create Label",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_create_label(params: CreateLabelInput) -> str:
    """
    Create a new label in a repository.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for creating labels. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        payload: Dict[str, Any] = {
            "name": params.name,
            "color": params.color.lstrip("#"),
        }
        if params.description is not None:
            payload["description"] = params.description
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/labels",
            method="POST",
            token=auth_token,
            json=payload
        )
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_delete_label",
    annotations={
        "title": "Delete Label",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_delete_label(params: DeleteLabelInput) -> str:
    """
    Delete a label from a repository.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for deleting labels. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/labels/{params.name}",
            method="DELETE",
            token=auth_token
        )
        return json.dumps({
            "success": True,
            "message": f"Label '{params.name}' deleted from {params.owner}/{params.repo}."
        }, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_list_stargazers",
    annotations={
        "title": "List Stargazers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_stargazers(params: ListStargazersInput) -> str:
    """
    List users who have starred a repository.
    """
    try:
        query: Dict[str, Any] = {}
        if params.per_page:
            query["per_page"] = params.per_page
        if params.page:
            query["page"] = params.page
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/stargazers",
            token=params.token,
            params=query
        )
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_star_repository",
    annotations={
        "title": "Star Repository",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_star_repository(params: StarRepositoryInput) -> str:
    """
    Star a repository for the authenticated user.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for starring repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        # PUT returns 204 No Content on success
        await _make_github_request(
            f"user/starred/{params.owner}/{params.repo}",
            method="PUT",
            token=auth_token
        )
        return json.dumps({
            "success": True,
            "message": f"Repository {params.owner}/{params.repo} has been starred."
        }, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_unstar_repository",
    annotations={
        "title": "Unstar Repository",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_unstar_repository(params: UnstarRepositoryInput) -> str:
    """
    Unstar a repository for the authenticated user.
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for unstarring repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        await _make_github_request(
            f"user/starred/{params.owner}/{params.repo}",
            method="DELETE",
            token=auth_token
        )
        return json.dumps({
            "success": True,
            "message": f"Repository {params.owner}/{params.repo} has been unstarred."
        }, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_get_authenticated_user",
    annotations={
        "title": "Get Authenticated User",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_get_authenticated_user(params: GetAuthenticatedUserInput) -> str:
    """
    Get the authenticated user's profile (the 'me' endpoint).
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for retrieving the authenticated user. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        data = await _make_github_request(
            "user",
            token=auth_token
        )
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_list_user_repos",
    annotations={
        "title": "List User Repositories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_user_repos(params: ListUserReposInput) -> str:
    """
    List repositories for the authenticated user or a specified user.
    """
    # When username is omitted, we must use the authenticated endpoint and require auth
    auth_token: Optional[str] = None
    if params.username is None:
        auth_token = await _get_auth_token_fallback(params.token)
        if not auth_token:
            return json.dumps({
                "error": "Authentication required",
                "message": "GitHub token required for listing your own repositories. Set GITHUB_TOKEN or pass a token, or provide a username to list public repos.",
                "success": False
            }, indent=2)
    else:
        auth_token = params.token
    
    try:
        query: Dict[str, Any] = {}
        if params.type:
            query["type"] = params.type
        if params.sort:
            query["sort"] = params.sort
        if params.direction:
            query["direction"] = params.direction
        if params.per_page:
            query["per_page"] = params.per_page
        if params.page:
            query["page"] = params.page
        
        if params.username:
            endpoint = f"users/{params.username}/repos"
        else:
            endpoint = "user/repos"
        
        data = await _make_github_request(
            endpoint,
            token=auth_token,
            params=query
        )
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_list_org_repos",
    annotations={
        "title": "List Organization Repositories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_list_org_repos(params: ListOrgReposInput) -> str:
    """
    List repositories for an organization.
    """
    try:
        query: Dict[str, Any] = {}
        if params.type:
            query["type"] = params.type
        if params.sort:
            query["sort"] = params.sort
        if params.direction:
            query["direction"] = params.direction
        if params.per_page:
            query["per_page"] = params.per_page
        if params.page:
            query["page"] = params.page
        
        data = await _make_github_request(
            f"orgs/{params.org}/repos",
            token=params.token,
            params=query
        )
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@conditional_tool(
    name="github_search_users",
    annotations={
        "title": "Search Users",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_search_users(params: SearchUsersInput) -> str:
    """
    Search for GitHub users using the public search API.
    """
    try:
        query_params: Dict[str, Any] = {
            "q": params.query,
            "per_page": params.per_page,
            "page": params.page
        }
        if params.sort:
            query_params["sort"] = params.sort
        if params.order:
            query_params["order"] = params.order.value if isinstance(params.order, Enum) else params.order
        
        data = await _make_github_request(
            "search/users",
            token=params.token,
            params=query_params
        )
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
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
                except Exception:
                    result["reviews"] = "Error fetching reviews"
            
            if params.include_commits:
                try:
                    commits = await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/commits",
                        token=params.token
                    )
                    result["commits"] = commits
                except Exception:
                    result["commits"] = "Error fetching commits"
            
            if params.include_files:
                try:
                    files = await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/files",
                        token=params.token
                    )
                    result["files"] = files
                except Exception:
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
        markdown += "## Changes\n"
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
            except Exception:
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
            except Exception:
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
            except Exception:
                markdown += "## Changed Files\n\nError fetching files.\n\n"
        
        return _truncate_response(markdown)
        
    except Exception as e:
        return _handle_api_error(e)

@conditional_tool(
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
        token = await _get_auth_token_fallback(params.token)
        if not token:
            return "Error: Authentication required for GraphQL. Set GITHUB_TOKEN or configure GitHub App authentication."

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

@conditional_tool(
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
        markdown = "# Code Search Results\n\n"
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
        # Return JSON error if response_format is JSON
        if params.response_format == ResponseFormat.JSON:
            error_data = {
                "error": True,
                "message": _handle_api_error(e),
                "query": params.query
            }
            return json.dumps(error_data, indent=2)
        return _handle_api_error(e)

@conditional_tool(
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
        markdown = "# Issue Search Results\n\n"
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
                    labels = ', '.join([f"`{label['name']}`" for label in issue['labels'][:5]])
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

@conditional_tool(
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

@conditional_tool(
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

@conditional_tool(
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
    
    Note:
        GitHub Apps currently cannot create releases that involve tagging commits,
        because there is no dedicated "releases" permission scope for Apps in
        the GitHub API. For this reason, authentication for this tool will
        automatically fall back to Personal Access Token (PAT) when a GitHub
        App token is not sufficient. This behavior is implemented in
        `get_auth_token()` and `_get_auth_token_fallback()`.
    
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
    # Get token (try param, then GitHub App, then PAT with automatic PAT fallback
    # for operations like releases where GitHub Apps lack permissions)
    # See: auth/github_app.get_auth_token for details.
    auth_token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for creating releases. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)

    try:
        # Get default branch and commit SHA if target_commitish not provided
        target_commitish = params.target_commitish
        if not target_commitish:
            repo_info = await _make_github_request(
                f"repos/{params.owner}/{params.repo}",
                token=auth_token
            )
            target_commitish = repo_info['default_branch']
        
        # Get commit SHA from target_commitish (could be branch name or SHA)
        # If it's a branch name, get the SHA; if it's already a SHA, use it
        if len(target_commitish) == 40 and all(c in '0123456789abcdef' for c in target_commitish.lower()):
            # It's already a SHA
            commit_sha = target_commitish
        else:
            # It's a branch name, get the SHA
            branch_ref = await _make_github_request(
                f"repos/{params.owner}/{params.repo}/git/ref/heads/{target_commitish}",
                token=auth_token
            )
            commit_sha = branch_ref['object']['sha']
        
        # CRITICAL: Create the Git tag FIRST using Git References API
        # This ensures the tag exists before creating the release
        # Without this, GitHub creates "untagged" releases
        try:
            # Check if tag already exists
            await _make_github_request(
                f"repos/{params.owner}/{params.repo}/git/refs/tags/{params.tag_name}",
                method="GET",
                token=auth_token
            )
            # Tag exists, that's fine - continue to create release
        except httpx.HTTPStatusError as tag_check_error:
            # Only create tag if it's a 404 (not found) error
            # If it's an auth error (401/403), we should fail immediately
            status_code = tag_check_error.response.status_code
            
            # If it's an auth error (401/403), re-raise it immediately
            if status_code in (401, 403):
                raise tag_check_error
            
            # Only create tag if it's a 404 (tag doesn't exist)
            if status_code == 404:
                tag_ref_data = {
                    "ref": f"refs/tags/{params.tag_name}",
                    "sha": commit_sha
                }
                try:
                    await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/git/refs",
                        method="POST",
                        token=auth_token,
                        json=tag_ref_data
                    )
                    # Tag created successfully - continue to create release
                except Exception as tag_create_error:
                    # If tag creation fails, raise the error (don't silently continue)
                    raise tag_create_error
            else:
                # Other HTTP errors (500, etc.) - re-raise
                raise tag_check_error
        except Exception as tag_check_error:
            # Non-HTTP errors (network, timeout, etc.) - re-raise
            raise tag_check_error
        
        # Now create the release (tag already exists)
        endpoint = f"repos/{params.owner}/{params.repo}/releases"
        body_data = {
            "tag_name": params.tag_name,
            "name": params.name or params.tag_name,
            "draft": params.draft or False,
            "prerelease": params.prerelease or False,
            "target_commitish": target_commitish
        }
        
        # Add optional fields
        if params.body:
            body_data["body"] = params.body
        
        # Create the release
        data = await _make_github_request(
            endpoint,
            method="POST",
            token=auth_token,
            json=body_data
        )
        
        # Return the FULL GitHub API response as JSON
        return json.dumps(data, indent=2)
        
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)

@conditional_tool(
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
    auth_token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for updating releases. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
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
        
        # Return the FULL GitHub API response as JSON
        return json.dumps(data, indent=2)
        
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)

# Phase 2.1: File Management Tools


@conditional_tool(
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
    auth_token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for creating files. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)

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
        
        # Return a wrapper that includes a stable "created" marker while preserving the full API response
        response = {
            "success": True,
            "created": True,
            "file": data
        }
        return json.dumps(response, indent=2)
        
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
            
            # Add helpful context for common errors
            if error_info["status_code"] == 422:
                error_info["hint"] = "This file already exists. Use 'github_update_file' to modify it, or 'github_delete_file' to remove it first."
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)


@conditional_tool(
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
    auth_token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for updating files. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)

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
        
        # Return the FULL GitHub API response as JSON
        return json.dumps(data, indent=2)
        
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
            
            # Add helpful context for common errors
            if error_info["status_code"] == 409:
                error_info["hint"] = "The file SHA doesn't match. The file may have been modified. Get the current SHA with 'github_get_file_content' and try again."
            elif error_info["status_code"] == 404:
                error_info["hint"] = "File not found. Use 'github_create_file' to create it first."
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)


@conditional_tool(
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
    auth_token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for deleting files. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)

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

@conditional_tool(
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
        token = await _get_auth_token_fallback(params.token)
        if not token:
            return "Error: GitHub token required for batch file operations. Set GITHUB_TOKEN or configure GitHub App authentication."
        
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
        
        response = "# Batch File Operations Complete! ✅\n\n"
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

@conditional_tool(
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
        "# Workflow Suggestion",
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

@conditional_tool(
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
    auth_token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for creating repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
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
        # Return the FULL GitHub API response as JSON
        return json.dumps(data, indent=2)
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)


@conditional_tool(
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
    auth_token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for deleting repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        await _make_github_request(f"repos/{params.owner}/{params.repo}", method="DELETE", token=auth_token)
        # DELETE operations return 204 No Content (empty response)
        # Return structured success JSON
        return json.dumps({
            "success": True,
            "message": f"Repository {params.owner}/{params.repo} deleted successfully",
            "deleted": True
        }, indent=2)
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)


@conditional_tool(
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
    auth_token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for updating repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        body: Dict[str, Any] = {}
        for field in ["name", "description", "homepage", "private", "has_issues", "has_projects", "has_wiki", "default_branch", "archived"]:
            value = getattr(params, field)
            if value is not None:
                body[field] = value
        data = await _make_github_request(f"repos/{params.owner}/{params.repo}", method="PATCH", token=auth_token, json=body)
        # Return the FULL GitHub API response as JSON
        return json.dumps(data, indent=2)
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)


@conditional_tool(
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
    auth_token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for transferring repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
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
        # Return the FULL GitHub API response as JSON
        return json.dumps(data, indent=2)
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)


@conditional_tool(
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
    auth_token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for archiving repositories. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        body = {"archived": params.archived}
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}",
            method="PATCH",
            token=auth_token,
            json=body
        )
        # Return the FULL GitHub API response as JSON
        return json.dumps(data, indent=2)
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)

@conditional_tool(
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
    # Get token (try param, then GitHub App, then PAT)
    token = await _get_auth_token_fallback(params.token)
    
    # Ensure we have a valid token before proceeding
    if not token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for merging pull requests. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
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
        
        # Return the FULL GitHub API response as JSON
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)

@conditional_tool(
    name="github_close_pull_request",
    annotations={
        "title": "Close Pull Request",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def github_close_pull_request(params: ClosePullRequestInput) -> str:
    """
    Close a pull request without merging.
    
    This tool closes a PR and optionally adds a closing comment explaining why.
    Useful for stale PRs, superseded PRs, or PRs that won't be merged.
    
    Args:
        params (ClosePullRequestInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pull_number (int): Pull request number
            - comment (Optional[str]): Closing comment/explanation
            - token (Optional[str]): GitHub token
    
    Returns:
        str: Confirmation with PR details
    
    Examples:
        - Use when: "Close PR #11"
        - Use when: "Close stale pull request"
        - Use when: "Close superseded PR with comment"
    
    Error Handling:
        - Returns error if PR not found (404)
        - Returns error if authentication fails (401/403)
        - Returns error if PR already closed (422)
    """
    
    # Get token (try param, then GitHub App, then PAT)
    token = await _get_auth_token_fallback(params.token)
    if not token:
        return json.dumps({
            "error": "Authentication required",
            "message": "GitHub token required for closing pull requests. Set GITHUB_TOKEN or configure GitHub App authentication.",
            "success": False
        }, indent=2)
    
    try:
        # Add comment if provided
        if params.comment:
            await _make_github_request(
                f"repos/{params.owner}/{params.repo}/issues/{params.pull_number}/comments",
                method="POST",
                token=token,
                json={"body": params.comment}
            )
        
        # Close the PR
        pr = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}",
            method="PATCH",
            token=token,
            json={"state": "closed"}
        )
        
        # Return the FULL GitHub API response as JSON
        return json.dumps(pr, indent=2)
        
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)

@conditional_tool(
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
        token = await _get_auth_token_fallback(params.token)
        if not token:
            return json.dumps({
                "error": "Authentication required",
                "message": "GitHub token required for creating PR reviews. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False
            }, indent=2)
        
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
        
        # Return the FULL GitHub API response as JSON
        return json.dumps(review, indent=2)
        
    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }
        
        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = e.response.text[:200] if e.response.text else "Unknown error"
        else:
            error_info["message"] = str(e)
        
        return json.dumps(error_info, indent=2)

# ============================================================================
# CODE-FIRST EXECUTION TOOL (The Only Tool Exposed to Claude)
# ============================================================================
# This is the ONLY tool Claude Desktop sees, providing 98% token reduction
# All 46 GitHub tools above are accessed via this tool through TypeScript code
# ============================================================================

@mcp.tool(
    name="execute_code",
    annotations={
        "title": "Execute TypeScript Code",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def execute_code(code: str) -> str:
    """
    Execute TypeScript code with access to all GitHub MCP tools.
    
    🚀 REVOLUTIONARY: 98% token reduction through code-first execution!
    
    💡 TOOL DISCOVERY:
    To see all available tools with complete schemas, use this in your code:
    ```typescript
    const tools = listAvailableTools();
    return tools;
    ```
    
    This returns a structured catalog of all 46 GitHub tools including:
    - Tool names and descriptions
    - Required/optional parameters with types
    - Return value descriptions
    - Usage examples for each tool
    - Organized by category
    
    📚 Quick Start Example:
    ```typescript
    // 1. Discover what's available (optional - only if you need to know)
    const tools = listAvailableTools();
    
    // 2. Use any tool directly
    const info = await callMCPTool("github_get_repo_info", {
        owner: "facebook",
        repo: "react"
    });
    
    return { availableTools: tools.totalTools, repoInfo: info };
    ```
    
    🔍 Search for Specific Tools:
    ```typescript
    // Find tools related to a topic
    const issueTools = searchTools("issue");
    
    // Get detailed info about a specific tool
    const toolInfo = getToolInfo("github_create_issue");
    ```
    
    🎯 Common Tool Categories:
    - Repository Management (7 tools): github_get_repo_info, github_create_repository, etc.
    - Issues (4 tools): github_list_issues, github_create_issue, etc.
    - Pull Requests (7 tools): github_list_pull_requests, github_merge_pull_request, etc.
    - Files (5 tools): github_get_file_content, github_create_file, etc.
    - Search (3 tools): github_search_code, github_search_repositories, etc.
    - Releases (4 tools): github_list_releases, github_create_release, etc.
    - Workflows (2 tools): github_list_workflows, github_get_workflow_runs
    - And 9 more categories...
    
    📖 Full documentation: https://github.com/crypto-ninja/github-mcp-server#tools
    
    All tools are called via: await callMCPTool(toolName, parameters)
    
    Benefits:
        - 98%+ token reduction vs traditional MCP
        - Full TypeScript type safety
        - Complex workflows in single execution
        - Conditional logic and loops
        - Error handling with try/catch
    """
    try:
        from src.github_mcp.deno_runtime import get_runtime
        
        runtime = get_runtime()
        result = runtime.execute_code(code)
        
        if result.get("success"):
            # Format successful result
            return_value = result.get("result", "Code executed successfully")
            
            # Return raw JSON for structured data (dict/list) so TypeScript can parse it
            if isinstance(return_value, (dict, list)):
                # Return raw JSON string - TypeScript client expects JSON, not markdown
                return json.dumps(return_value)
            elif isinstance(return_value, str):
                # For strings, check if it's already JSON
                if return_value.strip().startswith(('{', '[')):
                    # Already JSON string, return as-is
                    return return_value
                else:
                    # Plain string, format as markdown for readability
                    return f"✅ Code executed successfully\n\n**Result:**\n```\n{return_value}\n```"
            else:
                # Other types (numbers, booleans, etc.) - convert to JSON
                return json.dumps(return_value)
        else:
            # Format error
            error = result.get("error", "Unknown error")
            stack = result.get("stack", "")
            
            error_msg = f"❌ Code execution failed\n\n**Error:**\n```\n{error}\n```"
            if stack:
                error_msg += f"\n\n**Stack Trace:**\n```\n{stack}\n```"
            
            return error_msg
            
    except ImportError as e:
        return f"❌ Error: Deno runtime not available. {str(e)}\n\nPlease ensure:\n1. Deno is installed\n2. src/github_mcp/deno_runtime.py exists"
    except Exception as e:
        return f"❌ Unexpected error during code execution: {str(e)}"

# ============================================================================
# INTERNAL UTILITY FUNCTIONS (NOT MCP TOOLS)
# ============================================================================
# These functions are available for internal use and CLI utilities,
# but are NOT exposed as MCP tools to maintain the "1 tool" architecture.

async def health_check() -> str:
    """
    Internal health check function (use CLI: github-mcp-cli health).
    
    This function is NOT exposed as an MCP tool to maintain the "1 tool" architecture.
    Use the CLI utility for diagnostics: `github-mcp-cli health`
    
    Returns:
        str: JSON-formatted health status
    """
    try:
        # Check authentication status
        has_pat = bool(os.getenv("GITHUB_TOKEN"))
        has_app_id = bool(os.getenv("GITHUB_APP_ID"))
        has_app_installation = bool(os.getenv("GITHUB_APP_INSTALLATION_ID"))
        has_app_key = bool(os.getenv("GITHUB_APP_PRIVATE_KEY_PATH"))
        
        auth_status = "none"
        auth_method = None
        if has_app_id and has_app_installation and has_app_key:
            auth_status = "configured"
            auth_method = "github_app"
        elif has_pat:
            auth_status = "configured"
            auth_method = "pat"
        
        # Check Deno
        deno_available, deno_info = check_deno_installed()
        
        health_data = {
            "status": "healthy",
            "version": "2.4.0",
            "mode": "code_first" if CODE_FIRST_MODE else "internal",
            "authentication": {
                "status": auth_status,
                "method": auth_method,
                "pat_configured": has_pat,
                "app_configured": has_app_id and has_app_installation and has_app_key
            },
            "deno": {
                "available": deno_available,
                "version": deno_info if deno_available else None
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return json.dumps(health_data, indent=2)
        
    except Exception as e:
        error_data = {
            "status": "error",
            "version": "2.4.0",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return json.dumps(error_data, indent=2)

async def github_clear_token_cache() -> str:
    """
    Internal token cache clearing function (use CLI: github-mcp-cli clear-cache).
    
    This function is NOT exposed as an MCP tool to maintain the "1 tool" architecture.
    Use the CLI utility: `github-mcp-cli clear-cache`
    
    Use this after:
    - Updating GitHub App permissions
    - Re-installing the app
    - Getting permission errors despite having correct permissions set
    
    This forces the next API call to get a fresh token with current permissions.
    
    Returns:
        Confirmation message
    """
    has_app_id = bool(os.getenv("GITHUB_APP_ID"))
    has_app_installation = bool(os.getenv("GITHUB_APP_INSTALLATION_ID"))
    has_app_key = bool(os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")) or bool(os.getenv("GITHUB_APP_PRIVATE_KEY"))
    
    if has_app_id and has_app_installation and has_app_key:
        clear_token_cache()
        return "✅ GitHub App token cache cleared. Next API call will use a fresh token with current permissions."
    else:
        return "ℹ️ GitHub App not configured. Using PAT authentication (no cache to clear)."

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