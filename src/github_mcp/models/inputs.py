"""Pydantic input models for GitHub MCP tools."""

from typing import Optional, List, Dict, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Import enums and constants
from ..models.enums import (
    ResponseFormat,
    IssueState,
    PullRequestState,
    SortOrder,
    WorkflowRunStatus,
    WorkflowRunConclusion,
)

# Constants
DEFAULT_LIMIT = 20

# ============================================================================
# Input Models
# ============================================================================


class RepoInfoInput(BaseModel):
    """Input model for repository information retrieval."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ...,
        description="Repository owner username or organization (e.g., 'octocat', 'github')",
        min_length=1,
        max_length=100,
    )
    repo: str = Field(
        ...,
        description="Repository name (e.g., 'hello-world', 'docs')",
        min_length=1,
        max_length=100,
    )
    token: Optional[str] = Field(
        default=None,
        description="Optional GitHub personal access token for authenticated requests",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable",
    )


class ListIssuesInput(BaseModel):
    """Input model for listing repository issues."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner username", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: IssueState = Field(
        default=IssueState.OPEN,
        description="Issue state filter: 'open', 'closed', or 'all'",
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        description="Maximum results to return (1-100)",
        ge=1,
        le=100,
    )
    page: Optional[int] = Field(
        default=1, description="Page number for pagination", ge=1
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class CreateIssueInput(BaseModel):
    """Input model for creating GitHub issues."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner username", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    title: str = Field(..., description="Issue title", min_length=1, max_length=256)
    body: Optional[str] = Field(
        default=None, description="Issue description/body in Markdown format"
    )
    labels: Optional[List[str]] = Field(
        default=None, description="List of label names to apply", max_length=20
    )
    assignees: Optional[List[str]] = Field(
        default=None, description="List of usernames to assign", max_length=10
    )
    milestone: Optional[int] = Field(
        default=None, description="Milestone number to associate with this issue", ge=1
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class UpdateIssueInput(BaseModel):
    """Input model for updating GitHub issues."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Repository owner username or organization",
    )
    repo: str = Field(..., min_length=1, max_length=100, description="Repository name")
    issue_number: int = Field(..., ge=1, description="Issue number to update")
    state: Optional[str] = Field(None, description="Issue state: 'open' or 'closed'")
    title: Optional[str] = Field(
        None, min_length=1, max_length=256, description="New issue title"
    )
    body: Optional[str] = Field(
        None, description="New issue body/description in Markdown format"
    )
    labels: Optional[List[str]] = Field(
        None,
        max_length=20,
        description="List of label names to apply (replaces existing)",
    )
    assignees: Optional[List[str]] = Field(
        None,
        max_length=10,
        description="List of usernames to assign (replaces existing)",
    )
    milestone: Optional[int] = Field(
        None, description="Milestone number (use null to remove milestone)"
    )
    state_reason: Optional[str] = Field(
        None,
        description="Reason for state change: 'completed', 'not_planned', or 'reopened'",
    )
    token: Optional[str] = Field(
        None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class AddIssueCommentInput(BaseModel):
    """Input model for adding a comment to an existing issue."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Repository owner username or organization",
    )
    repo: str = Field(..., min_length=1, max_length=100, description="Repository name")
    issue_number: int = Field(..., ge=1, description="Issue number to comment on")
    body: str = Field(
        ...,
        min_length=1,
        max_length=65535,
        description="Comment content in Markdown format",
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class ListGistsInput(BaseModel):
    """Input model for listing gists for a user or the authenticated user."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    username: Optional[str] = Field(
        default=None,
        description="GitHub username to list gists for (omit for authenticated user)",
    )
    since: Optional[str] = Field(
        default=None, description="Only gists updated at or after this time (ISO 8601)"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number for pagination"
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - required when username is omitted)",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json', 'markdown', or 'compact'",
    )


class GetGistInput(BaseModel):
    """Input model for retrieving a single gist by ID."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    gist_id: str = Field(
        ..., min_length=1, max_length=200, description="ID of the gist to retrieve"
    )
    token: Optional[str] = Field(
        default=None, description="Optional GitHub token (for private gists)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json', 'markdown', or 'compact'",
    )


class CreateGistFileInput(BaseModel):
    """Input model for a single file in a gist create/update request."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    content: str = Field(..., description="File content")


