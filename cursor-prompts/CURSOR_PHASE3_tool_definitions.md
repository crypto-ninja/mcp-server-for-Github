# Cursor Prompt: Phase 3 - Update tool-definitions.ts

## Task
Update `src/github_mcp/deno_executor/tool-definitions.ts` to match the Python changes.

---

## Changes Required

For each tool that was updated in Python, update the TypeScript definition.

### Pattern for `per_page` → `limit`:

```typescript
// BEFORE
{
  name: "github_list_something",
  category: "Category",
  description: "...",
  parameters: {
    owner: { type: "string", required: true, description: "Repository owner" },
    repo: { type: "string", required: true, description: "Repository name" },
    per_page: { type: "number", required: false, description: "Results per page" },
    page: { type: "number", required: false, description: "Page number" }
  }
}

// AFTER
{
  name: "github_list_something",
  category: "Category", 
  description: "...",
  parameters: {
    owner: { type: "string", required: true, description: "Repository owner" },
    repo: { type: "string", required: true, description: "Repository name" },
    limit: { type: "number", required: false, description: "Maximum results (1-100, default 10)" },
    page: { type: "number", required: false, description: "Page number (default 1)" },
    response_format: { type: "string", required: false, description: "Output format: 'json', 'markdown', or 'compact'" }
  }
}
```

---

## Tools to Update

### Branch Management
- `github_list_branches` - per_page→limit, add response_format

### Commits
- `github_list_commits` - already has limit, verify response_format exists

### Discussions
- `github_list_discussions` - per_page→limit
- `github_list_discussion_comments` - per_page→limit  
- `github_list_discussion_categories` - ADD limit, page, response_format

### File Operations
- `github_list_repo_contents` - ADD limit, page
- `github_get_file_content` - add response_format

### Gists
- `github_list_gists` - per_page→limit, add response_format
- `github_get_gist` - add response_format

### GitHub Actions
- `github_list_workflows` - per_page→limit
- `github_list_workflow_run_jobs` - per_page→limit
- `github_list_workflow_run_artifacts` - per_page→limit
- `github_get_job_logs` - add response_format

### Issues
- `github_list_issues` - add response_format (has limit already)

### Labels
- `github_list_labels` - per_page→limit, add response_format

### Notifications
- `github_list_notifications` - per_page→limit

### Projects
- `github_list_repo_projects` - per_page→limit
- `github_list_org_projects` - per_page→limit
- `github_list_project_columns` - per_page→limit

### Pull Requests
- `github_list_pull_requests` - add response_format (has limit already)
- `github_get_pr_details` - add response_format
- `github_get_pr_overview_graphql` - add response_format

### Releases
- `github_list_releases` - per_page→limit

### Repository Management
- `github_list_repo_collaborators` - per_page→limit
- `github_list_repo_teams` - per_page→limit
- `github_get_repo_info` - add response_format

### Search
- Verify all search tools have limit, page, response_format

### Security
- `github_list_dependabot_alerts` - per_page→limit
- `github_list_org_dependabot_alerts` - per_page→limit
- `github_list_code_scanning_alerts` - per_page→limit
- `github_list_code_scanning_analyses` - per_page→limit
- `github_list_secret_scanning_alerts` - per_page→limit
- `github_list_repo_security_advisories` - per_page→limit, add response_format

### Stargazers
- `github_list_stargazers` - per_page→limit, add response_format

### Users
- `github_list_user_repos` - per_page→limit, add response_format
- `github_list_org_repos` - per_page→limit, add response_format
- `github_search_users` - per_page→limit, add response_format
- `github_get_authenticated_user` - add response_format

---

## Verify After Changes

```bash
# TypeScript compile check
cd src/github_mcp
deno check deno_executor/tool-definitions.ts

# Or just import test
deno eval "import { GITHUB_TOOLS } from './deno_executor/tool-definitions.ts'; console.log(GITHUB_TOOLS.length + ' tools OK')"
```

---

When done, tell me "Phase 3 complete" and I'll give you Phase 4 (tests).
