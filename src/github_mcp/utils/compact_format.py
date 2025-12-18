"""Compact format serializers for AI-optimized responses.

Reduces token usage by 80%+ by returning only essential fields.
"""

from typing import Any, Dict, List, Union


def compact_commit(commit: Dict[str, Any]) -> Dict[str, Any]:
    """Convert full commit to compact format."""
    return {
        "sha": commit.get("sha", "")[:7],
        "message": commit.get("commit", {}).get("message", "").split("\n")[0][:100],
        "author": commit.get("commit", {}).get("author", {}).get("name")
        or commit.get("author", {}).get("login", "unknown"),
        "date": commit.get("commit", {}).get("author", {}).get("date", ""),
    }


def compact_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Convert full issue/PR to compact format."""
    return {
        "number": issue.get("number"),
        "title": issue.get("title", "")[:100],
        "state": issue.get("state"),
        "author": issue.get("user", {}).get("login", "unknown"),
        "created": issue.get("created_at", ""),
        "url": issue.get("html_url", ""),
    }


def compact_repo(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Convert full repo to compact format."""
    return {
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "description": (repo.get("description") or "")[:100],
        "stars": repo.get("stargazers_count", 0),
        "language": repo.get("language"),
        "url": repo.get("html_url", ""),
    }


def compact_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Convert full user to compact format."""
    return {
        "login": user.get("login"),
        "name": user.get("name"),
        "type": user.get("type", "User"),
        "url": user.get("html_url", ""),
    }


def compact_branch(branch: Dict[str, Any]) -> Dict[str, Any]:
    """Convert full branch to compact format."""
    return {
        "name": branch.get("name"),
        "sha": branch.get("commit", {}).get("sha", "")[:7],
        "protected": branch.get("protected", False),
    }


def compact_release(release: Dict[str, Any]) -> Dict[str, Any]:
    """Convert full release to compact format."""
    return {
        "tag": release.get("tag_name"),
        "name": release.get("name") or release.get("tag_name"),
        "published": release.get("published_at", ""),
        "url": release.get("html_url", ""),
    }


def compact_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """Convert full workflow to compact format."""
    return {
        "id": workflow.get("id"),
        "name": workflow.get("name"),
        "state": workflow.get("state"),
        "path": workflow.get("path", ""),
    }


def compact_workflow_run(run: Dict[str, Any]) -> Dict[str, Any]:
    """Convert full workflow run to compact format."""
    return {
        "id": run.get("id"),
        "name": run.get("name"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "branch": run.get("head_branch"),
        "created": run.get("created_at", ""),
        "url": run.get("html_url", ""),
    }


def compact_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Convert security alert to compact format."""
    return {
        "number": alert.get("number"),
        "state": alert.get("state"),
        "severity": alert.get("security_advisory", {}).get("severity")
        or alert.get("rule", {}).get("severity", "unknown"),
        "package": alert.get("dependency", {}).get("package", {}).get("name", ""),
        "created": alert.get("created_at", ""),
    }


def compact_gist(gist: Dict[str, Any]) -> Dict[str, Any]:
    """Convert full gist to compact format."""
    files = list(gist.get("files", {}).keys())
    return {
        "id": gist.get("id"),
        "description": (gist.get("description") or "")[:100],
        "files": files[:5],
        "public": gist.get("public", True),
        "created": gist.get("created_at", ""),
        "url": gist.get("html_url", ""),
    }


def compact_notification(notification: Dict[str, Any]) -> Dict[str, Any]:
    """Convert notification to compact format."""
    return {
        "id": notification.get("id"),
        "reason": notification.get("reason"),
        "title": notification.get("subject", {}).get("title", "")[:100],
        "type": notification.get("subject", {}).get("type"),
        "repo": notification.get("repository", {}).get("full_name"),
        "updated": notification.get("updated_at", ""),
    }


def compact_label(label: Dict[str, Any]) -> Dict[str, Any]:
    """Convert label to compact format."""
    return {
        "name": label.get("name"),
        "color": label.get("color"),
        "description": (label.get("description") or "")[:50],
    }


def compact_project(project: Dict[str, Any]) -> Dict[str, Any]:
    """Convert project to compact format."""
    return {
        "id": project.get("id"),
        "name": project.get("name"),
        "state": project.get("state"),
        "url": project.get("html_url", ""),
    }


def compact_stargazer(stargazer: Dict[str, Any]) -> Dict[str, Any]:
    """Convert stargazer to compact format."""
    user = stargazer.get("user", stargazer)
    return compact_user(user)


def compact_collaborator(collaborator: Dict[str, Any]) -> Dict[str, Any]:
    """Convert collaborator to compact format."""
    return {
        "login": collaborator.get("login"),
        "permissions": collaborator.get("permissions", {}),
        "role": collaborator.get("role_name", ""),
    }


