# CLAUDE.md - AI Assistant Guide for GitHub MCP Server

## What You Have

**62 GitHub tools** accessed through a single `execute_code` tool.
Write TypeScript to discover, call, and chain tools dynamically.

## Tool Discovery

```typescript
// See all available tools by category
const tools = listAvailableTools();

// Search for tools by keyword  
const matches = searchTools("pull request");

// Get full details including required/optional params
const info = getToolInfo("github_create_issue");

// Get all tools in a category
const prTools = getToolsInCategory("Pull Requests");
```

**Always check `getToolInfo()`** - it shows exactly which parameters are required vs optional.

## Calling Tools

```typescript
const result = await callMCPTool("tool_name", { params });
```

**Example:**
```typescript
const issue = await callMCPTool("github_create_issue", {
  owner: "username",
  repo: "repository", 
  title: "Issue title",
  body: "Issue description"
});
// Result contains: number, html_url, title, state, labels, assignees, etc.
```

## Response Formats

Many tools support a `response_format` parameter:
- `"json"` - Structured data for programmatic use
- `"markdown"` - Formatted text for human readability

```typescript
// Get raw JSON for processing
const data = await callMCPTool("github_list_branches", {
  owner: "user", repo: "repo", response_format: "json"
});

// Get formatted markdown for display
const display = await callMCPTool("github_list_branches", {
  owner: "user", repo: "repo", response_format: "markdown"
});
```

## Tool Categories (62 total)

| Category | Count | Key Tools |
|----------|-------|-----------|
| Repository Management | 7 | get_repo_info, create_repository, search_repositories |
| Branch Management | 5 | list/create/get/delete/compare_branches |
| Issues | 5 | list/create/update_issue, add_issue_comment, search_issues |
| Pull Requests | 7 | create/merge/close_pr, get_pr_details, create_pr_review |
| File Operations | 10 | get_file_content, list_contents, create/update/delete_file, grep, read_chunk, str_replace, batch_file_operations |
| Releases | 4 | list/get/create/update_release |
| Search | 1 | search_code |
| Commits | 1 | list_commits |
| Users | 5 | get_authenticated_user, get_user_info, list_user_repos, list_org_repos, search_users |
| GitHub Actions | 2 | list_workflows, get_workflow_runs |
| Workspace | 3 | repo_read_file_chunk, workspace_grep, str_replace |
| Licensing | 1 | license_info |
| Advanced | 1 | suggest_workflow |

## Authentication

Handled automatically via environment variables.

**Recommended (Simple):** Personal Access Token

- Set `GITHUB_TOKEN` environment variable
- 5,000 requests/hour
- 2-minute setup

**Advanced (Power Users):** GitHub App  

- 15,000 requests/hour
- See `docs/ADVANCED_GITHUB_APP.md`
- Requires creating your own GitHub App

The server automatically uses GitHub App if configured, otherwise falls back to PAT.

## Common Errors

| Code | Meaning | Hint |
|------|---------|------|
| 404 | Resource not found | Check owner/repo/path exists |
| 403 | Permission denied | Token may lack required scope |
| 422 | Validation failed | Check required parameters |
| 429 | Rate limited | Wait and retry |

## Multi-Step Workflows

Chain tools in a single execution for efficiency:

```typescript
// Create branch → Add file → Open PR
const branch = await callMCPTool("github_create_branch", {
  owner: "user", repo: "repo", 
  branch: "feature/new-feature", from_ref: "main"
});

const file = await callMCPTool("github_create_file", {
  owner: "user", repo: "repo", 
  path: "src/feature.ts", content: "// New feature",
  message: "Add feature", branch: "feature/new-feature"
});

const pr = await callMCPTool("github_create_pull_request", {
  owner: "user", repo: "repo",
  title: "Add new feature", body: "Description...",
  head: "feature/new-feature", base: "main"
});

return { branch: branch.branch, file: file.success, pr_url: pr.pr.html_url };
```

## Key Principles

1. **Discover first** - Use `listAvailableTools()` or `searchTools()` when unsure
2. **Inspect before calling** - `getToolInfo()` shows required params and return structure
3. **Chain for efficiency** - Multiple tools in one `execute_code` is better than multiple calls
4. **Results contain IDs and URLs** - Useful for chaining (e.g., `issue.number`, `pr.html_url`)
5. **Human intent drives usage** - What you DO with results depends on what the human asked for