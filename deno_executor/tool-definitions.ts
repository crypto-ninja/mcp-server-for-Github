/**
 * Complete tool definitions for all GitHub MCP tools
 * This enables intelligent tool discovery without loading all tools into context
 */

export interface ToolParameter {
  type: string;
  required: boolean;
  description: string;
  example?: string;
}

export interface ToolDefinition {
  name: string;
  category: string;
  description: string;
  parameters: Record<string, ToolParameter>;
  returns: string;
  example: string;
}

export const GITHUB_TOOLS: ToolDefinition[] = [
  // REPOSITORY MANAGEMENT (7 tools)
  {
    name: "github_get_repo_info",
    category: "Repository Management",
    description: "Get detailed information about a GitHub repository including stars, forks, description, topics, and metadata",
    parameters: {
      owner: {
        type: "string",
        required: true,
        description: "Repository owner (username or organization)",
        example: "facebook"
      },
      repo: {
        type: "string",
        required: true,
        description: "Repository name",
        example: "react"
      }
    },
    returns: "Markdown formatted repository information",
    example: `const info = await callMCPTool("github_get_repo_info", {
  owner: "facebook",
  repo: "react"
});`
  },
  {
    name: "github_create_repository",
    category: "Repository Management",
    description: "Create a new GitHub repository",
    parameters: {
      name: { type: "string", required: true, description: "Repository name" },
      description: { type: "string", required: false, description: "Repository description" },
      private: { type: "boolean", required: false, description: "Make repository private", example: "false" }
    },
    returns: "Success confirmation with repository URL",
    example: `const result = await callMCPTool("github_create_repository", {
  name: "my-new-repo",
  description: "My awesome project",
  private: false
});`
  },
  {
    name: "github_update_repository",
    category: "Repository Management",
    description: "Update repository settings",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      name: { type: "string", required: false, description: "New repository name" },
      description: { type: "string", required: false, description: "New description" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_update_repository", {
  owner: "myuser",
  repo: "myrepo",
  description: "Updated description"
});`
  },
  {
    name: "github_delete_repository",
    category: "Repository Management",
    description: "Delete a GitHub repository (PERMANENT - cannot be undone!)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_delete_repository", {
  owner: "myuser",
  repo: "old-repo"
});`
  },
  {
    name: "github_transfer_repository",
    category: "Repository Management",
    description: "Transfer repository to another user or organization",
    parameters: {
      owner: { type: "string", required: true, description: "Current owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      new_owner: { type: "string", required: true, description: "New owner username or org" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_transfer_repository", {
  owner: "myuser",
  repo: "myrepo",
  new_owner: "myorg"
});`
  },
  {
    name: "github_archive_repository",
    category: "Repository Management",
    description: "Archive a repository (make it read-only)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_archive_repository", {
  owner: "myuser",
  repo: "archived-project"
});`
  },
  {
    name: "github_search_repositories",
    category: "Repository Management",
    description: "Search GitHub repositories with advanced query syntax",
    parameters: {
      query: { 
        type: "string", 
        required: true, 
        description: "Search query (supports language:, stars:, etc.)",
        example: "machine learning language:python stars:>1000"
      }
    },
    returns: "List of matching repositories with details",
    example: `const results = await callMCPTool("github_search_repositories", {
  query: "react language:javascript stars:>10000"
});`
  },

  // ISSUES (4 tools)
  {
    name: "github_list_issues",
    category: "Issues",
    description: "List issues in a repository with optional filtering by state",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      state: { type: "string", required: false, description: "'open', 'closed', or 'all'", example: "open" },
      limit: { type: "number", required: false, description: "Maximum number to return (1-100)", example: "10" }
    },
    returns: "Formatted list of issues with numbers, titles, states, and URLs",
    example: `const issues = await callMCPTool("github_list_issues", {
  owner: "facebook",
  repo: "react",
  state: "open",
  limit: 10
});`
  },
  {
    name: "github_create_issue",
    category: "Issues",
    description: "Create a new issue in a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      title: { type: "string", required: true, description: "Issue title" },
      body: { type: "string", required: false, description: "Issue description/body" }
    },
    returns: "Created issue details with number and URL",
    example: `const issue = await callMCPTool("github_create_issue", {
  owner: "myuser",
  repo: "myrepo",
  title: "Bug: Fix login error",
  body: "Users are experiencing login failures..."
});`
  },
  {
    name: "github_update_issue",
    category: "Issues",
    description: "Update an existing issue (state, title, body, labels)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      issue_number: { type: "number", required: true, description: "Issue number" },
      state: { type: "string", required: false, description: "'open' or 'closed'" },
      title: { type: "string", required: false, description: "New title" },
      body: { type: "string", required: false, description: "New body" },
      labels: { type: "array", required: false, description: "Array of label names" }
    },
    returns: "Updated issue details",
    example: `const result = await callMCPTool("github_update_issue", {
  owner: "myuser",
  repo: "myrepo",
  issue_number: 42,
  state: "closed",
  labels: ["bug", "fixed"]
});`
  },
  {
    name: "github_search_issues",
    category: "Issues",
    description: "Search issues and pull requests across GitHub",
    parameters: {
      query: { 
        type: "string", 
        required: true, 
        description: "Search query (supports is:issue, is:pr, label:, etc.)",
        example: "is:issue is:open label:bug repo:facebook/react"
      }
    },
    returns: "List of matching issues/PRs",
    example: `const results = await callMCPTool("github_search_issues", {
  query: "is:issue is:open label:bug repo:facebook/react"
});`
  },

  // PULL REQUESTS (7 tools)
  {
    name: "github_list_pull_requests",
    category: "Pull Requests",
    description: "List pull requests in a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      state: { type: "string", required: false, description: "'open', 'closed', or 'all'", example: "open" },
      limit: { type: "number", required: false, description: "Maximum number to return", example: "10" }
    },
    returns: "List of pull requests with numbers, titles, and states",
    example: `const prs = await callMCPTool("github_list_pull_requests", {
  owner: "facebook",
  repo: "react",
  state: "open"
});`
  },
  {
    name: "github_create_pull_request",
    category: "Pull Requests",
    description: "Create a new pull request",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      title: { type: "string", required: true, description: "PR title" },
      body: { type: "string", required: true, description: "PR description" },
      head: { type: "string", required: true, description: "Source branch name" },
      base: { type: "string", required: true, description: "Target branch (usually 'main' or 'master')" }
    },
    returns: "Created PR details with number and URL",
    example: `const pr = await callMCPTool("github_create_pull_request", {
  owner: "myuser",
  repo: "myrepo",
  title: "Add new feature",
  body: "This PR adds...",
  head: "feature-branch",
  base: "main"
});`
  },
  {
    name: "github_get_pr_details",
    category: "Pull Requests",
    description: "Get detailed information about a pull request",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      pull_number: { type: "number", required: true, description: "PR number" },
      include_reviews: { type: "boolean", required: false, description: "Include review comments" },
      include_commits: { type: "boolean", required: false, description: "Include commit history" }
    },
    returns: "Detailed PR information including reviews and commits if requested",
    example: `const details = await callMCPTool("github_get_pr_details", {
  owner: "facebook",
  repo: "react",
  pull_number: 12345,
  include_reviews: true
});`
  },
  {
    name: "github_get_pr_overview_graphql",
    category: "Pull Requests",
    description: "Get PR overview using efficient GraphQL query (faster than REST)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      pull_number: { type: "number", required: true, description: "PR number" }
    },
    returns: "PR overview with metadata",
    example: `const overview = await callMCPTool("github_get_pr_overview_graphql", {
  owner: "facebook",
  repo: "react",
  pull_number: 12345
});`
  },
  {
    name: "github_merge_pull_request",
    category: "Pull Requests",
    description: "Merge a pull request",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      pull_number: { type: "number", required: true, description: "PR number" },
      merge_method: { type: "string", required: false, description: "'merge', 'squash', or 'rebase'", example: "squash" }
    },
    returns: "Merge confirmation",
    example: `const result = await callMCPTool("github_merge_pull_request", {
  owner: "myuser",
  repo: "myrepo",
  pull_number: 42,
  merge_method: "squash"
});`
  },
  {
    name: "github_close_pull_request",
    category: "Pull Requests",
    description: "Close a pull request without merging",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      pull_number: { type: "number", required: true, description: "PR number" }
    },
    returns: "Close confirmation",
    example: `const result = await callMCPTool("github_close_pull_request", {
  owner: "myuser",
  repo: "myrepo",
  pull_number: 42
});`
  },
  {
    name: "github_create_pr_review",
    category: "Pull Requests",
    description: "Create a review on a pull request",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      pull_number: { type: "number", required: true, description: "PR number" },
      body: { type: "string", required: true, description: "Review comment" },
      event: { type: "string", required: false, description: "'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'" }
    },
    returns: "Review confirmation",
    example: `const review = await callMCPTool("github_create_pr_review", {
  owner: "myuser",
  repo: "myrepo",
  pull_number: 42,
  body: "Looks good to me!",
  event: "APPROVE"
});`
  },

  // FILES (5 tools)
  {
    name: "github_get_file_content",
    category: "File Operations",
    description: "Get the contents of a file from a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      path: { type: "string", required: true, description: "File path", example: "src/index.js" }
    },
    returns: "File content as text",
    example: `const content = await callMCPTool("github_get_file_content", {
  owner: "facebook",
  repo: "react",
  path: "README.md"
});`
  },
  {
    name: "github_list_repo_contents",
    category: "File Operations",
    description: "List files and directories in a repository path",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      path: { type: "string", required: false, description: "Directory path (empty for root)", example: "src" }
    },
    returns: "List of files and directories",
    example: `const contents = await callMCPTool("github_list_repo_contents", {
  owner: "facebook",
  repo: "react",
  path: "packages"
});`
  },

  // BRANCH MANAGEMENT (5 tools)
  {
    name: "github_list_branches",
    category: "Branch Management",
    description: "List all branches in a GitHub repository with protection status and commit information",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      protected: { type: "boolean", required: false, description: "Filter by protected status" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      response_format: { type: "string", required: false, description: "Output format: 'json' or 'markdown'" }
    },
    returns: "List of branches with names, commit SHAs, protection status, and default branch indicator",
    example: `const branches = await callMCPTool("github_list_branches", {
  owner: "myuser",
  repo: "myrepo",
  protected: false
});`
  },
  {
    name: "github_create_branch",
    category: "Branch Management",
    description: "Create a new branch from a specified ref (branch, tag, or commit SHA)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      branch: { type: "string", required: true, description: "New branch name" },
      from_ref: { type: "string", required: false, description: "Branch, tag, or commit SHA to branch from (default: 'main')" }
    },
    returns: "Success confirmation with branch details and URL",
    example: `const result = await callMCPTool("github_create_branch", {
  owner: "myuser",
  repo: "myrepo",
  branch: "feature/new-feature",
  from_ref: "main"
});`
  },
  {
    name: "github_get_branch",
    category: "Branch Management",
    description: "Get detailed information about a branch including protection status and latest commit",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      branch: { type: "string", required: true, description: "Branch name" },
      response_format: { type: "string", required: false, description: "Output format: 'json' or 'markdown'" }
    },
    returns: "Detailed branch information with commit details and protection status",
    example: `const branch = await callMCPTool("github_get_branch", {
  owner: "myuser",
  repo: "myrepo",
  branch: "feature-branch"
});`
  },
  {
    name: "github_delete_branch",
    category: "Branch Management",
    description: "Delete a branch from a repository. Cannot delete default or protected branches",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      branch: { type: "string", required: true, description: "Branch name to delete" }
    },
    returns: "Success confirmation (permanent operation)",
    example: `const result = await callMCPTool("github_delete_branch", {
  owner: "myuser",
  repo: "myrepo",
  branch: "old-feature-branch"
});`
  },
  {
    name: "github_compare_branches",
    category: "Branch Management",
    description: "Compare two branches to see commits ahead/behind and files changed. Useful before merging",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      base: { type: "string", required: true, description: "Base branch name (usually 'main')" },
      head: { type: "string", required: true, description: "Head branch name to compare" },
      response_format: { type: "string", required: false, description: "Output format: 'json' or 'markdown'" }
    },
    returns: "Comparison results with commits ahead/behind and files changed",
    example: `const comparison = await callMCPTool("github_compare_branches", {
  owner: "myuser",
  repo: "myrepo",
  base: "main",
  head: "feature-branch"
});`
  },
  {
    name: "github_create_file",
    category: "File Operations",
    description: "Create a new file in a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      path: { type: "string", required: true, description: "File path", example: "docs/new-file.md" },
      content: { type: "string", required: true, description: "File content" },
      message: { type: "string", required: true, description: "Commit message" }
    },
    returns: "Success confirmation with commit SHA",
    example: `const result = await callMCPTool("github_create_file", {
  owner: "myuser",
  repo: "myrepo",
  path: "README.md",
  content: "# My Project\\n\\nDescription here",
  message: "Add README"
});`
  },
  {
    name: "github_update_file",
    category: "File Operations",
    description: "Update an existing file in a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      path: { type: "string", required: true, description: "File path" },
      content: { type: "string", required: true, description: "New file content" },
      message: { type: "string", required: true, description: "Commit message" },
      sha: { type: "string", required: true, description: "Current file SHA (get from github_get_file_content)" }
    },
    returns: "Success confirmation with new commit SHA",
    example: `const result = await callMCPTool("github_update_file", {
  owner: "myuser",
  repo: "myrepo",
  path: "README.md",
  content: "Updated content",
      message: "Update README",
      sha: "abc123..."
});`
  },
  {
    name: "github_delete_file",
    category: "File Operations",
    description: "Delete a file from a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      path: { type: "string", required: true, description: "File path" },
      message: { type: "string", required: true, description: "Commit message" },
      sha: { type: "string", required: true, description: "Current file SHA" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_delete_file", {
  owner: "myuser",
  repo: "myrepo",
  path: "old-file.txt",
  message: "Remove old file",
  sha: "abc123..."
});`
  },
  {
    name: "github_grep",
    category: "File Operations",
    description: "Search for patterns in GitHub repository files using grep-like functionality. Returns only matching lines with context instead of full files (90%+ token efficient)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner", example: "facebook" },
      repo: { type: "string", required: true, description: "Repository name", example: "react" },
      pattern: { type: "string", required: true, description: "Regex pattern to search for", example: "TODO|FIXME" },
      ref: { type: "string", required: false, description: "Branch, tag, or commit SHA (defaults to default branch)" },
      file_pattern: { type: "string", required: false, description: "Glob pattern for files", example: "*.py" },
      path: { type: "string", required: false, description: "Optional subdirectory to search within" },
      case_sensitive: { type: "boolean", required: false, description: "Whether search is case-sensitive", example: "true" },
      context_lines: { type: "number", required: false, description: "Number of lines before/after match to include (0-5)", example: "2" },
      max_results: { type: "number", required: false, description: "Maximum matches to return (1-500)", example: "100" }
    },
    returns: "Formatted search results with file paths, line numbers, and matches",
    example: `const results = await callMCPTool("github_grep", {
  owner: "facebook",
  repo: "react",
  pattern: "async def",
  file_pattern: "*.py",
  max_results: 50
});`
  },
  {
    name: "github_read_file_chunk",
    category: "File Operations",
    description: "Read a specific range of lines from a GitHub repository file. Token-efficient file reading (90%+ savings vs full file)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner", example: "facebook" },
      repo: { type: "string", required: true, description: "Repository name", example: "react" },
      path: { type: "string", required: true, description: "File path in repository", example: "src/index.js" },
      start_line: { type: "number", required: false, description: "1-based starting line number", example: "50" },
      num_lines: { type: "number", required: false, description: "Number of lines to read (max 500)", example: "100" },
      ref: { type: "string", required: false, description: "Branch, tag, or commit SHA (defaults to default branch)" }
    },
    returns: "Numbered lines from the file with metadata",
    example: `const chunk = await callMCPTool("github_read_file_chunk", {
  owner: "facebook",
  repo: "react",
  path: "src/index.js",
  start_line: 50,
  num_lines: 100
});`
  },
  {
    name: "github_str_replace",
    category: "File Operations",
    description: "Replace an exact string match in a GitHub repository file with a new string. The match must be unique to prevent accidental replacements. Updates file via GitHub API",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner", example: "facebook" },
      repo: { type: "string", required: true, description: "Repository name", example: "react" },
      path: { type: "string", required: true, description: "File path in repository", example: "README.md" },
      old_str: { type: "string", required: true, description: "Exact string to find and replace (must be unique)" },
      new_str: { type: "string", required: true, description: "Replacement string" },
      ref: { type: "string", required: false, description: "Branch, tag, or commit SHA (defaults to default branch)" },
      commit_message: { type: "string", required: false, description: "Custom commit message (auto-generated if not provided)" },
      description: { type: "string", required: false, description: "Optional description of the change" }
    },
    returns: "Confirmation message with commit details",
    example: `const result = await callMCPTool("github_str_replace", {
  owner: "myuser",
  repo: "myrepo",
  path: "README.md",
  old_str: "v1.0.0",
  new_str: "v2.0.0"
});`
  },

  // BATCH OPERATIONS (1 tool)
  {
    name: "github_batch_file_operations",
    category: "File Operations",
    description: "Perform multiple file operations in a single commit (create/update/delete)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      operations: { type: "array", required: true, description: "Array of operations" },
      message: { type: "string", required: true, description: "Commit message" }
    },
    returns: "Success confirmation for all operations",
    example: `const result = await callMCPTool("github_batch_file_operations", {
  owner: "myuser",
  repo: "myrepo",
  operations: [
    { action: "create", path: "new.txt", content: "New file" },
    { action: "update", path: "existing.txt", content: "Updated", sha: "abc123" }
  ],
  message: "Batch update"
});`
  },

  // SEARCH (3 tools)
  {
    name: "github_search_code",
    category: "Search",
    description: "Search code across GitHub repositories",
    parameters: {
      query: { 
        type: "string", 
        required: true, 
        description: "Search query (supports repo:, language:, path:, etc.)",
        example: "TODO repo:facebook/react language:javascript"
      }
    },
    returns: "Code search results with file paths and snippets",
    example: `const results = await callMCPTool("github_search_code", {
  query: "function login repo:myuser/myrepo"
});`
  },

  // RELEASES (4 tools)
  {
    name: "github_list_releases",
    category: "Releases",
    description: "List releases in a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" }
    },
    returns: "List of releases with tags, dates, and descriptions",
    example: `const releases = await callMCPTool("github_list_releases", {
  owner: "facebook",
  repo: "react"
});`
  },
  {
    name: "github_get_release",
    category: "Releases",
    description: "Get details of a specific release",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      tag_name: { type: "string", required: true, description: "Release tag", example: "v1.0.0" }
    },
    returns: "Detailed release information",
    example: `const release = await callMCPTool("github_get_release", {
  owner: "facebook",
  repo: "react",
  tag_name: "v18.0.0"
});`
  },
  {
    name: "github_create_release",
    category: "Releases",
    description: "Create a new release",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      tag_name: { type: "string", required: true, description: "Git tag for release", example: "v1.0.0" },
      name: { type: "string", required: true, description: "Release title" },
      body: { type: "string", required: true, description: "Release notes/description" },
      draft: { type: "boolean", required: false, description: "Create as draft" },
      prerelease: { type: "boolean", required: false, description: "Mark as pre-release" }
    },
    returns: "Created release details with URL",
    example: `const release = await callMCPTool("github_create_release", {
  owner: "myuser",
  repo: "myrepo",
  tag_name: "v2.0.0",
  name: "Version 2.0.0",
  body: "Major release with new features...",
  draft: false,
  prerelease: false
});`
  },
  {
    name: "github_update_release",
    category: "Releases",
    description: "Update an existing release",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      tag_name: { type: "string", required: true, description: "Release tag" },
      name: { type: "string", required: false, description: "New title" },
      body: { type: "string", required: false, description: "New description" },
      draft: { type: "boolean", required: false, description: "Update draft status" },
      prerelease: { type: "boolean", required: false, description: "Update prerelease status" }
    },
    returns: "Updated release details",
    example: `const release = await callMCPTool("github_update_release", {
  owner: "myuser",
  repo: "myrepo",
  tag_name: "v2.0.0",
  body: "Updated release notes..."
});`
  },

  // WORKFLOWS (2 tools)
  {
    name: "github_list_workflows",
    category: "GitHub Actions",
    description: "List GitHub Actions workflows in a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" }
    },
    returns: "List of workflow files with IDs and paths",
    example: `const workflows = await callMCPTool("github_list_workflows", {
  owner: "facebook",
  repo: "react"
});`
  },
  {
    name: "github_get_workflow_runs",
    category: "GitHub Actions",
    description: "Get recent workflow runs",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      workflow_id: { type: "string", required: false, description: "Specific workflow ID" }
    },
    returns: "List of workflow runs with statuses and timestamps",
    example: `const runs = await callMCPTool("github_get_workflow_runs", {
  owner: "facebook",
  repo: "react"
});`
  },

  // COMMITS (1 tool)
  {
    name: "github_list_commits",
    category: "Commits",
    description: "List commits in a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      limit: { type: "number", required: false, description: "Maximum number to return", example: "10" }
    },
    returns: "List of commits with SHAs, messages, authors, and dates",
    example: `const commits = await callMCPTool("github_list_commits", {
  owner: "facebook",
  repo: "react",
  limit: 10
});`
  },

  // USERS (1 tool)
  {
    name: "github_get_user_info",
    category: "Users",
    description: "Get information about a GitHub user or organization",
    parameters: {
      username: { type: "string", required: true, description: "GitHub username or organization name" }
    },
    returns: "User profile information",
    example: `const user = await callMCPTool("github_get_user_info", {
  username: "torvalds"
});`
  },

  // ADVANCED (1 tool)
  {
    name: "github_suggest_workflow",
    category: "Advanced",
    description: "Get AI-powered workflow suggestions based on repository analysis",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" }
    },
    returns: "Suggested workflow improvements and best practices",
    example: `const suggestions = await callMCPTool("github_suggest_workflow", {
  owner: "myuser",
  repo: "myrepo"
});`
  },

  // WORKSPACE (3 tools)
  {
    name: "repo_read_file_chunk",
    category: "Workspace",
    description: "Read a chunk of lines from a file in the workspace repository",
    parameters: {
      path: { type: "string", required: true, description: "File path relative to repo root" },
      start_line: { type: "number", required: true, description: "Starting line number (1-indexed)" },
      num_lines: { type: "number", required: true, description: "Number of lines to read" }
    },
    returns: "File chunk with line numbers",
    example: `const chunk = await callMCPTool("repo_read_file_chunk", {
  path: "src/index.js",
  start_line: 1,
  num_lines: 50
});`
  },
  {
    name: "workspace_grep",
    category: "Workspace",
    description: "Search for pattern in workspace files (90-98% more token efficient than reading full files)",
    parameters: {
      pattern: { type: "string", required: true, description: "Regex pattern to search for" },
      file_pattern: { type: "string", required: false, description: "Glob pattern for files", example: "*.py" }
    },
    returns: "Matching lines with file paths and line numbers",
    example: `const matches = await callMCPTool("workspace_grep", {
  pattern: "TODO|FIXME",
  file_pattern: "*.js"
});`
  },
  {
    name: "str_replace",
    category: "Workspace",
    description: "Replace a string in a file (must be unique in the file)",
    parameters: {
      path: { type: "string", required: true, description: "File path" },
      old_str: { type: "string", required: true, description: "String to replace (must be unique)" },
      new_str: { type: "string", required: true, description: "Replacement string" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("str_replace", {
  path: "version.txt",
  old_str: "v1.0.0",
  new_str: "v2.0.0"
});`
  },

  // LICENSE (1 tool)
  {
    name: "github_license_info",
    category: "Licensing",
    description: "Display GitHub MCP Server license information and tier status",
    parameters: {},
    returns: "License tier and status information",
    example: `const license = await callMCPTool("github_license_info", {});`
  },

  // CODE EXECUTION (1 tool)
  {
    name: "execute_code",
    category: "Code Execution",
    description: "Execute TypeScript code with access to all GitHub MCP tools. Revolutionary 98% token reduction through code-first execution. Supports tool discovery, complex workflows, conditional logic, and error handling",
    parameters: {
      code: {
        type: "string",
        required: true,
        description: "TypeScript code to execute. Can call any GitHub tool via callMCPTool(), use listAvailableTools() for discovery, searchTools() to find tools, and getToolInfo() for details",
        example: `const info = await callMCPTool("github_get_repo_info", { owner: "facebook", repo: "react" });\nreturn info;`
      }
    },
    returns: "Execution result with success status, result data, or error information",
    example: `const result = await callMCPTool("execute_code", {
  code: \`const tools = listAvailableTools();
const info = await callMCPTool("github_get_repo_info", {
  owner: "facebook",
  repo: "react"
});
return { totalTools: tools.totalTools, repoInfo: info };\`
});`
  },
];

// Helper function to get tools by category
export function getToolsByCategory(category: string): ToolDefinition[] {
  return GITHUB_TOOLS.filter(tool => tool.category === category);
}

// Helper function to get all categories
export function getCategories(): string[] {
  const categories = new Set(GITHUB_TOOLS.map(tool => tool.category));
  return Array.from(categories).sort();
}

