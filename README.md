# GitHub MCP Server

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Tools](https://img.shields.io/badge/Tools-16-brightgreen.svg)](#-available-tools)

> **The most comprehensive GitHub MCP server** - Full GitHub workflow automation with Actions monitoring, advanced PR management, and intelligent code search. Built for AI-powered development teams.

👉 New here? Start with the quick guide: [START_HERE.md](START_HERE.md)

## ✨ What's New in Phase 1

🎉 **Major Update:** We've expanded from 8 to **14 powerful tools**, adding:

- **🔄 GitHub Actions Integration** - Monitor CI/CD workflows and runs
- **🔀 Enhanced PR Management** - Create PRs with reviews and detailed analysis  
- **🔍 Advanced Search** - Search code and issues across all of GitHub

[View Full Changelog](CHANGELOG.md)

---

## 🚀 Features Overview

### 📦 Repository Management (3 tools)
Complete repository exploration and file access capabilities.

- **Repository Info** - Comprehensive metadata, statistics, and configuration
- **Browse Contents** - Navigate directory structures and file trees
- **File Access** - Retrieve file contents from any branch or commit

### 🐛 Issue Management (3 tools)
Full issue lifecycle from creation to advanced search.

- **List Issues** - Browse with state filtering and pagination
- **Create Issues** - Open issues with labels and assignees
- **🆕 Search Issues** - Advanced search across repositories with filters

### 🔀 Pull Request Operations (3 tools)
Complete PR workflow from creation to detailed analysis.

- **List PRs** - View all pull requests with state filtering
- **🆕 Create PRs** - Open pull requests with draft support
- **🆕 PR Details** - Comprehensive analysis with reviews, commits, and files

### ⚡ GitHub Actions (2 tools)
Monitor and manage your CI/CD pipelines.

- **🆕 List Workflows** - View all GitHub Actions workflows
- **🆕 Workflow Runs** - Track execution status and results

### 📦 Release Management (2 tools)
Track and verify repository releases.

- **🆕 List Releases** - View all releases with stats
- **🆕 Get Release** - Detailed release information

### 🔍 Search & Discovery (2 tools)
Powerful search across GitHub's entire ecosystem.

- **Search Repositories** - Find repos with advanced filters
- **🆕 Search Code** - Locate code snippets across GitHub

### 👤 User Information (1 tool)
Profile and organization data retrieval.

- **User Profiles** - Get detailed user and org information

---

## 📋 Quick Start

### Prerequisites
- Python 3.10 or higher
- GitHub Personal Access Token (optional, but recommended)

### Installation

```bash
# Using pip
pip install mcp httpx pydantic --break-system-packages

# Or using uv (recommended)
uv pip install mcp httpx pydantic
```

### Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["/path/to/github_mcp.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

### Authentication

Generate a GitHub Personal Access Token:

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Generate a new token with these scopes:
   - `repo` - Full control of private repositories
   - `read:user` - Read user profile data
   - `read:org` - Read organization data
   - `workflow` - Update GitHub Action workflows (for Actions tools)
3. Use the token in your configuration

---

## 🛠️ Available Tools

### Repository Tools

#### `github_get_repo_info`
Retrieve comprehensive repository information including statistics, configuration, and metadata.

**Parameters:**
```json
{
  "owner": "facebook",
  "repo": "react",
  "token": "ghp_optional",
  "response_format": "markdown"
}
```

**Returns:** Stars, forks, issues, license, topics, creation date, and more.

---

#### `github_list_repo_contents`
Browse files and directories in a repository, with support for specific branches or commits.

**Parameters:**
```json
{
  "owner": "microsoft",
  "repo": "vscode",
  "path": "src",
  "ref": "main"
}
```

**Returns:** Directory listing with file sizes and types.

---

#### `github_get_file_content`
Retrieve the complete contents of any file in a repository.

**Parameters:**
```json
{
  "owner": "torvalds",
  "repo": "linux",
  "path": "README",
  "ref": "master"
}
```

**Returns:** File content with metadata (size, encoding, SHA).

---

### Issue Management

#### `github_list_issues`
List repository issues with flexible state filtering and pagination.

**Parameters:**
```json
{
  "owner": "tensorflow",
  "repo": "tensorflow",
  "state": "open",
  "limit": 30,
  "page": 1
}
```

**Returns:** Issue list with titles, labels, assignees, and status.

---

#### `github_create_issue`
Create new issues with markdown descriptions, labels, and assignees.

**Parameters:**
```json
{
  "owner": "myorg",
  "repo": "myproject",
  "title": "Bug: Application crashes on startup",
  "body": "## Description\n\nDetailed bug report...",
  "labels": ["bug", "priority-high"],
  "assignees": ["developer123"],
  "token": "ghp_required"
}
```

**Returns:** Created issue details with number and URL.

---

#### `github_search_issues` 🆕
Advanced issue search across GitHub with powerful filtering options.

**Parameters:**
```json
{
  "query": "is:open label:bug language:python",
  "sort": "created",
  "order": "desc",
  "limit": 50
}
```

**Query Qualifiers:**
- `is:open` / `is:closed` - Filter by state
- `label:bug` - Filter by labels
- `author:username` - Filter by author
- `assignee:username` - Filter by assignee
- `repo:owner/name` - Filter by repository
- `created:>2024-01-01` - Filter by date

**Returns:** Matching issues with full metadata.

---

### Pull Request Operations

#### `github_list_pull_requests`
List pull requests with state filtering and pagination support.

**Parameters:**
```json
{
  "owner": "facebook",
  "repo": "react",
  "state": "open",
  "limit": 20
}
```

**Returns:** PR list with titles, authors, branches, and status.

---

#### `github_create_pull_request` 🆕
Create pull requests with full control over branches, reviewers, and settings.

**Parameters:**
```json
{
  "owner": "myorg",
  "repo": "myproject",
  "title": "Add new feature",
  "head": "feature-branch",
  "base": "main",
  "body": "## Changes\n\n- Added feature X\n- Fixed bug Y",
  "draft": false,
  "maintainer_can_modify": true,
  "token": "ghp_required"
}
```

**Features:**
- ✅ Draft PR support
- ✅ Maintainer modification permissions
- ✅ Markdown descriptions
- ✅ Branch validation

**Returns:** Created PR details with number and URL.

---

#### `github_get_pr_details` 🆕
Get comprehensive pull request information including reviews, commits, and file changes.

**Parameters:**
```json
{
  "owner": "facebook",
  "repo": "react",
  "pull_number": 123,
  "include_reviews": true,
  "include_commits": true,
  "include_files": false
}
```

**Returns:**
- 📝 Full PR description and metadata
- ✅ Review status (approved, changes requested, commented)
- 💬 Review comments and feedback
- 📊 Commit history with authors
- 📁 Changed files summary (optional)
- 🔀 Merge status and conflicts
- 🎯 Mergeable state

**Perfect for:** AI-assisted code review, PR analysis, and workflow automation.

---

### GitHub Actions

#### `github_list_workflows` 🆕
List all GitHub Actions workflows configured in a repository.

**Parameters:**
```json
{
  "owner": "microsoft",
  "repo": "typescript",
  "token": "ghp_optional"
}
```

**Returns:** 
- Workflow names and IDs
- Configuration file paths
- Current state and badges
- Creation and update timestamps

---

#### `github_get_workflow_runs` 🆕
Monitor workflow execution history with advanced filtering.

**Parameters:**
```json
{
  "owner": "vercel",
  "repo": "next.js",
  "workflow_id": "ci.yml",
  "status": "completed",
  "conclusion": "success",
  "limit": 30
}
```

**Status Filters:**
- `queued` - Waiting to start
- `in_progress` - Currently running
- `completed` - Finished execution

**Conclusion Filters:**
- `success` ✅ - Passed successfully
- `failure` ❌ - Failed with errors
- `cancelled` - Manually cancelled
- `timed_out` - Exceeded time limit

**Returns:**
- 🔄 Run status with visual indicators
- 📊 Execution timing and duration
- 👤 Triggered by user
- 🌿 Branch and commit info
- 🔗 Direct links to runs

**Perfect for:** CI/CD monitoring, build status checks, deployment tracking.

---

### Release Management

#### `github_list_releases` 🆕
List all releases from a repository with pagination support.

**Parameters:**
```json
{
  "owner": "facebook",
  "repo": "react",
  "limit": 10
}
```

**Returns:**
- Release tags and titles
- Publication dates
- Author information
- Asset counts and downloads

---

#### `github_get_release` 🆕
Get detailed information about a specific release or the latest release.

**Parameters:**
```json
{
  "owner": "microsoft",
  "repo": "vscode",
  "tag": "latest"
}
```

**Features:**
- Use `"tag": "latest"` for most recent
- Use a specific tag (e.g., `"v1.2.3"`)
- Full release notes and asset details

---

### Search & Discovery

#### `github_search_repositories`
Search for repositories across GitHub with advanced filtering.

**Parameters:**
```json
{
  "query": "machine learning language:python stars:>5000",
  "sort": "stars",
  "order": "desc",
  "limit": 50
}
```

**Query Qualifiers:**
- `language:python` - Filter by language
- `stars:>1000` - Star count
- `forks:>50` - Fork count
- `topics:machine-learning` - Topics
- `created:>2023-01-01` - Creation date
- `archived:false` - Exclude archived

**Returns:** Repository list with statistics and metadata.

---

#### `github_search_code` 🆕
Search for code snippets across all of GitHub with powerful filters.

**Parameters:**
```json
{
  "query": "TODO language:python repo:org/repo",
  "sort": "indexed",
  "order": "desc",
  "limit": 100
}
```

**Query Qualifiers:**
- `language:python` - Filter by language
- `repo:owner/name` - Specific repository
- `path:src/` - File path
- `extension:py` - File extension
- `size:>1000` - File size
- `filename:test` - Filename

**Returns:**
- 📝 Code snippets with context
- 📁 File locations and paths
- 🔗 Direct links to code
- ⭐ Repository information

**Perfect for:** Finding code examples, locating TODOs, discovering patterns.

---

### User Information

#### `github_get_user_info`
Retrieve detailed information about GitHub users and organizations.

**Parameters:**
```json
{
  "username": "torvalds",
  "response_format": "markdown"
}
```

**Returns:**
- Profile information (bio, location, company)
- Statistics (repos, followers, following)
- Activity data
- Social links

---

## 🎯 Use Cases

### 🚀 For AI-Powered Development

**Automated Code Review:**
```
1. Monitor PR with github_get_pr_details
2. Check CI status with github_get_workflow_runs
3. Analyze changes and provide feedback
4. Track review comments automatically
```

**Intelligent Issue Triage:**
```
1. Search for similar issues with github_search_issues
2. Analyze patterns across repositories
3. Auto-assign based on expertise
4. Track issue resolution
```

**Repository Intelligence:**
```
1. Discover code patterns with github_search_code
2. Find best practices across projects
3. Locate security patterns
4. Track dependency usage
```

### 💼 For Development Teams

**CI/CD Monitoring:**
- Monitor workflow runs across all repos
- Track deployment success rates
- Get instant failure notifications
- Analyze build performance

**PR Workflow Automation:**
- Create PRs from feature branches
- Auto-assign reviewers
- Track review status
- Monitor merge conflicts

**Issue Management:**
- Create issues from AI analysis
- Search across all team repos
- Track label patterns
- Monitor issue velocity

### 📊 For Project Management

**Sprint Planning:**
- List all open issues and PRs
- Track team assignments
- Monitor completion rates
- Analyze workflow efficiency

**Release Management:**
- Track PR merge status
- Monitor CI/CD pipelines
- Validate release readiness
- Generate release notes

---

## 📊 Rate Limits

GitHub API rate limits (per hour):

| Type | Unauthenticated | Authenticated |
|------|----------------|---------------|
| Core API | 60 | 5,000 |
| Search API | 10 | 30 |
| Actions API | 0 | 1,000 |

**💡 Pro Tip:** Always use authentication to avoid rate limit issues!

---

## 🔒 Security Best Practices

### Token Management
1. **Never hardcode tokens** - Use environment variables
2. **Use minimal scopes** - Only grant necessary permissions
3. **Rotate regularly** - Change tokens every 90 days
4. **Separate tokens** - Different tokens for different purposes

### Permission Scopes

**Read-Only Operations:**
- `public_repo` - For public repositories only
- `read:user` - User profile access
- `read:org` - Organization data

**Write Operations:**
- `repo` - Full repository access (for creating issues/PRs)
- `workflow` - GitHub Actions management

**Enterprise:**
- `admin:org` - Organization administration
- `admin:repo_hook` - Webhook management

---

## 🐛 Error Handling

Comprehensive error messages with actionable guidance:

- **404 Not Found** - Resource doesn't exist (check owner/repo/file names)
- **401 Unauthorized** - Invalid or missing token
- **403 Forbidden** - Insufficient permissions (check token scopes)
- **422 Unprocessable** - Invalid request parameters
- **429 Rate Limited** - Too many requests (wait before retrying)

All errors include suggestions for resolution!

---

## 📝 Response Formats

### Markdown (Default)
Human-readable formatted output with:
- 📊 Clear hierarchical structure
- 🎨 Visual indicators and emojis
- 📅 Formatted timestamps
- 🔗 Direct links
- 📝 Code snippets

### JSON
Machine-readable structured data:
- Complete field information
- Nested objects and arrays
- Perfect for programmatic processing
- Includes pagination metadata

**Toggle format:**
```json
{
  "response_format": "json"  // or "markdown"
}
```

---

## ⚡ Performance Tips

1. **Use Pagination** - Request only what you need (default: 20 items)
2. **Filter Results** - Use state, label, and date filters
3. **Cache Responses** - Store frequently accessed data locally
4. **Batch Operations** - Group related requests
5. **Monitor Rate Limits** - Check `X-RateLimit-*` headers
6. **Authenticate Always** - 5,000 vs 60 requests/hour
7. **Optional Includes** - Skip heavy data (like file diffs) when not needed

---

## 🚦 Response Limits

- **Character Limit:** 25,000 per response
- **Auto-truncation:** Includes clear notices
- **Pagination Guidance:** Suggestions for filtering

When limits are exceeded, the server provides:
- Truncation indicators
- Pagination recommendations
- Filter suggestions

---

## 🧪 Testing

### Validate Installation
```bash
# Check Python syntax
python -m py_compile github_mcp.py

# Test with timeout
timeout 5s python github_mcp.py
```

### Claude Desktop Testing
1. Add server to configuration
2. Restart Claude Desktop
3. Ask Claude: "List workflows in facebook/react"
4. Verify tools appear in Claude's interface

---

## 📚 Documentation

- **[GitHub REST API](https://docs.github.com/en/rest)** - Official API documentation
- **[Model Context Protocol](https://modelcontextprotocol.io)** - MCP specification
- **[Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)** - Token creation guide
- **[GitHub Actions](https://docs.github.com/en/actions)** - Actions documentation

---

## 📜 License

### Dual Licensing Model

#### 🆓 Open Source (AGPL v3)
**Perfect for:**
- ✅ Open source projects
- ✅ Personal use
- ✅ Educational purposes
- ✅ Non-commercial use

**Requirement:** Share your source code

#### 💼 Commercial License
**Perfect for:**
- ✅ Commercial applications
- ✅ Proprietary software
- ✅ SaaS products
- ✅ Internal business tools

**Pricing:** Starting at £399/year

📄 **[View Full Licensing Details](LICENSING.md)**

### License Comparison

| Feature | AGPL v3 | Commercial |
|---------|---------|------------|
| Price | Free | £399+/year |
| Source Sharing | Required | Not Required |
| Commercial Use | ✅ (with source) | ✅ |
| Proprietary Use | ❌ | ✅ |
| Support | Community | Priority |
| SLA | ❌ | ✅ (Enterprise) |

### Contact

**Need a commercial license?**
- 📧 Email: [licensing@mcplabs.co.uk](mailto:licensing@mcplabs.co.uk)
- 🐛 GitHub: [Open an issue](https://github.com/crypto-ninja/github-mcp-server/issues/new?title=Commercial+License+Inquiry)
- 🌐 Website: [mcplabs.co.uk](https://mcplabs.co.uk) (coming soon)

---

## 🤝 Contributing

We welcome contributions! Key areas:

### High Priority
- **Phase 2 Features:** Release management, branch operations
- **Performance:** Caching layer implementation
- **Documentation:** Additional examples and use cases
- **Testing:** Comprehensive test suite

### Medium Priority
- **Error Recovery:** Retry logic and resilience
- **Logging:** Enhanced debugging capabilities
- **Monitoring:** Usage analytics and metrics

### Future Features
- **Webhook Management** (Enterprise)
- **Repository Creation** (Enterprise)
- **Advanced Analytics**

**See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.**

---

## 🎉 What's Next?

### Phase 2 (Coming Soon)
- **Release Management** - List releases, get latest release
- **Collaboration Tools** - Contributors, collaborators, permissions
- **Branch Management** - List branches, create branches, protection status

### Phase 3 (Future)
- **Webhook Management** - Create and manage webhooks (Enterprise)
- **Repository Management** - Create repos, fork repos (Enterprise)
- **Advanced Analytics** - Custom metrics and insights (Enterprise)

---

## 🗺️ Phase 2 Development Roadmap

We're actively building Phase 2 features through dogfooding — using our own product reveals what's missing!

### Phase 2.1: File Management Tools 🔨

**Status:** Planning → [Issue #2](https://github.com/crypto-ninja/github-mcp-server/issues/2)

**Tools to Add:**
- `github_delete_file` — Delete files from repositories
- `github_create_file` — Create new files with content
- `github_update_file` — Modify existing file contents
- `github_commit_changes` — Batch commits with custom messages

**Why:** Discovered while cleaning up our own repository — we could read files but not modify them!

**Timeline:** Q4 2025

### Phase 2.2: Repository Management Tools 🏗️

**Status:** Planning → [Issue #3](https://github.com/crypto-ninja/github-mcp-server/issues/3)

**Tools to Add:**
- `github_create_repository` — Create new repos (personal & org)
- `github_delete_repository` — Delete repos (with safety checks)
- `github_update_repository` — Modify repo settings
- `github_transfer_repository` — Transfer ownership
- `github_archive_repository` — Archive/unarchive repos

**Why:** While reviewing workflows, we realized we can do everything TO a repo except CREATE it!

**Timeline:** Q4 2025

### Phase 3: Enterprise Features 🏢

**Status:** Future Planning

- Webhook management
- Collaborator management
- Team permissions
- Advanced analytics
- Organization administration

**Timeline:** 2026

### 🐕🍖 The Dogfooding Process

Each feature comes from actually using the tool:

1. Use the product on our own repo
2. Hit a limitation — "Wait, I can't do X?"
3. Create an issue — using the tool itself!
4. Build the feature — fill the gap
5. Ship and repeat ✨

Want to contribute? Check out the Phase 2 issues and share your use cases!

---

## 💬 Support

- **📖 Documentation:** You're reading it!
- **🐛 Bug Reports:** [GitHub Issues](https://github.com/crypto-ninja/github-mcp-server/issues)
- **💡 Feature Requests:** [GitHub Discussions](https://github.com/crypto-ninja/github-mcp-server/discussions)
- **📧 Email:** [licensing@mcplabs.co.uk](mailto:licensing@mcplabs.co.uk)

---

## ⭐ Star History

If you find this project useful, please star it on GitHub! ⭐

---

**Built with ❤️ by [MCP Labs](https://mcplabs.co.uk)**

*Empowering AI-driven development workflows*