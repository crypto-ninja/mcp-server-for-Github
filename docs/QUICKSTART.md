# 🚀 Quick Start Guide - GitHub MCP Server

Get up and running with the GitHub MCP Server in 5 minutes!

## Step 1: Install Dependencies (1 minute)

Choose one method:

### Option A: Using pip
```bash
pip install mcp httpx pydantic --break-system-packages
```

### Option B: Using UV (Recommended)
```bash
# Install UV if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install mcp httpx pydantic
```

## Step 2: Choose Authentication

### Option A: GitHub App (Recommended for orgs)

Set the following environment variables in your MCP client config:

```json
{
  "env": {
    "GITHUB_AUTH_MODE": "app",
    "GITHUB_APP_ID": "123456",
    "GITHUB_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----...",
    "GITHUB_APP_INSTALLATION_ID": "7890123"
  }
}
```

Benefits: short-lived tokens, fine-grained permissions.

### Option B: Personal Access Token (PAT)

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name it: "Claude MCP GitHub Server"
4. Select scopes:
   - ✅ `repo` (for private repos and creating issues)
   - ✅ `read:user` (for user info)
   - ✅ `read:org` (for organization info)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

**Note**: You can skip this step for read-only access to public repositories.

## Step 3: Configure Claude Desktop (2 minutes)

### Find Your Config File

**macOS:**
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

### Add Server Configuration

Replace `/path/to/github_mcp.py` with the actual path to your file:

```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": [
        "/path/to/github_mcp.py"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

**Example paths:**
- macOS: `/Users/yourname/github_mcp.py`
- Windows: `C:\\Users\\yourname\\github_mcp.py`
- Linux: `/home/yourname/github_mcp.py`

### Alternative: Without Token (Public Repos Only)

```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": [
        "/path/to/github_mcp.py"
      ]
    }
  }
}
```

## Step 4: Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

## Step 5: Test It! (30 seconds)

Open a new conversation in Claude and try:

### Test 1: Repository Information
```
"What can you tell me about the tensorflow/tensorflow repository?"
```

Claude should automatically use the GitHub MCP server and return detailed information about TensorFlow's GitHub repository.

### Test 2: Search Repositories
```
"Find me some popular Python machine learning repositories with over 10,000 stars"
```

### Test 3: View Issues
```
"Show me the open issues in the microsoft/vscode repository"
```

### Test 4: User Information
```
"Tell me about the GitHub user 'torvalds'"
```

## 🎉 Success!

If you see detailed responses with GitHub data, you're all set!

## 🔥 Quick Examples

### Example 1: Research Projects
```
"I'm interested in learning about Rust. Can you find and describe 
the top 3 Rust repositories on GitHub?"
```

### Example 2: Bug Investigation
```
"Search for open issues in the facebook/react repository related 
to hooks. Show me the most recent 5."
```

### Example 3: Developer Profiles
```
"Look up information about the GitHub users 'gvanrossum' and 'torvalds'. 
Who has more followers?"
```

### Example 4: Repository Exploration
```
"Show me the directory structure of the tensorflow/tensorflow 
repository. What's in the root folder?"
```

### Example 5: File Content
```
"Get the README.md file from the rust-lang/rust repository and 
summarize its main points."
```

## 🛠️ Troubleshooting

### "Server not connecting"

1. **Check the path**: Ensure the path to `github_mcp.py` is absolute and correct
2. **Verify Python**: Run `python --version` (should be 3.10+)
3. **Test the server**: Run `python /path/to/github_mcp.py` (it should start without errors)
4. **Check logs**: Look at Claude Desktop logs for errors

### "Authentication errors"

1. **Verify token**: Go to https://github.com/settings/tokens and check if your token is active
2. **Check scopes**: Ensure your token has the required permissions
3. **Update config**: Make sure the token in the config file is correct

### "Rate limit exceeded"

1. **Use a token**: Authenticated requests have much higher limits (5000/hour vs 60/hour)
2. **Wait**: Rate limits reset every hour
3. **Check usage**: Go to https://github.com/settings/tokens to see API usage

### "Python not found"

**macOS/Linux:**
```bash
which python3
# Use the full path in your config:
# "command": "/usr/local/bin/python3"
```

**Windows:**
```cmd
where python
REM Use the full path in your config
```

### "Module not found: mcp"

Dependencies not installed. Run:
```bash
pip install mcp httpx pydantic --break-system-packages
```

## 📚 Next Steps

1. **Read the README**: Check out `README.md` for complete tool documentation
2. **Explore tools**: Try all 8 GitHub tools available
3. **Check architecture**: See `ARCHITECTURE.md` for system design
4. **Review configuration**: Read `CONFIGURATION.md` for advanced setup

## 🎯 Pro Tips

### Tip 1: Save Your Token Safely
Never commit your token to version control. Use environment variables or system keychains.

### Tip 2: Use Specific Queries
Instead of "Tell me about React", try:
```
"Get detailed statistics for the facebook/react repository including 
stars, forks, and recent activity"
```

### Tip 3: Combine Tools
Claude can use multiple tools in sequence:
```
"Find the most popular Python web framework, then show me its 
open issues and tell me what the main pain points are"
```

### Tip 4: Request Specific Formats
```
"Give me the repository info for tensorflow/tensorflow in JSON format"
```

### Tip 5: Use Pagination
For large result sets:
```
"Show me page 2 of open issues in microsoft/vscode"
```

## 🆘 Getting Help

If you encounter issues:

1. **Check syntax**: Run `python -m py_compile github_mcp.py`
2. **Test manually**: Run `python github_mcp.py` and check for errors
3. **Review logs**: Check Claude Desktop logs
4. **Verify dependencies**: Ensure all packages are installed
5. **Test token**: Try using GitHub's API directly to verify your token

## ⚡ Performance Tips

1. **Be specific**: More specific queries = better results
2. **Use filters**: Apply state, label, and date filters when listing issues/PRs
3. **Paginate wisely**: Don't request huge result sets at once
4. **Check token**: Using a token dramatically improves rate limits

## 🎊 You're Ready!

You now have a powerful GitHub integration for Claude! Use it to:
- Research open source projects
- Track issues and pull requests
- Explore codebases
- Find repositories by criteria
- Analyze developer activity
- And much more!

**Happy coding! 🚀**
