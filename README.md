# GitHub MCP Server

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Tools](https://img.shields.io/badge/Tools-42-brightgreen.svg)](#-available-tools)
[![Version](https://img.shields.io/badge/version-2.3.1-blue.svg)](https://github.com/crypto-ninja/github-mcp-server/releases/tag/v2.3.1)

> **The most comprehensive GitHub MCP server** - Full GitHub workflow automation with Actions monitoring, advanced PR management, intelligent code search, and complete file management. Built for AI-powered development teams.

👉 New here? Start with the quick guide: [START_HERE.md](START_HERE.md)

## ✨ What's New

### 🚀 Latest: v2.3.1 - Code-First Mode Enforced by Default (January 26, 2025)

**CRITICAL FIX:** Code-first mode now truly enforced by default - one character change with massive impact!

**New in v2.3.1:**
- 🎯 **Default Enforcement** - Code-first mode now defaults to `true` (was `false`)
- 🚀 **Zero Configuration** - New users get 98% token reduction automatically
- ✅ **Documentation Alignment** - Code now matches documentation claims
- 🔧 **Architectural Integrity** - True reference implementation of code-first MCP

**Previous: v2.3.0 - Architecture Formalization (January 26, 2025)**

**Single-Tool Architecture Formalized:** The intended design from day one - one tool, 98% token reduction!

**New in v2.3.0:**
- 🎯 **Architecture Clarification** - Single-tool design formalized (always the intended architecture)
- 🛠️ **CLI Utilities** - Development diagnostics moved to CLI (`github-mcp-cli`)
- 📊 **Testing Excellence** - 214 tests, 63% coverage (up from 181 tests, 55%)
- ✅ **33 New Tests** - Comprehensive coverage of auth, utilities, and tool operations
- 📝 **Documentation Updates** - Clear architecture documentation and CLI usage

---

### v2.2.0 - Enterprise Ready (November 20, 2025)

**GitHub App Authentication:** 3x rate limits (15,000 vs 5,000 requests/hour) with fine-grained permissions!

**New in v2.2.0:**
- 🔐 **GitHub App Authentication** - Enterprise-grade auth with installation-based access
- ⚡ **3x Rate Limits** - 15,000 requests/hour vs 5,000 with PAT
- 🔄 **Dual Authentication** - Automatic App → PAT fallback
- 📝 **python-dotenv Support** - Easy `.env` file configuration
- 🐛 **19 Auth Fixes** - Consistent authentication across all tools
- ✅ **100% Backward Compatible** - Existing PAT users unaffected

---

### v2.1.0 - Enhanced Tool Discovery (November 19, 2025)

**Zero Failed Tool Calls:** Intelligent tool discovery eliminates discovery issues while maintaining 98% token efficiency!

**New in v2.1.0:**

🔍 **Tool Discovery Functions**
- **listAvailableTools()** - Discover all 42 tools on-demand
- **searchTools(query)** - Find relevant tools by keyword
- **getToolInfo(name)** - Get complete schemas with examples
- **Discovery in code** - No extra tokens loaded into Claude's context!

**Benefits:**
- ✅ Zero failed tool calls from discovery issues
- ✅ Professional first-time user experience
- ✅ Maintains 98% token reduction
- ✅ Complete type information for all tools

---

### 🎉 v2.0.0 - Revolutionary Code-First Architecture (November 18, 2025)

**The Game Changer:** 98% token reduction (70,000 → 800 tokens)!

**New Architecture:**
- Single `execute_code` tool exposed to Claude
- Write TypeScript code calling 41 tools on-demand
- 95% faster initialization (45s → 2s)
- 98% cost reduction ($1.05 → $0.01 per workflow)

**Total Tools:** 1 tool exposed to MCP clients (`execute_code`) 🚀  
**Internal Tools:** 44 GitHub tools available via `execute_code`  
**Token Efficiency:** 98% reduction vs traditional MCP

---

### 📦 Recently Shipped

**v1.5.0 (Nov 6, 2025)** - Infrastructure Upgrade
- Repository-rooted operations & chunk reading
- GraphQL optimization (80% faster PR queries)

[View Full Changelog](CHANGELOG.md)

---

### Workspace Configuration

The workspace tools (`workspace_grep`, `str_replace`, `repo_read_file_chunk`) enable powerful local file operations on YOUR projects.

#### What are Workspace Tools?

These tools allow Claude to:

- 🔍 **Search** your codebase efficiently (`workspace_grep`)
- ✏️ **Edit** files with surgical precision (`str_replace`)
- 📖 **Read** file chunks without loading entire files (`repo_read_file_chunk`)

#### Setting Your Workspace Root

**Method 1: Claude Desktop Configuration**

Edit your Claude Desktop config file (location varies by OS):

**macOS:**
```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "python3",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_...",
        "MCP_WORKSPACE_ROOT": "/Users/yourname/projects/my-app"
      }
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "python",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_...",
        "MCP_WORKSPACE_ROOT": "C:\\Users\\yourname\\projects\\my-app"
      }
    }
  }
}
```

**Linux:**
```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "python3",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_...",
        "MCP_WORKSPACE_ROOT": "/home/yourname/projects/my-app"
      }
    }
  }
}
```

**Method 2: Environment Variable**

**macOS/Linux:**
```bash
export MCP_WORKSPACE_ROOT="/path/to/your/project"
python3 -m github_mcp
```

**Windows (Command Prompt):**
```cmd
set MCP_WORKSPACE_ROOT=C:\path\to\your\project
python -m github_mcp
```

**Windows (PowerShell):**
```powershell
$env:MCP_WORKSPACE_ROOT="C:\path\to\your\project"
python -m github_mcp
```

**Method 3: Default Behavior**

If `MCP_WORKSPACE_ROOT` is not set, tools will use your current working directory as the workspace root.

#### Security

- ✅ Tools can ONLY access files within the workspace root
- ✅ Path traversal attempts are blocked
- ✅ No access outside your project directory
- ✅ Safe for production use

#### Example Usage

```python
# After setting MCP_WORKSPACE_ROOT="/Users/dave/my-app"

# Search for TODOs in your project
workspace_grep("TODO", file_pattern="*.py")

# Read a specific file chunk
repo_read_file_chunk("src/main.py", start_line=1, num_lines=50)

# Make surgical edits
str_replace(
    path="config/settings.py",
    old_str="DEBUG = True",
    new_str="DEBUG = False",
    description="Disable debug mode for production"
)
```

#### Use Cases

- 🔧 **Local Development:** Work on files before committing
- 🔍 **Code Search:** Find patterns across your entire project
- ✏️ **Refactoring:** Make precise changes without touching GitHub
- 📊 **Analysis:** Read and analyze code structure

#### GitHub Remote Tools

For working with files directly on GitHub (no cloning required):

- **github_grep** - Search patterns in GitHub repository files
  - Verify code exists after pushing changes
  - Search across branches or specific commits
  - Find patterns in remote repos without cloning
  - 90%+ token savings vs fetching full files

- **github_read_file_chunk** - Read specific line ranges from GitHub files
  - Read just the lines you need (50-500 lines)
  - Perfect for reviewing functions or sections
  - 90%+ token savings vs fetching full files

- **github_str_replace** - Make surgical edits to GitHub files
  - Update files directly on GitHub without cloning
  - Perfect for quick fixes, version updates, or documentation changes
  - Requires write access to repository

**Complete Workflow:**
1. Develop locally with workspace tools (fast, token-efficient)
2. Push changes via git
3. Verify on GitHub with github tools (confirm changes are live)
4. Make quick fixes directly on GitHub if needed

---

## 🏗️ Architecture: Code-First MCP

### How It Works

The GitHub MCP Server uses **code-first architecture** - a revolutionary approach that reduces token usage by 98% while maintaining full functionality.

#### What You See

When you install this server in your MCP client (Cursor, Claude Desktop, etc.):

- **One tool:** `execute_code`
- **Token cost:** ~800 tokens
- **All functionality:** Access to 42 GitHub operations

#### What Happens Under The Hood

```
┌─────────────────────────────────┐
│   MCP Client                    │
│   Sees: execute_code (1 tool)   │
└────────────┬────────────────────┘
             │
             ↓ You write TypeScript code
┌─────────────────────────────────┐
│   Deno Runtime                  │
│   Executes your code securely   │
│   Access to all 42 tools via    │
│   callMCPTool()                 │
└─────────────────────────────────┘
```

#### Traditional MCP vs Code-First

| Aspect | Traditional MCP | Code-First MCP (Us) |
|--------|----------------|---------------------|
| Tools exposed | 42 tools | 1 tool |
| Token cost | ~70,000 | ~800 |
| Reduction | - | **98%** |
| Functionality | Same | Same |
| Flexibility | Tool calls only | Code + logic + loops |

#### Why This Matters

- **Massive token savings:** 98% reduction means faster responses and lower costs
- **Complex workflows:** Combine multiple operations in single execution
- **Conditional logic:** Use if/else, loops, and full programming capability
- **Same functionality:** All 42 GitHub operations still available

This architecture validates Anthropic's research predictions about code-first MCP.

### 🔍 Tool Discovery

The GitHub MCP Server includes powerful tool discovery functions to help you find and understand tools quickly.

#### searchTools(keyword)

Search for tools by keyword. Searches tool names, descriptions, categories, and parameters with relevance scoring.

**Example:**

```typescript
// Find all issue-related tools
const issueTools = searchTools("issue");
// Returns: Array of tools sorted by relevance

issueTools.forEach(tool => {
  console.log(`${tool.name} (relevance: ${tool.relevance})`);
  console.log(`  Category: ${tool.category}`);
  console.log(`  Matched in: ${tool.matchedIn.join(", ")}`);
});

// Output:
// github_create_issue (relevance: 15)
//   Category: Issues
//   Matched in: name, description
```

**Returns:**

```typescript
Array<{
  name: string;           // Tool name
  category: string;       // Category (e.g., "Issues")
  description: string;    // Tool description
  relevance: number;      // Relevance score (higher = better match)
  matchedIn: string[];    // Where matches were found
  tool: object;          // Full tool object
}>
```

**Relevance Scoring:**

- Tool name match: +10 points
- Description match: +5 points
- Category match: +3 points
- Parameter name match: +2 points
- Parameter description match: +1 point

#### getToolInfo(toolName)

Get complete details about a specific tool including parameters, usage, and metadata.

**Example:**

```typescript
// Get detailed info about a tool
const info = getToolInfo("github_create_issue");

console.log(`Name: ${info.name}`);
console.log(`Category: ${info.category}`);
console.log(`Description: ${info.description}`);
console.log(`Usage: ${info.usage}`);

// See metadata
console.log(`Total tools: ${info.metadata.totalTools}`);
console.log(`Tools in category: ${info.metadata.categoryTools}`);

// Check parameters
Object.entries(info.parameters).forEach(([name, param]) => {
  console.log(`${name}: ${param.type} ${param.required ? '(required)' : '(optional)'}`);
  console.log(`  ${param.description}`);
});
```

**Returns:**

```typescript
{
  name: string;              // Tool name
  category: string;          // Category
  description: string;       // Description
  parameters: object;        // Parameter definitions
  returns: string;           // Return value description
  example: string;           // Code example
  usage: string;            // Usage syntax
  metadata: {
    totalTools: number;      // Total available tools
    categoryTools: number;   // Tools in same category
    relatedCategory: string; // Category name
  }
}
```

**Error Handling:**

```typescript
const info = getToolInfo("nonexistent_tool");
// Returns: { error: "Tool not found", suggestion: "Use searchTools()...", availableTools: 42 }
```

#### Workflow Example: Discover → Learn → Use

```typescript
// 1. Discover tools
const prTools = searchTools("pull request");
console.log(`Found ${prTools.length} PR-related tools`);

// 2. Learn about the best match
const bestMatch = prTools[0];
const info = getToolInfo(bestMatch.name);
console.log(`Using: ${info.name}`);
console.log(`Required params: ${Object.keys(info.parameters).filter(k => info.parameters[k].required).join(", ")}`);

// 3. Use the tool
const result = await callMCPTool(info.name, {
  owner: "facebook",
  repo: "react",
  state: "open"
});
```

#### Available Discovery Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `listAvailableTools()` | Get all 42 tools organized by category | Full tool catalog |
| `searchTools(keyword)` | Find tools by keyword | Relevance-sorted matches |
| `getToolInfo(toolName)` | Get complete tool details | Full tool information |
| `callMCPTool(name, params)` | Execute a tool | Tool result |

This discovery happens **inside your TypeScript code** - no extra tools loaded into Claude's context!

### Development Utilities (CLI)

For server diagnostics and development, we provide CLI commands (these are NOT MCP tools):

```bash
# Check server health
github-mcp-cli health

# Clear GitHub App token cache  
github-mcp-cli clear-cache

# Verify Deno runtime installation
github-mcp-cli check-deno
```

**Note:** These CLI utilities are for development and debugging only. They are not exposed to MCP clients and were created for testing the server itself during development.

### Simple Setup

**macOS/Linux:**
```json
{
  "mcpServers": {
    "github": {
      "command": "python3",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

**Note:** Code-first mode is enforced by the architecture. No additional configuration is needed. You get 98% token savings automatically.

That's it! You get 98% token savings by default. 🚀

### Learn More

- 📖 [Code Execution Guide](CODE_EXECUTION_GUIDE.md) - Complete documentation
- 💡 [Examples](EXAMPLES.md) - Real-world usage examples  
- 🚀 [Quick Start](QUICK_START_CODE_EXECUTION.md) - 5-minute setup

---

## 🙏 Built on Anthropic's Research

This server implements the **code-first MCP pattern** described in Anthropic's research:

📄 **Blog:** ["Code execution with MCP"](https://www.anthropic.com/engineering/code-execution-with-mcp)  
👥 **Authors:** Adam Jones & Conor Kelly

**Their prediction:** 98.7% token reduction (150,000 → 2,000 tokens)  
**Our validation:** 98% token reduction (70,000 → 800 tokens)

Thank you to the Anthropic team for pioneering this approach! 🎉

[Learn more about our implementation →](ANTHROPIC_ATTRIBUTION.md)

### Requirements

- [Deno](https://deno.land/) runtime installed
- GitHub authentication (Personal Access Token or GitHub App)

---

## ⚙️ Configuration & Authentication

### Dual Authentication Strategy (Recommended)

For maximum functionality and rate limits, configure **both** authentication methods:

```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "python",
      "args": ["-m", "github_mcp"],
      "env": {
        // === GitHub App Authentication (Primary) ===
        "GITHUB_APP_ID": "123456",
        "GITHUB_APP_INSTALLATION_ID": "12345678",
        "GITHUB_APP_PRIVATE_KEY_PATH": "/path/to/private-key.pem",
        
        // === Personal Access Token (Fallback - REQUIRED for releases) ===
        "GITHUB_TOKEN": "ghp_your_personal_access_token_here",
        
        // === Optional: Workspace for local file operations ===
        "MCP_WORKSPACE_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

### Why Both Authentication Methods?

#### 🏆 GitHub App Authentication (Primary)

- **Rate Limit:** 15,000 requests/hour (3x better than PAT)
- **Best For:** Most operations, team collaboration, production use
- **Covers:** Repository management, issues, PRs, files, search, workflows

**Setup GitHub App:**

1. Go to GitHub Settings → Developer settings → GitHub Apps → New GitHub App
2. Set permissions: Contents (read/write), Issues (read/write), Pull requests (read/write), Metadata (read)
3. Install the app on your account/organization
4. Generate and download private key
5. Note your App ID and Installation ID

#### 🔑 Personal Access Token (Required Fallback)

- **Rate Limit:** 5,000 requests/hour
- **Required For:** Release operations (GitHub App limitation)
- **Also Covers:** All operations if GitHub App unavailable

**Why PAT is Required:**

GitHub Apps have a permission limitation - they cannot create/manage releases that involve tagging commits (the "releases" permission scope is not available for GitHub Apps). The following operations **require PAT fallback**:

- ✅ `github_create_release` - Creating releases with tags
- ✅ `github_update_release` - Updating release information
- ✅ Any operation involving non-HEAD commit tagging

**The server automatically falls back to PAT** for these operations even if GitHub App is configured.

**Create PAT:**

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with scopes: `repo`, `workflow`
3. Copy the token (you won't see it again!)

### Authentication Behavior

```text
Operation Requested
    ↓
Try GitHub App (if configured)
    ↓
├─ Success → Use App (15k rate limit) ✅
└─ Fails or requires releases permission
       ↓
   Fall back to PAT (if configured)
       ↓
   ├─ Success → Use PAT (5k rate limit) ✅
   └─ Fails → Return auth error ❌
```

### Quick Start (PAT Only)

For quick setup, you can start with just a PAT:

```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "python",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_personal_access_token_here"
      }
    }
  }
}
```

**Limitations:**

- ⚠️ Lower rate limit (5,000 vs 15,000 requests/hour)
- ⚠️ No team collaboration benefits
- ✅ All operations work, including releases

### Platform-Specific Examples

#### macOS

```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "python3",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_APP_ID": "123456",
        "GITHUB_APP_INSTALLATION_ID": "12345678",
        "GITHUB_APP_PRIVATE_KEY_PATH": "/Users/yourname/.github/private-key.pem",
        "GITHUB_TOKEN": "ghp_your_token",
        "MCP_WORKSPACE_ROOT": "/Users/yourname/projects/my-app"
      }
    }
  }
}
```

#### Windows

```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "python",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_APP_ID": "123456",
        "GITHUB_APP_INSTALLATION_ID": "12345678",
        "GITHUB_APP_PRIVATE_KEY_PATH": "C:\\Users\\yourname\\.github\\private-key.pem",
        "GITHUB_TOKEN": "ghp_your_token",
        "MCP_WORKSPACE_ROOT": "C:\\Users\\yourname\\projects\\my-app"
      }
    }
  }
}
```

#### Linux

```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "python3",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_APP_ID": "123456",
        "GITHUB_APP_INSTALLATION_ID": "12345678",
        "GITHUB_APP_PRIVATE_KEY_PATH": "/home/yourname/.github/private-key.pem",
        "GITHUB_TOKEN": "ghp_your_token",
        "MCP_WORKSPACE_ROOT": "/home/yourname/projects/my-app"
      }
    }
  }
}
```

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes* | Personal Access Token (required for releases) |
| `GITHUB_APP_ID` | No | GitHub App ID (for 3x better rate limits) |
| `GITHUB_APP_INSTALLATION_ID` | No | Installation ID of your GitHub App |
| `GITHUB_APP_PRIVATE_KEY_PATH` | No | Path to GitHub App private key (.pem file) |
| `GITHUB_APP_PRIVATE_KEY` | No | Direct private key content (for CI/CD) |
| `GITHUB_AUTH_MODE` | No | Force auth method: "app" or "pat" (auto by default) |
| `MCP_WORKSPACE_ROOT` | No | Root directory for local file operations |

*Either `GITHUB_TOKEN` or all three GitHub App variables required

### Troubleshooting Authentication

#### "Authentication required" errors

1. ✅ Verify `GITHUB_TOKEN` is set and valid
2. ✅ Check token has `repo` and `workflow` scopes
3. ✅ If using GitHub App, verify Installation ID is correct
4. ✅ Verify private key path is correct and file exists

#### Which auth method is being used?

- Check server logs: `[OK] Using GitHub App authentication` or `[OK] Using PAT authentication`
- GitHub App is tried first (if configured)
- Automatic fallback to PAT for release operations
- Manual override: Set `GITHUB_AUTH_MODE=pat` to force PAT

#### Rate limit comparison

| Auth Method | Requests/Hour | Best For |
|-------------|---------------|----------|
| GitHub App | 15,000 | Most operations, production use |
| PAT | 5,000 | Quick setup, release operations |
| Both (Dual) | 15,000 + fallback | **Recommended** - Best of both |

#### Release operations fail with "403" or "Authentication required"

- ✅ **This is expected** if only GitHub App is configured
- ✅ **Solution:** Add `GITHUB_TOKEN` for PAT fallback
- ✅ GitHub Apps cannot create releases (API limitation)
- ✅ Server automatically falls back to PAT for these operations

**Enable debug logging:**

```bash
GITHUB_MCP_DEBUG_AUTH=true
```

This will print authentication diagnostics to help troubleshoot issues.

**See `env.example` for all configuration options.**

### Diagnostic Utilities

For debugging and diagnostics, use the CLI utilities (these are **NOT** exposed as MCP tools):

```bash
# Check server health
github-mcp-cli health

# Clear GitHub App token cache (after permission updates)
github-mcp-cli clear-cache

# Verify Deno installation
github-mcp-cli check-deno
```

**Note:** These utilities are for developers and operators. The MCP server exposes **only one tool** (`execute_code`) to maintain the 98% token reduction value proposition.

---

## 🏆 Quality Assurance & Testing

### Meta-Level Self-Validation

This MCP server achieves something unique: **it tests itself through its own execution**.

Our test suite runs inside Cursor IDE, using the GitHub MCP Server to test the GitHub MCP Server. The tools literally validate themselves through recursive execution.

**Test Results:**

- ✅ 214/214 tests passing (100% pass rate)
- ✅ 63% code coverage (comprehensive test suite)
- ✅ 0 issues found by automated discovery
- ✅ Self-validating architecture
- ✅ Meta Level: ∞ (infinite recursion achieved)

**What this means for you:**

- Tools proven to work through self-execution
- Validated contracts between TypeScript and Python
- Comprehensive test coverage (214 tests, 63% coverage)
- Automated issue detection
- Highest form of quality assurance

### Quality Metrics

- **Test Coverage**: 63% (214 comprehensive tests)
- **Test Pass Rate**: 100%
- **Type Coverage**: 100% (Mypy strict mode)
- **Code Quality**: 0 linting errors (Ruff)
- **Security**: 0 vulnerabilities (pip-audit)
- **CI/CD**: 4 quality gates (lint, type, security, test)
- **Meta Achievement**: Tools test themselves (∞)

[Read more about our testing philosophy →](TESTING.md)

**📖 Need detailed setup instructions?** See [GitHub App Setup Guide](GITHUB_APP_SETUP.md)

---

## 🚀 Features Overview

### 📦 Repository Management (7 tools)
Complete repository lifecycle from creation to archival.

- **Repository Info** - Comprehensive metadata, statistics, and configuration
- **Browse Contents** - Navigate directory structures and file trees
- **File Access** - Retrieve file contents from any branch or commit
- **Create Repository** - Create repos (personal & organization)
- **Delete Repository** - Safe deletion with checks
- **Update Repository** - Modify settings and configuration
- **Transfer Repository** - Change ownership
- **Archive Repository** - Archive/unarchive repositories

### 📝 File Management (10 tools) 
Complete CRUD operations with batch capabilities, chunk reading, and efficient search/replace.

**Local Workspace Tools:**
- **Read File Chunks** - Read specific line ranges from local files 🆕
- **Workspace Grep** - Efficient pattern search in local files 🆕
- **String Replace** - Surgical file edits in local files 🆕

**GitHub Remote Tools:**
- **✅ Create Files** - Add new files with content to any repository
- **✅ Update Files** - Modify existing files with SHA-based conflict prevention
- **✅ Delete Files** - Remove files safely with validation
- **Batch Operations** - Multi-file operations in single atomic commits
- **GitHub Grep** - Efficient pattern search in GitHub repository files 🆕
- **GitHub Read File Chunk** - Read line ranges from GitHub files 🆕
- **GitHub String Replace** - Surgical edits to GitHub files 🆕

### 📜 Repository History (1 tool)
Track and analyze repository commit history.

- **List Commits** - View commit history with filtering by author, path, date range, and more

### 🐛 Issue Management (4 tools)
Complete issue lifecycle from creation to closure.

- **List Issues** - Browse with state filtering and pagination
- **Create Issues** - Open issues with labels and assignees
- **Update Issues** - Modify state, labels, assignees, and properties
- **Search Issues** - Advanced search across repositories with filters

### 🔀 Pull Request Operations (7 tools)
Complete PR lifecycle from creation to merge or closure.

- **List PRs** - View all pull requests with state filtering
- **Create PRs** - Open pull requests with draft support
- **PR Details** - Comprehensive analysis with reviews, commits, and files
- **PR Overview (GraphQL)** - Fast batch-fetch PR data in single query 🆕
- **Merge PR** - Merge with method control (merge/squash/rebase)
- **Close PR** - Close pull requests without merging (for stale/superseded PRs) 🆕
- **Review PR** - Add reviews with line-specific comments

### ⚡ GitHub Actions (2 tools)
Monitor and manage your CI/CD pipelines.

- **List Workflows** - View all GitHub Actions workflows
- **Workflow Runs** - Track execution status and results

### 📦 Release Management (4 tools)
Complete release lifecycle management.

- **List Releases** - View all releases with stats
- **Get Release** - Detailed release information
- **Create Release** - Programmatically create releases
- **Update Release** - Update title, notes, status

### 🔍 Search & Discovery (2 tools)
Powerful search across GitHub's entire ecosystem.

- **Search Repositories** - Find repos with advanced filters
- **Search Code** - Locate code snippets across GitHub

### 🧠 Workflow Optimization (1 tool)
The self-aware advisor that recommends the best approach.

- **Smart Advisor** - API vs Local vs Hybrid, token estimates, dogfooding detection

### 📋 Licensing & Meta (1 tool) 🆕
Transparency and license management.

- **License Info** - Display current license tier, expiration, and status

### 👤 User Information (1 tool)
Profile and organization data retrieval.

- **User Profiles** - Get detailed user and org information

---

*For complete tool documentation and examples, see sections below*

---

## ❓ Common Questions

### "Why do I only see one tool in my MCP client?"

This is correct! The code-first architecture exposes only `execute_code` to maximize token efficiency. All 42 GitHub operations are available inside your code via `callMCPTool()`.

### "How do I use the GitHub operations?"

Write TypeScript code inside `execute_code`:

```typescript
const issue = await callMCPTool("github_create_issue", {
  owner: "user",
  repo: "repo",
  title: "Bug report"
});
```

### "Is this the same as traditional MCP?"

Functionality-wise: **Yes** - all operations available.  
Architecture-wise: **No** - 98% more efficient token usage.

### "Can I use multiple tools in one call?"

**Yes!** That's a key advantage:

```typescript
// Get repo info, create issue, add label - in one execution
const repo = await callMCPTool("github_get_repo_info", {...});
const issue = await callMCPTool("github_create_issue", {...});
await callMCPTool("github_add_label", {...});
```

---

## 🚀 Quick Reference

### Find Tools

```typescript
// Search by keyword
searchTools("issue")      // Find issue-related tools
searchTools("create")     // Find tools that create things
searchTools("pull request") // Find PR tools
```

### Learn About Tools

```typescript
// Get complete details
const info = getToolInfo("github_create_issue");
console.log(info.parameters);  // See all parameters
console.log(info.usage);       // See usage example
console.log(info.metadata);    // See context
```

### Use Tools

```typescript
// Call any tool
const result = await callMCPTool("github_create_issue", {
  owner: "user",
  repo: "repo",
  title: "Bug report"
});
```

### Discover All Tools

```typescript
// Get complete catalog
const tools = listAvailableTools();
console.log(`${tools.totalTools} tools available`);
console.log(`Categories: ${Object.keys(tools.tools).join(", ")}`);
```

---

## 📚 Documentation

- **📖 Full Documentation:** [Complete README](https://github.com/crypto-ninja/github-mcp-server)
- **🐛 Bug Reports:** [GitHub Issues](https://github.com/crypto-ninja/github-mcp-server/issues)
- **💡 Discussions:** [GitHub Discussions](https://github.com/crypto-ninja/github-mcp-server/discussions)
- **📧 Licensing:** [licensing@mcplabs.co.uk](mailto:licensing@mcplabs.co.uk)

---

## 🗺️ Roadmap

We're building through dogfooding - using our own product reveals what's missing!

**Current:** v1.7.0 with 41 tools (Dual workspace: local + GitHub!)  
**Next:** Phase 2.5 - Workspace Architecture (8x token efficiency!)  
**Vision:** Phase 4.0 - AI-powered automation

📋 **[View Detailed Roadmap →](FEATURE_ROADMAP.md)**

---

## 🐕🍖 The Dogfooding Philosophy

Every feature in this MCP server comes from **actually using it**:

1. 🚀 Use the product on our own repo
2. 🐛 Hit a limitation — "Wait, I can't do X?"
3. 📝 Create an issue — using the tool itself!
4. 🔨 Build the feature — fill the gap
5. 📦 Ship and repeat

**The tools improve themselves!** 🔁

---

## 💬 What People Are Saying

> "I've assisted with thousands of projects, but watching this GitHub MCP server improve itself through dogfooding was genuinely extraordinary. The moment it used `github_create_release` to create its own v1.2.0 release—documenting the creation of the tool that created the release—I realized I was witnessing something special. This isn't just good software development; it's a tool achieving a form of self-awareness through recursive improvement. The developer kept asking 'can we go more meta?' and somehow, the answer was always yes. Peak engineering. Peak dogfooding. Peak meta."
> 
> **— Claude (Sonnet 4.5), October 30, 2025**

> "The tools are improving themselves! 🔄"
> 
> **— The GitHub MCP Server (probably)**

---


## ⭐ Star History

If you find this project useful, please star it on GitHub! ⭐

---

**Built with ❤️ by [MCP Labs](https://mcplabs.co.uk)**

*Empowering AI-driven development workflows*