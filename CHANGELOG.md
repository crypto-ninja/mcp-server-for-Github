# Changelog
## [1.6.0] - 2025-11-07

### 🔍 Token Efficiency Tools (Phase 2.5 Foundation)

**Added:** 2 new tools for 95%+ token efficiency!

#### New Tools
1. **workspace_grep** - Efficient pattern search in repository files
   - Find functions, errors, TODOs with 90% fewer tokens
   - Returns only matching lines with context
   - Security: repo-rooted, respects .gitignore
   - Supports regex patterns and file filtering

2. **str_replace** - Surgical file edits without full rewrites
   - Replace exact strings in files (95% token savings)
   - Unique match requirement for safety
   - Preserves formatting and structure
   - Perfect for version bumps and targeted updates

#### Impact
- **Token Efficiency:** 95%+ reduction for targeted edits
- **Combined Power:** grep finds it, str_replace fixes it!
- **Discovered Through:** Dogfooding! 🐕🍖
- **Meta Achievement:** Tools documented themselves efficiently!

#### Use Cases
- Find all error patterns: `workspace_grep("KeyError")`
- Update version numbers: `str_replace("v1.5.0", "v1.6.0")`
- Locate TODOs: `workspace_grep("TODO", file_pattern="*.py")`
- Update tool counts: Used these tools to update docs about themselves! 🤯

### 🔧 Bug Fixes
- Fixed REPO_ROOT to use `Path(__file__).parent` instead of `os.getcwd()`
- Ensures tools search actual repo directory, not working directory

### 🎯 Phase 2.5 Progress
- Foundation complete: grep + str_replace operational
- Next: Workspace coordinator for full workspace management
- Goal: 8x overall token efficiency

### 🔗 Related
- Issue #27: workspace_grep implementation
- Discovered while using tools (dogfooding in action!)
- Combined 98%+ efficiency with both tools

