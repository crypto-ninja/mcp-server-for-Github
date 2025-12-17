"""GitHub MCP Tools - All 112 tool functions."""

from .repositories import (
    github_get_repo_info,
    github_create_repository,
    github_update_repository,
    github_archive_repository,
    github_list_user_repos,
    github_list_org_repos,
)

from .branches import (
    github_list_branches,
    github_create_branch,
    github_get_branch,
    github_delete_branch,
    github_compare_branches,
)

from .issues import (
    github_list_issues,
    github_create_issue,
    github_update_issue,
)

from .pull_requests import (
    github_list_pull_requests,
    github_create_pull_request,
    github_get_pr_details,
    github_get_pr_overview_graphql,
    github_merge_pull_request,
    github_close_pull_request,
    github_create_pr_review,
)

from .files import (
    github_get_file_content,
    github_create_file,
    github_update_file,
    github_delete_file,
    github_list_repo_contents,
    github_grep,
    github_batch_file_operations,
    github_str_replace,
    github_read_file_chunk,
)

from .commits import (
    github_list_commits,
)

from .releases import (
    github_list_releases,
    github_get_release,
    github_create_release,
    github_update_release,
    github_delete_release,
)

from .actions import (
    github_list_workflows,
    github_get_workflow,
    github_get_workflow_runs,
    github_trigger_workflow,
    github_get_workflow_run,
    github_list_workflow_run_jobs,
    github_get_job,
    github_get_job_logs,
    github_rerun_workflow,
    github_rerun_failed_jobs,
    github_cancel_workflow_run,
    github_list_workflow_run_artifacts,
    github_get_artifact,
    github_delete_artifact,
    github_suggest_workflow,
)

from .security import (
    github_list_dependabot_alerts,
    github_get_dependabot_alert,
    github_update_dependabot_alert,
    github_list_org_dependabot_alerts,
    github_list_code_scanning_alerts,
    github_get_code_scanning_alert,
    github_update_code_scanning_alert,
    github_list_code_scanning_analyses,
    github_list_secret_scanning_alerts,
    github_get_secret_scanning_alert,
    github_update_secret_scanning_alert,
    github_list_repo_security_advisories,
    github_get_security_advisory,
)

from .projects import (
    github_list_repo_projects,
    github_list_org_projects,
    github_get_project,
    github_create_repo_project,
    github_create_org_project,
    github_update_project,
    github_delete_project,
    github_list_project_columns,
    github_create_project_column,
)

from .discussions import (
    github_list_discussions,
    github_get_discussion,
    github_list_discussion_categories,
    github_list_discussion_comments,
    github_create_discussion,
    github_update_discussion,
    github_add_discussion_comment,
)

from .notifications import (
    github_list_notifications,
    github_get_thread,
    github_mark_thread_read,
    github_mark_notifications_read,
    github_get_thread_subscription,
    github_set_thread_subscription,
)

from .collaborators import (
    github_list_repo_collaborators,
    github_check_collaborator,
    github_list_repo_teams,
)

from .users import (
    github_get_user_info,
    github_get_authenticated_user,
    github_search_users,
)

from .gists import (
    github_list_gists,
    github_get_gist,
    github_create_gist,
    github_update_gist,
    github_delete_gist,
)

from .labels import (
    github_list_labels,
    github_create_label,
    github_delete_label,
)

from .search import (
    github_search_code,
    github_search_repositories,
    github_search_issues,
)

from .comments import (
    github_add_issue_comment,
)

from .stargazers import (
    github_list_stargazers,
    github_star_repository,
    github_unstar_repository,
)

from .misc import (
    github_license_info,
)

from .workspace import (
    workspace_grep,
    workspace_str_replace,
    workspace_read_file,
)

__all__ = [
    # Repositories (6)
    "github_get_repo_info",
    "github_create_repository",
    "github_update_repository",
    "github_archive_repository",
    "github_list_user_repos",
    "github_list_org_repos",
    # Branches (5)
    "github_list_branches",
    "github_create_branch",
    "github_get_branch",
    "github_delete_branch",
    "github_compare_branches",
    # Issues (3)
    "github_list_issues",
    "github_create_issue",
    "github_update_issue",
    # Pull Requests (7)
    "github_list_pull_requests",
    "github_create_pull_request",
    "github_get_pr_details",
    "github_get_pr_overview_graphql",
    "github_merge_pull_request",
    "github_close_pull_request",
    "github_create_pr_review",
    # Files (9)
    "github_get_file_content",
    "github_create_file",
    "github_update_file",
    "github_delete_file",
    "github_list_repo_contents",
    "github_grep",
    "github_batch_file_operations",
    "github_str_replace",
    "github_read_file_chunk",
    # Commits (1)
    "github_list_commits",
    # Releases (5)
    "github_list_releases",
    "github_get_release",
    "github_create_release",
    "github_update_release",
    "github_delete_release",
    # Actions (14)
    "github_list_workflows",
    "github_get_workflow",
    "github_get_workflow_runs",
    "github_trigger_workflow",
    "github_get_workflow_run",
    "github_list_workflow_run_jobs",
    "github_get_job",
    "github_get_job_logs",
    "github_rerun_workflow",
    "github_rerun_failed_jobs",
    "github_cancel_workflow_run",
    "github_list_workflow_run_artifacts",
    "github_get_artifact",
    "github_delete_artifact",
    # Security (13)
    "github_list_dependabot_alerts",
    "github_get_dependabot_alert",
    "github_update_dependabot_alert",
    "github_list_org_dependabot_alerts",
    "github_list_code_scanning_alerts",
    "github_get_code_scanning_alert",
    "github_update_code_scanning_alert",
    "github_list_code_scanning_analyses",
    "github_list_secret_scanning_alerts",
    "github_get_secret_scanning_alert",
    "github_update_secret_scanning_alert",
    "github_list_repo_security_advisories",
    "github_get_security_advisory",
    # Projects (9)
    "github_list_repo_projects",
    "github_list_org_projects",
    "github_get_project",
    "github_create_repo_project",
    "github_create_org_project",
    "github_update_project",
    "github_delete_project",
    "github_list_project_columns",
    "github_create_project_column",
    # Discussions (7)
    "github_list_discussions",
    "github_get_discussion",
    "github_list_discussion_categories",
    "github_list_discussion_comments",
    "github_create_discussion",
    "github_update_discussion",
    "github_add_discussion_comment",
    # Notifications (6)
    "github_list_notifications",
    "github_get_thread",
    "github_mark_thread_read",
    "github_mark_notifications_read",
    "github_get_thread_subscription",
    "github_set_thread_subscription",
    # Collaborators (3)
    "github_list_repo_collaborators",
    "github_check_collaborator",
    "github_list_repo_teams",
    # Users (3)
    "github_get_user_info",
    "github_get_authenticated_user",
    "github_search_users",
    # Gists (5)
    "github_list_gists",
    "github_get_gist",
    "github_create_gist",
    "github_update_gist",
    "github_delete_gist",
    # Labels (3)
    "github_list_labels",
    "github_create_label",
    "github_delete_label",
    # Search (3)
    "github_search_code",
    "github_search_repositories",
    "github_search_issues",
    # Comments (1)
    "github_add_issue_comment",
    # Stargazers (3)
    "github_list_stargazers",
    "github_star_repository",
    "github_unstar_repository",
    # Misc (1)
    "github_license_info",
    # Actions - Workflow Suggestion (1)
    "github_suggest_workflow",
    # Workspace (3) - LOCAL file operations
    "workspace_grep",
    "workspace_str_replace",
    "workspace_read_file",
]
