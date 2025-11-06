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
      "args": [
        "/path/to/github_mcp.py"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_your_personal_access_token_here"
      }
    }
  }
}
```

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
        "/path/to/github_mcp.py"
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
- `GITHUB_AUTH_MODE=app`
- `GITHUB_APP_ID` (numeric)
- `GITHUB_APP_PRIVATE_KEY` (PEM string)
- `GITHUB_APP_INSTALLATION_ID` (numeric)

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
- Verify the path to `github_mcp.py` is absolute and correct
- Check that Python is in your PATH
- Ensure all dependencies are installed (`mcp`, `httpx`, `pydantic`)

### Authentication Errors
- Verify your GitHub token is valid
- Check token scopes/permissions
- Ensure the token isn't expired

### Permission Errors
- On Unix systems, make sure `github_mcp.py` has execute permissions:
  ```bash
  chmod +x /path/to/github_mcp.py
  ```

### Rate Limiting
- Use a GitHub token to increase rate limits
- The server will return clear error messages when rate limits are hit

## Advanced Configuration

### Multiple Tokens
If you need different tokens for different operations, you can pass tokens directly in tool calls rather than using environment variables.

### Custom Base URL (GitHub Enterprise)
For GitHub Enterprise installations, you can modify the `API_BASE_URL` constant in `github_mcp.py`:

```python
API_BASE_URL = "https://github.your-company.com/api/v3"
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
