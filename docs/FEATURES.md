# 🌟 GitHub MCP Server - Feature Showcase

> **💡 AI Optimization Tip**: For AI agents, use `response_format: "compact"` to save 80-97% tokens. Examples below show `markdown` for human readability, but `compact` is recommended for programmatic use. See [Token Efficiency Guide](TOKEN_EFFICIENCY.md) for details.

## Visual Tour of Capabilities

### 🔍 Tool #1: Repository Information

**What it does**: Fetches comprehensive metadata about any GitHub repository

**Input (for human display):**
```json
{
  "owner": "facebook",
  "repo": "react",
  "response_format": "markdown"
}
```

**Input (for AI agents - recommended):**
```json
{
  "owner": "facebook",
  "repo": "react",
  "response_format": "compact"
}
```

**Output Preview:**
```markdown
# facebook/react

**Description:** The library for web and native user interfaces

## Statistics
- ⭐ Stars: 227,000
- 🍴 Forks: 46,000
- 👁️ Watchers: 6,800
- 🐛 Open Issues: 1,200

## Details
- **Owner:** facebook (Organization)
- **Created:** 2013-05-24 16:15:54 UTC
- **Last Updated:** 2024-10-23 08:30:22 UTC
- **Default Branch:** main
- **Language:** JavaScript
- **License:** MIT License
- **Topics:** react, framework, frontend, javascript, library

## URLs
- **Homepage:** https://react.dev
- **Clone URL:** https://github.com/facebook/react.git
- **Repository:** https://github.com/facebook/react
```

**Real-world use cases:**
- Research competitor projects
- Find repository statistics for reports
- Verify license compatibility
- Check project activity levels

---

### 📋 Tool #2: List Issues

**What it does**: Browse repository issues with powerful filtering

**Input:**
```json
{
  "owner": "microsoft",
  "repo": "vscode",
  "state": "open",
  "limit": 5
}
```

**Output Preview:**
```markdown
# Issues for microsoft/vscode

**State:** open | **Page:** 1 | **Showing:** 5 issues

## #12345: Editor freezes when opening large files
- **State:** open
- **Author:** @developer123
- **Created:** 2024-10-20 14:23:10 UTC
- **Labels:** `bug`, `editor`, `performance`
- **Comments:** 15
- **URL:** https://github.com/microsoft/vscode/issues/12345

**Preview:** When opening files larger than 100MB, the editor becomes 
unresponsive and requires force quit...

---

## #12344: Feature request: Add dark mode for terminals
- **State:** open
- **Author:** @userlove
- **Created:** 2024-10-19 09:15:33 UTC
- **Labels:** `feature-request`, `terminal`
- **Assignees:** @vscode-team
- **Comments:** 8
...
```

**Real-world use cases:**
- Bug tracking for your projects
- Finding issues to contribute to
- Understanding common problems
- Sprint planning with issue lists

---

### ✏️ Tool #3: Create Issue

**What it does**: Creates new issues with labels and assignees

**Input:**
```json
{
  "owner": "myorg",
  "repo": "myproject",
  "title": "Bug: Login page crashes on mobile",
  "body": "## Description\nLogin page crashes...\n\n## Steps...",
  "labels": ["bug", "mobile", "priority-high"],
  "assignees": ["developer1"],
  "token": "ghp_token"
}
```

**Output Preview:**
```markdown
✅ Issue Created Successfully!

**Issue:** #456 - Bug: Login page crashes on mobile
**State:** open
**URL:** https://github.com/myorg/myproject/issues/456
**Created:** 2024-10-23 09:10:15 UTC
**Author:** @you
**Labels:** `bug`, `mobile`, `priority-high`
**Assignees:** @developer1
```

**Real-world use cases:**
- Automated bug reporting from logs
- Creating issues from customer feedback
- Sprint planning automation
- Task assignment workflows

---

### 🔎 Tool #4: Search Repositories

**What it does**: Advanced repository search with multiple criteria

**Input:**
```json
{
  "query": "machine learning language:python stars:>5000",
  "sort": "stars",
  "order": "desc",
  "limit": 3
}
```

**Output Preview:**
```markdown
# Repository Search Results

**Query:** machine learning language:python stars:>5000
**Total Results:** 1,243
**Showing:** 3 repositories (Page 1)

## tensorflow/tensorflow
An Open Source Machine Learning Framework for Everyone

- ⭐ Stars: 185,000
- 🍴 Forks: 74,000
- Language: Python
- Updated: 2024-10-23 05:30:11 UTC
- URL: https://github.com/tensorflow/tensorflow
- Topics: `machine-learning`, `deep-learning`, `python`, `tensorflow`

---

## pytorch/pytorch
Tensors and Dynamic neural networks in Python

- ⭐ Stars: 82,000
- 🍴 Forks: 22,000
- Language: Python
...
```