def compact_file_content(content: Dict[str, Any]) -> Dict[str, Any]:
    """Convert file content to compact format."""
    return {
        "name": content.get("name"),
        "path": content.get("path"),
        "type": content.get("type"),
        "size": content.get("size"),
        "sha": content.get("sha", "")[:7],
    }


def compact_discussion(discussion: Dict[str, Any]) -> Dict[str, Any]:
    """Convert discussion to compact format."""
    return {
        "number": discussion.get("number"),
        "title": discussion.get("title", "")[:100],
        # Support both GraphQL (author/login, createdAt, url) and REST (user/login, created_at, html_url)
        "author": (discussion.get("author", {}) or discussion.get("user", {})).get(
            "login", "unknown"
        ),
        "category": (
            discussion.get("category", {}) or discussion.get("repository", {})
        ).get("name"),
        "created": discussion.get("createdAt", "") or discussion.get("created_at", ""),
        "url": discussion.get("url", "") or discussion.get("html_url", ""),
    }


def compact_artifact(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Convert workflow artifact to compact format."""
    return {
        "id": artifact.get("id"),
        "name": artifact.get("name"),
        "size": artifact.get("size_in_bytes"),
        "expired": artifact.get("expired", False),
        "created": artifact.get("created_at", ""),
    }


def compact_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """Convert workflow job to compact format."""
    return {
        "id": job.get("id"),
        "name": job.get("name"),
        "status": job.get("status"),
        "conclusion": job.get("conclusion"),
        "started": job.get("started_at", ""),
        "completed": job.get("completed_at", ""),
    }


def compact_thread(thread: Dict[str, Any]) -> Dict[str, Any]:
    """Convert notification thread to compact format."""
    subject = thread.get("subject", {})
    repo = thread.get("repository", {})
    return {
        "id": thread.get("id"),
        "reason": thread.get("reason"),
        "unread": thread.get("unread", False),
        "title": (subject.get("title") or "")[:100],
        "type": subject.get("type"),
        "repo": repo.get("full_name"),
        "url": subject.get("url") or thread.get("url", ""),
        "updated": thread.get("updated_at", ""),
    }


def compact_comment(comment: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a generic comment (e.g., discussion comment) to compact format."""
    return {
        "id": comment.get("id"),
        "author": comment.get("user", {}).get("login", "unknown"),
        "created": comment.get("created_at", ""),
        "updated": comment.get("updated_at", ""),
        "url": comment.get("html_url", ""),
        "body": (comment.get("body") or "")[:200],
    }


def compact_search_code(result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a code search result to compact format."""
    repo = result.get("repository", {}) or {}
    return {
        "path": result.get("path"),
        "repo": repo.get("full_name"),
        "url": result.get("html_url", ""),
    }


def compact_advisory(advisory: Dict[str, Any]) -> Dict[str, Any]:
    """Convert security advisory to compact format."""
    return {
        "id": advisory.get("ghsa_id") or advisory.get("id"),
        "summary": (advisory.get("summary") or "")[:120],
        "severity": advisory.get("severity"),
        "published": advisory.get("published_at", ""),
        "url": advisory.get("html_url", ""),
    }


# Mapping of resource types to compact functions
COMPACT_SERIALIZERS = {
    "commit": compact_commit,
    "issue": compact_issue,
    "pull_request": compact_issue,
    "pr": compact_issue,
    "repo": compact_repo,
    "repository": compact_repo,
    "user": compact_user,
    "branch": compact_branch,
    "release": compact_release,
    "workflow": compact_workflow,
    "workflow_run": compact_workflow_run,
    "run": compact_workflow_run,
    "alert": compact_alert,
    "gist": compact_gist,
    "notification": compact_notification,
    "label": compact_label,
    "project": compact_project,
    "stargazer": compact_stargazer,
    "collaborator": compact_collaborator,
    "file": compact_file_content,
    "content": compact_file_content,
    "discussion": compact_discussion,
    "artifact": compact_artifact,
    "job": compact_job,
    "thread": compact_thread,
    "comment": compact_comment,
    "search_code": compact_search_code,
    "advisory": compact_advisory,
}


def to_compact(data: Union[Dict, List], resource_type: str) -> Union[Dict, List]:
    """Convert data to compact format based on resource type.

    Args:
        data: Single item dict or list of items
        resource_type: Type of resource (commit, issue, repo, etc.)

    Returns:
        Compact version of the data
    """
    serializer = COMPACT_SERIALIZERS.get(resource_type)
    if not serializer:
        return data

    if isinstance(data, list):
        return [serializer(item) for item in data]
    return serializer(data)


def format_response(data: Any, response_format: str, resource_type: str) -> Any:
    """Format response based on requested format.

    Args:
        data: The data to format
        response_format: 'json', 'markdown', or 'compact'
        resource_type: Type of resource for compact formatting

    Returns:
        Formatted data
    """
    if response_format == "compact":
        return to_compact(data, resource_type)
    # json and markdown pass through (markdown handled elsewhere)
    return data
