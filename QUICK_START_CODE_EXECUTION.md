# Quick Start: Code-First Execution

## 5-Minute Setup

### 1. Install Deno

```bash
# Mac/Linux
curl -fsSL https://deno.land/install.sh | sh

# Windows (PowerShell)
irm https://deno.land/install.ps1 | iex

# Verify installation
deno --version
```

### 2. Configure Claude Desktop

Add to `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "github": {
      "command": "cmd",
      "args": ["/c", "python", "C:\\path\\to\\github_mcp.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

**That's it!** Code-first architecture is enabled by default. 🚀

### 3. Restart Claude Desktop

Completely close and reopen Claude Desktop.

### 4. Test It

In Claude, try:
```
Use execute_code to get info about facebook/react
```

### 5. Verify Token Savings

Compare:

- Traditional: ~70,000 tokens
- Code-first: ~1,600 tokens
- Savings: 98%+ 🚀

## Common Commands

```typescript
// Get repo info
const info = await callMCPTool("github_get_repo_info", {
    owner: "owner",
    repo: "repo"
});

// List issues
const issues = await callMCPTool("github_list_issues", {
    owner: "owner",
    repo: "repo",
    state: "open",
    limit: 10
});

// Search code
const results = await callMCPTool("github_search_code", {
    query: "TODO repo:owner/repo"
});
```

## Full Documentation

- [Complete Guide](CODE_EXECUTION_GUIDE.md)
- [Examples](EXAMPLES.md)
- [README](README.md)

---

**You're ready to go! 🚀**

