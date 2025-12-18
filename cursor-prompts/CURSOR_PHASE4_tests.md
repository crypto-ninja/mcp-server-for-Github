# Cursor Prompt: Phase 4 - Update Tests

## Task
Update test files to use `limit` instead of `per_page` and add compact format tests.

---

## Find & Replace in All Test Files

Search across `tests/` directory:
```
per_page= → limit=
per_page: → limit:
"per_page" → "limit"
```

---

## Test Files to Check

Run this to find all test files with per_page:
```bash
grep -r "per_page" tests/ --include="*.py"
```

Common files that will need updates:
- `tests/test_branches.py`
- `tests/test_issues.py`
- `tests/test_pull_requests.py`
- `tests/test_releases.py`
- `tests/test_repositories.py`
- `tests/test_users.py`
- `tests/test_actions.py`
- `tests/test_security.py`
- `tests/test_gists.py`
- `tests/test_discussions.py`
- `tests/test_notifications.py`
- `tests/test_projects.py`
- `tests/test_labels.py`
- `tests/test_stargazers.py`

---

## Add Compact Format Tests (Optional but Recommended)

Add to appropriate test files:

```python
@pytest.mark.asyncio
async def test_list_issues_compact_format():
    """Test compact format returns minimal fields."""
    result = await github_list_issues(
        ListIssuesInput(
            owner="test-owner",
            repo="test-repo",
            limit=5,
            response_format="compact"
        )
    )
    
    if isinstance(result, list) and len(result) > 0:
        # Compact should only have these fields
        expected_fields = {"number", "title", "state", "author", "created", "url"}
        actual_fields = set(result[0].keys())
        assert actual_fields == expected_fields, f"Unexpected fields: {actual_fields - expected_fields}"


@pytest.mark.asyncio
async def test_list_commits_compact_format():
    """Test compact format for commits."""
    result = await github_list_commits(
        ListCommitsInput(
            owner="test-owner",
            repo="test-repo",
            limit=3,
            response_format="compact"
        )
    )
    
    if isinstance(result, list) and len(result) > 0:
        expected_fields = {"sha", "message", "author", "date"}
        actual_fields = set(result[0].keys())
        assert actual_fields == expected_fields
```

---

## Run Full Test Suite

```bash
# Quick check - just import tests
pytest tests/ --collect-only

# Run all tests
pytest tests/ -v

# If any fail, fix them one at a time
pytest tests/test_branches.py -v
pytest tests/test_issues.py -v
# etc.
```

---

## Common Issues to Fix

### 1. Input model field names changed
```python
# BEFORE
ListBranchesInput(owner="x", repo="y", per_page=10)

# AFTER
ListBranchesInput(owner="x", repo="y", limit=10)
```

### 2. Mock responses may need updates
If tests mock GitHub API responses, they should still work since we're only changing our parameter names, not the API response structure.

### 3. New field validation
```python
# This should now fail (limit max is 100)
ListBranchesInput(owner="x", repo="y", limit=500)  # ValidationError
```

---

## Final Verification

```bash
# Full test suite
pytest tests/ -v --tb=short

# Should see all tests pass
# Expected: ~320 tests passed
```

---

When all tests pass, tell me "Phase 4 complete" and we'll run final verification and commit!
