# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-24

### 🎉 Phase 1 Complete - Major Feature Release

This release adds **6 powerful new tools**, expanding from 8 to 14 total tools and positioning this as the most comprehensive GitHub MCP server available.

### ✨ Added

#### GitHub Actions Integration (Phase 1.1)
- **`github_list_workflows`** - List all GitHub Actions workflows in a repository
  - View workflow configurations and status
  - Get workflow IDs for monitoring
  - See creation and update timestamps
  
- **`github_get_workflow_runs`** - Monitor workflow execution history
  - Filter by status (queued, in_progress, completed)
  - Filter by conclusion (success, failure, cancelled, etc.)
  - Visual status indicators with emojis
  - Detailed timing and execution info
  - Perfect for CI/CD monitoring and debugging

#### Enhanced PR Management (Phase 1.2)
- **`github_create_pull_request`** - Create pull requests programmatically
  - Full branch control (head → base)
  - Draft PR support
  - Maintainer modification permissions
  - Markdown description support
  - Branch validation
  
- **`github_get_pr_details`** - Comprehensive PR analysis
  - Full PR metadata and description
  - Review status (approved, changes requested, commented)
  - Review comments and feedback
  - Commit history with authors
  - Changed files summary (optional)
  - Merge status and conflict detection
  - Perfect for AI-assisted code review

#### Advanced Search Capabilities (Phase 1.3)
- **`github_search_issues`** - Advanced issue search across GitHub
  - Search by labels, state, author, assignee
  - Repository filtering
  - Date range support
  - Comment count filtering
  - Rich query syntax support
  
- **`github_search_code`** - Search code across all of GitHub
  - Language filtering
  - Repository targeting
  - File path and extension filtering
  - Code snippet results with context
  - Perfect for finding examples and patterns

### 🎯 Enhanced

- **Enum Classes** - Added comprehensive enum coverage:
  - `WorkflowRunStatus` - All workflow execution states
  - `WorkflowRunConclusion` - All possible run outcomes
  - `PRMergeMethod` - Merge, squash, rebase options
  - `PRReviewState` - All review states

- **Input Models** - New Pydantic models with validation:
  - `ListWorkflowsInput`
  - `GetWorkflowRunsInput`
  - `CreatePullRequestInput`
  - `GetPullRequestDetailsInput`
  - `SearchIssuesInput`
  - `SearchCodeInput`

- **Feature List** - Updated header documentation to reflect new capabilities

### 📊 Statistics

- **New Tools:** 6 (+75% from v1.0)
- **Total Tools:** 14
- **Lines of Code:** +833 lines across Phase 1
- **Enums:** +4 new type-safe enums
- **Input Models:** +6 new validated models

### 🚀 Impact

**Workflow Coverage:**
- ✅ Complete PR lifecycle (list → create → analyze)
- ✅ Full CI/CD monitoring (workflows → runs → status)
- ✅ Advanced search (code + issues)
- ✅ Issue management (list → create → search)

**Commercial Value:**
- Major differentiator in GitHub MCP space
- Enables AI-powered development workflows
- Full automation capabilities
- Enterprise-ready features

### 🔧 Technical Details

**Phase 1.1 (Actions):** 236 lines
- GitHub Actions API integration
- Workflow listing and monitoring
- Run status tracking with visual indicators

**Phase 1.2 (PRs):** 321 lines  
- PR creation with draft support
- Comprehensive PR details with reviews
- Commit history and file changes
- Merge status and conflict detection

**Phase 1.3 (Search):** 276 lines
- Advanced code search across GitHub
- Issue search with rich filtering
- Query syntax support
- Pagination for large result sets

### 🐛 Bug Fixes

- Fixed copyright header (now consistently MCP Labs)
- Updated feature documentation in file headers
- Improved error handling for new endpoints

### 📚 Documentation

- Complete README overhaul showcasing Phase 1
- Added comprehensive tool documentation
- New use case examples
- Performance tips and best practices
- Enhanced licensing information

### ⬆️ Dependencies

No new dependencies required - still just:
- `mcp>=1.0.0`
- `httpx>=0.25.0`
- `pydantic>=2.0.0`

### 🙏 Acknowledgments

Special thanks to the MCP community for feedback and support during Phase 1 development!

[1.1.0]: https://github.com/crypto-ninja/github-mcp-server/releases/tag/v1.1.0

## [1.0.0] - 2025-10-23

### Added
- Initial release of GitHub MCP Server
- 8 comprehensive tools for GitHub integration:
  - `github_get_repo_info` - Fetch repository information
  - `github_list_issues` - List repository issues
  - `github_create_issue` - Create new issues
  - `github_search_repositories` - Advanced repository search
  - `github_get_file_content` - Retrieve file contents
  - `github_list_pull_requests` - List pull requests
  - `github_get_user_info` - Get user/organization info
  - `github_list_repo_contents` - Browse repository contents
- Full Pydantic v2 input validation
- Dual response formats (JSON and Markdown)
- Comprehensive error handling with actionable messages
- Smart pagination support
- 25,000 character limit with intelligent truncation
- Tool annotations for MCP clients
- Optional GitHub token authentication
- Rate limit management
- Async/await throughout for performance
- Extensive documentation (70KB+):
  - Complete README
  - Quick Start Guide
  - Configuration Guide
  - Feature Showcase
  - Architecture Documentation
  - Project Summary
- 10 evaluation test scenarios
- Example configurations
- Contributing guidelines
- MIT License

### Features
- Production-ready code quality
- 100% type hint coverage
- Enterprise-grade error handling
- Security best practices
- Comprehensive docstrings
- DRY principle throughout
- Clean code architecture

[1.0.0]: https://github.com/yourusername/github-mcp-server/releases/tag/v1.0.0
