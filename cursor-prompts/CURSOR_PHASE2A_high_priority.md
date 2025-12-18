# Cursor Prompt: Phase 2A - High Priority Tools

## Overview
Update the most commonly used tools first. These 6 files cover the core functionality.

---

## 1. `src/github_mcp/tools/branches.py`

### Tool: `github_list_branches`
**Changes:** `per_page` → `limit`, add `response_format`

Find the Input model and update:
```python
# BEFORE
per_page: int = Field(default=30, ...)
page: int = Field(...)

# AFTER
limit: int = Field(default=10, ge=1, le=100, description="Maximum results (1-100)")
page: int = Field(default=1, ge=1, description="Page number")
response_format: str = Field(default="json", description="Output format: 'json', 'markdown', or 'compact'")
```

In the function, add at the end before return:
```python
from github_mcp.utils.compact_format import format_response

# Before returning
if params.response_format == "compact":
    result = format_response(result, "compact", "branch")
return result
```

---

## 2. `src/github_mcp/tools/issues.py`

### Tool: `github_list_issues`
**Changes:** Add `response_format` (already has `limit`)

Add to Input model:
```python
response_format: str = Field(default="json", description="Output format: 'json', 'markdown', or 'compact'")
```

In function, add compact handling:
```python
from github_mcp.utils.compact_format import format_response

if params.response_format == "compact":
    result = format_response(result, "compact", "issue")
```

---

## 3. `src/github_mcp/tools/pull_requests.py`

### Tools to update:
- `github_list_pull_requests` - add `response_format`
- `github_get_pr_details` - add `response_format`
- `github_get_pr_overview_graphql` - add `response_format`

Add to each Input model:
```python
response_format: str = Field(default="json", description="Output format: 'json', 'markdown', or 'compact'")
```

In each function, add compact handling with resource type "pr" or "pull_request".

---

## 4. `src/github_mcp/tools/releases.py`

### Tool: `github_list_releases`
**Changes:** `per_page` → `limit`

```python
# BEFORE
per_page: int = Field(default=30, ...)

# AFTER  
limit: int = Field(default=10, ge=1, le=100, description="Maximum results (1-100)")
response_format: str = Field(default="json", description="Output format: 'json', 'markdown', or 'compact'")
```

---

## 5. `src/github_mcp/tools/repositories.py`

### Tools to update:
- `github_list_repo_collaborators` - `per_page` → `limit`
- `github_list_repo_teams` - `per_page` → `limit`
- `github_get_repo_info` - add `response_format`

For list tools:
```python
limit: int = Field(default=10, ge=1, le=100, description="Maximum results (1-100)")
page: int = Field(default=1, ge=1, description="Page number")
response_format: str = Field(default="json", description="Output format: 'json', 'markdown', or 'compact'")
```

For get_repo_info:
```python
response_format: str = Field(default="json", description="Output format: 'json', 'markdown', or 'compact'")
```

---

## 6. `src/github_mcp/tools/users.py`

### Tools to update:
- `github_list_user_repos` - `per_page` → `limit`, add `response_format`
- `github_list_org_repos` - `per_page` → `limit`, add `response_format`
- `github_search_users` - `per_page` → `limit`, add `response_format`
- `github_get_authenticated_user` - add `response_format`

---

## Important: API Call Updates

When renaming `per_page` to `limit`, also update the GitHub API call:

```python
# BEFORE
response = await client.get(url, params={"per_page": params.per_page, "page": params.page})

# AFTER
response = await client.get(url, params={"per_page": params.limit, "page": params.page})
# Note: GitHub API still uses per_page, we just renamed our param
```

---

## Quick Test After Each File

```bash
# Test the specific module imports
python -c "from github_mcp.tools.branches import *; print('branches OK')"
python -c "from github_mcp.tools.issues import *; print('issues OK')"
python -c "from github_mcp.tools.pull_requests import *; print('pull_requests OK')"
python -c "from github_mcp.tools.releases import *; print('releases OK')"
python -c "from github_mcp.tools.repositories import *; print('repositories OK')"
python -c "from github_mcp.tools.users import *; print('users OK')"
```

---

When done, tell me "Phase 2A complete" and I'll give you Phase 2B (Actions, Security, etc).
