# Response Formats Reference

All tools that return GitHub data support a `response_format` parameter.

## Available Formats

### `compact` (Recommended)

Returns only essential fields. Best for:
- Listing resources
- Status checks
- Quick lookups
- AI agent workflows

### `json`

Returns full GitHub API response. Best for:
- Deep inspection
- Programmatic processing
- Full body/description content
- When you need specific fields not in compact

### `markdown`

Returns human-readable formatted text. Best for:
- Displaying to users
- Documentation
- Reports

## Compact Field Reference

### Repository (`github_get_repo_info`)
```json
{
  "name": "react",
  "description": "The library for web and native user interfaces.",
  "stars": 225000,
  "forks": 46000,
  "language": "JavaScript",
  "default_branch": "main",
  "url": "https://github.com/facebook/react"
}
```

### Branch (`github_get_branch`, `github_list_branches`)
```json
{
  "name": "main",
  "sha": "abc123",
  "protected": true
}
```

### Issue (`github_list_issues`)
```json
{
  "number": 42,
  "title": "Bug in authentication",
  "state": "open",
  "author": "octocat",
  "created": "2025-01-15T10:30:00Z",
  "url": "https://github.com/owner/repo/issues/42"
}
```

### Pull Request (`github_list_pull_requests`)
```json
{
  "number": 123,
  "title": "Add new feature",
  "state": "open",
  "author": "developer",
  "head": "feature-branch",
  "base": "main",
  "url": "https://github.com/owner/repo/pull/123"
}
```

### Commit (`github_list_commits`)
```json
{
  "sha": "abc1234",
  "message": "Fix authentication bug",
  "author": "developer",
  "date": "2025-01-15T14:30:00Z"
}
```

### Workflow Run (`github_get_workflow_runs`)
```json
{
  "id": 12345678,
  "name": "CI",
  "status": "completed",
  "conclusion": "success",
  "branch": "main",
  "created": "2025-01-15T10:00:00Z",
  "url": "https://github.com/owner/repo/actions/runs/12345678"
}
```

### User (`github_get_user_info`)
```json
{
  "login": "octocat",
  "name": "The Octocat",
  "type": "User",
  "url": "https://github.com/octocat"
}
```

### Release (`github_list_releases`, `github_get_release`)
```json
{
  "tag": "v1.0.0",
  "name": "Version 1.0.0",
  "published": "2025-01-15T12:00:00Z",
  "url": "https://github.com/owner/repo/releases/tag/v1.0.0"
}
```

### Search Results

All search tools return:
```json
{
  "total_count": 150,
  "items": [/* compact items */]
}
```

## Tools Supporting Compact Format

### Full Support (26 tools)

- `github_get_repo_info`
- `github_list_branches`
- `github_get_branch`
- `github_list_issues`
- `github_list_commits`
- `github_list_pull_requests`
- `github_get_pr_overview_graphql`
- `github_get_workflow`
- `github_get_workflow_runs`
- `github_get_workflow_run`
- `github_search_issues`
- `github_search_repositories`
- `github_search_code`
- `github_get_user_info`
- `github_get_authenticated_user`
- `github_search_users`
- `github_list_labels`
- `github_check_collaborator`
- `github_list_stargazers`
- `github_list_gists`
- `github_list_releases`
- `github_get_release`
- `github_list_notifications`
- `github_compare_branches`
- `github_get_job`
- `github_get_artifact`

### Tools Without Format (Action-based)

Create, update, and delete operations return confirmation messages rather than data, so format doesn't apply:
- `github_create_*` tools
- `github_update_*` tools
- `github_delete_*` tools