class CreateGistInput(BaseModel):
    """Input model for creating a new gist."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    description: Optional[str] = Field(
        default=None, description="Description of the gist"
    )
    public: Optional[bool] = Field(
        default=False, description="Whether the gist is public (default: false)"
    )
    files: Dict[str, CreateGistFileInput] = Field(
        ..., description="Mapping of filename to file content"
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class UpdateGistInput(BaseModel):
    """Input model for updating an existing gist."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    gist_id: str = Field(
        ..., min_length=1, max_length=200, description="ID of the gist to update"
    )
    description: Optional[str] = Field(
        default=None, description="New description for the gist"
    )
    files: Optional[Dict[str, Optional[CreateGistFileInput]]] = Field(
        default=None,
        description="Files to add/update/delete. To delete a file, set its value to null.",
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class DeleteGistInput(BaseModel):
    """Input model for deleting a gist."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    gist_id: str = Field(
        ..., min_length=1, max_length=200, description="Gist ID to delete"
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


class SearchRepositoriesInput(BaseModel):
    """Input model for searching GitHub repositories."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    query: str = Field(
        ...,
        description="Search query (e.g., 'language:python stars:>1000', 'machine learning')",
        min_length=1,
        max_length=256,
    )
    sort: Optional[str] = Field(
        default=None,
        description="Sort field: 'stars', 'forks', 'updated', 'help-wanted-issues'",
    )
    order: Optional[SortOrder] = Field(
        default=SortOrder.DESC, description="Sort order: 'asc' or 'desc'"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100
    )
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetFileContentInput(BaseModel):
    """Input model for retrieving file content from a repository."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(
        ...,
        description="File path in the repository (e.g., 'src/main.py', 'README.md')",
        min_length=1,
        max_length=500,
    )
    ref: Optional[str] = Field(
        default=None,
        description="Branch, tag, or commit SHA (defaults to repository's default branch)",
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown', 'json', or 'compact'",
    )


class ListCommitsInput(BaseModel):
    """Input model for listing repository commits."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    sha: Optional[str] = Field(
        default=None,
        description="Branch name, tag, or commit SHA (defaults to default branch)",
    )
    path: Optional[str] = Field(
        default=None, description="Only commits containing this file path"
    )
    author: Optional[str] = Field(
        default=None, description="Filter by commit author (username or email)"
    )
    since: Optional[str] = Field(
        default=None, description="Only commits after this date (ISO 8601 format)"
    )
    until: Optional[str] = Field(
        default=None, description="Only commits before this date (ISO 8601 format)"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100
    )
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListBranchesInput(BaseModel):
    """Input model for listing repository branches."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    protected: Optional[bool] = Field(
        default=None, description="Filter by protected status"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        description="Maximum results (1-100)",
        ge=1,
        le=100,
    )
    page: Optional[int] = Field(
        default=1, description="Page number for pagination", ge=1
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Response format"
    )


class CreateBranchInput(BaseModel):
    """Input model for creating a new branch."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    branch: str = Field(
        ..., description="New branch name", min_length=1, max_length=250
    )
    from_ref: str = Field(
        default="main", description="Branch, tag, or commit SHA to branch from"
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


class GetBranchInput(BaseModel):
    """Input model for getting branch details."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    branch: str = Field(..., description="Branch name", min_length=1, max_length=250)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Response format"
    )


class DeleteBranchInput(BaseModel):
    """Input model for deleting a branch."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    branch: str = Field(
        ..., description="Branch name to delete", min_length=1, max_length=250
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


class CompareBranchesInput(BaseModel):
    """Input model for comparing two branches."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    base: str = Field(..., description="Base branch name", min_length=1, max_length=250)
    head: str = Field(
        ..., description="Head branch name to compare", min_length=1, max_length=250
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Response format"
    )


class ListPullRequestsInput(BaseModel):
    """Input model for listing pull requests."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: PullRequestState = Field(
        default=PullRequestState.OPEN,
        description="PR state: 'open', 'closed', or 'all'",
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100
    )
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetUserInfoInput(BaseModel):
    """Input model for retrieving user information."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    username: str = Field(
        ...,
        description="GitHub username (e.g., 'octocat')",
        min_length=1,
        max_length=100,
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListRepoContentsInput(BaseModel):
    """Input model for listing repository contents."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: Optional[str] = Field(
        default="", description="Directory path (empty for root directory)"
    )
    ref: Optional[str] = Field(default=None, description="Branch, tag, or commit")
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListWorkflowsInput(BaseModel):
    """Input model for listing GitHub Actions workflows."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetWorkflowRunsInput(BaseModel):
    """Input model for getting GitHub Actions workflow runs."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    workflow_id: Optional[str] = Field(
        default=None,
        description="Workflow ID or name (optional - gets all workflows if not specified)",
    )
    status: Optional[WorkflowRunStatus] = Field(
        default=None, description="Filter by run status"
    )
    conclusion: Optional[WorkflowRunConclusion] = Field(
        default=None, description="Filter by run conclusion"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100
    )
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class CreatePullRequestInput(BaseModel):
    """Input model for creating GitHub pull requests."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    title: str = Field(
        ..., description="Pull request title", min_length=1, max_length=256
    )
    head: str = Field(
        ..., description="Source branch name", min_length=1, max_length=100
    )
    base: str = Field(
        ...,
        description="Target branch name (default: main)",
        min_length=1,
        max_length=100,
    )
    body: Optional[str] = Field(
        default=None, description="Pull request description in Markdown format"
    )
    draft: Optional[bool] = Field(
        default=False, description="Create as draft pull request"
    )
    maintainer_can_modify: Optional[bool] = Field(
        default=True, description="Allow maintainers to modify the PR"
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class GetPullRequestDetailsInput(BaseModel):
    """Input model for getting detailed pull request information."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    pull_number: int = Field(..., description="Pull request number", ge=1)
    include_reviews: Optional[bool] = Field(
        default=True, description="Include review information"
    )
    include_commits: Optional[bool] = Field(
        default=True, description="Include commit information"
    )
    include_files: Optional[bool] = Field(
        default=False, description="Include changed files (can be large)"
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GraphQLPROverviewInput(BaseModel):
    """Input for GraphQL PR overview query (batch read)."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    pull_number: int = Field(..., description="Pull request number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class SearchCodeInput(BaseModel):
    """Input model for searching code across GitHub."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    query: str = Field(
        ...,
        description="Code search query (e.g., 'TODO language:python', 'function authenticate')",
        min_length=1,
        max_length=256,
    )
    sort: Optional[str] = Field(
        default=None, description="Sort field: 'indexed' (default)"
    )
    order: Optional[SortOrder] = Field(
        default=SortOrder.DESC, description="Sort order: 'asc' or 'desc'"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100
    )
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class SearchIssuesInput(BaseModel):
    """Input model for searching issues across GitHub."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    query: str = Field(
        ...,
        description="Issue search query (e.g., 'bug language:python', 'security in:title')",
        min_length=1,
        max_length=256,
    )
    sort: Optional[str] = Field(
        default=None, description="Sort field: 'created', 'updated', 'comments'"
    )
    order: Optional[SortOrder] = Field(
        default=SortOrder.DESC, description="Sort order: 'asc' or 'desc'"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT, description="Maximum results (1-100)", ge=1, le=100
    )
    page: Optional[int] = Field(default=1, description="Page number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListReleasesInput(BaseModel):
    """Input model for listing repository releases."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        description="Maximum results (1-100)",
        ge=1,
        le=100,
    )
    page: Optional[int] = Field(
        default=1, description="Page number for pagination", ge=1
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListLabelsInput(BaseModel):
    """Input model for listing labels in a repository."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number for pagination"
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json', 'markdown', or 'compact'",
    )


class CreateLabelInput(BaseModel):
    """Input model for creating a label in a repository."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=50, description="Label name")
    color: str = Field(
        ...,
        min_length=3,
        max_length=10,
        description="6-character hex color code without '#' (GitHub accepts up to 10 chars including alpha)",
    )
    description: Optional[str] = Field(
        default=None, max_length=255, description="Label description"
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class DeleteLabelInput(BaseModel):
    """Input model for deleting a label from a repository."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    name: str = Field(
        ..., min_length=1, max_length=50, description="Label name to delete"
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class ListStargazersInput(BaseModel):
    """Input model for listing stargazers on a repository."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number for pagination"
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json', 'markdown', or 'compact'",
    )


class StarRepositoryInput(BaseModel):
    """Input model for starring a repository."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class UnstarRepositoryInput(BaseModel):
    """Input model for unstarring a repository."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class GetAuthenticatedUserInput(BaseModel):
    """Input model for getting the authenticated user's profile."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json', 'markdown', or 'compact'",
    )


class ListUserReposInput(BaseModel):
    """Input model for listing repositories for a user."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    username: Optional[str] = Field(
        default=None,
        description="GitHub username to list repositories for (omit for authenticated user)",
    )
    type: Optional[str] = Field(
        default="owner",
        description="Repository type: 'all', 'owner', 'member' (default: 'owner')",
    )
    sort: Optional[str] = Field(
        default="full_name",
        description="Sort field: 'created', 'updated', 'pushed', 'full_name' (default: 'full_name')",
    )
    direction: Optional[str] = Field(
        default="asc", description="Sort direction: 'asc' or 'desc' (default: 'asc')"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number for pagination"
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json', 'markdown', or 'compact'",
    )


