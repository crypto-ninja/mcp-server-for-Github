# CLAUDE.md - AI Assistant Guide for GitHub MCP Server

## What You Have

**112 tools** (111 internal + execute_code) accessed through a single `execute_code` tool.
Write TypeScript to discover, call, and chain tools dynamically.

## Local vs Remote Tools

The server provides two types of file operation tools:

| Operation | Local (workspace_*) | Remote (github_*) |
|-----------|---------------------|-------------------|
| Read file | `workspace_read_file` | `github_get_file_content` |
| Search/grep | `workspace_grep` | `github_search_code` |
| Edit file | `workspace_str_replace` | `github_str_replace` |

**When to use Local (workspace_*) tools:**
- Reading/editing uncommitted local files
- Working in your development environment
- Files in MCP_WORKSPACE_ROOT directory

**When to use Remote (github_*) tools:**
- Reading files from GitHub repositories
- Creating commits, PRs, issues
- Any operation that hits the GitHub API

**Key difference:** Local tools work on YOUR filesystem. Remote tools work via GitHub's API and create commits.

## Tool Discovery

```typescript
// See all available tools (compact format - names grouped by category)
const tools = listAvailableTools();
// Returns: { totalTools: 112, categories: [{ name: "Issues", count: 5, tools: [...] }, ...] }

// Search for tools by keyword (compact results)
const matches = searchTools("pull request");
// Returns: [{ name: "github_create_pull_request", category: "Pull Requests", description: "..." }, ...]

// Get FULL details about a specific tool (parameters, examples, etc.)
const info = getToolInfo("github_create_issue");
// Returns complete tool definition with all parameters and examples

// Get all tools in a category
const prTools = getToolsInCategory("Pull Requests");
```

**Discovery Workflow:**
1. `listAvailableTools()` → See all tool names by category (compact)
2. `searchTools(keyword)` → Find relevant tools (compact)
3. `getToolInfo(toolName)` → Get full details (parameters, examples)
4. `callMCPTool(name, params)` → Execute the tool

**Always use `getToolInfo()`** before calling unfamiliar tools - it shows required vs optional parameters.

## Calling Tools

```typescript
const result = await callMCPTool("tool_name", { params });
```

**Key Feature:** `callMCPTool` automatically converts JavaScript objects to Pydantic models, so you can pass plain objects:

```typescript
// This works! Dict params are automatically converted to models
const issue = await callMCPTool("github_create_issue", {
  owner: "username",
  repo: "repository", 
  title: "Issue title",
  body: "Issue description"
});
// Result contains: number, html_url, title, state, labels, assignees, etc.
```

**Multiline Code Support:** You can write complex workflows with multiple tool calls:

