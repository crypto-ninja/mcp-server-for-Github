# Tool Response Format Audit Results

## Summary

- **Total Tools Audited:** 46 internal tools
- **Tools Returning JSON:** ~25 tools
- **Tools Returning Formatted Strings:** ~15 tools  
- **Tools Needing Fix:** ~15 tools (write operations returning strings)
- **Tools with Mixed Responses:** ~6 tools (conditional JSON/string)

## Critical Issues Found

### ❌ HIGH PRIORITY - Write Operations Returning Strings

These tools return formatted strings instead of JSON, making programmatic use difficult:

| Tool | Line | Issue | Priority |
|------|------|-------|----------|
| `github_create_issue` | 2461 | Returns formatted markdown string | 🔴 HIGH |
| `github_create_pull_request` | 3946 | Returns formatted markdown string | ✅ FIXED |
| `github_create_file` | 4969 | Returns formatted markdown string | 🔴 HIGH |
| `github_update_file` | ~5050 | Returns formatted markdown string | 🔴 HIGH |
| `github_create_release` | ~4720 | Returns formatted markdown string | 🔴 HIGH |
| `github_update_release` | ~4850 | Returns formatted markdown string | 🔴 HIGH |
| `github_merge_pull_request` | 5708 | Returns formatted markdown string | 🔴 HIGH |
| `github_close_pull_request` | ~5780 | Returns formatted markdown string | 🔴 HIGH |
| `github_create_pr_review` | ~5900 | Returns formatted markdown string | 🔴 HIGH |
| `github_create_repository` | 5489 | Returns formatted string | 🔴 HIGH |
| `github_delete_repository` | 5520 | Returns formatted string | 🔴 HIGH |
| `github_update_repository` | 5556 | Returns formatted string | 🔴 HIGH |
| `github_transfer_repository` | 5595 | Returns formatted string | 🔴 HIGH |
| `github_archive_repository` | 5633 | Returns formatted string | 🔴 HIGH |
| `github_create_branch` | 3102 | ✅ Returns JSON | ✅ GOOD |

### ⚠️ MEDIUM PRIORITY - Error Handling Inconsistency

Many tools use `_handle_api_error()` which returns formatted strings instead of JSON:

| Tool | Line | Issue | Priority |
|------|------|-------|----------|
| Most write operations | Various | Errors return strings via `_handle_api_error()` | 🟡 MEDIUM |

### ✅ GOOD - Tools Returning JSON

These tools already return proper JSON responses:

| Tool | Line | Returns | Notes |
|------|------|---------|-------|
| `github_list_issues` | ~2305 | `json.dumps(data)` | ✅ Full API response |
| `github_get_repo_info` | ~2171 | `json.dumps(data)` | ✅ Full API response |
| `github_list_pull_requests` | ~3386 | `json.dumps(data)` | ✅ Full API response |
| `github_list_releases` | ~4487 | `json.dumps(data)` | ✅ Full API response |
| `github_list_branches` | ~2929 | `json.dumps(data)` | ✅ Full API response |
| `github_create_branch` | 3102 | `json.dumps(data)` | ✅ Full API response |
| `github_get_branch` | ~3124 | `json.dumps(data)` | ✅ Full API response |
| `github_delete_branch` | ~3203 | `json.dumps(data)` | ✅ Full API response |
| `github_compare_branches` | ~3293 | `json.dumps(data)` | ✅ Full API response |
| `github_search_repositories` | ~2609 | `json.dumps(data)` | ✅ Full API response |
| `github_search_code` | ~4236 | `json.dumps(data)` | ✅ Full API response |
| `github_search_issues` | ~4360 | `json.dumps(data)` | ✅ Full API response |
| `github_list_commits` | ~2808 | `json.dumps(data)` | ✅ Full API response |
| `github_list_workflows` | ~3695 | `json.dumps(data)` | ✅ Full API response |
| `github_get_workflow_runs` | ~3768 | `json.dumps(data)` | ✅ Full API response |
| `github_list_repo_contents` | ~3566 | `json.dumps(data)` | ✅ Full API response |
| `github_get_file_content` | ~2709 | Conditional (JSON/Markdown) | ⚠️ Has response_format |
| `github_grep` | ~1701 | Conditional (JSON/Markdown) | ⚠️ Has response_format |
| `github_read_file_chunk` | ~1920 | Conditional (JSON/Markdown) | ⚠️ Has response_format |

## Patterns Found

### Pattern 1: Formatted Success Messages (❌ BAD)

Found in ~15 write operations:

```python
# BAD PATTERN
result = f"""✅ Issue Created Successfully!

**Issue:** #{data['number']} - {data['title']}
**State:** {data['state']}
**URL:** {data['html_url']}
...
"""
return result  # ❌ Returns string, not JSON
```

**Fix:** Replace with:
```python
# GOOD PATTERN
return json.dumps(data, indent=2)  # ✅ Returns full GitHub API response
```

### Pattern 2: Error Handling with Strings (❌ BAD)

