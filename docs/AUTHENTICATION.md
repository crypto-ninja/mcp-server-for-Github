# Authentication Guide

## Quick Start (Recommended)

For most users, a Personal Access Token (PAT) is the simplest setup:

1. Go to GitHub → Settings → Developer settings → **Personal access tokens**.
2. Create a new token with the required scopes (see below).
3. Set the environment variable:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

**Rate Limit:** 5,000 requests/hour

---

## Required Token Scopes

| Scope        | Purpose                     |
|-------------|-----------------------------|
| `repo`      | Full repository access      |
| `read:org`  | Read organization data      |
| `read:user` | Read user profile data      |
| `workflow`  | GitHub Actions access       |

> You can often start with just `repo` for personal projects and expand scopes as needed.

---

## Advanced: GitHub App Authentication

For higher rate limits (15,000 req/hour), power users can create their own GitHub App.

**See:** [Advanced GitHub App Setup](ADVANCED_GITHUB_APP.md)

GitHub App auth is optional but recommended for:

- CI/CD pipelines
- Heavy automation and large organizations
- High-concurrency or bulk operations

---

## Authentication Fallback Order

The server resolves authentication in this order:

1. **Explicit token** – `token` parameter passed directly to a tool.
2. **GitHub App** – When `GITHUB_AUTH_MODE=app` and App credentials are configured.
3. **Personal Access Token** – `GITHUB_TOKEN` environment variable.

This matches the behavior implemented in `auth/github_app.py` and `github_mcp.py`.

---

## Environment Variables

| Variable                      | Required | Description                                   |
|-------------------------------|----------|-----------------------------------------------|
| `GITHUB_TOKEN`                | Yes*     | Personal Access Token                         |
| `GITHUB_AUTH_MODE`           | No       | Set to `app` to prefer GitHub App auth        |
| `GITHUB_APP_ID`              | No       | GitHub App ID (for App auth)                  |
| `GITHUB_APP_INSTALLATION_ID` | No       | App Installation ID                           |
| `GITHUB_APP_PRIVATE_KEY_PATH`| No       | Path to App private key (`.pem` file)         |

`*` Required unless you are relying solely on GitHub App authentication.

---

## Rate Limits Comparison

| Auth Method | Rate Limit    | Setup Time   | Recommended For          |
|------------|---------------|-------------|--------------------------|
| PAT        | 5,000/hour    | ~2 minutes  | Most users, local dev    |
| GitHub App | 15,000/hour   | 15–20 mins  | Power users, CI/CD, prod |

Use PAT first to get started quickly, then add GitHub App when you need more throughput.


