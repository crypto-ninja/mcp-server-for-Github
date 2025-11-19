# GitHub MCP Server

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Tools](https://img.shields.io/badge/Tools-42-brightgreen.svg)](#-available-tools)
[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/crypto-ninja/github-mcp-server/releases/tag/v2.1.0)

> **The most comprehensive GitHub MCP server** - Full GitHub workflow automation with Actions monitoring, advanced PR management, intelligent code search, and complete file management. Built for AI-powered development teams.

👉 New here? Start with the quick guide: [START_HERE.md](START_HERE.md)

## ✨ What's New

### 🚀 Latest: v2.1.0 - Enhanced Tool Discovery (November 19, 2025)

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

**Total Tools:** 42 (41 GitHub + 1 execute_code) 🚀  
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

## 🚀 Revolutionary: Code-First Architecture

The GitHub MCP Server v2.0 uses a revolutionary **code-first architecture** that reduces token usage by **98%** compared to traditional MCP servers!

### The Problem with Traditional MCP

**Traditional MCP Servers:**
```
Load all 41 tools → 70,000 tokens → $1.05 per conversation
```

Every tool must be loaded into Claude's context, consuming massive tokens.

### The GitHub MCP Server Solution

**Code-First Architecture:**
```
Load 1 tool → 800 tokens → $0.01 per conversation
```

**98% token reduction! 🚀**

### How It Works

Instead of loading all 41 tools, Claude only sees the `execute_code` tool. You simply describe what you want, and Claude writes TypeScript code that calls tools on-demand:

**You ask:**
```
Get info about facebook/react and list recent issues
```

**Claude writes and executes:**
```typescript
const info = await callMCPTool("github_get_repo_info", {
    owner: "facebook",
    repo: "react"
});

const issues = await callMCPTool("github_list_issues", {
    owner: "facebook",
    repo: "react",
    state: "open",
    limit: 5
});

return { repo: "facebook/react", info, issues };
```

### Tool Discovery

Don't know what tools are available? Discover them dynamically:

```typescript
// List all available tools
const tools = listAvailableTools();
console.log(`Total tools: ${tools.totalTools}`);
console.log(`Categories: ${tools.categories.join(", ")}`);

// Search for specific tools
const issueTools = searchTools("issue");
console.log(`Found ${issueTools.length} tools related to issues`);

// Get detailed info about a tool
const toolInfo = getToolInfo("github_create_issue");
console.log(toolInfo.example);
```

This discovery happens **inside your TypeScript code** - no extra tools loaded into Claude's context!

### Benefits

✅ 98% token reduction - 70,000 → 800 tokens  
✅ 98% cost reduction - $1.05 → $0.01 per conversation  
✅ 95% faster initialization - 45s → 2s  
✅ More powerful - Loops, conditionals, complex logic  
✅ Easier to use - Just describe what you want  
✅ Same capabilities - All 41 tools available

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

That's it! No configuration needed - you get 98% savings by default. 🚀

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
- GitHub personal access token

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