Found in most tools:

```python
# BAD PATTERN
except Exception as e:
    return _handle_api_error(e)  # ❌ Returns formatted string
```

**Fix:** Replace with:
```python
# GOOD PATTERN
except Exception as e:
    error_info = {
        "success": False,
        "error": str(e),
        "type": type(e).__name__
    }
    if isinstance(e, httpx.HTTPStatusError):
        error_info["status_code"] = e.response.status_code
        try:
            error_body = e.response.json()
            error_info["message"] = error_body.get("message", "Unknown error")
            error_info["errors"] = error_body.get("errors", [])
        except:
            error_info["message"] = str(e)
    return json.dumps(error_info, indent=2)  # ✅ Returns JSON
```

### Pattern 3: Conditional Responses (⚠️ ACCEPTABLE)

Found in display-focused tools:

```python
# ACCEPTABLE PATTERN (for display tools)
if params.response_format == ResponseFormat.JSON:
    return json.dumps(result, indent=2)
else:
    return f"# Markdown formatted output\n\n..."  # For human readability
```

**Decision:** Keep this pattern for tools like `github_get_file_content`, `github_grep` where human-readable output is useful.

## Action Items

### High Priority (Breaks programmatic use)

1. [x] ✅ Fix `github_create_pull_request` - Returns JSON now
2. [ ] ❌ Fix `github_create_issue` - Returns formatted string
3. [ ] ❌ Fix `github_create_file` - Returns formatted string
4. [ ] ❌ Fix `github_update_file` - Returns formatted string
5. [ ] ❌ Fix `github_create_release` - Returns formatted string
6. [ ] ❌ Fix `github_update_release` - Returns formatted string
7. [ ] ❌ Fix `github_merge_pull_request` - Returns formatted string
8. [ ] ❌ Fix `github_close_pull_request` - Returns formatted string
9. [ ] ❌ Fix `github_create_pr_review` - Returns formatted string
10. [ ] ❌ Fix `github_create_repository` - Returns formatted string
11. [ ] ❌ Fix `github_delete_repository` - Returns formatted string
12. [ ] ❌ Fix `github_update_repository` - Returns formatted string
13. [ ] ❌ Fix `github_transfer_repository` - Returns formatted string
14. [ ] ❌ Fix `github_archive_repository` - Returns formatted string

### Medium Priority (Inconsistent errors)

1. [ ] Standardize error responses across all tools
2. [ ] Update `_handle_api_error()` to return JSON (or create new helper)
3. [ ] Add `status_code` to all error responses

### Low Priority (Enhancement)

1. [ ] Add `response_format` parameter to more display-focused tools
2. [ ] Document which tools return markdown vs JSON
3. [ ] Create helper function for structured error responses

## Recommendations

### 1. All Write Operations Should Return JSON

**Rationale:** Write operations (create, update, delete) are typically used programmatically. The full GitHub API response contains all necessary information (IDs, URLs, status, etc.) that calling code needs.

**Implementation:**
- Replace formatted strings with `return json.dumps(data, indent=2)`
- This returns the complete GitHub API response object

### 2. All Errors Should Be Structured JSON

**Rationale:** Programmatic error handling requires structured data, not formatted strings.

**Implementation:**
- Create helper function `_format_error_json(e: Exception) -> str`
- Returns JSON with: `success`, `error`, `type`, `status_code`, `message`, `errors`
- Replace all `return _handle_api_error(e)` with structured JSON

### 3. Read Operations Can Have Conditional Format

**Rationale:** Some read operations benefit from human-readable markdown (e.g., file content display).

**Implementation:**
- Keep `response_format` parameter for display-focused tools
- Default to JSON for programmatic use
- Markdown for human readability

### 4. Success Responses Should Be Full API Response

**Rationale:** Don't summarize - return everything GitHub gives us. The calling code can format it as needed.

**Implementation:**
- Never return `{"success": True}` as a summary
- Always return the full GitHub API response object
- Include all fields: `number`, `html_url`, `state`, `title`, etc.

## Testing Plan

After fixes, test each category:

1. **Repository Tools:** Create, update, delete - should return JSON
2. **Issue Tools:** Create, update - should return JSON
3. **PR Tools:** Create, merge, close, review - should return JSON
4. **File Tools:** Create, update, delete - should return JSON
5. **Release Tools:** Create, update - should return JSON
6. **Branch Tools:** Already return JSON ✅

Test with:
```typescript
const result = await callMCPTool("github_create_issue", {...});
const data = JSON.parse(result);
console.log(data.number);  // Should work without regex!
```

## Next Steps

1. ✅ Fix `github_create_pull_request` (DONE)
2. Fix remaining 13 write operations
3. Standardize error handling
4. Test all fixes
5. Update CHANGELOG
6. Commit to feature branch

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Status:** IN PROGRESS

**Progress:** 1/14 write operations fixed (7%)

**Estimated Time:** 2-3 hours to fix all remaining tools


