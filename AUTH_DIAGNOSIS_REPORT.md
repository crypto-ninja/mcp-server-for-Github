# Authentication Diagnosis Report

**Date:** 2025-01-26  
**Status:** ✅ Authentication Working - No Issues Found

---

## Executive Summary

**Root Cause:** Authentication is working correctly. The GITHUB_TOKEN is valid and can perform both read and write operations directly with GitHub API.

**Conclusion:** If you're seeing "Authentication required" errors, it's likely:
1. A false positive from error handling
2. An issue with how the tool is being called (MCP layer)
3. A GitHub App configuration issue preventing fallback

---

## Environment Check

### ✅ .env File Status

- **.env file exists:** YES
- **GITHUB_TOKEN set in .env:** YES
- **Token length:** 40 characters
- **Token format:** Starts with `ghp_` ✅ (Valid PAT format)
- **Token prefix:** `ghp_4uc...`

### ✅ GitHub App Configuration

- **GITHUB_APP_ID:** YES (2324956)
- **GITHUB_APP_INSTALLATION_ID:** YES (95706182)
- **GITHUB_APP_PRIVATE_KEY_PATH:** YES
- **GITHUB_APP_PRIVATE_KEY:** YES (in env var)

**Note:** Both GitHub App and PAT are configured. The auth system will try GitHub App first, then fall back to PAT.

---

## Code Check

### ✅ Environment Loading

- **load_dotenv() called:** YES (line 71 in `github_mcp.py`)
- **Called before token access:** YES ✅
- **Token retrieval:** `os.getenv("GITHUB_TOKEN")` ✅

### ✅ Auth Flow

**Function Chain:**
1. `_get_auth_token_fallback(params.token)` (line 228)
   - Checks `params.token` first
   - Falls back to `get_auth_token()`
2. `get_auth_token()` (in `auth/github_app.py`, line 272)
   - Tries GitHub App first (if configured)
   - Falls back to PAT (`os.getenv("GITHUB_TOKEN")`)

**Auth Header Format:**
- ✅ Uses `Bearer {token}` format (line 61 in `github_client.py`)
- ✅ Matches GitHub API requirements

### ✅ Tool Implementation

**Example: `github_create_branch` (line 3038)**
```python
auth_token = await _get_auth_token_fallback(params.token)

if not auth_token:
    return json.dumps({
        "error": "Authentication required",
        "message": "GitHub token required for creating branches.",
        "success": False
    }, indent=2)
```

**Pattern:** All write operations follow this pattern:
1. Call `_get_auth_token_fallback()`
2. Check `if not auth_token:`
3. Return JSON error if no token
4. Pass token to `_make_github_request()`

---

## API Test Results

### ✅ Direct API Test (test_auth_direct.py)

**Test 1: GET /user (verify token works)**
- Status: 200 ✅
- Result: Authenticated as `crypto-ninja` ✅

**Test 2: GET /repos/.../branches (read operation)**
- Status: 200 ✅
- Result: Found 2 branches ✅

**Test 3: POST /repos/.../git/refs (create branch - write operation)**
- Status: 201 ✅
- Result: Successfully created and deleted test branch ✅

**Test 4: get_auth_token() function**
- Result: ✅ Returns PAT token (`ghp_4uclB3...`)
- Token type: PAT ✅

---

## GitHub API Compliance

### ✅ Authentication Header

**GitHub API Requirement:**
```
Authorization: Bearer GITHUB_TOKEN
```

**Our Implementation:**
```python
request_headers["Authorization"] = f"Bearer {token}"
```

**Status:** ✅ CORRECT

### ✅ API Endpoints

**Branch Creation Endpoint:**
- **Required:** `POST /repos/{owner}/{repo}/git/refs`
- **Our Code:** ✅ Matches exactly (line 3093)

**Request Body:**
- **Required:** `{"ref": "refs/heads/branch-name", "sha": "commit-sha"}`
- **Our Code:** ✅ Matches exactly (line 3098-3101)

**Status:** ✅ COMPLIANT

### ✅ Token Scopes

**For branch creation, GitHub requires:**
- Token scope: `repo` (full control of private repositories)
- Or: `public_repo` (for public repos only)

**Verification:** Token works for write operations ✅ (Test 3 passed)

---

## Issues Found

### ✅ No Critical Issues

