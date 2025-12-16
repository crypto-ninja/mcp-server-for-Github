# GitHub API Parameter Audit

**Date:** 2025-12-11  
**Version:** 2.5.4  
**Tools Audited:** 6/109 (High-Priority Core Operations)  
**Status:** Initial Audit Complete

---

## Summary

- **Tools Audited:** 6 high-priority tools
- **Missing Parameters Found:** 15+ parameters across 6 tools
- **Parameters Added:** 12 (3 in github_create_release + 9 in Phase 1 implementation)
- **Priority Breakdown:**
  - **Must Have:** 8 parameters
  - **Nice to Have:** 7+ parameters

---

## Findings by Category

### Issues

| Tool | Current Params | Missing Params | Priority | Status |
|------|----------------|----------------|----------|--------|
| `github_create_issue` | owner, repo, title, body, labels, assignees, token | `milestone` (int) | **Must Have** | ✅ DONE |
| `github_update_issue` | owner, repo, issue_number, state, title, body, labels, assignees, milestone, token | `state_reason` (str: "completed", "not_planned", "reopened") | **Nice to Have** | TODO |
| `github_list_issues` | owner, repo, state, limit, page, token, response_format | ✅ Complete | - | ✅ |

**Notes:**
- `milestone` is commonly used for project management
- `state_reason` helps distinguish why an issue was closed (completed vs not planned)

---

### Pull Requests

| Tool | Current Params | Missing Params | Priority | Status |
|------|----------------|----------------|----------|--------|
| `github_create_pull_request` | owner, repo, title, head, base, body, draft, maintainer_can_modify, token | ✅ Complete | - | ✅ |
| `github_merge_pull_request` | owner, repo, pull_number, merge_method, commit_title, commit_message, token | `sha` (str) - ensures HEAD hasn't changed | **Must Have** | ✅ DONE |
| `github_update_pull_request` | Need to check | TBD | TBD | TODO |

**Notes:**
- `sha` parameter prevents race conditions when merging PRs that may have new commits

---

### Releases

| Tool | Current Params | Missing Params | Priority | Status |
|------|----------------|----------------|----------|--------|
| `github_create_release` | owner, repo, tag_name, name, body, draft, prerelease, target_commitish, **generate_release_notes**, **discussion_category_name**, **make_latest**, token | ✅ Complete | - | ✅ |
| `github_update_release` | owner, repo, release_id, tag_name, name, body, draft, prerelease, token | `generate_release_notes`, `discussion_category_name`, `make_latest` | **Nice to Have** | TODO |
| `github_list_releases` | owner, repo, per_page, page, token, response_format | ✅ Complete | - | ✅ |
| `github_get_release` | owner, repo, tag, token, response_format | ✅ Complete | - | ✅ |

**Notes:**
- `update_release` should support the same advanced params as `create_release` for consistency

---

### Repositories

| Tool | Current Params | Missing Params | Priority | Status |
|------|----------------|----------------|----------|--------|
| `github_create_repository` | owner, name, description, private, auto_init, gitignore_template, license_template, token | `allow_squash_merge` (bool), `allow_merge_commit` (bool), `allow_rebase_merge` (bool), `delete_branch_on_merge` (bool), `allow_auto_merge` (bool), `allow_update_branch` (bool), `squash_merge_commit_title` (str), `squash_merge_commit_message` (str) | **Must Have** | ✅ DONE |
| `github_update_repository` | owner, repo, name, description, homepage, private, has_issues, has_projects, has_wiki, default_branch, archived, token | Same merge-related params as create | **Must Have** | ✅ DONE |
| `github_get_repo_info` | owner, repo, token, response_format | ✅ Complete | - | ✅ |

**Notes:**
- Merge settings are critical for repository configuration
- Many teams need to control merge methods and auto-merge behavior

---

### Files

| Tool | Current Params | Missing Params | Priority | Status |
|------|----------------|----------------|----------|--------|
| `github_create_file` | owner, repo, path, content, message, branch, token | `committer` (object: name, email), `author` (object: name, email) | **Nice to Have** | TODO |
| `github_update_file` | owner, repo, path, content, message, sha, branch, token | `committer` (object: name, email), `author` (object: name, email) | **Nice to Have** | TODO |
| `github_delete_file` | owner, repo, path, message, sha, branch, token | `committer` (object: name, email), `author` (object: name, email) | **Nice to Have** | TODO |

**Notes:**
- `committer`/`author` useful for CI/CD where you want specific attribution
- Less critical for most use cases

---

### Branches

| Tool | Current Params | Missing Params | Priority | Status |
|------|----------------|----------------|----------|--------|
| `github_create_branch` | owner, repo, branch, from_ref, token | ✅ Complete | - | ✅ |
| `github_delete_branch` | owner, repo, branch, token | ✅ Complete | - | ✅ |
| `github_list_branches` | owner, repo, protected, per_page, token, response_format | ✅ Complete | - | ✅ |
| `github_get_branch` | owner, repo, branch, token, response_format | ✅ Complete | - | ✅ |
| `github_compare_branches` | owner, repo, base, head, token, response_format | ✅ Complete | - | ✅ |

**Notes:**
- Branch operations appear complete

---

## Priority Implementation Plan

### Phase 1: Must Have (High Priority)

1. **`github_create_issue`** - Add `milestone` parameter
2. **`github_merge_pull_request`** - Add `sha` parameter
3. **`github_create_repository`** - Add merge-related parameters (8 params)
4. **`github_update_repository`** - Add merge-related parameters (8 params)

**Estimated Impact:** 4 tools, 10 new parameters

---

### Phase 2: Nice to Have (Medium Priority)

1. **`github_update_issue`** - Add `state_reason` parameter
2. **`github_update_release`** - Add 3 params (generate_release_notes, discussion_category_name, make_latest)
3. **File operations** - Add `committer`/`author` objects (3 tools)

**Estimated Impact:** 5 tools, 6 new parameters

---

## Implementation Checklist

For each parameter addition:

- [ ] Update Pydantic model in `src/github_mcp/models/inputs.py`
- [ ] Update function in `src/github_mcp/tools/<category>.py`
- [ ] Update TypeScript definitions in `deno_executor/tool-definitions.ts`
- [ ] Add/update tests in `tests/test_individual_tools.py`
- [ ] Update CHANGELOG.md
- [ ] Run quality checks (ruff, mypy, pytest)
- [ ] Verify against GitHub API docs

---

## Next Steps

1. ✅ Complete audit of high-priority tools
2. ⏳ Implement Phase 1 (Must Have) parameters
3. ⏳ Implement Phase 2 (Nice to Have) parameters
4. ⏳ Audit remaining 103 tools (lower priority categories)

---

## References

- [GitHub REST API - Issues](https://docs.github.com/en/rest/issues/issues)
- [GitHub REST API - Pull Requests](https://docs.github.com/en/rest/pulls/pulls)
- [GitHub REST API - Repositories](https://docs.github.com/en/rest/repos/repos)
- [GitHub REST API - Releases](https://docs.github.com/en/rest/releases/releases)
- [GitHub REST API - Contents](https://docs.github.com/en/rest/repos/contents)
