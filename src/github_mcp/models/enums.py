"""Enums for GitHub MCP Server."""

from enum import Enum


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"
    COMPACT = "compact"


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
