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

  // STARGAZERS (3 tools)
  {
    name: "github_list_stargazers",
    category: "Stargazers",
    description: "List users who have starred a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)", example: "30" },
      page: { type: "number", required: false, description: "Page number for pagination", example: "1" }
    },
    returns: "List of users who starred the repository, including login and profile URLs",
    example: `const stargazers = await callMCPTool("github_list_stargazers", {
  owner: "facebook",
  repo: "react",
  per_page: 10
});`
  },
  {
    name: "github_star_repository",
    category: "Stargazers",
    description: "Star a repository for the authenticated user",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" }
    },
    returns: "Success confirmation that the repository was starred",
    example: `const result = await callMCPTool("github_star_repository", {
  owner: "myuser",
  repo: "myrepo"
});`
  },
  {
    name: "github_unstar_repository",
    category: "Stargazers",
    description: "Unstar a repository for the authenticated user",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" }
    },
    returns: "Success confirmation that the repository was unstarred",
    example: `const result = await callMCPTool("github_unstar_repository", {
  owner: "myuser",
  repo: "myrepo"
});`
  },

  // LABELS (3 tools)
  {
    name: "github_list_labels",
    category: "Labels",
    description: "List all labels in a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)", example: "30" },
      page: { type: "number", required: false, description: "Page number for pagination", example: "1" }
    },
    returns: "List of labels including name, color, and description",
    example: `const labels = await callMCPTool("github_list_labels", {
  owner: "myuser",
  repo: "myrepo"
});`
  },
  {
    name: "github_create_label",
    category: "Labels",
    description: "Create a new label in a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      name: { type: "string", required: true, description: "Label name" },
      color: { type: "string", required: true, description: "6-character hex color code without '#'", example: "ff0000" },
      description: { type: "string", required: false, description: "Label description" }
    },
    returns: "Created label details including name, color, and description",
    example: `const label = await callMCPTool("github_create_label", {
  owner: "myuser",
  repo: "myrepo",
  name: "bug",
  color: "d73a4a",
  description: "Something isn't working"
});`
  },
  {
    name: "github_delete_label",
    category: "Labels",
    description: "Delete a label from a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      name: { type: "string", required: true, description: "Label name to delete" }
    },
    returns: "Success confirmation message",
    example: `const result = await callMCPTool("github_delete_label", {
  owner: "myuser",
  repo: "myrepo",
  name: "old-label"
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
    name: "github_add_issue_comment",
    category: "Issues",
    description: "Add a comment to an existing issue",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      issue_number: { type: "number", required: true, description: "Issue number to comment on" },
      body: { type: "string", required: true, description: "Comment content in Markdown format" }
    },
    returns: "Created comment details including id, URL, author, timestamps, and body",
    example: `const comment = await callMCPTool("github_add_issue_comment", {
  owner: "myuser",
  repo: "myrepo",
  issue_number: 42,
  body: "Thanks for reporting this! We'll look into it."
});`
  },

  // GISTS (4 tools)
  {
    name: "github_list_gists",
    category: "Gists",
    description: "List gists for the authenticated user or a specified user",
    parameters: {
      username: { type: "string", required: false, description: "GitHub username (omit for authenticated user)" },
      since: { type: "string", required: false, description: "Only gists updated after this time (ISO 8601)" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)", example: "30" },
      page: { type: "number", required: false, description: "Page number for pagination", example: "1" }
    },
    returns: "List of gists with id, description, visibility, files, and URLs",
    example: `const gists = await callMCPTool("github_list_gists", {
  username: "octocat",
  per_page: 10
});`
  },
  {
    name: "github_get_gist",
    category: "Gists",
    description: "Get the full content and metadata for a specific gist",
    parameters: {
      gist_id: { type: "string", required: true, description: "ID of the gist to retrieve" }
    },
    returns: "Full gist details including files, owner, history, and URLs",
    example: `const gist = await callMCPTool("github_get_gist", {
  gist_id: "aa5a315d61ae9438b18d"
});`
  },
  {
    name: "github_create_gist",
    category: "Gists",
    description: "Create a new gist with one or more files",
    parameters: {
      description: { type: "string", required: false, description: "Description of the gist" },
      public: { type: "boolean", required: false, description: "Whether the gist is public (default: false)" },
      files: { type: "object", required: true, description: "Mapping of filename to { content }" }
    },
    returns: "Created gist details including id, html_url, and files",
    example: `const gist = await callMCPTool("github_create_gist", {
  description: "Example gist from GitHub MCP",
  public: false,
  files: {
    "hello.py": { content: "print('Hello from MCP!')" },
    "README.md": { content: "# My Gist\\nCreated via GitHub MCP Server." }
  }
});`
  },
  {
    name: "github_update_gist",
    category: "Gists",
    description: "Update an existing gist's description or files. To delete a file, set its value to null in the files object",
    parameters: {
      gist_id: { type: "string", required: true, description: "ID of the gist to update" },
      description: { type: "string", required: false, description: "New description" },
      files: { type: "object", required: false, description: "Files to add/update/delete" }
    },
    returns: "Updated gist details including id, html_url, and files",
    example: `const gist = await callMCPTool("github_update_gist", {
  gist_id: "aa5a315d61ae9438b18d",
  description: "Updated description",
  files: {
    "hello.py": { content: "print('Updated content')" },
    "old.txt": null
  }
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
    description: "Get detailed information about a specific release or the latest release",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      tag: { type: "string", required: false, description: "Release tag (e.g., 'v1.0.0') or 'latest' for most recent (default: 'latest')", example: "v1.0.0" },
      response_format: { type: "string", required: false, description: "Output format: 'json' or 'markdown' (default: 'markdown')" }
    },
    returns: "Detailed release information with tag, status, dates, author, and URL",
    example: `const release = await callMCPTool("github_get_release", {
  owner: "facebook",
  repo: "react",
  tag: "v18.0.0"
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
    description: "Update an existing GitHub release. Only provided fields will be updated - others remain unchanged",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      release_id: { type: "string", required: true, description: "Release ID or tag name (e.g., 'v1.2.0')" },
      tag_name: { type: "string", required: false, description: "New tag name (use carefully!)" },
      name: { type: "string", required: false, description: "New release title" },
      body: { type: "string", required: false, description: "New release notes/description in Markdown format" },
      draft: { type: "boolean", required: false, description: "Set draft status" },
      prerelease: { type: "boolean", required: false, description: "Set pre-release status" }
    },
    returns: "Updated release details with confirmation",
    example: `const release = await callMCPTool("github_update_release", {
  owner: "myuser",
  repo: "myrepo",
  release_id: "v2.0.0",
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
  {
    name: "github_get_workflow",
    category: "GitHub Actions",
    description: "Get details about a specific GitHub Actions workflow",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      workflow_id: { type: "string", required: true, description: "Workflow ID (numeric) or workflow file name (e.g., 'ci.yml')" }
    },
    returns: "Workflow details including configuration and status",
    example: `const workflow = await callMCPTool("github_get_workflow", {
  owner: "facebook",
  repo: "react",
  workflow_id: "ci.yml"
});`
  },
  {
    name: "github_trigger_workflow",
    category: "GitHub Actions",
    description: "Trigger a workflow dispatch event (manually run a workflow)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      workflow_id: { type: "string", required: true, description: "Workflow ID or file name" },
      ref: { type: "string", required: true, description: "Branch, tag, or commit SHA to trigger workflow on" },
      inputs: { type: "object", required: false, description: "Input parameters for workflow (key-value pairs)" }
    },
    returns: "Success confirmation (202 Accepted)",
    example: `const result = await callMCPTool("github_trigger_workflow", {
  owner: "myuser",
  repo: "myrepo",
  workflow_id: "deploy.yml",
  ref: "main",
  inputs: { environment: "production" }
});`
  },
  {
    name: "github_get_workflow_run",
    category: "GitHub Actions",
    description: "Get detailed information about a specific workflow run",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      run_id: { type: "number", required: true, description: "Workflow run ID" }
    },
    returns: "Detailed workflow run information including status, conclusion, timing, and jobs",
    example: `const run = await callMCPTool("github_get_workflow_run", {
  owner: "facebook",
  repo: "react",
  run_id: 12345
});`
  },
  {
    name: "github_list_workflow_run_jobs",
    category: "GitHub Actions",
    description: "List all jobs in a workflow run",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      run_id: { type: "number", required: true, description: "Workflow run ID" },
      filter: { type: "string", required: false, description: "Filter jobs: 'latest' or 'all'" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of jobs with status, conclusion, steps, and timing",
    example: `const jobs = await callMCPTool("github_list_workflow_run_jobs", {
  owner: "facebook",
  repo: "react",
  run_id: 12345,
  filter: "latest"
});`
  },
  {
    name: "github_get_job",
    category: "GitHub Actions",
    description: "Get detailed information about a specific job",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      job_id: { type: "number", required: true, description: "Job ID" }
    },
    returns: "Detailed job information including status, conclusion, steps, and runner",
    example: `const job = await callMCPTool("github_get_job", {
  owner: "facebook",
  repo: "react",
  job_id: 67890
});`
  },
  {
    name: "github_get_job_logs",
    category: "GitHub Actions",
    description: "Get logs for a specific job",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      job_id: { type: "number", required: true, description: "Job ID" }
    },
    returns: "Job logs as plain text (may be truncated if very large)",
    example: `const logs = await callMCPTool("github_get_job_logs", {
  owner: "facebook",
  repo: "react",
  job_id: 67890
});`
  },
  {
    name: "github_rerun_workflow",
    category: "GitHub Actions",
    description: "Rerun a workflow run (re-runs all jobs)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      run_id: { type: "number", required: true, description: "Workflow run ID" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_rerun_workflow", {
  owner: "myuser",
  repo: "myrepo",
  run_id: 12345
});`
  },
  {
    name: "github_rerun_failed_jobs",
    category: "GitHub Actions",
    description: "Rerun only the failed jobs in a workflow run",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      run_id: { type: "number", required: true, description: "Workflow run ID" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_rerun_failed_jobs", {
  owner: "myuser",
  repo: "myrepo",
  run_id: 12345
});`
  },
  {
    name: "github_cancel_workflow_run",
    category: "GitHub Actions",
    description: "Cancel a workflow run (in-progress or queued)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      run_id: { type: "number", required: true, description: "Workflow run ID" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_cancel_workflow_run", {
  owner: "myuser",
  repo: "myrepo",
  run_id: 12345
});`
  },
  {
    name: "github_list_workflow_run_artifacts",
    category: "GitHub Actions",
    description: "List artifacts from a workflow run",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      run_id: { type: "number", required: true, description: "Workflow run ID" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of artifacts with names, sizes, and download URLs",
    example: `const artifacts = await callMCPTool("github_list_workflow_run_artifacts", {
  owner: "facebook",
  repo: "react",
  run_id: 12345
});`
  },
  {
    name: "github_get_artifact",
    category: "GitHub Actions",
    description: "Get details about a specific artifact",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      artifact_id: { type: "number", required: true, description: "Artifact ID" }
    },
    returns: "Artifact details including name, size, creation date, expiration, and download URL",
    example: `const artifact = await callMCPTool("github_get_artifact", {
  owner: "facebook",
  repo: "react",
  artifact_id: 12345
});`
  },
  {
    name: "github_delete_artifact",
    category: "GitHub Actions",
    description: "Delete an artifact (permanent, cannot be undone)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      artifact_id: { type: "number", required: true, description: "Artifact ID" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_delete_artifact", {
  owner: "myuser",
  repo: "myrepo",
  artifact_id: 12345
});`
  },

  // SECURITY - DEPENDABOT (4 tools)
  {
    name: "github_list_dependabot_alerts",
    category: "Security",
    description: "List Dependabot security alerts for a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      state: { type: "string", required: false, description: "Filter by state: 'open', 'dismissed', 'fixed'" },
      severity: { type: "string", required: false, description: "Filter by severity: 'low', 'medium', 'high', 'critical'" },
      ecosystem: { type: "string", required: false, description: "Filter by ecosystem (e.g., 'npm', 'pip', 'maven')" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of Dependabot alerts with vulnerability details",
    example: `const alerts = await callMCPTool("github_list_dependabot_alerts", {
  owner: "facebook",
  repo: "react",
  severity: "critical"
});`
  },
  {
    name: "github_get_dependabot_alert",
    category: "Security",
    description: "Get details about a specific Dependabot alert",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      alert_number: { type: "number", required: true, description: "Alert number" }
    },
    returns: "Detailed alert information including vulnerability details and remediation guidance",
    example: `const alert = await callMCPTool("github_get_dependabot_alert", {
  owner: "facebook",
  repo: "react",
  alert_number: 123
});`
  },
  {
    name: "github_update_dependabot_alert",
    category: "Security",
    description: "Update a Dependabot alert (dismiss or reopen)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      alert_number: { type: "number", required: true, description: "Alert number" },
      state: { type: "string", required: true, description: "New state: 'dismissed' or 'open'" },
      dismissed_reason: { type: "string", required: false, description: "Reason for dismissal: 'fix_started', 'inaccurate', 'no_bandwidth', 'not_used', 'tolerable_risk'" },
      dismissed_comment: { type: "string", required: false, description: "Optional comment when dismissing (max 280 chars)" }
    },
    returns: "Updated alert details",
    example: `const result = await callMCPTool("github_update_dependabot_alert", {
  owner: "myuser",
  repo: "myrepo",
  alert_number: 123,
  state: "dismissed",
  dismissed_reason: "false_positive"
});`
  },
  {
    name: "github_list_org_dependabot_alerts",
    category: "Security",
    description: "List Dependabot alerts across an organization",
    parameters: {
      org: { type: "string", required: true, description: "Organization name" },
      state: { type: "string", required: false, description: "Filter by state: 'open', 'dismissed', 'fixed'" },
      severity: { type: "string", required: false, description: "Filter by severity: 'low', 'medium', 'high', 'critical'" },
      ecosystem: { type: "string", required: false, description: "Filter by ecosystem" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of organization-wide Dependabot alerts",
    example: `const alerts = await callMCPTool("github_list_org_dependabot_alerts", {
  org: "myorg",
  severity: "critical"
});`
  },

  // SECURITY - CODE SCANNING (4 tools)
  {
    name: "github_list_code_scanning_alerts",
    category: "Security",
    description: "List code scanning alerts for a repository (CodeQL, ESLint, etc.)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      state: { type: "string", required: false, description: "Filter by state: 'open', 'dismissed', 'fixed'" },
      severity: { type: "string", required: false, description: "Filter by severity: 'critical', 'high', 'medium', 'low', 'warning', 'note'" },
      tool_name: { type: "string", required: false, description: "Filter by tool name (e.g., 'CodeQL', 'ESLint')" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of code scanning alerts with details",
    example: `const alerts = await callMCPTool("github_list_code_scanning_alerts", {
  owner: "facebook",
  repo: "react",
  tool_name: "CodeQL"
});`
  },
  {
    name: "github_get_code_scanning_alert",
    category: "Security",
    description: "Get details about a specific code scanning alert",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      alert_number: { type: "number", required: true, description: "Alert number" }
    },
    returns: "Detailed alert information including rule details, location, and remediation guidance",
    example: `const alert = await callMCPTool("github_get_code_scanning_alert", {
  owner: "facebook",
  repo: "react",
  alert_number: 123
});`
  },
  {
    name: "github_update_code_scanning_alert",
    category: "Security",
    description: "Update a code scanning alert (dismiss or reopen)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      alert_number: { type: "number", required: true, description: "Alert number" },
      state: { type: "string", required: true, description: "New state: 'dismissed' or 'open'" },
      dismissed_reason: { type: "string", required: false, description: "Reason for dismissal: 'false_positive', 'wont_fix', 'used_in_tests'" },
      dismissed_comment: { type: "string", required: false, description: "Optional comment when dismissing (max 280 chars)" }
    },
    returns: "Updated alert details",
    example: `const result = await callMCPTool("github_update_code_scanning_alert", {
  owner: "myuser",
  repo: "myrepo",
  alert_number: 123,
  state: "dismissed",
  dismissed_reason: "false_positive"
});`
  },
  {
    name: "github_list_code_scanning_analyses",
    category: "Security",
    description: "List code scanning analyses for a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      tool_name: { type: "string", required: false, description: "Filter by tool name" },
      ref: { type: "string", required: false, description: "Filter by branch/tag/commit" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of code scanning analyses with status, tool, and commit information",
    example: `const analyses = await callMCPTool("github_list_code_scanning_analyses", {
  owner: "facebook",
  repo: "react",
  tool_name: "CodeQL"
});`
  },

  // SECURITY - SECRET SCANNING (3 tools)
  {
    name: "github_list_secret_scanning_alerts",
    category: "Security",
    description: "List secret scanning alerts for a repository (exposed API keys, tokens, etc.)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      state: { type: "string", required: false, description: "Filter by state: 'open', 'resolved'" },
      secret_type: { type: "string", required: false, description: "Filter by secret type (e.g., 'github_personal_access_token')" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of secret scanning alerts with details",
    example: `const alerts = await callMCPTool("github_list_secret_scanning_alerts", {
  owner: "facebook",
  repo: "react",
  state: "open"
});`
  },
  {
    name: "github_get_secret_scanning_alert",
    category: "Security",
    description: "Get details about a specific secret scanning alert",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      alert_number: { type: "number", required: true, description: "Alert number" }
    },
    returns: "Detailed alert information including secret type, location, and resolution status",
    example: `const alert = await callMCPTool("github_get_secret_scanning_alert", {
  owner: "facebook",
  repo: "react",
  alert_number: 123
});`
  },
  {
    name: "github_update_secret_scanning_alert",
    category: "Security",
    description: "Update a secret scanning alert (resolve or reopen)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      alert_number: { type: "number", required: true, description: "Alert number" },
      state: { type: "string", required: true, description: "New state: 'resolved' or 'open'" },
      resolution: { type: "string", required: false, description: "Resolution: 'false_positive', 'wont_fix', 'revoked', 'used_in_tests'" }
    },
    returns: "Updated alert details",
    example: `const result = await callMCPTool("github_update_secret_scanning_alert", {
  owner: "myuser",
  repo: "myrepo",
  alert_number: 123,
      state: "resolved",
      resolution: "revoked"
});`
  },

  // SECURITY - SECURITY ADVISORIES (2 tools)
  {
    name: "github_list_repo_security_advisories",
    category: "Security",
    description: "List security advisories (GHSA) for a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      state: { type: "string", required: false, description: "Filter by state: 'triage', 'draft', 'published', 'closed'" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of security advisories with details",
    example: `const advisories = await callMCPTool("github_list_repo_security_advisories", {
  owner: "facebook",
  repo: "react",
  state: "published"
});`
  },
  {
    name: "github_get_security_advisory",
    category: "Security",
    description: "Get details about a specific security advisory (GHSA)",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      ghsa_id: { type: "string", required: true, description: "GitHub Security Advisory ID (e.g., 'GHSA-xxxx-xxxx-xxxx')" }
    },
    returns: "Detailed advisory information including description, severity, affected versions, and remediation guidance",
    example: `const advisory = await callMCPTool("github_get_security_advisory", {
  owner: "facebook",
  repo: "react",
  ghsa_id: "GHSA-xxxx-xxxx-xxxx"
});`
  },

  // PROJECTS (9 tools)
  {
    name: "github_list_repo_projects",
    category: "Projects",
    description: "List projects (classic) for a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      state: { type: "string", required: false, description: "Filter by state: 'open', 'closed', 'all' (default: 'open')" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of projects with details",
    example: `const projects = await callMCPTool("github_list_repo_projects", {
  owner: "facebook",
  repo: "react",
  state: "open"
});`
  },
  {
    name: "github_list_org_projects",
    category: "Projects",
    description: "List projects (classic) for an organization",
    parameters: {
      org: { type: "string", required: true, description: "Organization name" },
      state: { type: "string", required: false, description: "Filter by state: 'open', 'closed', 'all' (default: 'open')" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of organization projects",
    example: `const projects = await callMCPTool("github_list_org_projects", {
  org: "myorg",
  state: "open"
});`
  },
  {
    name: "github_get_project",
    category: "Projects",
    description: "Get details about a specific project",
    parameters: {
      project_id: { type: "number", required: true, description: "Project ID" }
    },
    returns: "Detailed project information including name, description, state, and metadata",
    example: `const project = await callMCPTool("github_get_project", {
  project_id: 12345
});`
  },
  {
    name: "github_create_repo_project",
    category: "Projects",
    description: "Create a new project for a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      name: { type: "string", required: true, description: "Project name" },
      body: { type: "string", required: false, description: "Project description" }
    },
    returns: "Created project details",
    example: `const project = await callMCPTool("github_create_repo_project", {
  owner: "myuser",
  repo: "myrepo",
  name: "Sprint Planning",
  body: "Project board for tracking sprint tasks"
});`
  },
  {
    name: "github_create_org_project",
    category: "Projects",
    description: "Create a new project for an organization",
    parameters: {
      org: { type: "string", required: true, description: "Organization name" },
      name: { type: "string", required: true, description: "Project name" },
      body: { type: "string", required: false, description: "Project description" }
    },
    returns: "Created project details",
    example: `const project = await callMCPTool("github_create_org_project", {
  org: "myorg",
  name: "Q1 Goals",
  body: "Organization-wide project board"
});`
  },
  {
    name: "github_update_project",
    category: "Projects",
    description: "Update a project (name, description, state)",
    parameters: {
      project_id: { type: "number", required: true, description: "Project ID" },
      name: { type: "string", required: false, description: "New project name" },
      body: { type: "string", required: false, description: "New project description" },
      state: { type: "string", required: false, description: "New state: 'open' or 'closed'" }
    },
    returns: "Updated project details",
    example: `const project = await callMCPTool("github_update_project", {
  project_id: 12345,
  name: "Updated Name",
  state: "closed"
});`
  },
  {
    name: "github_delete_project",
    category: "Projects",
    description: "Delete a project (permanent, cannot be undone)",
    parameters: {
      project_id: { type: "number", required: true, description: "Project ID" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_delete_project", {
  project_id: 12345
});`
  },
  {
    name: "github_list_project_columns",
    category: "Projects",
    description: "List columns in a project",
    parameters: {
      project_id: { type: "number", required: true, description: "Project ID" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of project columns (e.g., 'To Do', 'In Progress', 'Done')",
    example: `const columns = await callMCPTool("github_list_project_columns", {
  project_id: 12345
});`
  },
  {
    name: "github_create_project_column",
    category: "Projects",
    description: "Create a new column in a project",
    parameters: {
      project_id: { type: "number", required: true, description: "Project ID" },
      name: { type: "string", required: true, description: "Column name" }
    },
    returns: "Created column details",
    example: `const column = await callMCPTool("github_create_project_column", {
  project_id: 12345,
  name: "Review"
});`
  },

  // DISCUSSIONS (4 tools)
  {
    name: "github_list_discussions",
    category: "Discussions",
    description: "List discussions for a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      category: { type: "string", required: false, description: "Filter by category slug" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of discussions with details",
    example: `const discussions = await callMCPTool("github_list_discussions", {
  owner: "facebook",
  repo: "react",
  category: "general"
});`
  },
  {
    name: "github_get_discussion",
    category: "Discussions",
    description: "Get details about a specific discussion",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      discussion_number: { type: "number", required: true, description: "Discussion number" }
    },
    returns: "Detailed discussion information including title, body, category, author, and comments count",
    example: `const discussion = await callMCPTool("github_get_discussion", {
  owner: "facebook",
  repo: "react",
  discussion_number: 123
});`
  },
  {
    name: "github_list_discussion_categories",
    category: "Discussions",
    description: "List discussion categories for a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" }
    },
    returns: "List of discussion categories (e.g., 'General', 'Q&A', 'Ideas', 'Announcements')",
    example: `const categories = await callMCPTool("github_list_discussion_categories", {
  owner: "facebook",
  repo: "react"
});`
  },
  {
    name: "github_list_discussion_comments",
    category: "Discussions",
    description: "List comments in a discussion",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      discussion_number: { type: "number", required: true, description: "Discussion number" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of discussion comments including replies and reactions",
    example: `const comments = await callMCPTool("github_list_discussion_comments", {
  owner: "facebook",
  repo: "react",
  discussion_number: 123
});`
  },

  // NOTIFICATIONS (6 tools)
  {
    name: "github_list_notifications",
    category: "Notifications",
    description: "List notifications for the authenticated user (requires User Access Token - UAT)",
    parameters: {
      all: { type: "boolean", required: false, description: "Show all notifications (including read ones)" },
      participating: { type: "boolean", required: false, description: "Show only notifications where user is participating" },
      since: { type: "string", required: false, description: "Only show notifications updated after this time (ISO 8601)" },
      before: { type: "string", required: false, description: "Only show notifications updated before this time (ISO 8601)" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of notifications with details",
    example: `const notifications = await callMCPTool("github_list_notifications", {
  all: false,
  participating: true
});`
  },
  {
    name: "github_get_thread",
    category: "Notifications",
    description: "Get details about a notification thread (requires User Access Token - UAT)",
    parameters: {
      thread_id: { type: "string", required: true, description: "Thread ID" }
    },
    returns: "Detailed thread information including subject, reason, and repository details",
    example: `const thread = await callMCPTool("github_get_thread", {
  thread_id: "123"
});`
  },
  {
    name: "github_mark_thread_read",
    category: "Notifications",
    description: "Mark a notification thread as read (requires User Access Token - UAT)",
    parameters: {
      thread_id: { type: "string", required: true, description: "Thread ID" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_mark_thread_read", {
  thread_id: "123"
});`
  },
  {
    name: "github_mark_notifications_read",
    category: "Notifications",
    description: "Mark notifications as read (requires User Access Token - UAT)",
    parameters: {
      last_read_at: { type: "string", required: false, description: "Timestamp to mark as read up to (ISO 8601)" },
      read: { type: "boolean", required: false, description: "Mark as read (default: true)" }
    },
    returns: "Success confirmation",
    example: `const result = await callMCPTool("github_mark_notifications_read", {
  read: true
});`
  },
  {
    name: "github_get_thread_subscription",
    category: "Notifications",
    description: "Get subscription status for a notification thread (requires User Access Token - UAT)",
    parameters: {
      thread_id: { type: "string", required: true, description: "Thread ID" }
    },
    returns: "Subscription status (subscribed, ignored, reason)",
    example: `const subscription = await callMCPTool("github_get_thread_subscription", {
  thread_id: "123"
});`
  },
  {
    name: "github_set_thread_subscription",
    category: "Notifications",
    description: "Set subscription status for a notification thread (requires User Access Token - UAT)",
    parameters: {
      thread_id: { type: "string", required: true, description: "Thread ID" },
      ignored: { type: "boolean", required: false, description: "Whether to ignore the thread (default: false)" }
    },
    returns: "Updated subscription status",
    example: `const result = await callMCPTool("github_set_thread_subscription", {
  thread_id: "123",
  ignored: true
});`
  },

  // COLLABORATORS & TEAMS (3 tools)
  {
    name: "github_list_repo_collaborators",
    category: "Repository Management",
    description: "List collaborators for a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      affiliation: { type: "string", required: false, description: "Filter by affiliation: 'outside', 'direct', 'all' (default: 'all')" },
      permission: { type: "string", required: false, description: "Filter by permission: 'pull', 'push', 'admin'" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of collaborators with their permission levels",
    example: `const collaborators = await callMCPTool("github_list_repo_collaborators", {
  owner: "facebook",
  repo: "react",
  permission: "admin"
});`
  },
  {
    name: "github_check_collaborator",
    category: "Repository Management",
    description: "Check if a user is a collaborator on a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      username: { type: "string", required: true, description: "GitHub username to check" }
    },
    returns: "Collaborator status (is collaborator or not)",
    example: `const status = await callMCPTool("github_check_collaborator", {
  owner: "facebook",
  repo: "react",
  username: "octocat"
});`
  },
  {
    name: "github_list_repo_teams",
    category: "Repository Management",
    description: "List teams with access to a repository",
    parameters: {
      owner: { type: "string", required: true, description: "Repository owner" },
      repo: { type: "string", required: true, description: "Repository name" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)" },
      page: { type: "number", required: false, description: "Page number" }
    },
    returns: "List of teams with their permission levels",
    example: `const teams = await callMCPTool("github_list_repo_teams", {
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
    name: "github_get_authenticated_user",
    category: "Users",
    description: "Get the authenticated user's profile (the 'me' endpoint)",
    parameters: {},
    returns: "Authenticated user profile information including login, name, email, bio, and stats",
    example: `const me = await callMCPTool("github_get_authenticated_user", {});`
  },
  {
    name: "github_get_user_info",
    category: "Users",
    description: "Get public information about any GitHub user by username",
    parameters: {
      username: { type: "string", required: true, description: "GitHub username to look up" },
      response_format: { type: "string", required: false, description: "Response format: 'json' or 'markdown' (default: 'json')" }
    },
    returns: "User profile information including name, bio, company, location, public repos count, followers, following, and profile URL",
    example: `const user = await callMCPTool("github_get_user_info", {
  username: "torvalds"
});`
  },
  {
    name: "github_list_user_repos",
    category: "Users",
    description: "List repositories for a user or for the authenticated user",
    parameters: {
      username: { type: "string", required: false, description: "GitHub username (omit for authenticated user)" },
      type: { type: "string", required: false, description: "Repo type: 'all', 'owner', 'member' (default: 'owner')" },
      sort: { type: "string", required: false, description: "Sort field: 'created', 'updated', 'pushed', 'full_name'" },
      direction: { type: "string", required: false, description: "Sort direction: 'asc' or 'desc'" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)", example: "30" },
      page: { type: "number", required: false, description: "Page number for pagination", example: "1" }
    },
    returns: "List of repositories with names, visibility, fork status, language, stars, and URLs",
    example: `const repos = await callMCPTool("github_list_user_repos", {
  username: "octocat",
  per_page: 20
});`
  },
  {
    name: "github_list_org_repos",
    category: "Users",
    description: "List repositories for an organization",
    parameters: {
      org: { type: "string", required: true, description: "Organization name" },
      type: { type: "string", required: false, description: "Repo type: 'all', 'public', 'private', 'forks', 'sources', 'member'" },
      sort: { type: "string", required: false, description: "Sort field: 'created', 'updated', 'pushed', 'full_name'" },
      direction: { type: "string", required: false, description: "Sort direction: 'asc' or 'desc'" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)", example: "30" },
      page: { type: "number", required: false, description: "Page number for pagination", example: "1" }
    },
    returns: "List of organization repositories with names, visibility, fork status, language, stars, and URLs",
    example: `const repos = await callMCPTool("github_list_org_repos", {
  org: "github"
});`
  },
  {
    name: "github_search_users",
    category: "Users",
    description: "Search for GitHub users using the public search API",
    parameters: {
      query: { type: "string", required: true, description: "Search query (supports qualifiers like 'location:', 'language:', 'followers:>100')" },
      sort: { type: "string", required: false, description: "Sort field: 'followers', 'repositories', or 'joined'" },
      order: { type: "string", required: false, description: "Sort order: 'asc' or 'desc'" },
      per_page: { type: "number", required: false, description: "Results per page (1-100, default 30)", example: "30" },
      page: { type: "number", required: false, description: "Page number for pagination", example: "1" }
    },
    returns: "Search results including total count and matching user profiles",
    example: `const users = await callMCPTool("github_search_users", {
  query: "location:London followers:>100",
  per_page: 10
});`
  },

  // ADVANCED (1 tool)
  {
    name: "github_suggest_workflow",
    category: "Advanced",
    description: "Recommend whether to use API tools, local git, or a hybrid approach based on operation type, file size, number of edits, and file count",
    parameters: {
      operation: { type: "string", required: true, description: "Operation type (e.g., 'update_readme', 'create_release', 'multiple_file_edits')" },
      file_size: { type: "number", required: false, description: "Estimated file size in bytes" },
      num_edits: { type: "number", required: false, description: "Number of separate edit operations (default: 1)" },
      file_count: { type: "number", required: false, description: "Number of files being modified (default: 1)" },
      description: { type: "string", required: false, description: "Additional context about the task" },
      response_format: { type: "string", required: false, description: "Output format: 'json' or 'markdown' (default: 'markdown')" }
    },
    returns: "Workflow recommendation (API, local, or hybrid) with rationale and token estimates",
    example: `const suggestion = await callMCPTool("github_suggest_workflow", {
  operation: "update_readme",
  file_size: 5000,
  num_edits: 1,
  file_count: 1
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