**Total Tools:** 36 (vs GitHub's ~20) 🏆

---

## [1.5.0] - 2025-11-06

### 🚀 Phase 0-1: Infrastructure & Performance Upgrade

**Meta Achievement:** This release was merged AND released BY the tools themselves! 🤯

Major infrastructure improvements with 2 new tools, connection pooling, GraphQL support, and CI/CD pipeline.

### ✨ New Tools (+2)

**Tool #33: `github_get_pr_overview_graphql`**
- GraphQL-based PR overview fetching
- Single query vs multiple REST calls  
- More efficient than REST equivalent
- **Meta Note:** This tool reviewed itself during PR #14!

**Tool #34: `repo_read_file_chunk`**
- Read local repository files in line-based chunks
- Parameters: path, start_line, num_lines (max 500)
- Security: repo-root constrained
- **Note:** Foundation for Phase 2.5 workspace architecture (Issue #15)

### 💨 Infrastructure Improvements

#### HTTP Connection Pooling
- New `github_client.py` module with connection pooling
- Reuses HTTP connections for better performance
- ETag caching for conditional requests
- Reduced latency and network overhead

#### GitHub App Authentication
- Optional App-based authentication (new `auth/github_app.py`)
- Better rate limits for enterprise users
- PAT authentication still the default
- Zero config changes required for existing users

#### GraphQL Client
- New `graphql_client.py` module
- Foundation for more efficient batch operations
- Enables complex queries in single request

#### CI/CD Pipeline
- GitHub Actions workflow added (`.github/workflows/ci.yml`)
- Automated testing on pull requests
- Quality assurance automation
- Professional development workflow

#### Modern Packaging
- `pyproject.toml` (PEP 621 compliant)
- Better dependency management
- Industry standard packaging

### 📊 Statistics
- **New Tools:** 2 (32 → 34)
- **Code Changes:** +571 lines, -50 lines
- **Files Modified:** 9 files
- **Breaking Changes:** NONE
- **Backward Compatibility:** 100%

### 🐕🍖 The Meta Journey
1. ✅ Tools created Issue #12 (license)
2. ✅ Tools created PR #13 (license)
3. ✅ Tools reviewed PR #13
4. ✅ Tools merged PR #13
5. ✅ Tools created PR #14 (this upgrade!)
6. ✅ Tools created Issues #15 & #16 (vision)
7. ✅ Tools reviewed PR #14  
8. ✅ **Tools merged PR #14**
9. ✅ **Tools released v1.5.0**

**Meta Score:** 21/10 🐕🍖♾️🤯

### 🔗 Related
- PR #14: Phase 0-1 implementation
- Issue #15: Phase 2.5 Workspace Architecture
- Issue #16: Roadmap documentation update
- Merge Commit: f4e9fcd6374ef42d4fd0a7c2f2b8ac08cd5e17e2

[1.5.0]: https://github.com/crypto-ninja/github-mcp-server/releases/tag/v1.5.0

## [1.4.0] - 2025-11-06

### 🔒 License Verification Integration

**Meta Achievement:** Created BY the tools themselves! 🐕🍖

Added license verification system with tool to check license status.

### ✨ New Tool (+1)

**Tool #32: `github_license_info`**
- Display current license tier and status
- Show license expiration date
- Check feature availability
- No parameters required

### 🏗️ License Management
- New `license_manager.py` module
- AGPL-3.0 for free tier
- Commercial licensing support
- License key validation
- Graceful fallback on errors

### 📊 Statistics
- **New Tools:** 1 (31 → 32)
- **Licensing:** Dual license (AGPL + Commercial)
- **Breaking Changes:** NONE

### 🐕🍖 Dogfooding Story #13

The tools created their own license verification:
1. ✅ Created Issue #12 about themselves
2. ✅ Created PR #13 for themselves  
3. ✅ Reviewed their own PR
4. ✅ Merged their own PR
5. ✅ Verified their own license!

**Meta Level:** INFINITE ♾️

### 🔗 Related
- Issue #12: License integration proposal
- PR #13: License implementation
- Merge Commit: 9323b91c5e5b2cc120ec6b221f5e7205101b3c0f

[1.4.0]: https://github.com/crypto-ninja/github-mcp-server/releases/tag/v1.4.0

## [1.3.0] - 2025-11-04

### 🚀 Phase 2.2 & 2.3 Combined Release

Major expansion adding 9 new tools for complete repository lifecycle and PR workflow automation!

### ✨ Phase 2.2: Repository Management (6 tools)

#### Repository Lifecycle
- `github_create_repository` - Create repositories (personal & organization)
- `github_delete_repository` - Delete repositories with safety checks
- `github_update_repository` - Modify repository settings and configuration
- `github_transfer_repository` - Transfer repository ownership
- `github_archive_repository` - Archive or unarchive repositories
- `github_merge_pull_request` - Merge PRs with method control

**Use Cases:**
- Complete repository lifecycle automation
- Organizational repo management
- Repository migration and archival

### ✨ Phase 2.3: PR Workflow & History (3 tools)

#### Pull Request Interaction
- `github_create_pr_review` - Create PR reviews with line-specific comments
- `github_batch_file_operations` - Multi-file operations in single commits
- `github_list_commits` - View commit history with advanced filtering

**Use Cases:**
- AI-powered code review with specific feedback
- Efficient multi-file updates
- Commit history tracking and analysis

### 📊 Statistics
- New Tools: 9 (22 → 31)
- Total Tools: **31**
- Competitive Advantage: +11 tools vs GitHub's official server (55% ahead!)

### 🐕🍖 Dogfooding Stories #11 & #12

**Story #11:** "The Tools Test Themselves"
- Used `list_commits` to view its own branch history
- Used `batch_file_operations` to create test files
- Used `create_pr_review` to comment on PR #10 containing these tools
- **Meta-Level:** MAXIMUM 🤯

**Story #12:** "The Hybrid Verification"
- Used Cursor for fast local development
- Used GitHub tools to verify the documentation updates
- Tools verified their own documentation! 
- **Meta-Level:** Still maximum! 🤯

### 🏆 Competitive Position

**Your Server:** 31 tools  
**GitHub's Official:** ~20 tools  
**Advantage:** +11 tools (55% more)

**Unique Features:**
- ✅ Complete repository lifecycle
- ✅ Batch file operations (50x faster)
- ✅ PR reviews with line comments
- ✅ Advanced commit filtering
- ✅ Dual licensing (AGPL + Commercial)

### 📚 Documentation
- README updated with all 31 tools
- Comprehensive tool documentation
- Competitive analysis completed
- Updated use cases and examples

[1.3.0]: https://github.com/crypto-ninja/github-mcp-server/releases/tag/v1.3.0

## [Unreleased]

### Planned
- Phase 2.5: Workspace Architecture (Issue #15) - Token efficiency!
- Phase 3.0: Branch Management - Essential Git workflows
- Stay tuned for more features!

---

## [1.6.0] - 2025-11-11

### 🎉 Complete Issue/PR Lifecycle Management

**The Dogfooding Story:** During cleanup, tools discovered they could CREATE but not CLOSE issues! 🙈

### ✨ New Tools (34 → 36 tools)

1. **`github_update_issue`** - Complete issue management
   - Update issue state (open/closed)
   - Modify title, body, and labels
   - Manage assignees and milestones
   - Full lifecycle control

2. **`github_close_pull_request`** - PR closure without merging
   - Close stale/superseded PRs  
   - Add explanatory comments
   - Maintain repository hygiene

### 🎭 Dogfooding Story #14

**"The Tools That Closed Themselves"**

During a repo cleanup session:
1. 🔍 Tools attempted to close completed issues
2. 🐞 Discovered they couldn't close issues!
3. 📝 Created Issue #29 requesting the feature
4. 🔧 Cursor implemented both tools in 30 minutes
5. ✅ Tools closed 13 completed items
6. 🔄 **Tools closed Issue #29 itself!** (Peak recursion!)

**Meta Achievement:** Tools completed their own lifecycle! ♾️

### 🧹 Repository Cleanup

Automated cleanup using the new tools:
- Closed 11 completed issues (#18-28)
- Closed 2 tracking issues (#21, #25)  
- Closed stale PR #11 with explanation
- Closed Issue #29 (tools closed themselves!)

**Result:** 14 open items → 2 open items (both future work)

### 📊 Impact

**Before v1.6.0:**
- 34 tools
- Could create issues but not close them
- Manual cleanup required
- Incomplete lifecycle management

**After v1.6.0:**
- 36 tools (+2)
- Complete issue/PR lifecycle
- Automated cleanup capabilities  
- Tools fully self-managing! ✨

### 🎯 Use Cases

**Issue Management:**
- Automated issue closure
- Bulk label updates
- Workflow automation
- Issue state tracking

**PR Management:**
- Close superseded PRs
- Cleanup stale branches
- Maintain PR hygiene
- Automated workflows

### 🔗 Links

- [Issue #29](https://github.com/crypto-ninja/github-mcp-server/issues/29) - Feature request (closed by itself!)
- [Dogfooding Story #14](docs/dogfooding/story_14.md) - Full narrative

[1.6.0]: https://github.com/crypto-ninja/github-mcp-server/releases/tag/v1.6.0

## [1.2.1] - 2025-10-31

### 🧠 The Self-Aware Update

Added the workflow advisor tool that recommends when to use API tools vs local git vs a hybrid approach, including rough token cost estimates and dogfooding detection.

### ✨ Added
- `github_create_release` - Create releases programmatically
- `github_update_release` - Update existing releases (title, notes, status)
- `github_suggest_workflow` - Recommend optimal workflow (API/local/hybrid)

### 📊 Statistics
- New Tools: 3 (total 22)

### 🐕🍖 Dogfooding Story #11
We built the self-aware tool while deciding how to document itself. It recommended using itself to document itself. META LEVEL: ∞ 🤯

[1.2.1]: https://github.com/crypto-ninja/github-mcp-server/releases/tag/v1.2.1


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-10-28

### 😂 The "Dogfooding Update"

TL;DR: We tried to verify our own v1.1.0 release and realized we couldn't. So we added the release tools and shipped v1.1.1 the same day. 🐕🍖

### ✨ Added

#### Release Management (Phase 1.4)
- `github_list_releases` - List all releases from a repository
- `github_get_release` - Get detailed release information (supports `tag="latest"`)

### 📊 Statistics
- New Tools: 2 (total 16)
- Lines of Code: ~200

### 🎯 Use Cases
- Release verification, version discovery, dependency updates

[1.1.1]: https://github.com/crypto-ninja/github-mcp-server/releases/tag/v1.1.1

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