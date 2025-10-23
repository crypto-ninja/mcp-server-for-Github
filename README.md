# GitHub MCP Server

A comprehensive Model Context Protocol (MCP) server that enables AI assistants to seamlessly interact with GitHub repositories, issues, pull requests, and more.

## 🚀 Features

### Repository Management
- **Get Repository Info** - Fetch detailed metadata about any GitHub repository
- **List Repository Contents** - Browse files and directories in a repository
- **Get File Content** - Retrieve and display file contents from any branch or commit

### Issue Management
- **List Issues** - Browse repository issues with state filtering and pagination
- **Create Issues** - Create new issues with labels and assignees
- **Search Issues** - Find specific issues across repositories

### Pull Requests
- **List Pull Requests** - View open, closed, or all pull requests
- **PR Details** - Get comprehensive information about pull request status and changes

### Search & Discovery
- **Search Repositories** - Find repositories with advanced filters (language, stars, topics)
- **Search Code** - Locate code snippets across GitHub
- **Search Users** - Find GitHub users and organizations

### User Information
- **Get User Info** - Retrieve profile information for any GitHub user or organization

## 📋 Installation

### Prerequisites
- Python 3.10 or higher
- `pip` or `uv` package manager

### Install Dependencies

```bash
# Using pip
pip install mcp httpx pydantic --break-system-packages

# Or using uv (recommended)
uv pip install mcp httpx pydantic
```

## 🔧 Configuration

### GitHub Authentication

For public repository access, no authentication is required. For private repositories or to increase rate limits, provide a GitHub Personal Access Token:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with appropriate scopes:
   - `repo` - Full control of private repositories
   - `read:user` - Read user profile data
   - `read:org` - Read organization data
3. Use the token in tool calls via the `token` parameter

### Running the Server

#### Stdio Transport (recommended for Claude Desktop)

```bash
python github_mcp.py
```

#### With UV

```bash
uv run github_mcp.py
```

## 🛠️ Tool Reference

### github_get_repo_info

Retrieve comprehensive information about a repository.

**Parameters:**
- `owner` (str, required) - Repository owner username or organization
- `repo` (str, required) - Repository name
- `token` (str, optional) - GitHub personal access token
- `response_format` (str, optional) - Output format: "markdown" (default) or "json"

**Example:**
```json
{
  "owner": "facebook",
  "repo": "react",
  "response_format": "markdown"
}
```

### github_list_issues

List issues from a repository with filtering options.

**Parameters:**
- `owner` (str, required) - Repository owner
- `repo` (str, required) - Repository name
- `state` (str, optional) - Issue state: "open" (default), "closed", or "all"
- `limit` (int, optional) - Maximum results per page (1-100, default 20)
- `page` (int, optional) - Page number for pagination (default 1)
- `token` (str, optional) - GitHub token
- `response_format` (str, optional) - Output format

**Example:**
```json
{
  "owner": "microsoft",
  "repo": "vscode",
  "state": "open",
  "limit": 10
}
```

### github_create_issue

Create a new issue in a repository.

**Parameters:**
- `owner` (str, required) - Repository owner
- `repo` (str, required) - Repository name
- `title` (str, required) - Issue title
- `body` (str, optional) - Issue description in Markdown format
- `labels` (list[str], optional) - Label names to apply (max 20)
- `assignees` (list[str], optional) - Usernames to assign (max 10)
- `token` (str, required) - GitHub token with repo access

**Example:**
```json
{
  "owner": "myorg",
  "repo": "myproject",
  "title": "Bug: Application crashes on startup",
  "body": "## Description\n\nThe application crashes immediately after launch.\n\n## Steps to Reproduce\n1. Start the app\n2. Wait 2 seconds\n3. Crash occurs",
  "labels": ["bug", "priority-high"],
  "assignees": ["developer123"],
  "token": "ghp_your_token_here"
}
```

### github_search_repositories

Search for repositories with advanced filtering.

**Parameters:**
- `query` (str, required) - Search query with optional qualifiers
- `sort` (str, optional) - Sort field: "stars", "forks", "updated", "help-wanted-issues"
- `order` (str, optional) - Sort order: "asc" or "desc" (default)
- `limit` (int, optional) - Maximum results (1-100, default 20)
- `page` (int, optional) - Page number
- `token` (str, optional) - GitHub token
- `response_format` (str, optional) - Output format

**Query Qualifiers:**
- `language:python` - Repositories in Python
- `stars:>1000` - More than 1000 stars
- `topics:machine-learning` - Tagged with topic
- `created:>2023-01-01` - Created after date
- `fork:false` - Exclude forks
- `archived:false` - Exclude archived repos

**Example:**
```json
{
  "query": "machine learning language:python stars:>5000",
  "sort": "stars",
  "order": "desc",
  "limit": 20
}
```

### github_get_file_content

Retrieve file content from a repository.

**Parameters:**
- `owner` (str, required) - Repository owner
- `repo` (str, required) - Repository name
- `path` (str, required) - File path in repository
- `ref` (str, optional) - Branch, tag, or commit SHA (defaults to default branch)
- `token` (str, optional) - GitHub token

**Example:**
```json
{
  "owner": "torvalds",
  "repo": "linux",
  "path": "README",
  "ref": "master"
}
```

### github_list_pull_requests

List pull requests from a repository.

**Parameters:**
- `owner` (str, required) - Repository owner
- `repo` (str, required) - Repository name
- `state` (str, optional) - PR state: "open" (default), "closed", or "all"
- `limit` (int, optional) - Maximum results (1-100, default 20)
- `page` (int, optional) - Page number
- `token` (str, optional) - GitHub token
- `response_format` (str, optional) - Output format