```typescript
// Get repository info
const repo = await callMCPTool("github_get_repo_info", {
  owner: "facebook",
  repo: "react"
});

// List branches
const branches = await callMCPTool("github_list_branches", {
  owner: "facebook",
  repo: "react"
});

// List open issues
const issues = await callMCPTool("github_list_issues", {
  owner: "facebook",
  repo: "react",
  state: "open"
});

// Return combined result
return { 
  repo: repo.name, 
  branchCount: branches.length, 
  openIssues: issues.length 
};
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

## Tool Categories (111 total)

| Category | Count | Key Tools |
|----------|-------|-----------|
| GitHub Actions | 14 | list_workflows, get_workflow_runs, trigger_workflow, get_workflow_run, list_run_jobs, get_job, get_job_logs, rerun_workflow, cancel_workflow, list_artifacts, get_artifact, delete_artifact |
| Security | 13 | list_dependabot_alerts, get_dependabot_alert, update_dependabot_alert, list_code_scanning_alerts, list_secret_scanning_alerts, list_security_advisories |
| File Operations | 9 | get_file_content, list_contents, create/update/delete_file, grep, read_chunk, workspace_str_replace, batch_file_operations |
| Projects | 9 | list_repo_projects, list_org_projects, get_project, create_project, update_project, delete_project, list_columns, create_column |
| Repository Management | 8 | get_repo_info, create_repository, update_repository, list_user_repos, list_org_repos, list_collaborators, check_collaborator, list_teams |
| Pull Requests | 7 | create/merge/close_pr, get_pr_details, get_pr_overview_graphql, create_pr_review |
| **Discussions** | **7** | list_discussions, get_discussion, list_categories, list_comments, **create_discussion, update_discussion, add_discussion_comment** |
| Notifications | 6 | list_notifications, get_thread, mark_thread_read, mark_notifications_read, get_subscription, set_subscription |
| Branch Management | 5 | list/create/get/delete/compare_branches |
| Gists | 5 | list_gists, get_gist, create_gist, update_gist, delete_gist |
| Releases | 5 | list/get/create/update/delete_release |
| Issues | 5 | list/create/update_issue, add_issue_comment |
| Users | 5 | get_user_info, get_authenticated_user, search_users, list_user_repos, list_org_repos |
| Labels | 3 | list_labels, create_label, delete_label |
| Stargazers | 3 | list_stargazers, star_repository, unstar_repository |
| Workspace (Local) | 3 | workspace_read_file, workspace_grep, workspace_str_replace |
| Search | 1 | search_code |
| Commits | 1 | list_commits |

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

## Error Handling

### Tool Call Errors

When calling tools, you may encounter HTTP errors:

| Code | Meaning | Hint |
|------|---------|------|
| 404 | Resource not found | Check owner/repo/path exists |
| 403 | Permission denied | Token may lack required scope |
| 422 | Validation failed | Check required parameters |
| 429 | Rate limited | Wait and retry |

### Unknown Tool

When using `getToolInfo()` with a tool name that doesn't exist, it returns a helpful error object instead of crashing:

```typescript
const info = getToolInfo("unknown_tool");
// Returns: { 
//   error: "Tool 'unknown_tool' not found", 
//   suggestion: "Use searchTools() to find available tools", 
//   availableTools: 112 
// }
```

This makes it easy to handle typos or unknown tool names gracefully. Use `searchTools(keyword)` to find the correct tool name.

### Code Execution Errors

When executing code via `execute_code`, responses use a standardized format:

**Success:**

```typescript
{
  error: false,
  data: { /* your result */ }
}
```

**Error:**

```typescript
{
  error: true,
  message: "Human-readable error message",
  code: "ERROR_CODE",  // e.g., "VALIDATION_ERROR", "EXECUTION_ERROR"
  details: { /* optional context */ }
}
```

Common error codes:

- `VALIDATION_ERROR` - Code failed validation (blocked patterns, etc.)
- `EXECUTION_ERROR` - Runtime error during execution
- `TOOL_ERROR` - Error calling an MCP tool
- `TIMEOUT` - Execution exceeded 60s limit

See [Error Handling Guide](docs/ERROR_HANDLING.md) for complete documentation.

## Multi-Step Workflows

Chain tools in a single execution for efficiency. **Connection pooling** makes subsequent tool calls 97% faster (~108ms vs ~4000ms):

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

return { branch: branch.branch, file: file.success, pr_url: pr.url };
```

**Performance Note:** The first `execute_code` call takes ~4000ms (cold start), but subsequent calls within the same session use connection pooling and complete in ~108ms (97% faster!).

## GraphQL Tools

Some GitHub operations require GraphQL instead of REST. The server handles this automatically:

**Discussion Write Operations (GraphQL):**
```typescript
// Create a new discussion
const discussion = await callMCPTool("github_create_discussion", {
    owner: "org",
    repo: ".github",
    category_id: "DIC_xxx",  // Get from github_list_discussion_categories
    title: "New Feature Request",
    body: "Description of the feature..."
});

// Update an existing discussion
await callMCPTool("github_update_discussion", {
    owner: "org",
    repo: ".github",
    discussion_number: 123,
    body: "Updated content..."
});

// Add a comment to a discussion
await callMCPTool("github_add_discussion_comment", {
    owner: "org",
    repo: ".github",
    discussion_number: 123,
    body: "Great idea! Here's my feedback..."
});
```

**Note:** To create a discussion, you first need the `category_id` from `github_list_discussion_categories`.

## Performance

**Connection Pooling:** The server uses persistent Deno processes with MCP connections, providing:

- **First call:** ~4000ms (cold start - process creation + MCP initialization)
- **Subsequent calls:** ~108ms (warm - pooled process reuse)
- **97% latency reduction** for multi-tool workflows

This means chaining multiple tool calls in a single `execute_code` execution is highly efficient.

## Key Principles

1. **Discover first** - Use `listAvailableTools()` to see tool names by category
2. **Search to narrow** - Use `searchTools(keyword)` to find relevant tools
3. **Inspect before calling** - `getToolInfo(toolName)` shows required params and examples
4. **Chain for efficiency** - Multiple tools in one `execute_code` is better than multiple calls (97% faster with pooling!)
5. **Dict params work** - Pass plain JavaScript objects to `callMCPTool` - they're automatically converted to Pydantic models
6. **Multiline code supported** - Write complex workflows with multiple tool calls, conditionals, and loops
7. **Results contain IDs and URLs** - Useful for chaining (e.g., `issue.number`, `pr.html_url`)
8. **Human intent drives usage** - What you DO with results depends on what the human asked for
