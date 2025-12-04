# Advanced: Create Your Own GitHub App

> ⚠️ **This guide is for power users!**
> 
> Most users should use a **Personal Access Token (PAT)** - it's simpler and works great.
> See the [Quick Start in README](../README.md#quick-start) for PAT setup.
>
> Only follow this guide if you need:
> - Higher rate limits (15,000 vs 5,000 requests/hour)
> - Fine-grained repository permissions
> - Enterprise-level throughput for heavy automation

## Why Create Your Own GitHub App?

| Feature | Personal Access Token | Your Own GitHub App |
|---------|----------------------|---------------------|
| Rate Limit | 5,000/hour | 15,000/hour |
| Setup Time | 2 minutes | 15-20 minutes |
| Complexity | Simple | Advanced |
| Best For | Most users, local dev | Heavy automation, enterprise |

## Prerequisites

Before starting, ensure you have:

- GitHub account with admin access to target repositories
- Python 3.10+ installed
- Deno installed (for code execution)
- 15-20 minutes for setup

---

## Step 1: Create a GitHub App

## Required Permissions

For all **62 tools** to work with GitHub App authentication, configure these repository permissions:

### Repository Permissions

| Permission | Level | Required For |
|------------|-------|-------------|
| **Contents** | Read and write ✅ | Branch operations, file operations |
| **Issues** | Read and write ✅ | Issue operations |
| **Pull requests** | Read and write ✅ | PR operations |
| **Metadata** | Read-only ✅ | Repository information |
| **Workflows** | Read and write (optional) | GitHub Actions |

### Tools by Permission

**Contents (Read and write):**
- `github_list_branches`
- `github_create_branch`
- `github_get_branch`
- `github_delete_branch`
- `github_compare_branches`
- `github_create_file`
- `github_update_file`
- `github_delete_file`

**Issues (Read and write):**
- `github_create_issue`
- `github_update_issue`
- `github_list_issues`

**Pull requests (Read and write):**
- `github_create_pull_request`
- `github_merge_pull_request`
- `github_close_pull_request`
- `github_create_pr_review`

---

## Rate Limits Comparison

| Auth Method | Rate Limit | Use Case |
|------------|-----------|----------|
| **PAT (Personal Access Token)** | 5,000 requests/hour | Simple setup, personal projects |
| **GitHub App** | 15,000 requests/hour | Production, heavy usage ✅ |

GitHub App provides **3x better rate limits** - highly recommended for:
- CI/CD pipelines
- Multiple concurrent operations
- Heavy API usage
- Production environments

---

## Automatic Fallback

The server implements automatic auth fallback:

```
1. Try params.token (if provided explicitly)
2. If GITHUB_AUTH_MODE=app → Try GitHub App authentication
3. If App auth fails → Automatically fall back to PAT (GITHUB_TOKEN)
4. All paths have exception handling ✅
```

**This ensures tools always work** even if:
- GitHub App credentials are misconfigured
- App permissions are insufficient
- App auth has temporary issues

---

## Setup Steps

### Step 1: Create GitHub App

1. Go to: https://github.com/settings/apps/new
2. Fill in:
   - **GitHub App name**: Your app name (e.g., "My MCP Server")
   - **Homepage URL**: Your website or repo URL
   - **Webhook**: Uncheck "Active" (not needed for MCP)
3. Set **Repository permissions**:
   - Contents: Read and write
   - Issues: Read and write
   - Pull requests: Read and write
   - Metadata: Read-only
4. Click "Create GitHub App"
5. Note your **App ID** (shown at top of settings page)

### Step 2: Generate Private Key

1. Scroll to "Private keys" section
2. Click "Generate a private key"
3. Download the `.pem` file
4. Store it securely (e.g., `~/.github/my-app-private-key.pem`)

### Step 3: Install App on Repositories

1. Go to: https://github.com/settings/installations
2. Click "Install" next to your app
3. Select repositories to grant access
4. Note your **Installation ID** from the URL:
   `https://github.com/settings/installations/INSTALLATION_ID`

### Step 4: Configure Environment

Add to your `.env` file:

```bash
# GitHub App Configuration (Recommended - 15,000 requests/hour)
GITHUB_APP_ID=123456
GITHUB_APP_INSTALLATION_ID=12345678
GITHUB_APP_PRIVATE_KEY_PATH=/path/to/private-key.pem

# PAT Fallback (Required - 5,000 requests/hour)
GITHUB_TOKEN=ghp_your_personal_access_token

# Auth Mode (optional - defaults to trying App first)
GITHUB_AUTH_MODE=app
```

### Step 5: Restart MCP Server

Restart your MCP server to pick up the new configuration.

---

## Verification

### Test Script

Run the test script to verify configuration:

```bash
python test_github_app_auth.py
```

Expected output:
```
======================================================================
GITHUB APP AUTH TEST
======================================================================

GITHUB_APP_ID: ✅
GITHUB_APP_INSTALLATION_ID: ✅
GITHUB_APP_PRIVATE_KEY_PATH: ✅

🔧 Getting GitHub App token...
✅ Token obtained (length: 40)

📊 Rate Limit: 15000/hour
✅ Using GitHub App rate limits!

======================================================================
```

### Manual Verification

Check your rate limit in any tool response or use:

```typescript
// In execute_code
const info = await callMCPTool("github_get_repo_info", {
  owner: "your-org",
  repo: "your-repo"
});
// Check response headers for X-RateLimit-Limit
```

---

## Troubleshooting

### "App auth failed, falling back to PAT"

**Cause:** GitHub App authentication failed
**Solution:**
1. Check `GITHUB_APP_ID` is correct
2. Check `GITHUB_APP_INSTALLATION_ID` is correct
3. Check private key file exists and is readable
4. Verify app is installed on the target repositories

### "Rate limit: 5000/hour" (Expected 15000)

**Cause:** Using PAT instead of App auth
**Solution:**
1. Verify all GitHub App environment variables are set
2. Check private key file permissions
3. Ensure app has required permissions
4. Run `test_github_app_auth.py` for diagnostics

### Branch Operations Failing

**Cause:** Missing "Contents: Read and write" permission
**Solution:**
1. Go to: https://github.com/settings/apps
2. Edit your app
3. Change "Contents" from "Read-only" to "Read and write"
4. Go to: https://github.com/settings/installations
5. Accept the new permissions

### Permission Changes Not Taking Effect

After changing app permissions:
1. Go to: https://github.com/settings/installations
2. Find your app installation
3. Click "Accept new permissions"
4. Wait 1-2 minutes for propagation
5. Restart MCP server

---

## Security Best Practices

1. **Never commit private keys** - Add `*.pem` to `.gitignore`
2. **Use environment variables** - Don't hardcode credentials
3. **Minimum permissions** - Only grant what's needed
4. **Regular rotation** - Rotate PAT tokens periodically
5. **Audit access** - Review app installations regularly

---

## Related Documentation

- [Configuration Guide](./CONFIGURATION.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Quick Start](./QUICKSTART.md)

---

*Last updated: November 2025 (v2.4.0)*
