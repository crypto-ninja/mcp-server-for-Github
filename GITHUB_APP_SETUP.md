# GitHub App Setup Guide

This guide walks you through setting up GitHub App authentication for GitHub MCP Server.

## Why Use GitHub App?

- ⚡ **3x faster** - 15,000 requests/hour vs 5,000 with PAT
- 🔐 **More secure** - Fine-grained permissions
- 🏢 **Enterprise-ready** - Organizational control
- 👥 **Team-friendly** - Per-repository access

## Prerequisites

- A GitHub account
- Admin access to repositories you want to access
- 15 minutes for setup

## Step-by-Step Setup

### 1. Create GitHub App

1. Go to https://github.com/settings/apps/new

2. Fill in the form:

   - **GitHub App name:** `My GitHub MCP Server` (must be unique)
   - **Homepage URL:** `https://github.com/crypto-ninja/github-mcp-server`
   - **Webhook:** Uncheck "Active" (we don't need webhooks)

### 2. Configure Permissions

Under "Repository permissions," set:

| Permission | Access Level | Why Needed |
|------------|--------------|------------|
| Contents | Read and write | Clone, read, and commit files |
| Issues | Read and write | Create, read, update issues |
| Pull requests | Read and write | Create, review, merge PRs |
| Metadata | Read-only | Access repo metadata (automatic) |
| Actions | Read and write | Trigger workflows, read logs |
| Administration | Read and write | Manage repo settings |
| Commit statuses | Read-only | Read CI/CD status |

### ⚠️ Known Limitation: Releases Permission

**Issue:** As of November 2025, the "Releases" permission is **missing from the GitHub App permissions UI** for some apps. This is a known GitHub platform issue.

**Impact:** 

- GitHub Apps cannot create, update, or delete releases
- The `github_create_release`, `github_update_release` tools will fail with "Permission denied"

**Workaround:** Use **PAT fallback authentication**

This server has dual authentication built-in. If GitHub App auth fails, it automatically falls back to Personal Access Token (PAT):

1. **Generate a PAT:**

   - Go to: https://github.com/settings/tokens/new
   - Note: "MCP Server - Full access"
   - Expiration: 90 days (or your preference)
   - Scopes: Select **`repo`** (full control - includes releases)
   - Generate token

2. **Add to environment:**

```bash
   export GITHUB_TOKEN="ghp_your_token_here"
```

3. **Automatic fallback:**

   - Server tries GitHub App first
   - If releases permission missing → automatically uses PAT
   - No code changes needed!

**Verification:**

```bash
# Check which auth method is active
curl http://localhost:3000/health

# Should show:
# "authentication": {
#   "method": "pat",  # ← Using PAT fallback
#   "pat_configured": true,
#   "app_configured": true
# }
```

**When to use PAT fallback:**

- ✅ Release operations (create, update, delete)
- ✅ Any operation failing with "Permission denied" despite correct GitHub App config
- ✅ When you need permissions not available in GitHub App UI

**Security Note:** PATs are user-scoped (not app-scoped) and more powerful. Keep them secure and rotate regularly.

### 3. Create the App

1. Click "Create GitHub App"
2. Note your **App ID** (shown at top of page)

### 4. Generate Private Key

1. Scroll down to "Private keys"
2. Click "Generate a private key"
3. A `.pem` file will download automatically
4. **Save this file securely!** You can only download it once
5. Move it to a safe location:

   ```bash
   # Example locations:
   # Linux/Mac: ~/github-mcp-key.pem
   # Windows: C:\Users\YourName\github-mcp-key.pem
   ```

### 5. Install the App

1. Click "Install App" in the left sidebar
2. Choose your account (personal or organization)
3. Choose repository access:

   - **All repositories** - App can access all your repos
   - **Only select repositories** - Choose specific repos

4. Click "Install"
5. **Note the Installation ID** from the URL:

   ```
   https://github.com/settings/installations/12345678
                                              ^^^^^^^^
                                              This is your Installation ID
   ```

### 6. Configure MCP Server

Create a `.env` file in your project:

```bash
# GitHub App Authentication
GITHUB_APP_ID=123456                    # From step 3
GITHUB_APP_INSTALLATION_ID=789012       # From step 5
GITHUB_APP_PRIVATE_KEY_PATH=/path/to/github-mcp-key.pem  # From step 4

# Optional: PAT fallback
GITHUB_TOKEN=ghp_your_token_here
```

### 7. Test the Setup

Restart your MCP server and check the logs:

```bash
# Enable debug logging
GITHUB_MCP_DEBUG_AUTH=true python -m github_mcp
```

You should see:

```
🔍 AUTH DIAGNOSTIC:
  Using GitHub App authentication
  Token type: ghs_... (installation token)
```

## Troubleshooting

### "Invalid JWT" Error

- Check your App ID is correct
- Ensure private key file path is correct
- Verify file permissions (should be readable)

### "Installation not found" Error

- Check Installation ID is correct
- Verify app is installed on your account
- Try reinstalling the app

### "Not Found" or "403" Errors

- Verify app has correct permissions
- Check app is installed on the repository you're accessing
- For organizations, verify app is approved

### Still Using PAT Instead of App

- Check environment variables are set correctly
- Restart MCP server completely
- Enable debug logging to see which auth is used

## For Organizations

### Enterprise Setup

1. Organization owner installs the app
2. Choose "Only select repositories"
3. Add specific repos as needed
4. Team members use the shared Installation ID

### Security Best Practices

- Use "Only select repositories" for granular control
- Rotate private keys periodically
- Monitor app usage in organization audit logs
- Review app permissions regularly

## Need Help?

- Check `env.example` for configuration examples
- Enable debug logging: `GITHUB_MCP_DEBUG_AUTH=true`
- Open an issue: https://github.com/crypto-ninja/github-mcp-server/issues