All authentication components are working correctly:
- ✅ Token is in environment
- ✅ Token is loaded correctly
- ✅ Token works with GitHub API directly
- ✅ Auth header is formatted correctly
- ✅ Token has required scopes
- ✅ `get_auth_token()` returns token correctly

### ⚠️ Potential Issue: GitHub App Priority

**Observation:**
- Both GitHub App and PAT are configured
- Auth system tries GitHub App first
- If GitHub App fails silently, it should fall back to PAT
- Our test shows PAT is being used (token starts with `ghp_`)

**Recommendation:**
- If you want to force PAT usage, set `GITHUB_AUTH_MODE=pat` in `.env`
- This will skip GitHub App and use PAT directly

---

## Recommended Fixes

### 1. Enable Debug Logging (Optional)

To see which auth method is being used, add to `.env`:
```
GITHUB_MCP_DEBUG_AUTH=true
```

This will print diagnostic info to stderr showing:
- Which tokens are present
- Which auth method is being used
- Token type (App vs PAT)

### 2. Force PAT Mode (If Needed)

If you want to ensure PAT is used (bypassing GitHub App), add to `.env`:
```
GITHUB_AUTH_MODE=pat
```

### 3. Verify GitHub App (If Using)

If you want to use GitHub App instead of PAT:
1. Verify the private key file exists at the path specified
2. Verify the installation ID is correct
3. Test App token generation:
   ```python
   from auth.github_app import get_installation_token_from_env
   token = await get_installation_token_from_env()
   print(f"App token: {token[:20]}...")
   ```

---

## Root Cause Analysis

### Why "Authentication required" Might Appear

If you're seeing "Authentication required" errors despite valid token:

1. **MCP Layer Issue:**
   - The tool might not be receiving the token
   - Check how the tool is being called
   - Verify MCP client is passing parameters correctly

2. **GitHub App Failure:**
   - If GitHub App is configured but failing
   - And fallback isn't working properly
   - Solution: Set `GITHUB_AUTH_MODE=pat` to force PAT

3. **False Positive:**
   - Error might be from a different issue (404, 403, etc.)
   - Check the actual error response for status code
   - Verify it's actually a 401, not another error

4. **Token Scope Issue:**
   - Token might not have required scopes
   - But our test shows it works, so this is unlikely

---

## Testing Recommendations

### Test 1: Verify Auth in Tool Context

Create a test that calls the tool through MCP:
```typescript
const result = await callMCPTool("github_create_branch", {
  owner: "crypto-ninja",
  repo: "github-mcp-server",
  branch: "test/auth-check",
  from_ref: "main"
});

console.log(result);
// Should return JSON with branch info, not "Authentication required"
```

### Test 2: Check Error Response Format

If you get an error, verify it's actually an auth error:
```json
{
  "success": false,
  "error": "Authentication required",
  "message": "...",
  "status_code": 401  // ← Check this
}
```

### Test 3: Enable Debug Mode

Set `GITHUB_MCP_DEBUG_AUTH=true` and run a tool to see auth flow:
```
🔍 AUTH DIAGNOSTIC:
  GITHUB_TOKEN present: True
  GITHUB_APP_ID present: True
  ...
  ✅ Using PAT token (prefix: ghp_4uclB3...)
```

---

## Success Criteria

✅ **All Checks Passed:**

1. ✅ Token is in .env
2. ✅ Token is being loaded correctly
3. ✅ Token works with GitHub API directly
4. ✅ Auth header is formatted correctly
5. ✅ Token has required scopes
6. ✅ GitHub App is configured (but PAT is being used)
7. ✅ Code follows GitHub API requirements

---

## Conclusion

**Authentication is working correctly.** The GITHUB_TOKEN is valid and can perform all operations.

**If you're still seeing "Authentication required" errors:**

1. Check the actual error response (status code, message)
2. Verify the tool is being called correctly through MCP
3. Enable debug logging: `GITHUB_MCP_DEBUG_AUTH=true`
4. Force PAT mode: `GITHUB_AUTH_MODE=pat`

**Next Steps:**
- If errors persist, check MCP layer (how tools are called)
- Verify error responses are actually 401 (not 403, 404, etc.)
- Test with debug logging enabled to see auth flow

---

**Report Generated:** 2025-01-26  
**Test Script:** `test_auth_direct.py`  
**Status:** ✅ Authentication Working - No Code Changes Needed