class ListOrgReposInput(BaseModel):
    """Input model for listing repositories for an organization."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    org: str = Field(..., description="Organization name", min_length=1, max_length=100)
    type: Optional[str] = Field(
        default="all",
        description="Repository type: 'all', 'public', 'private', 'forks', 'sources', 'member'",
    )
    sort: Optional[str] = Field(
        default="full_name",
        description="Sort field: 'created', 'updated', 'pushed', 'full_name' (default: 'full_name')",
    )
    direction: Optional[str] = Field(
        default="asc", description="Sort direction: 'asc' or 'desc' (default: 'asc')"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number for pagination"
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json', 'markdown', or 'compact'",
    )


class SearchUsersInput(BaseModel):
    """Input model for searching GitHub users."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    query: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Search query (supports qualifiers like 'location:', 'language:', 'followers:>100')",
    )
    sort: Optional[str] = Field(
        default=None, description="Sort field: 'followers', 'repositories', or 'joined'"
    )
    order: Optional[SortOrder] = Field(
        default=SortOrder.DESC, description="Sort order: 'asc' or 'desc'"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(
        default=1, ge=1, description="Page number for pagination"
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json', 'markdown', or 'compact'",
    )


class GetReleaseInput(BaseModel):
    """Input model for getting a specific release or latest release."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    tag: Optional[str] = Field(
        default="latest",
        description="Release tag (e.g., 'v1.1.0') or 'latest' for most recent",
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class CreateReleaseInput(BaseModel):
    """Input model for creating GitHub releases."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    tag_name: str = Field(
        ...,
        description="Git tag name for the release (e.g., 'v1.2.0')",
        min_length=1,
        max_length=100,
    )
    name: Optional[str] = Field(
        default=None, description="Release title (defaults to tag_name if not provided)"
    )
    body: Optional[str] = Field(
        default=None, description="Release notes/description in Markdown format"
    )
    draft: Optional[bool] = Field(
        default=False, description="Create as draft release (not visible publicly)"
    )
    prerelease: Optional[bool] = Field(
        default=False, description="Mark as pre-release (not production ready)"
    )
    target_commitish: Optional[str] = Field(
        default=None,
        description="Commit SHA, branch, or tag to create release from (defaults to default branch)",
    )
    generate_release_notes: bool = Field(
        default=False,
        description="Auto-generate release notes from merged PRs and commits since last release",
    )
    discussion_category_name: Optional[str] = Field(
        default=None,
        description="Create a linked discussion in this category (e.g., 'Announcements')",
    )
    make_latest: Optional[str] = Field(
        default=None, description="Control 'Latest' badge: 'true', 'false', or 'legacy'"
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class UpdateReleaseInput(BaseModel):
    """Input model for updating GitHub releases."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    release_id: Union[int, str] = Field(
        ..., description="Release ID (numeric) or tag name (e.g., 'v1.2.0')"
    )
    tag_name: Optional[str] = Field(
        default=None, description="New tag name (use carefully!)"
    )
    name: Optional[str] = Field(default=None, description="New release title")
    body: Optional[str] = Field(
        default=None, description="New release notes/description in Markdown format"
    )
    draft: Optional[bool] = Field(default=None, description="Set draft status")
    prerelease: Optional[bool] = Field(
        default=None, description="Set pre-release status"
    )
    generate_release_notes: Optional[bool] = Field(
        default=None,
        description="Auto-generate release notes from merged PRs and commits since last release",
    )
    discussion_category_name: Optional[str] = Field(
        default=None,
        description="Create a linked discussion in this category (e.g., 'Announcements')",
    )
    make_latest: Optional[str] = Field(
        default=None,
        description="Control 'Latest' badge: 'true', 'false', or 'legacy'",
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class DeleteReleaseInput(BaseModel):
    """Input model for deleting a release."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    release_id: int = Field(..., description="Release ID to delete")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


# Workflow Optimization Model


class WorkflowSuggestionInput(BaseModel):
    """Input model for workflow optimization suggestions."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    operation: str = Field(
        ...,
        description="Operation type (e.g., 'update_readme', 'create_release', 'multiple_file_edits')",
        min_length=1,
        max_length=200,
    )
    file_size: Optional[int] = Field(
        default=None, description="Estimated file size in bytes", ge=0
    )
    num_edits: Optional[int] = Field(
        default=1, description="Number of separate edit operations", ge=1
    )
    file_count: Optional[int] = Field(
        default=1, description="Number of files being modified", ge=1
    )
    description: Optional[str] = Field(
        default=None, description="Additional context about the task"
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


# Phase 2.2: Repository Management Models


class CreateRepositoryInput(BaseModel):
    """Input model for creating repositories (user or org)."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: Optional[str] = Field(
        default=None,
        description="Organization owner (if creating in an org); omit for user repo",
    )
    name: str = Field(..., description="Repository name", min_length=1, max_length=100)
    description: Optional[str] = Field(
        default=None, description="Repository description"
    )
    private: Optional[bool] = Field(
        default=False, description="Create as private repository"
    )
    auto_init: Optional[bool] = Field(
        default=True, description="Initialize with README"
    )
    gitignore_template: Optional[str] = Field(
        default=None, description="Gitignore template name (e.g., 'Python')"
    )
    license_template: Optional[str] = Field(
        default=None, description="License template (e.g., 'mit')"
    )
    allow_squash_merge: Optional[bool] = Field(
        default=True, description="Allow squash merging of pull requests"
    )
    allow_merge_commit: Optional[bool] = Field(
        default=True, description="Allow merge commits for pull requests"
    )
    allow_rebase_merge: Optional[bool] = Field(
        default=True, description="Allow rebase merging of pull requests"
    )
    delete_branch_on_merge: Optional[bool] = Field(
        default=False,
        description="Automatically delete head branch when pull requests are merged",
    )
    allow_auto_merge: Optional[bool] = Field(
        default=False, description="Allow auto-merge for pull requests"
    )
    allow_update_branch: Optional[bool] = Field(
        default=False,
        description="Allow pull request head branch to be updated even if it's behind base branch",
    )
    squash_merge_commit_title: Optional[str] = Field(
        default=None,
        description="Default title for squash merge commits (PR_TITLE, COMMIT_OR_PR_TITLE)",
    )
    squash_merge_commit_message: Optional[str] = Field(
        default=None,
        description="Default message for squash merge commits (PR_BODY, COMMIT_MESSAGES, BLANK)",
    )
    token: Optional[str] = Field(
        default=None, description="GitHub personal access token"
    )