**Query Qualifiers Examples:**
- `language:python` - Python repositories
- `stars:>1000` - More than 1000 stars
- `topics:web` - Tagged with 'web' topic
- `created:>2024-01-01` - Created this year
- `fork:false` - Exclude forks
- `archived:false` - Exclude archived

**Real-world use cases:**
- Technology research
- Finding libraries and tools
- Competitive analysis
- Learning resources discovery

---

### 📄 Tool #5: Get File Content

**What it does**: Retrieves file contents from any branch or commit

**Input:**
```json
{
  "owner": "torvalds",
  "repo": "linux",
  "path": "README",
  "ref": "master"
}
```

**Output Preview:**
```markdown
# File: README

**Path:** README
**Size:** 1,234 bytes
**Type:** file
**Encoding:** base64
**SHA:** abc123def456...
**URL:** https://github.com/torvalds/linux/blob/master/README

---

**Content:**

```
Linux kernel
============

This is the Linux kernel source code...
```
```

**Real-world use cases:**
- Code review and analysis
- Documentation retrieval
- Configuration file inspection
- Script extraction for automation

---

### 🔀 Tool #6: List Pull Requests

**What it does**: Browse repository pull requests with status info

**Input:**
```json
{
  "owner": "facebook",
  "repo": "react",
  "state": "open",
  "limit": 3
}
```

**Output Preview:**
```markdown
# Pull Requests for facebook/react

**State:** open | **Page:** 1 | **Showing:** 3 PRs

## #2345: Fix: Memory leak in useEffect hook
- **State:** open
- **Author:** @contributor
- **Created:** 2024-10-22 11:20:45 UTC
- **Branch:** fix-memory-leak → main
- **Labels:** `bug`, `performance`
- **Comments:** 12
- **URL:** https://github.com/facebook/react/pull/2345

**Description:** This PR fixes a memory leak that occurs when...

---
```

**Real-world use cases:**
- Code review workflows
- Contribution tracking
- Release planning
- Team coordination

---

### 👤 Tool #7: Get User Information

**What it does**: Retrieves detailed user or organization profiles

**Input:**
```json
{
  "username": "torvalds",
  "response_format": "markdown"
}
```

**Output Preview:**
```markdown
# Linus Torvalds
**@torvalds** (User)

## Profile
- **Location:** Portland, OR
- **Email:** torvalds@linux-foundation.org
- **Website:** https://github.com/torvalds

## Statistics
- Public Repos: 6
- Public Gists: 0
- Followers: 250,000
- Following: 0

## Activity
- **Account Created:** 2011-09-03 15:26:22 UTC
- **Last Updated:** 2024-10-20 18:45:33 UTC

**Profile URL:** https://github.com/torvalds
```

**Real-world use cases:**
- Developer research
- Team member verification
- Contribution analysis
- Network mapping

---

### 📁 Tool #8: List Repository Contents

**What it does**: Browse directory structure and file listings

**Input:**
```json
{
  "owner": "facebook",
  "repo": "react",
  "path": "packages",
  "ref": "main"
}
```

**Output Preview:**
```markdown
# Contents of /packages
**Repository:** facebook/react
**Ref:** main

**Items:** 15

## 📁 Directories
- `react/`
- `react-dom/`
- `react-reconciler/`
- `scheduler/`
- `shared/`

## 📄 Files
- `package.json` (2.3 KB)
- `README.md` (1.8 KB)
```

**Real-world use cases:**
- Codebase exploration
- Project structure analysis
- Finding specific files
- Repository navigation

---

## 🎯 Advanced Usage Scenarios

### Scenario 1: Technology Stack Analysis
```
Claude Conversation:
User: "I want to build a web scraping tool. Find me the top 3 Python 
web scraping libraries on GitHub and compare their features."

Claude uses:
1. github_search_repositories (query: "web scraping language:python")
2. github_get_repo_info (for each top result)
3. github_get_file_content (to read README files)

Result: Comprehensive comparison with stars, features, and use cases
```

### Scenario 2: Bug Investigation Workflow
```
User: "Help me understand the performance issues in the React 
repository. Find related open issues."

Claude uses:
1. github_list_issues (owner: "facebook", repo: "react", state: "open")
2. Filters for issues with "performance" label
3. github_get_repo_info (to understand project context)

Result: List of performance-related issues with analysis
```

