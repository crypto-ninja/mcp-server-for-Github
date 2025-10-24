#!/usr/bin/env python3
"""

GitHub MCP Server - A comprehensive Model Context Protocol server for GitHub integration.

Copyright (C) 2025 crypto-ninja
https://github.com/crypto-ninja/github-mcp-server

This software is available under a dual licensing model:

1. AGPL v3 License - For open source projects and personal use
   See LICENSE-AGPL file for full terms
   https://www.gnu.org/licenses/agpl-3.0.html

2. Commercial License - For commercial/proprietary use
   See LICENSE-COMMERCIAL file for full terms
   Contact: https://github.com/crypto-ninja/github-mcp-server/issues

Key AGPL v3 Requirements:
- Source code must be made available to users
- Modifications must be released under AGPL v3
- Network use is considered distribution
- Commercial use allowed IF source code is shared

For proprietary/commercial use WITHOUT sharing source code,
a commercial license is required.

For licensing inquiries:
https://github.com/crypto-ninja/github-mcp-server/issues/new?title=Commercial+License+Inquiry
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

GitHub MCP Server - A comprehensive Model Context Protocol server for GitHub integration.

This server provides tools to interact with GitHub repositories, issues, pull requests,
and more. It enables AI assistants to seamlessly integrate with GitHub workflows.

Features:
- Repository management and exploration
- Issue creation, search, and management
- Pull request operations
- File content retrieval
- User and organization information
- Search across repositories, code, and users
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
    token: str = Field(..., description="GitHub personal access token (required for creating issues)")

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
            - token (str): GitHub token (required)
    
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
            token=params.token,
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

# Entry point
if __name__ == "__main__":
    mcp.run()