class PRReviewComment(BaseModel):
    """Single review comment on a PR."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    path: str = Field(
        ..., description="File path in the PR", min_length=1, max_length=500
    )
    position: Optional[int] = Field(
        default=None, description="Line position in the diff (deprecated, use line)"
    )
    line: Optional[int] = Field(default=None, description="Line number in the file")
    side: Optional[str] = Field(
        default="RIGHT", description="Side of diff: 'LEFT' (old) or 'RIGHT' (new)"
    )
    body: str = Field(
        ..., description="Comment text in Markdown", min_length=1, max_length=65536
    )

    @field_validator("side")
    @classmethod
    def validate_side(cls, v):
        if v not in ["LEFT", "RIGHT"]:
            raise ValueError("side must be 'LEFT' or 'RIGHT'")
        return v


class CreatePRReviewInput(BaseModel):
    """Input model for creating pull request reviews."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    pull_number: int = Field(..., description="Pull request number", ge=1)
    event: str = Field(
        default="COMMENT",
        description="Review action: 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'",
    )
    body: Optional[str] = Field(
        default=None, description="General review comment (Markdown)"
    )
    comments: Optional[List[PRReviewComment]] = Field(
        default=None, description="Line-specific comments", max_length=100
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )

    @field_validator("event")
    @classmethod
    def validate_event(cls, v):
        if v not in ["APPROVE", "REQUEST_CHANGES", "COMMENT"]:
            raise ValueError("event must be 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v, info):
        event = info.data.get("event")
        comments = info.data.get("comments")
        if event in ["APPROVE", "REQUEST_CHANGES"]:
            if not v and not comments:
                raise ValueError(f"{event} requires either body or comments")
        return v


class UpdateRepositoryInput(BaseModel):
    """Input model for updating repository settings."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    name: Optional[str] = Field(default=None, description="New repository name")
    description: Optional[str] = Field(default=None, description="New description")
    homepage: Optional[str] = Field(default=None, description="Homepage URL")
    private: Optional[bool] = Field(
        default=None, description="Set repository visibility"
    )
    has_issues: Optional[bool] = Field(default=None, description="Enable issues")
    has_projects: Optional[bool] = Field(default=None, description="Enable projects")
    has_wiki: Optional[bool] = Field(default=None, description="Enable wiki")
    default_branch: Optional[str] = Field(
        default=None, description="Set default branch"
    )
    archived: Optional[bool] = Field(
        default=None, description="Archive/unarchive repository"
    )
    allow_squash_merge: Optional[bool] = Field(
        default=None, description="Allow squash merging of pull requests"
    )
    allow_merge_commit: Optional[bool] = Field(
        default=None, description="Allow merge commits for pull requests"
    )
    allow_rebase_merge: Optional[bool] = Field(
        default=None, description="Allow rebase merging of pull requests"
    )
    delete_branch_on_merge: Optional[bool] = Field(
        default=None,
        description="Automatically delete head branch when pull requests are merged",
    )
    allow_auto_merge: Optional[bool] = Field(
        default=None, description="Allow auto-merge for pull requests"
    )
    allow_update_branch: Optional[bool] = Field(
        default=None,
        description="Allow pull request head branch to be updated even if it's behind base branch",
    )
    squash_merge_commit_title: Optional[str] = Field(
        default=None,
        description="Default title for squash merge commits (PR_TITLE, COMMIT_OR_PR_TITLE)",
    )
    squash_merge_commit_message: Optional[str] = Field(
        default=None,
        description="Default message for squash merge commits (PR_BODY, COMMIT_MESSAGES, BLANK)",
    )
    token: Optional[str] = Field(
        default=None, description="GitHub personal access token"
    )


class ArchiveRepositoryInput(BaseModel):
    """Input model for archiving or unarchiving repositories."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    archived: bool = Field(..., description="True to archive, False to unarchive")
    token: Optional[str] = Field(
        default=None, description="GitHub personal access token"
    )


class MergePullRequestInput(BaseModel):
    """Input model for merging pull requests."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    pull_number: int = Field(..., description="Pull request number", ge=1)
    merge_method: Optional[str] = Field(
        default="squash", description="Merge method: 'merge', 'squash', or 'rebase'"
    )
    commit_title: Optional[str] = Field(
        default=None, description="Custom commit title for merge commit"
    )
    commit_message: Optional[str] = Field(
        default=None, description="Custom commit message for merge commit"
    )
    sha: Optional[str] = Field(
        default=None,
        description="SHA of the head commit that must match the pull request's head (prevents race conditions)",
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class ClosePullRequestInput(BaseModel):
    """Input model for closing pull requests."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., min_length=1, max_length=100, description="Repository owner"
    )
    repo: str = Field(..., min_length=1, max_length=100, description="Repository name")
    pull_number: int = Field(..., ge=1, description="Pull request number to close")
    comment: Optional[str] = Field(
        None, description="Optional comment to add when closing"
    )
    token: Optional[str] = Field(
        None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


# Phase 2.1: File Management Models


class GitUserInfo(BaseModel):
    """Git user information for commits."""

    name: str = Field(..., description="Name of the user", min_length=1)
    email: str = Field(..., description="Email of the user", min_length=1)


class CreateFileInput(BaseModel):
    """Input model for creating files in a repository."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(
        ...,
        description="File path (e.g., 'docs/README.md', 'src/main.py')",
        min_length=1,
        max_length=500,
    )
    content: str = Field(
        ..., description="File content (will be base64 encoded automatically)"
    )
    message: str = Field(
        ..., description="Commit message", min_length=1, max_length=500
    )
    branch: Optional[str] = Field(
        default=None,
        description="Branch name (defaults to repository's default branch)",
    )
    committer: Optional["GitUserInfo"] = Field(
        default=None,
        description="Custom committer info (name and email)",
    )
    author: Optional["GitUserInfo"] = Field(
        default=None,
        description="Custom author info (name and email)",
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class UpdateFileInput(BaseModel):
    """Input model for updating files in a repository."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(
        ..., description="File path to update", min_length=1, max_length=500
    )
    content: str = Field(..., description="New file content")
    message: str = Field(
        ..., description="Commit message", min_length=1, max_length=500
    )
    sha: str = Field(
        ...,
        description="SHA of the file being replaced (get from github_get_file_content)",
    )
    branch: Optional[str] = Field(
        default=None,
        description="Branch name (defaults to repository's default branch)",
    )
    committer: Optional["GitUserInfo"] = Field(
        default=None,
        description="Custom committer info (name and email)",
    )
    author: Optional["GitUserInfo"] = Field(
        default=None,
        description="Custom author info (name and email)",
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class DeleteFileInput(BaseModel):
    """Input model for deleting files from a repository."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(
        ..., description="File path to delete", min_length=1, max_length=500
    )
    message: str = Field(
        ..., description="Commit message", min_length=1, max_length=500
    )
    sha: str = Field(
        ...,
        description="SHA of the file being deleted (get from github_get_file_content)",
    )
    branch: Optional[str] = Field(
        default=None,
        description="Branch name (defaults to repository's default branch)",
    )
    committer: Optional["GitUserInfo"] = Field(
        default=None,
        description="Custom committer info (name and email)",
    )
    author: Optional["GitUserInfo"] = Field(
        default=None,
        description="Custom author info (name and email)",
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


class FileOperation(BaseModel):
    """Single file operation within a batch."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    operation: str = Field(
        ..., description="Operation type: 'create', 'update', or 'delete'"
    )
    path: str = Field(
        ..., description="File path in repository", min_length=1, max_length=500
    )
    content: Optional[str] = Field(
        default=None, description="File content (required for create/update)"
    )
    sha: Optional[str] = Field(
        default=None, description="Current file SHA (required for update/delete)"
    )

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v):
        if v not in ["create", "update", "delete"]:
            raise ValueError("operation must be 'create', 'update', or 'delete'")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v, info):
        operation = info.data.get("operation")
        if operation in ["create", "update"] and not v:
            raise ValueError(f"content is required for {operation} operations")
        return v

    @field_validator("sha")
    @classmethod
    def validate_sha(cls, v, info):
        operation = info.data.get("operation")
        if operation in ["update", "delete"] and not v:
            raise ValueError(f"sha is required for {operation} operations")
        return v