### Scenario 3: Developer Research
```
User: "Who are the most active contributors to the Linux kernel?"

Claude uses:
1. github_get_repo_info (owner: "torvalds", repo: "linux")
2. github_list_pull_requests (to see recent contributions)
3. github_get_user_info (for top contributors)

Result: Profile analysis of key contributors
```

### Scenario 4: Project Setup
```
User: "I need to set up a React Native project. Show me the 
official setup instructions."

Claude uses:
1. github_search_repositories (query: "react-native")
2. github_get_repo_info (owner: "facebook", repo: "react-native")
3. github_get_file_content (path: "README.md")

Result: Step-by-step setup guide extracted from official docs
```

---

## 🎨 Response Format Comparison

### Markdown Format (Default)
**Best for**: Human reading, presentations, documentation

**Characteristics:**
- 📊 Visual formatting with emoji and headers
- 🕐 Human-readable timestamps
- 📝 Clear hierarchical structure
- ✂️ Preview snippets for long content
- 🎯 Focused on key information

### JSON Format
**Best for**: Programmatic processing, data extraction

**Characteristics:**
- 🔧 Complete field information
- 📦 Nested objects and arrays
- 🤖 Machine-parseable structure
- 📊 All metadata included
- 🔄 Suitable for further processing

**Example Request:**
```json
{
  "response_format": "json"
}
```

---

## 💡 Power User Tips

### Tip 1: Chain Multiple Queries
```
"Find Python machine learning repos with >10k stars, then get the 
README from the top result and summarize the key features"
```
Claude will automatically use multiple tools in sequence.

### Tip 2: Use Advanced Search Syntax
```
query: "language:rust stars:>5000 created:>2023-01-01 fork:false"
```
Combine multiple criteria for precise results.

### Tip 3: Paginate Through Large Results
```
page: 1  # First 20 results
page: 2  # Next 20 results
page: 3  # And so on...
```

### Tip 4: Monitor Specific Repositories
```
"Create a daily summary of issues created in tensorflow/tensorflow 
in the last 24 hours"
```

### Tip 5: Research Workflows
```
"Compare the three most popular JavaScript frameworks on GitHub 
by stars, activity, and community size"
```

---

## 🚀 Integration Examples

### With Project Management
```python
# Automated issue creation from bug reports
create_issue(
    title=f"Bug Report: {error_type}",
    body=f"Error: {error_message}\n\nStack trace:\n{stack_trace}",
    labels=["bug", "automated"],
    assignees=["on-call-developer"]
)
```

### With CI/CD Pipelines
```python
# Check PR status before deployment
prs = list_pull_requests(
    owner="myorg",
    repo="myproject",
    state="open"
)
# Block deployment if critical PRs are open
```

### With Analytics
```python
# Track repository growth
repo_info = get_repo_info(
    owner="myorg",
    repo="myproject"
)
# Log stars, forks, issues to analytics platform
```

---

## 📊 Performance Metrics

| Tool | Avg Response Time | Rate Limit Cost |
|------|-------------------|-----------------|
| get_repo_info | ~200ms | 1 request |
| list_issues | ~300ms | 1 request |
| search_repositories | ~400ms | 1 search request |
| create_issue | ~300ms | 1 request |
| get_file_content | ~250ms | 1 request |
| list_pull_requests | ~300ms | 1 request |
| get_user_info | ~200ms | 1 request |
| list_repo_contents | ~250ms | 1 request |

**Rate Limits:**
- **Without Token**: 60 requests/hour
- **With Token**: 5,000 requests/hour
- **Search API**: 10 requests/minute

---

## 🎓 Learning Resources

Want to get the most out of this MCP server?

1. **Start with basics**: Try each tool individually
2. **Combine tools**: Let Claude chain multiple operations
3. **Use filters**: Leverage GitHub's query syntax
4. **Check docs**: Read the README for detailed info
5. **Experiment**: Try different queries and see what works

---

## 🏆 What Makes This Server Special

✨ **8 Comprehensive Tools** - Complete GitHub workflow coverage
🛡️ **Production-Ready** - Error handling, pagination, limits
📚 **Well-Documented** - Every tool fully explained
🎯 **Type-Safe** - Pydantic validation prevents errors
⚡ **High-Performance** - Async operations throughout
🔒 **Secure** - Optional auth, no hardcoded credentials
🎨 **Flexible** - JSON or Markdown output formats
🧪 **Tested** - 10 evaluation scenarios included

**This is not just a simple API wrapper - it's a thoughtfully designed, 
production-grade MCP server that makes GitHub accessible to AI!** 🚀
