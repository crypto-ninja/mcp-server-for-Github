# 🚀 GitHub MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

> A comprehensive, production-ready Model Context Protocol (MCP) server that enables AI assistants to seamlessly interact with GitHub repositories, issues, pull requests, and more.

## ✨ Features

- **🏢 Repository Management** - Browse, search, and analyze GitHub repositories
- **🐛 Issue Tracking** - List, create, and manage issues
- **🔀 Pull Requests** - View and track pull request status
- **🔍 Advanced Search** - Multi-criteria repository and code search
- **📄 File Access** - Retrieve file contents from any branch or commit
- **👤 User Profiles** - Get detailed user and organization information
- **🎯 Production Ready** - Error handling, rate limiting, pagination
- **📚 Extensive Docs** - 70KB+ of comprehensive documentation

## 📋 Quick Start

### Installation

```bash
pip install mcp httpx pydantic
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

### Try It!

Ask Claude:
```
"What can you tell me about the tensorflow/tensorflow repository?"
```

## 📚 Documentation

- **[START_HERE.md](START_HERE.md)** - Quick overview and welcome guide
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute setup guide
- **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** - Advanced configuration
- **[docs/FEATURES.md](docs/FEATURES.md)** - Complete feature showcase
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design
- **[docs/INDEX.md](docs/INDEX.md)** - Documentation navigator

## 🛠️ Tools Available

| Tool | Description | Auth Required |
|------|-------------|---------------|
| `github_get_repo_info` | Get repository details | Optional |
| `github_list_issues` | List repository issues | Optional |
| `github_create_issue` | Create new issues | Required |
| `github_search_repositories` | Search GitHub repos | Optional |
| `github_get_file_content` | Get file contents | Optional |
| `github_list_pull_requests` | List pull requests | Optional |
| `github_get_user_info` | Get user profiles | Optional |
| `github_list_repo_contents` | Browse directories | Optional |

## 🎯 Use Cases

- **Development Teams** - Code review, issue tracking, repository discovery
- **Project Managers** - Sprint planning, team coordination, progress tracking
- **Researchers** - Technology trends, repository analysis, developer activity

## 🔒 Security

- Optional authentication (not required for public repos)
- No credentials stored in code
- Rate limit management
- Input validation with Pydantic
- Actionable error messages

## 📊 Project Stats

- **Lines of Code:** 1,200+
- **Tools:** 8 comprehensive implementations
- **Documentation:** 70KB+ across 8 files
- **Type Coverage:** 100%
- **Test Scenarios:** 10 evaluation cases

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built following [Model Context Protocol](https://modelcontextprotocol.io) best practices and guidelines.

---

**Made with ❤️ by the MCP community**