class BatchFileOperationsInput(BaseModel):
    """Input model for batch file operations."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    operations: List[FileOperation] = Field(
        ...,
        description="List of file operations to perform",
        min_length=1,
        max_length=50,
    )
    message: str = Field(
        ...,
        description="Commit message for all operations",
        min_length=1,
        max_length=500,
    )
    branch: Optional[str] = Field(
        default=None, description="Target branch (defaults to default branch)"
    )
    token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token (optional - uses GITHUB_TOKEN env var if not provided)",
    )


# Safe local file chunk reading


class ReadFileChunkInput(BaseModel):
    """Input model for reading a chunk of a local file (repo-root constrained)."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    path: str = Field(
        ...,
        description="Relative path under the server's repository root",
        min_length=1,
        max_length=500,
    )
    start_line: int = Field(default=1, description="1-based starting line number", ge=1)
    num_lines: int = Field(
        default=200, description="Number of lines to read (max 500)", ge=1, le=500
    )


class WorkspaceGrepInput(BaseModel):
    """Input model for workspace grep search."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    pattern: str = Field(
        ..., description="Regex pattern to search for", min_length=1, max_length=500
    )
    repo_path: str = Field(
        default="",
        description="Optional subdirectory to search within (relative to repo root)",
        max_length=500,
    )
    context_lines: int = Field(
        default=2,
        description="Number of lines before/after match to include (0-5)",
        ge=0,
        le=5,
    )
    max_results: int = Field(
        default=100, description="Maximum matches to return (1-500)", ge=1, le=500
    )
    file_pattern: str = Field(
        default="*",
        description="Glob pattern for files to search (e.g., '*.py', '*.md')",
        max_length=100,
    )
    case_sensitive: bool = Field(
        default=True, description="Whether search is case-sensitive"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format (markdown or json)"
    )


class StrReplaceInput(BaseModel):
    """Input model for string replacement in files."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    path: str = Field(
        ...,
        description="Relative path to file under repository root",
        min_length=1,
        max_length=500,
    )
    old_str: str = Field(
        ...,
        description="Exact string to find and replace (must be unique match)",
        min_length=1,
    )
    new_str: str = Field(..., description="Replacement string", min_length=0)
    description: Optional[str] = Field(
        default=None, description="Optional description of the change", max_length=200
    )


