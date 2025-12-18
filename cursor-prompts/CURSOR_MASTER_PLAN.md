# Tool Standardization - Master Plan for v2.5.6

## Quick Summary

**Goal:** Standardize 36 tools for AI optimization
- Rename `per_page` → `limit` (23 tools)
- Add `response_format` with "compact" option (17 tools)
- Add pagination to 2 tools missing it
- Default limit = 10 (was 20-30)
- No backward compatibility needed (no users yet!)

---

## Execution Order

### Phase 1: Create Utility
📄 `CURSOR_PHASE1_compact_format.md`
- Create `src/github_mcp/utils/compact_format.py`
- ~5 minutes

### Phase 2A: High Priority Tools (6 files)
📄 `CURSOR_PHASE2A_high_priority.md`
- branches.py, issues.py, pull_requests.py
- releases.py, repositories.py, users.py
- ~20 minutes

### Phase 2B: Remaining Tools (9 files)
📄 `CURSOR_PHASE2B_remaining.md`
- actions.py, security.py, gists.py, discussions.py
- notifications.py, projects.py, labels.py
- stargazers.py, file_operations.py
- ~25 minutes

### Phase 3: TypeScript Definitions
📄 `CURSOR_PHASE3_tool_definitions.md`
- Update tool-definitions.ts
- ~15 minutes

### Phase 4: Tests
📄 `CURSOR_PHASE4_tests.md`
- Update all tests to use `limit`
- Add compact format tests
- ~15 minutes

---

## After All Phases Complete

### 1. Run Full Test Suite
```bash
pytest tests/ -v
# Should pass ~320 tests
```

### 2. Update Version
In `pyproject.toml`, ensure version is `2.5.6`

### 3. Update CHANGELOG.md
Add entry for standardization:
```markdown
## [2.5.6] - 2024-12-17

### Added
- Compact response format (`response_format: "compact"`) for 80%+ token reduction
- Standardized pagination with `limit` parameter (replaces `per_page`)

### Changed
- Default limit reduced to 10 (was 20-30) for better performance
- All list tools now support consistent pagination

### Fixed
- Buffer overflow prevention with lower default limits
- Consistent parameter naming across all tools

### Breaking Changes
- `per_page` parameter renamed to `limit` (no users affected)
```

### 4. Commit
```bash
git add -A
git commit -m "feat: Standardize pagination and add compact response format (#35)

- Rename per_page → limit across 23 tools
- Add response_format param to 17 tools  
- Add limit+page to 2 tools missing pagination
- Implement compact format for 80%+ token reduction
- Default limit lowered to 10 (was 20-30)

Closes #35"
```

### 5. Merge & Release
```bash
git checkout main
git merge refactor/consolidate-deno-executor  # Include consolidation too
git push origin main
git tag v2.5.6
git push origin v2.5.6  # Triggers PyPI publish
```

---

## Files Modified Summary

| Category | Files | Changes |
|----------|-------|---------|
| New utility | 1 | compact_format.py |
| Python tools | 15 | All tool files |
| TypeScript | 1 | tool-definitions.ts |
| Tests | ~15 | Test files |
| Config | 1 | pyproject.toml |
| Docs | 1 | CHANGELOG.md |

---

## Token Reduction Examples

| Resource | Full JSON | Compact | Reduction |
|----------|-----------|---------|-----------|
| Commit | ~3000 chars | ~120 chars | 96% |
| Issue | ~2500 chars | ~150 chars | 94% |
| Repo | ~4000 chars | ~180 chars | 95% |
| User | ~1500 chars | ~100 chars | 93% |
| Branch | ~800 chars | ~60 chars | 92% |

---

## Checklist

- [ ] Phase 1: compact_format.py created
- [ ] Phase 2A: High priority tools updated  
- [ ] Phase 2B: Remaining tools updated
- [ ] Phase 3: tool-definitions.ts updated
- [ ] Phase 4: Tests updated and passing
- [ ] Version bumped to 2.5.6
- [ ] CHANGELOG.md updated
- [ ] All tests pass (320+)
- [ ] Committed to branch
- [ ] Merged to main
- [ ] Tagged v2.5.6
- [ ] Issue #35 closed

---

Good luck! 🚀
