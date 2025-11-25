# Claude Desktop Configuration for GitHub MCP Server

## Configuration Location

### macOS
`~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
`%APPDATA%\Claude\claude_desktop_config.json`

### Linux
`~/.config/Claude/claude_desktop_config.json`

## Configuration Example

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_personal_access_token_here"
      }
    }
  }
}
```

**Note:** Code-first mode is enforced by the architecture. No additional configuration is needed. You get 98% token savings automatically.

## Using UV (Recommended)

If you're using UV for dependency management:

```json
{
  "mcpServers": {
    "github": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp",
        "--with",
        "httpx",
        "--with",
        "pydantic",
        "python",
        "-m",
        "github_mcp"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_your_personal_access_token_here"
      }
    }
  }
}
```

## Environment Variables

### GitHub App (recommended for orgs)
- `GITHUB_APP_ID` (numeric)
- `GITHUB_APP_INSTALLATION_ID` (numeric)
- `GITHUB_APP_PRIVATE_KEY` (PEM string) OR `GITHUB_APP_PRIVATE_KEY_PATH` (path to .pem file)

**Note:** You can use either `GITHUB_APP_PRIVATE_KEY` (for CI/CD) or `GITHUB_APP_PRIVATE_KEY_PATH` (for local development). The server will automatically use GitHub App if configured, with PAT as fallback.

### Personal Access Token (PAT)
- `GITHUB_TOKEN` (fine-grained or classic)

**How to create:**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name like "Claude MCP Server"
4. Select scopes:
   - `repo` - Full control of private repositories
   - `read:user` - Read user profile data
   - `read:org` - Read organization data
5. Click "Generate token"
6. Copy the token and add it to your configuration

**Benefits of PAT:**
- 5,000 requests per hour (vs 60 without token)
- Access to private repositories
- Ability to create issues and perform write operations
- Access to more detailed information

## Scopes & Permissions (minimum)

- File writes (create/update/delete): contents:write
- PR operations (create/merge/review): pull_requests:write
- Issues (create/search): issues:write (for writes)
- Releases: contents:write (publish)
- Actions (list runs/workflows): actions:read

## Testing the Configuration

After adding the configuration:

1. Restart Claude Desktop
2. Open a new conversation
3. Try a simple query: "What information is available about the tensorflow/tensorflow repository?"
4. Claude should automatically use the GitHub MCP server to fetch the information

## Troubleshooting

### Server Not Connecting
- Verify Python is in your PATH: `python --version` (should be 3.9+)
- Ensure the package is installed: `pip show github-mcp-server`
- Test the module: `python -m github_mcp` (should start without errors)
- Ensure all dependencies are installed: `pip install mcp httpx pydantic`

### Authentication Errors
- Verify your GitHub token is valid
- Check token scopes/permissions
- Ensure the token isn't expired

### Permission Errors
- If using file-based execution, ensure the file has execute permissions
- For module-based execution (`python -m github_mcp`), no special permissions needed

### Rate Limiting
- Use a GitHub token to increase rate limits
- The server will return clear error messages when rate limits are hit

## Advanced Configuration

### Multiple Tokens
If you need different tokens for different operations, you can pass tokens directly in tool calls rather than using environment variables.

### Custom Base URL (GitHub Enterprise)
For GitHub Enterprise installations, set the `GITHUB_API_BASE_URL` environment variable:

```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["-m", "github_mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here",
        "GITHUB_API_BASE_URL": "https://github.your-company.com/api/v3"
      }
    }
  }
}
```

## Security Notes

1. **Never commit tokens to version control**
2. **Use environment variables** for sensitive data
3. **Rotate tokens regularly** 
4. **Use fine-grained tokens** with minimal required permissions
5. **Monitor token usage** in GitHub settings

## Monitoring

GitHub provides rate limit information in response headers:
- `X-RateLimit-Limit` - Maximum requests per hour
- `X-RateLimit-Remaining` - Remaining requests
- `X-RateLimit-Reset` - Time when limit resets (Unix timestamp)

The server handles these automatically and provides clear error messages when limits are reached.