class GitHubGrepInput(BaseModel):
    """Input model for GitHub repository grep search."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    pattern: str = Field(
        ..., description="Regex pattern to search for", min_length=1, max_length=500
    )
    ref: Optional[str] = Field(
        default=None,
        description="Branch, tag, or commit SHA (defaults to default branch)",
    )
    file_pattern: Optional[str] = Field(
        default="*",
        description="Glob pattern for files (e.g., '*.py', '*.md')",
        max_length=100,
    )
    path: Optional[str] = Field(
        default="", description="Optional subdirectory to search within", max_length=500
    )
    case_sensitive: Optional[bool] = Field(
        default=True, description="Whether search is case-sensitive"
    )
    context_lines: Optional[int] = Field(
        default=2,
        description="Number of lines before/after match to include (0-5)",
        ge=0,
        le=5,
    )
    max_results: Optional[int] = Field(
        default=100, description="Maximum matches to return (1-500)", ge=1, le=500
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format (markdown or json)"
    )


class GitHubReadFileChunkInput(BaseModel):
    """Input model for reading chunks from GitHub files."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(
        ..., description="File path in repository", min_length=1, max_length=500
    )
    start_line: int = Field(default=1, description="1-based starting line number", ge=1)
    num_lines: int = Field(
        default=200, description="Number of lines to read (max 500)", ge=1, le=500
    )
    ref: Optional[str] = Field(
        default=None,
        description="Branch, tag, or commit SHA (defaults to default branch)",
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


class GitHubStrReplaceInput(BaseModel):
    """Input model for string replacement in GitHub files."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    path: str = Field(
        ..., description="File path in repository", min_length=1, max_length=500
    )
    old_str: str = Field(
        ...,
        description="Exact string to find and replace (must be unique match)",
        min_length=1,
    )
    new_str: str = Field(..., description="Replacement string", min_length=0)
    ref: Optional[str] = Field(
        default=None,
        description="Branch, tag, or commit SHA (defaults to default branch)",
    )
    commit_message: Optional[str] = Field(
        default=None,
        description="Custom commit message (auto-generated if not provided)",
        max_length=500,
    )
    description: Optional[str] = Field(
        default=None, description="Optional description of the change", max_length=200
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


# ============================================================================


class GetWorkflowInput(BaseModel):
    """Input model for getting a specific workflow."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    workflow_id: str = Field(
        ...,
        description="Workflow ID (numeric) or workflow file name (e.g., 'ci.yml')",
        min_length=1,
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class TriggerWorkflowInput(BaseModel):
    """Input model for triggering a workflow dispatch."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    workflow_id: str = Field(
        ...,
        description="Workflow ID (numeric) or workflow file name (e.g., 'ci.yml')",
        min_length=1,
    )
    ref: str = Field(
        ...,
        description="Branch, tag, or commit SHA to trigger workflow on",
        min_length=1,
    )
    inputs: Optional[Dict[str, str]] = Field(
        default=None, description="Input parameters for workflow (key-value pairs)"
    )
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for triggering workflows)"
    )


class GetWorkflowRunInput(BaseModel):
    """Input model for getting a specific workflow run."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListWorkflowRunJobsInput(BaseModel):
    """Input model for listing jobs in a workflow run."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    filter: Optional[str] = Field(
        default=None, description="Filter jobs: 'latest' or 'all'"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetJobInput(BaseModel):
    """Input model for getting a specific job."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    job_id: int = Field(..., description="Job ID", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetJobLogsInput(BaseModel):
    """Input model for getting job logs."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    job_id: int = Field(..., description="Job ID", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown', 'json', or 'compact'",
    )


class RerunWorkflowInput(BaseModel):
    """Input model for rerunning a workflow."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for rerunning workflows)"
    )


class RerunFailedJobsInput(BaseModel):
    """Input model for rerunning failed jobs in a workflow run."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for rerunning workflows)"
    )


class CancelWorkflowRunInput(BaseModel):
    """Input model for canceling a workflow run."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for canceling workflows)"
    )


