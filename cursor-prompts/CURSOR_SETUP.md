# Cursor Setup: Tool Standardization for v2.5.6

## Context

You're working on the GitHub MCP Server - a tool built FOR AI agents (Claude) to interact with GitHub. The primary user of these tools is Claude itself, so they need to be consistent and optimized for AI usage.

**Issue:** #35 - Standardize pagination and add compact response format
**Branch:** `feat/tool-standardization` (already created on remote)
**Goal:** Make all 36 tools consistent and AI-optimized

## Problems We're Fixing

1. **Inconsistent params:** Some tools use `per_page`, others use `limit`, others use `max_results`
2. **No compact output:** Tools return massive JSON responses that waste tokens
3. **High defaults:** Default limits of 20-30 cause buffer overflows

## The Solution

1. Standardize on `limit` + `page` for all list tools
2. Add `response_format` param with "compact" option (80%+ token reduction)
3. Default `limit` to 10

## Your Task

I've added prompt files in `cursor-prompts/` folder. Execute them in order:

1. **Phase 1:** `CURSOR_PHASE1_compact_format.md` - Create utility (~5 min)
2. **Phase 2A:** `CURSOR_PHASE2A_high_priority.md` - Core tools (~20 min)
3. **Phase 2B:** `CURSOR_PHASE2B_remaining.md` - Other tools (~25 min)
4. **Phase 3:** `CURSOR_PHASE3_tool_definitions.md` - TypeScript (~15 min)
5. **Phase 4:** `CURSOR_PHASE4_tests.md` - Tests (~15 min)

**Master checklist:** `CURSOR_MASTER_PLAN.md`

## Git Workflow

We're following proper PR workflow:

```bash
# Make sure you're on the feature branch
git checkout feat/tool-standardization

# After completing each phase, commit:
git add -A
git commit -m "feat: <description> (#35)"

# Push periodically:
git push origin feat/tool-standardization
```

**Commit message format:**
- `feat: Add compact_format.py utility (#35)`
- `feat: Standardize pagination in core tools (#35)`
- `feat: Update tool-definitions.ts (#35)`
- `test: Update tests for new param names (#35)`

## Key Files

| Type | Location |
|------|----------|
| Python tools | `src/github_mcp/tools/*.py` |
| TypeScript defs | `src/github_mcp/deno_executor/tool-definitions.ts` |
| Tests | `tests/*.py` |
| New utility | `src/github_mcp/utils/compact_format.py` (create this) |

## Quick Reference

### Standard List Tool Params:
```python
limit: int = Field(default=10, ge=1, le=100, description="Maximum results (1-100)")
page: int = Field(default=1, ge=1, description="Page number")
response_format: str = Field(default="json", description="Output format: 'json', 'markdown', or 'compact'")
```

### In API calls (GitHub still uses per_page):
```python
response = await client.get(url, params={"per_page": params.limit, "page": params.page})
```

## Start

First, make sure you're on the right branch:
```bash
git fetch origin
git checkout feat/tool-standardization
```

Then read and execute `cursor-prompts/CURSOR_PHASE1_compact_format.md`

Let's go! 🚀
