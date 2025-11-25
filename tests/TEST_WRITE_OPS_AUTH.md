# Write Operations Authentication Tests

## Overview

This document describes the test suite for write operations authentication validation.

## Test Files

### 1. `test_write_operations_auth.py` (Unit Tests - ✅ Adds to Coverage)

**Location:** `tests/test_write_operations_auth.py`

**Purpose:** Unit tests that verify authentication validation logic using mocked API calls.

**Coverage:** ✅ **YES** - These tests use pytest and mocks, so they:
- Are automatically discovered by pytest
- Add to test coverage metrics
- Run fast (no real API calls)
- Can be run in CI/CD

**Tests:** 12 tests covering all 10 fixed write operations:
- `test_github_create_file_no_auth` - Verifies auth validation
- `test_github_create_file_with_auth` - Verifies success path
- `test_github_update_file_no_auth`
- `test_github_delete_file_no_auth`
- `test_github_create_release_no_auth`
- `test_github_update_release_no_auth`
- `test_github_create_repository_no_auth`
- `test_github_delete_repository_no_auth`
- `test_github_update_repository_no_auth`
- `test_github_transfer_repository_no_auth`
- `test_github_archive_repository_no_auth`
- `test_github_merge_pull_request_no_auth`

**Run:** `pytest tests/test_write_operations_auth.py -v`

---

### 2. `test_write_operations_integration.py` (Integration Tests - ⚠️ Manual Only)

**Location:** `tests/test_write_operations_integration.py`

**Purpose:** End-to-end integration tests that make real GitHub API calls.

**Coverage:** ❌ **NO** - This is a manual integration test script that:
- Makes real API calls (requires authentication)
- Tests actual GitHub API behavior
- Useful for validation but not part of automated test suite
- Should be run manually before releases

**Tests:** 10 integration tests covering:
- File operations (create, update, delete)
- Release operations (create, update)
- Repository operations (update, archive, delete)
- Authentication error handling

**Run:** `python tests/test_write_operations_integration.py`

**Note:** This script requires:
- Valid GitHub authentication (PAT or GitHub App)
- Test repository access
- Manual cleanup of test artifacts

---

## Coverage Impact

### Before Adding Tests
- Coverage: ~63% (214 tests)
- Missing: Authentication validation paths in write operations

### After Adding Tests
- Coverage: **Improved** (12 new tests)
- New Coverage: Authentication validation logic in 10 write operations
- Total Tests: **226 tests** (214 + 12)

---

## Running Tests

### Run Unit Tests (Fast, Mocked)
```bash
# Run all auth validation tests
pytest tests/test_write_operations_auth.py -v

# Run with coverage
pytest tests/test_write_operations_auth.py --cov=github_mcp --cov-report=term

# Run all tests
pytest tests/ -v
```

### Run Integration Tests (Manual, Real API)
```bash
# Requires authentication configured
python tests/test_write_operations_integration.py
```

---

## Test Strategy

### Unit Tests (test_write_operations_auth.py)
- ✅ Fast execution
- ✅ No external dependencies
- ✅ Adds to coverage
- ✅ Can run in CI/CD
- ✅ Tests authentication validation logic

### Integration Tests (test_write_operations_integration.py)
- ⚠️ Requires real API access
- ⚠️ Slower execution
- ⚠️ Manual cleanup needed
- ✅ Validates end-to-end behavior
- ✅ Useful for pre-release validation

---

## What Gets Tested

### Authentication Validation
All tests verify that when `_get_auth_token_fallback()` returns `None`:
1. The function returns a JSON error response
2. Error message is clear: "Authentication required"
3. Success flag is `False`
4. No API calls are made

### Success Path
Tests also verify that with valid authentication:
1. API calls are made correctly
2. Success responses are formatted properly

---

## Adding New Tests

When adding new write operations, add tests to both:

1. **Unit Test** (`test_write_operations_auth.py`):
   ```python
   @pytest.mark.asyncio
   @patch('github_mcp._get_auth_token_fallback')
   async def test_new_operation_no_auth(self, mock_get_token):
       mock_get_token.return_value = None
       # ... test logic
   ```

2. **Integration Test** (`test_write_operations_integration.py`):
   ```python
   async def test_new_operation():
       # ... real API call test
   ```

---

## Summary

- ✅ **Unit tests** (`test_write_operations_auth.py`) are in `tests/` folder
- ✅ **Unit tests** add to coverage (12 new tests)
- ✅ **Unit tests** run automatically with pytest
- ⚠️ **Integration tests** are manual validation scripts
- ✅ **All 10 fixed write operations** have test coverage

**Status:** Ready for v2.3.0 release! 🚀

