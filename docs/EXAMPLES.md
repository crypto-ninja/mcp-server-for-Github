# GitHub MCP Server - Code Execution Examples

(Contents moved from root EXAMPLES.md)

See root version history for full details. This file was relocated from project root as part of cleanup.


# GitHub MCP Server - Code Execution Examples

## Table of Contents

- [Simple Examples](#simple-examples)
- [Intermediate Examples](#intermediate-examples)
- [Advanced Examples](#advanced-examples)
- [Error Handling](#error-handling)
- [Real-World Workflows](#real-world-workflows)

## Simple Examples

### Get Repository Info

```typescript
const info = await callMCPTool("github_get_repo_info", {
    owner: "facebook",
    repo: "react"
});
return info;
```

### List Issues

```typescript
const issues = await callMCPTool("github_list_issues", {
    owner: "microsoft",
    repo: "vscode",
    state: "open",
    limit: 10
});
return issues;
```

### Search Repositories

```typescript
const results = await callMCPTool("github_search_repositories", {
    query: "machine learning language:python stars:>1000"
});
return results;
```

## Intermediate Examples

### Get Repo + Issues

```typescript
const repoInfo = await callMCPTool("github_get_repo_info", {
    owner: "facebook",
    repo: "react"
});

const issues = await callMCPTool("github_list_issues", {
    owner: "facebook",
    repo: "react",
    state: "open",
    limit: 5
});

return {
    repo: "facebook/react",
    repoFetched: repoInfo.length > 0,
    issuesFetched: issues.length > 0
};
```

### Create Issue with Validation

```typescript
// First check if repo exists
const repoInfo = await callMCPTool("github_get_repo_info", {
    owner: "myorg",
    repo: "myrepo"
});

if (repoInfo.includes("Not Found")) {
    return { error: "Repository not found" };
}

// Create the issue
const issue = await callMCPTool("github_create_issue", {
    owner: "myorg",
    repo: "myrepo",
    title: "New Feature Request",
    body: "Please add this feature..."
});

return { 
    success: true,
    issueCreated: true
};
```

## Advanced Examples

### Batch Issue Creation

```typescript
const issues = [];
const titles = [
    "Setup CI/CD pipeline",
    "Add test coverage",
    "Update documentation"
];

for (const title of titles) {
    const issue = await callMCPTool("github_create_issue", {
        owner: "myorg",
        repo: "myrepo",
        title: title,
        body: `Automated issue: ${title}`
    });
    issues.push(title);
}

return {
    created: issues.length,
    titles: issues
};
```

### Multi-Repo Analysis

```typescript
const repos = [
    { owner: "facebook", repo: "react" },
    { owner: "vuejs", repo: "vue" },
    { owner: "angular", repo: "angular" }
];

const results = [];

for (const repo of repos) {
    const info = await callMCPTool("github_get_repo_info", {
        owner: repo.owner,
        repo: repo.repo
    });
    
    results.push({
        name: `${repo.owner}/${repo.repo}`,
        fetched: info.length > 0
    });
}

return { repos: results };
```

### Conditional Workflow

```typescript
const repoInfo = await callMCPTool("github_get_repo_info", {
    owner: "facebook",
    repo: "react"
});

const isJavaScript = repoInfo.includes("JavaScript");
const isTypeScript = repoInfo.includes("TypeScript");

if (isTypeScript) {
    return { language: "TypeScript", analyzed: true };
} else if (isJavaScript) {
    return { language: "JavaScript", analyzed: true };
} else {
    return { language: "unknown", needsInvestigation: true };
}
```

## Error Handling

### Try-Catch Pattern

```typescript
try {
    const info = await callMCPTool("github_get_repo_info", {
        owner: "this-does-not",
        repo: "exist-12345"
    });
    return { success: true, info };
} catch (error) {
    return { 
        success: false,
        error: "Repository not found"
    };
}
```

### Validation Before Action

```typescript
// Validate input
const owner = "facebook";
const repo = "react";

if (!owner || !repo) {
    return { error: "Owner and repo are required" };
}

// Get repo info
const repoInfo = await callMCPTool("github_get_repo_info", {
    owner: owner,
    repo: repo
});

if (repoInfo.includes("Not Found")) {
    return { error: "Repository does not exist" };
}

return { success: true, repo: `${owner}/${repo}` };
```

## Real-World Workflows

### Release Creation

```typescript
const commits = await callMCPTool("github_list_commits", {
    owner: "myorg",
    repo: "myrepo",
    limit: 1
});

const release = await callMCPTool("github_create_release", {
    owner: "myorg",
    repo: "myrepo",
    tag_name: "v1.2.0",
    name: "Release v1.2.0",
    body: "Release notes here..."
});

return {
    action: "release_created",
    version: "v1.2.0",
    success: true
};
```

### PR Workflow

```typescript
const prDetails = await callMCPTool("github_get_pr_details", {
    owner: "myorg",
    repo: "myrepo",
    pull_number: 42,
    include_reviews: true
});

const isApproved = prDetails.includes("APPROVED");

if (isApproved) {
    const mergeResult = await callMCPTool("github_merge_pull_request", {
        owner: "myorg",
        repo: "myrepo",
        pull_number: 42,
        merge_method: "squash"
    });
    
    return {
        action: "merged",
        pr: 42,
        success: true
    };
} else {
    return {
        action: "waiting_for_approval",
        pr: 42
    };
}
```

### Code Search Analysis

```typescript
const todos = await callMCPTool("github_search_code", {
    query: "TODO repo:myorg/myrepo"
});

const fixmes = await callMCPTool("github_search_code", {
    query: "FIXME repo:myorg/myrepo"
});

return {
    todosFound: todos.includes("Found"),
    fixmesFound: fixmes.includes("Found"),
    recommendation: "Review code comments"
};
```

---

See [CODE_EXECUTION_GUIDE.md](CODE_EXECUTION_GUIDE.md) for full documentation.
