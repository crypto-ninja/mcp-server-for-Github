# Token Efficiency Guide

This server is designed for AI agents where every token counts. Here's how to maximize efficiency.

## Why Token Efficiency Matters

- **Cost**: Fewer tokens = lower API costs
- **Context**: More room for your actual work
- **Speed**: Smaller payloads = faster responses
- **Quality**: Less noise = better AI reasoning

## Two Levels of Optimization

### 1. Code-First Architecture (98% reduction)

Traditional MCP servers load ALL tool definitions into context:
- 112 tools × ~500 tokens each = **~56,000 tokens** just for tool schemas

Our approach: Load ONE `execute_code` tool, discover others on-demand:
- 1 tool definition = **~800 tokens**
- **98% reduction** before you even start working!

### 2. Compact Response Format (80-97% reduction)

Every tool that returns data supports `response_format: "compact"`:
```typescript
// Full JSON (default for backward compatibility)
const fullRepo = await callMCPTool("github_get_repo_info", {
  owner: "facebook", repo: "react",
  response_format: "json"
});
// Returns: ~4,000 characters with all GitHub API fields

// Compact (recommended)
const compactRepo = await callMCPTool("github_get_repo_info", {
  owner: "facebook", repo: "react",
  response_format: "compact"
});
// Returns: ~200 characters with essential fields only
// { name, description, stars, forks, language, default_branch, url }
```

## Savings by Category

### Repository & Branch Tools

| Tool | Full JSON | Compact | Savings |
|------|-----------|---------|---------|
| `github_get_repo_info` | ~4,000 chars | ~200 chars | 95% |
| `github_list_branches` | ~800 chars/branch | ~50 chars/branch | 94% |
| `github_get_branch` | ~1,200 chars | ~80 chars | 93% |

### Issue & PR Tools

| Tool | Full JSON | Compact | Savings |
|------|-----------|---------|---------|
| `github_list_issues` | ~2,500 chars/issue | ~150 chars/issue | 94% |
| `github_list_pull_requests` | ~3,000 chars/PR | ~180 chars/PR | 94% |
| `github_get_pr_overview_graphql` | N/A | ~1,800 chars | 91% vs REST |

### Commit & Workflow Tools

| Tool | Full JSON | Compact | Savings |
|------|-----------|---------|---------|
| `github_list_commits` | ~3,000 chars/commit | ~100 chars/commit | 97% |
| `github_get_workflow_runs` | ~2,000 chars/run | ~120 chars/run | 94% |
| `github_get_workflow_run` | ~2,500 chars | ~150 chars | 94% |

### Search Tools

| Tool | Full JSON | Compact | Savings |
|------|-----------|---------|---------|
| `github_search_issues` | ~2,500 chars/result | ~150 chars/result | 94% |
| `github_search_repositories` | ~4,000 chars/result | ~200 chars/result | 95% |
| `github_search_code` | ~500 chars/result | ~100 chars/result | 80% |

## GraphQL vs REST

For Pull Requests, we offer both:

| Tool | Type | Size | Use When |
|------|------|------|----------|
| `github_get_pr_overview_graphql` | GraphQL | ~1,800 chars | Status, stats, reviews |
| `github_get_pr_details` | REST | ~20,000 chars | Need actual code diffs |

**91% smaller** with GraphQL when you don't need the patch content!

## Best Practices

### Always Do
```typescript
// ✅ Use compact for lists
const issues = await callMCPTool("github_list_issues", {
  owner, repo, limit: 20, response_format: "compact"
});

// ✅ Use compact for status checks
const runs = await callMCPTool("github_get_workflow_runs", {
  owner, repo, workflow_id: "ci.yml", response_format: "compact"
});

// ✅ Use GraphQL for PR overview
const pr = await callMCPTool("github_get_pr_overview_graphql", {
  owner, repo, pull_number, response_format: "compact"
});
```

### Only Use Full JSON When
```typescript
// ✅ Need full issue/PR body content
const fullIssue = await callMCPTool("github_get_issue", {
  owner, repo, issue_number, response_format: "json"
});

// ✅ Need actual code diffs
const prWithDiff = await callMCPTool("github_get_pr_details", {
  owner, repo, pull_number, include_files: true
});

// ✅ Processing raw data programmatically
const fullCommit = await callMCPTool("github_list_commits", {
  owner, repo, response_format: "json"  // Need PGP signatures, tree, etc.
});
```

## Bulk Operations

Before editing multiple files, check the most efficient approach:
```typescript
const suggestion = await callMCPTool("github_suggest_workflow", {
  operation: "multiple_file_edits",
  file_count: 10,
  num_edits: 25
});
// Returns: "LOCAL" with potential savings of 300,000+ tokens!
```

## Total Impact

For a typical development session:

| Without Optimization | With Optimization | Savings |
|---------------------|-------------------|---------|
| ~56,000 tokens (tool schemas) | ~800 tokens | 98% |
| ~50,000 tokens (responses) | ~5,000 tokens | 90% |
| **~106,000 total** | **~5,800 total** | **95%** |

**That's 18x more efficient than traditional MCP servers!**