**Example:**
```json
{
  "owner": "tensorflow",
  "repo": "tensorflow",
  "state": "open",
  "limit": 15
}
```

### github_get_user_info

Get information about a GitHub user or organization.

**Parameters:**
- `username` (str, required) - GitHub username
- `token` (str, optional) - GitHub token
- `response_format` (str, optional) - Output format

**Example:**
```json
{
  "username": "torvalds",
  "response_format": "markdown"
}
```

### github_list_repo_contents

List files and directories in a repository path.

**Parameters:**
- `owner` (str, required) - Repository owner
- `repo` (str, required) - Repository name
- `path` (str, optional) - Directory path (empty for root)
- `ref` (str, optional) - Branch, tag, or commit
- `token` (str, optional) - GitHub token
- `response_format` (str, optional) - Output format

**Example:**
```json
{
  "owner": "facebook",
  "repo": "react",
  "path": "packages",
  "ref": "main"
}
```

## 📊 Rate Limits

GitHub API has the following rate limits:

- **Unauthenticated requests:** 60 requests per hour
- **Authenticated requests:** 5,000 requests per hour
- **Search API:** 10 requests per minute (authenticated) or 10 per minute (unauthenticated)

**Recommendation:** Always use authentication tokens to avoid rate limit issues.

## 🔒 Security Best Practices

1. **Token Storage:** Never hardcode tokens in your code. Use environment variables or secure credential storage.

2. **Token Scopes:** Only grant the minimum required permissions:
   - Read-only operations: `public_repo` scope
   - Private repositories: `repo` scope
   - Creating issues: `repo` scope

3. **Token Rotation:** Regularly rotate your GitHub tokens

4. **Error Handling:** The server provides clear error messages without exposing sensitive information

## 🎯 Use Cases

### For Development Teams
- **Code Review Workflow:** List and analyze pull requests
- **Issue Tracking:** Create and search issues programmatically
- **Documentation:** Fetch README and documentation files
- **Repository Discovery:** Find relevant open-source projects

### For Project Management
- **Sprint Planning:** List open issues and PRs
- **Team Coordination:** Assign issues to team members
- **Progress Tracking:** Monitor repository activity

### For Research & Analysis
- **Repository Analysis:** Gather statistics on popular projects
- **Trend Identification:** Search for repositories by topic and technology
- **User Profiles:** Analyze developer contributions

## 🐛 Error Handling

The server provides comprehensive error handling with actionable messages:

- **404 Not Found:** Resource doesn't exist - verify repository/user/file names
- **401 Unauthorized:** Invalid or missing authentication token
- **403 Forbidden:** Insufficient permissions - check token scopes
- **422 Unprocessable Entity:** Invalid request parameters
- **429 Rate Limited:** Too many requests - wait before retrying

## 📝 Response Formats

### Markdown Format (Default)
Human-readable formatted text with:
- Headers and sections
- Emoji icons for visual clarity
- Formatted timestamps
- Clear hierarchical structure
- Preview snippets for long content

### JSON Format
Machine-readable structured data:
- Complete field information
- Nested objects and arrays
- Suitable for programmatic processing
- Pagination metadata included

## 🚦 Character Limits

The server implements a 25,000 character limit per response to prevent overwhelming results. When limits are exceeded:

- Data is automatically truncated
- Clear truncation notice is provided
- Guidance on using filters/pagination is included

## 🔄 Pagination

For endpoints returning multiple items:
- Default limit: 20 items per page
- Maximum limit: 100 items per page
- Use `page` parameter to navigate through results
- Response includes pagination metadata

## 🧪 Testing

To test the server:

```bash
# Verify Python syntax
python -m py_compile github_mcp.py

# Run with timeout for testing
timeout 5s python github_mcp.py
```

For comprehensive testing, use the MCP evaluation harness or connect to Claude Desktop.

## 📚 Additional Resources

- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

## 📜 License

This project is available under a **dual licensing model**:

### 🆓 Open Source License (AGPL v3)
Free for open source projects, personal use, and educational purposes.  
**Requirement:** You must share your source code.

### 💼 Commercial License
For commercial/proprietary use without sharing source code.  
**Pricing:** Starting at £399/year

📄 **[View Full Licensing Details](LICENSING.md)**

**Need a commercial license?** [Contact us](mailto:licensing@mcplabs.co.uk) or [open an issue](https://github.com/crypto-ninja/github-mcp-server/issues/new?title=Commercial+License+Inquiry)

---

## 🤔 Which License Do I Need?

| Your Use Case | License Needed |
|---------------|----------------|
| Open source project | AGPL v3 (Free) ✅ |
| Personal/hobby project | AGPL v3 (Free) ✅ |
| Education/research | AGPL v3 (Free) ✅ |
| Commercial SaaS product | Commercial 💼 |
| Internal business tool (proprietary) | Commercial 💼 |
| Closed-source software | Commercial 💼 |

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:
- Additional GitHub API endpoints
- Workflow automation tools
- GitHub Actions integration
- Enhanced search capabilities
- Caching layer for common requests

## ⚡ Performance Tips

1. **Use Pagination:** Request only needed items
2. **Filter Results:** Apply state and label filters
3. **Cache Responses:** Implement caching for frequently accessed data
4. **Batch Operations:** Group related requests when possible
5. **Monitor Rate Limits:** Check X-RateLimit headers in responses