class ListWorkflowRunArtifactsInput(BaseModel):
    """Input model for listing artifacts from a workflow run."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    run_id: int = Field(..., description="Workflow run ID", ge=1)
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetArtifactInput(BaseModel):
    """Input model for getting artifact details."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    artifact_id: int = Field(..., description="Artifact ID", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class DeleteArtifactInput(BaseModel):
    """Input model for deleting an artifact."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    artifact_id: int = Field(..., description="Artifact ID", ge=1)
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for deleting artifacts)"
    )


class ListDependabotAlertsInput(BaseModel):
    """Input model for listing Dependabot alerts."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: Optional[str] = Field(
        default=None, description="Filter by state: 'open', 'dismissed', 'fixed'"
    )
    severity: Optional[str] = Field(
        default=None,
        description="Filter by severity: 'low', 'medium', 'high', 'critical'",
    )
    ecosystem: Optional[str] = Field(
        default=None, description="Filter by ecosystem (e.g., 'npm', 'pip', 'maven')"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetDependabotAlertInput(BaseModel):
    """Input model for getting a specific Dependabot alert."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class UpdateDependabotAlertInput(BaseModel):
    """Input model for updating a Dependabot alert."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    state: str = Field(..., description="New state: 'dismissed' or 'open'")
    dismissed_reason: Optional[str] = Field(
        default=None,
        description="Reason for dismissal: 'fix_started', 'inaccurate', 'no_bandwidth', 'not_used', 'tolerable_risk'",
    )
    dismissed_comment: Optional[str] = Field(
        default=None, max_length=280, description="Optional comment when dismissing"
    )
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for updating alerts)"
    )


class ListOrgDependabotAlertsInput(BaseModel):
    """Input model for listing organization Dependabot alerts."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    org: str = Field(..., description="Organization name", min_length=1, max_length=100)
    state: Optional[str] = Field(
        default=None, description="Filter by state: 'open', 'dismissed', 'fixed'"
    )
    severity: Optional[str] = Field(
        default=None,
        description="Filter by severity: 'low', 'medium', 'high', 'critical'",
    )
    ecosystem: Optional[str] = Field(default=None, description="Filter by ecosystem")
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


# Code Scanning Input Models


class ListCodeScanningAlertsInput(BaseModel):
    """Input model for listing code scanning alerts."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: Optional[str] = Field(
        default=None, description="Filter by state: 'open', 'dismissed', 'fixed'"
    )
    severity: Optional[str] = Field(
        default=None,
        description="Filter by severity: 'critical', 'high', 'medium', 'low', 'warning', 'note'",
    )
    tool_name: Optional[str] = Field(
        default=None, description="Filter by tool name (e.g., 'CodeQL', 'ESLint')"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetCodeScanningAlertInput(BaseModel):
    """Input model for getting a specific code scanning alert."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class UpdateCodeScanningAlertInput(BaseModel):
    """Input model for updating a code scanning alert."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    state: str = Field(..., description="New state: 'dismissed' or 'open'")
    dismissed_reason: Optional[str] = Field(
        default=None,
        description="Reason for dismissal: 'false_positive', 'wont_fix', 'used_in_tests'",
    )
    dismissed_comment: Optional[str] = Field(
        default=None, max_length=280, description="Optional comment when dismissing"
    )
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for updating alerts)"
    )


class ListCodeScanningAnalysesInput(BaseModel):
    """Input model for listing code scanning analyses."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    tool_name: Optional[str] = Field(default=None, description="Filter by tool name")
    ref: Optional[str] = Field(default=None, description="Filter by branch/tag/commit")
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


# Secret Scanning Input Models


class ListSecretScanningAlertsInput(BaseModel):
    """Input model for listing secret scanning alerts."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: Optional[str] = Field(
        default=None, description="Filter by state: 'open', 'resolved'"
    )
    secret_type: Optional[str] = Field(
        default=None,
        description="Filter by secret type (e.g., 'github_personal_access_token')",
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetSecretScanningAlertInput(BaseModel):
    """Input model for getting a specific secret scanning alert."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class UpdateSecretScanningAlertInput(BaseModel):
    """Input model for updating a secret scanning alert."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    alert_number: int = Field(..., description="Alert number", ge=1)
    state: str = Field(..., description="New state: 'resolved' or 'open'")
    resolution: Optional[str] = Field(
        default=None,
        description="Resolution: 'false_positive', 'wont_fix', 'revoked', 'used_in_tests'",
    )
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for updating alerts)"
    )


# Security Advisories Input Models


class ListRepoSecurityAdvisoriesInput(BaseModel):
    """Input model for listing repository security advisories."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: Optional[str] = Field(
        default=None,
        description="Filter by state: 'triage', 'draft', 'published', 'closed'",
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetSecurityAdvisoryInput(BaseModel):
    """Input model for getting a specific security advisory."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    ghsa_id: str = Field(
        ...,
        description="GitHub Security Advisory ID (e.g., 'GHSA-xxxx-xxxx-xxxx')",
        min_length=1,
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


# Dependabot Tools


class ListRepoProjectsInput(BaseModel):
    """Input model for listing repository projects."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    state: Optional[str] = Field(
        default="open", description="Filter by state: 'open', 'closed', 'all'"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListOrgProjectsInput(BaseModel):
    """Input model for listing organization projects."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    org: str = Field(..., description="Organization name", min_length=1, max_length=100)
    state: Optional[str] = Field(
        default="open", description="Filter by state: 'open', 'closed', 'all'"
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetProjectInput(BaseModel):
    """Input model for getting a specific project."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    project_id: int = Field(..., description="Project ID", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class CreateRepoProjectInput(BaseModel):
    """Input model for creating a repository project."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    name: str = Field(..., description="Project name", min_length=1, max_length=100)
    body: Optional[str] = Field(default=None, description="Project description")
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for creating projects)"
    )


class CreateOrgProjectInput(BaseModel):
    """Input model for creating an organization project."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    org: str = Field(..., description="Organization name", min_length=1, max_length=100)
    name: str = Field(..., description="Project name", min_length=1, max_length=100)
    body: Optional[str] = Field(default=None, description="Project description")
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for creating projects)"
    )


class UpdateProjectInput(BaseModel):
    """Input model for updating a project."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    project_id: int = Field(..., description="Project ID", ge=1)
    name: Optional[str] = Field(
        default=None, min_length=1, max_length=100, description="New project name"
    )
    body: Optional[str] = Field(default=None, description="New project description")
    state: Optional[str] = Field(
        default=None, description="New state: 'open' or 'closed'"
    )
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for updating projects)"
    )


