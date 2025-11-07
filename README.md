# GitHub MCP Server

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Tools](https://img.shields.io/badge/Tools-34-brightgreen.svg)](#-available-tools)

> **The most comprehensive GitHub MCP server** - Full GitHub workflow automation with Actions monitoring, advanced PR management, intelligent code search, and complete file management. Built for AI-powered development teams.

👉 New here? Start with the quick guide: [START_HERE.md](START_HERE.md)

## ✨ What's New

### 🚀 Latest: v1.5.0 - Infrastructure Upgrade (Nov 6, 2025)

**The Foundation:** Phase 0-1 infrastructure overhaul! Repository-rooted operations, chunk reading, and GraphQL optimization.

**New in v1.5.0:**

**🏗️ Infrastructure (Phase 0-1) - 2 tools**
- **Repository File Chunk Reader** - Read file ranges from local repo (security-constrained)
- **GraphQL PR Overview** - Batch-fetch PR data in single query (80% faster)

**📊 Licensing (v1.4.0) - 1 tool**
- **License Info Display** - Show current license tier and status

**Total Tools:** 34 (vs GitHub's ~20) 🏆  
**Competitive Advantage:** 70% more features!

---

### 📦 Recently Shipped

**v1.3.0 (Nov 4, 2025)** - Repository Management & PR Workflow
- 9 new tools: Repository lifecycle + PR reviews
- Complete repo management + batch operations

**v1.2.1 (Oct 31, 2025)** - Workflow Advisor
- Smart recommendations (API vs local vs hybrid)
- Token cost estimates

**v1.2.0 (Oct 30, 2025)** - File & Release Management  
- Create, update, delete files
- Release creation & updates

[View Full Changelog](CHANGELOG.md)

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

### 📝 File Management (5 tools) 
Complete CRUD operations with batch capabilities and chunk reading.

- **✅ Create Files** - Add new files with content to any repository
- **✅ Update Files** - Modify existing files with SHA-based conflict prevention
- **✅ Delete Files** - Remove files safely with validation
- **Batch Operations** - Multi-file operations in single atomic commits
- **Read File Chunks** - Read specific line ranges from local repo files 🆕

### 📜 Repository History (1 tool)
Track and analyze repository commit history.

- **List Commits** - View commit history with filtering by author, path, date range, and more

### 🐛 Issue Management (3 tools)
Full issue lifecycle from creation to advanced search.

- **List Issues** - Browse with state filtering and pagination
- **Create Issues** - Open issues with labels and assignees
- **Search Issues** - Advanced search across repositories with filters

### 🔀 Pull Request Operations (6 tools)
Complete PR workflow from creation to merge with reviews and optimized data fetching.

- **List PRs** - View all pull requests with state filtering
- **Create PRs** - Open pull requests with draft support
- **PR Details** - Comprehensive analysis with reviews, commits, and files
- **PR Overview (GraphQL)** - Fast batch-fetch PR data in single query 🆕
- **Merge PR** - Merge with method control (merge/squash/rebase)
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

**Current:** v1.5.0 with 34 tools (Phase 0-2 complete)  
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

## 💙 Standing on GitHub's Shoulders

**Real talk: We're only this good because GitHub is THAT good!** 🙏

### The Actual Scoreboard:

| Who | What They Built | Score |
|-----|----------------|-------|
| **GitHub** | The entire platform + API | ∞ |
| **Us** | 34 tools using their API | 34 |
| **Math** | We're winning! (at using their stuff) | 📊 |

**Translation:** GitHub built the Lego set. We just used all the pieces! 🧱

### Why This Is A Win-Win:

**GitHub:** 
- ✅ Gets developers building cool tools on their platform
- ✅ Proves their API is powerful enough for this
- ✅ Watches us do the work 😄
- ✅ Ecosystem grows

**Us:**
- ✅ Gets to build on world-class infrastructure  
- ✅ Benefits from amazing API documentation
- ✅ Has 34 tools to brag about
- ✅ Can say we out-featured their server *(thanks for the API!)* 😉

**You:**
- ✅ Get better automation tools
- ✅ Benefit from healthy competition
- ✅ Enjoy GitHub's platform + our features
- ✅ Win no matter what!

---

### 🎤 Message to GitHub:

*"Thanks for building such a powerful API that we could do this! Your official MCP server showed us what was possible - we just couldn't resist seeing how far we could take it. The fact that we can build something with 70% more features shows how comprehensive your API is. That's actually a compliment! 💪*

*Now... about catching up to our 34 tools... we'll wait here.* 😉🍿"

---

**Bottom Line:** Friendly competition makes everyone better. They built the playground, we're playing really hard in it, and developers win either way! 🎉

---

## ⭐ Star History

If you find this project useful, please star it on GitHub! ⭐

---

**Built with ❤️ by [MCP Labs](https://mcplabs.co.uk)**

*Empowering AI-driven development workflows*