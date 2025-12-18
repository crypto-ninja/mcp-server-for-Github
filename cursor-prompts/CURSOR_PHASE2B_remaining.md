# Cursor Prompt: Phase 2B - Remaining Tools

## Overview
Update the remaining tool files. Same pattern as Phase 2A.

---

## 7. `src/github_mcp/tools/actions.py`

### Tools to update:
- `github_list_workflows` - `per_page` → `limit`
- `github_list_workflow_run_jobs` - `per_page` → `limit`
- `github_list_workflow_run_artifacts` - `per_page` → `limit`
- `github_get_job_logs` - add `response_format`

For list tools, update Input models:
```python
limit: int = Field(default=10, ge=1, le=100, description="Maximum results (1-100)")
page: int = Field(default=1, ge=1, description="Page number")
response_format: str = Field(default="json", description="Output format: 'json', 'markdown', or 'compact'")
```

Resource types for compact: "workflow", "job", "artifact"

---

## 8. `src/github_mcp/tools/security.py`

### Tools to update (ALL need `per_page` → `limit`):
- `github_list_dependabot_alerts`
- `github_list_org_dependabot_alerts`
- `github_list_code_scanning_alerts`
- `github_list_code_scanning_analyses`
- `github_list_secret_scanning_alerts`
- `github_list_repo_security_advisories` (also add `response_format`)

All use resource type "alert" for compact format.

---

## 9. `src/github_mcp/tools/gists.py`

### Tools to update:
- `github_list_gists` - `per_page` → `limit`, add `response_format`
- `github_get_gist` - add `response_format`

Resource type: "gist"

---

## 10. `src/github_mcp/tools/discussions.py`

### Tools to update:
- `github_list_discussions` - `per_page` → `limit`
- `github_list_discussion_comments` - `per_page` → `limit`
- `github_list_discussion_categories` - ADD `limit` + `page` (currently has none)

Resource type: "discussion"

---

## 11. `src/github_mcp/tools/notifications.py`

### Tool: `github_list_notifications`
**Changes:** `per_page` → `limit`

Resource type: "notification"

---

## 12. `src/github_mcp/tools/projects.py`

### Tools to update:
- `github_list_repo_projects` - `per_page` → `limit`
- `github_list_org_projects` - `per_page` → `limit`
- `github_list_project_columns` - `per_page` → `limit`

Resource type: "project"

---

## 13. `src/github_mcp/tools/labels.py`

### Tool: `github_list_labels`
**Changes:** `per_page` → `limit`, add `response_format`

Resource type: "label"

---

## 14. `src/github_mcp/tools/stargazers.py`

### Tool: `github_list_stargazers`
**Changes:** `per_page` → `limit`, add `response_format`

Resource type: "stargazer"

---

## 15. `src/github_mcp/tools/file_operations.py` (or contents.py)

### Tools to update:
- `github_list_repo_contents` - ADD `limit` + `page` (currently has none)
- `github_get_file_content` - add `response_format`

Resource types: "content", "file"

---

## Standard Pattern Reminder

### Input Model:
```python
class ListSomethingInput(BaseModel):
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results (1-100)")
    page: int = Field(default=1, ge=1, description="Page number")
    response_format: str = Field(default="json", description="Output format: 'json', 'markdown', or 'compact'")
```

### Function:
```python
from github_mcp.utils.compact_format import format_response

async def list_something(params: ListSomethingInput):
    # ... existing code ...
    
    # GitHub API still uses per_page
    response = await client.get(url, params={"per_page": params.limit, "page": params.page})
    result = response.json()
    
    # Format response
    if params.response_format == "compact":
        return format_response(result, "compact", "resource_type")
    return result
```

---

## Quick Test

```bash
# Test all modules import correctly
python -c "
from github_mcp.tools.actions import *
from github_mcp.tools.security import *
from github_mcp.tools.gists import *
from github_mcp.tools.discussions import *
from github_mcp.tools.notifications import *
from github_mcp.tools.projects import *
from github_mcp.tools.labels import *
from github_mcp.tools.stargazers import *
print('All imports OK')
"
```

---

When done, tell me "Phase 2B complete" and I'll give you Phase 3 (tool-definitions.ts).