class DeleteProjectInput(BaseModel):
    """Input model for deleting a project."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    project_id: int = Field(..., description="Project ID", ge=1)
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for deleting projects)"
    )


class ListProjectColumnsInput(BaseModel):
    """Input model for listing project columns."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    project_id: int = Field(..., description="Project ID", ge=1)
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class CreateProjectColumnInput(BaseModel):
    """Input model for creating a project column."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    project_id: int = Field(..., description="Project ID", ge=1)
    name: str = Field(..., description="Column name", min_length=1, max_length=100)
    token: Optional[str] = Field(
        default=None, description="GitHub token (required for creating columns)"
    )


# Projects Tools


class ListDiscussionsInput(BaseModel):
    """Input model for listing discussions."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, description="Filter by category slug")
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetDiscussionInput(BaseModel):
    """Input model for getting a specific discussion."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    discussion_number: int = Field(..., description="Discussion number", ge=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListDiscussionCategoriesInput(BaseModel):
    """Input model for listing discussion categories."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListDiscussionCommentsInput(BaseModel):
    """Input model for listing discussion comments."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    discussion_number: int = Field(..., description="Discussion number", ge=1)
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class CreateDiscussionInput(BaseModel):
    """Input model for creating a discussion."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    category_id: str = Field(
        ...,
        description="Discussion category node_id (from github_list_discussion_categories)",
        min_length=1,
    )
    title: str = Field(
        ..., description="Discussion title", min_length=1, max_length=200
    )
    body: str = Field(..., description="Discussion body (markdown)", min_length=1)
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


class UpdateDiscussionInput(BaseModel):
    """Input model for updating a discussion."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    discussion_number: int = Field(..., description="Discussion number", ge=1)
    title: Optional[str] = Field(
        None, description="New title", min_length=1, max_length=200
    )
    body: Optional[str] = Field(None, description="New body (markdown)")
    category_id: Optional[str] = Field(
        None, description="Move to different category (node_id)"
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


class AddDiscussionCommentInput(BaseModel):
    """Input model for adding a comment to a discussion."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    discussion_number: int = Field(..., description="Discussion number", ge=1)
    body: str = Field(..., description="Comment body (markdown)", min_length=1)
    reply_to_id: Optional[str] = Field(
        None, description="Reply to a specific comment (comment node_id)"
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")


# Discussions Tools


class ListNotificationsInput(BaseModel):
    """Input model for listing notifications."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    all: Optional[bool] = Field(
        default=False, description="Show all notifications (including read ones)"
    )
    participating: Optional[bool] = Field(
        default=False, description="Show only notifications where user is participating"
    )
    since: Optional[str] = Field(
        default=None,
        description="Only show notifications updated after this time (ISO 8601)",
    )
    before: Optional[str] = Field(
        default=None,
        description="Only show notifications updated before this time (ISO 8601)",
    )
    limit: Optional[int] = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=100,
        description="Maximum results (1-100)",
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(
        default=None, description="GitHub token (required - UAT only)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class GetThreadInput(BaseModel):
    """Input model for getting a notification thread."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    thread_id: str = Field(..., description="Thread ID", min_length=1)
    token: Optional[str] = Field(
        default=None, description="GitHub token (required - UAT only)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class MarkThreadReadInput(BaseModel):
    """Input model for marking a thread as read."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    thread_id: str = Field(..., description="Thread ID", min_length=1)
    token: Optional[str] = Field(
        default=None, description="GitHub token (required - UAT only)"
    )


class MarkNotificationsReadInput(BaseModel):
    """Input model for marking notifications as read."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    last_read_at: Optional[str] = Field(
        default=None, description="Timestamp to mark as read up to (ISO 8601)"
    )
    read: Optional[bool] = Field(
        default=True, description="Mark as read (default: true)"
    )
    token: Optional[str] = Field(
        default=None, description="GitHub token (required - UAT only)"
    )


class GetThreadSubscriptionInput(BaseModel):
    """Input model for getting thread subscription status."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    thread_id: str = Field(..., description="Thread ID", min_length=1)
    token: Optional[str] = Field(
        default=None, description="GitHub token (required - UAT only)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class SetThreadSubscriptionInput(BaseModel):
    """Input model for setting thread subscription."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    thread_id: str = Field(..., description="Thread ID", min_length=1)
    ignored: Optional[bool] = Field(
        default=False, description="Whether to ignore the thread"
    )
    token: Optional[str] = Field(
        default=None, description="GitHub token (required - UAT only)"
    )


# Notifications Tools


class ListRepoCollaboratorsInput(BaseModel):
    """Input model for listing repository collaborators."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    affiliation: Optional[str] = Field(
        default="all", description="Filter by affiliation: 'outside', 'direct', 'all'"
    )
    permission: Optional[str] = Field(
        default=None, description="Filter by permission: 'pull', 'push', 'admin'"
    )
    per_page: Optional[int] = Field(
        default=30, ge=1, le=100, description="Results per page"
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class CheckCollaboratorInput(BaseModel):
    """Input model for checking if a user is a collaborator."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    username: str = Field(
        ..., description="GitHub username to check", min_length=1, max_length=100
    )
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


class ListRepoTeamsInput(BaseModel):
    """Input model for listing repository teams."""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )

    owner: str = Field(
        ..., description="Repository owner", min_length=1, max_length=100
    )
    repo: str = Field(..., description="Repository name", min_length=1, max_length=100)
    per_page: Optional[int] = Field(
        default=30, ge=1, le=100, description="Results per page"
    )
    page: Optional[int] = Field(default=1, ge=1, description="Page number")
    token: Optional[str] = Field(default=None, description="Optional GitHub token")
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, description="Output format"
    )


# Collaborators & Teams Tools
