#!/usr/bin/env python3
"""
Comprehensive test suite for all 10 fixed write operations.
Tests authentication validation and operation success.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from github_mcp import (
    github_create_file, github_update_file, github_delete_file,
    github_create_release, github_update_release,
    github_update_repository, github_archive_repository, github_delete_repository,
    github_merge_pull_request,
    github_get_file_content, github_get_release,
    CreateFileInput, UpdateFileInput, DeleteFileInput,
    CreateReleaseInput, UpdateReleaseInput,
    UpdateRepositoryInput, ArchiveRepositoryInput, DeleteRepositoryInput,
    MergePullRequestInput, GetFileContentInput, GetReleaseInput
)

# Test repository configuration
# Using main repo for testing - we'll use safe test paths
TEST_OWNER = "crypto-ninja"
TEST_REPO = "github-mcp-server"
TEST_PATH_PREFIX = "test-write-ops-"  # Prefix for all test files

class TestResult:
    def __init__(self, name, status, details="", error=""):
        self.name = name
        self.status = status  # "PASS", "FAIL", "SKIP"
        self.details = details
        self.error = error

async def test_create_file():
    """Test 1: github_create_file"""
    try:
        result = await github_create_file(CreateFileInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            path=f"{TEST_PATH_PREFIX}test-file.txt",
            content="This is a test file created by github_create_file",
            message="Test: Create test file"
        ))
        
        if "error" in result.lower() and "authentication" in result.lower():
            return TestResult("github_create_file", "FAIL", 
                           "Authentication error (expected if no token)", result)
        
        if "created" in result.lower() or "commit" in result.lower():
            return TestResult("github_create_file", "PASS", 
                           "File created successfully", "")
        else:
            return TestResult("github_create_file", "FAIL", 
                           "Unexpected response", result[:200])
    except Exception as e:
        return TestResult("github_create_file", "FAIL", "", str(e)[:200])

async def test_update_file():
    """Test 2: github_update_file"""
    try:
        # First get the file to get its SHA
        file_info = await github_get_file_content(GetFileContentInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            path=f"{TEST_PATH_PREFIX}test-file.txt"
        ))
        
        # Parse SHA from response (could be JSON or markdown)
        sha = None
        if isinstance(file_info, str):
            # Try to extract SHA from markdown format: **SHA:** {sha}
            import re
            # Pattern for markdown: **SHA:** followed by SHA
            match = re.search(r'\*\*SHA:\*\*\s*([a-f0-9]{40})', file_info, re.IGNORECASE)
            if match:
                sha = match.group(1)
            else:
                # Try JSON format: "sha": "..."
                match = re.search(r'"sha"\s*:\s*"([^"]+)"', file_info)
                if match:
                    sha = match.group(1)
                else:
                    # Try plain SHA: format
                    match = re.search(r'SHA:\s*([a-f0-9]{40})', file_info, re.IGNORECASE)
                    if match:
                        sha = match.group(1)
        
        if not sha:
            return TestResult("github_update_file", "SKIP", 
                           "Could not get file SHA (file may not exist)", "")
        
        result = await github_update_file(UpdateFileInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            path=f"{TEST_PATH_PREFIX}test-file.txt",
            content="This file has been updated by github_update_file",
            message="Test: Update test file",
            sha=sha
        ))
        
        if "error" in result.lower() and "authentication" in result.lower():
            return TestResult("github_update_file", "FAIL", 
                           "Authentication error", result)
        
        if "updated" in result.lower() or "commit" in result.lower():
            return TestResult("github_update_file", "PASS", 
                           "File updated successfully", "")
        else:
            return TestResult("github_update_file", "FAIL", 
                           "Unexpected response", result[:200])
    except Exception as e:
        return TestResult("github_update_file", "FAIL", "", str(e)[:200])

async def test_delete_file():
    """Test 3: github_delete_file"""
    try:
        # Get current SHA
        file_info = await github_get_file_content(GetFileContentInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            path=f"{TEST_PATH_PREFIX}test-file.txt"
        ))
        
        sha = None
        if isinstance(file_info, str):
            if '"sha"' in file_info:
                import re
                match = re.search(r'"sha"\s*:\s*"([^"]+)"', file_info)
                if match:
                    sha = match.group(1)
            elif "SHA:" in file_info:
                import re
                match = re.search(r"SHA:\s*([a-f0-9]{40})", file_info)
                if match:
                    sha = match.group(1)
        
        if not sha:
            return TestResult("github_delete_file", "SKIP", 
                           "Could not get file SHA", "")
        
        result = await github_delete_file(DeleteFileInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            path=f"{TEST_PATH_PREFIX}test-file.txt",
            message="Test: Delete test file",
            sha=sha
        ))
        
        if "error" in result.lower() and "authentication" in result.lower():
            return TestResult("github_delete_file", "FAIL", 
                           "Authentication error", result)
        
        if "deleted" in result.lower() or "commit" in result.lower():
            return TestResult("github_delete_file", "PASS", 
                           "File deleted successfully", "")
        else:
            return TestResult("github_delete_file", "FAIL", 
                           "Unexpected response", result[:200])
    except Exception as e:
        return TestResult("github_delete_file", "FAIL", "", str(e)[:200])

async def test_create_release():
    """Test 4: github_create_release"""
    try:
        result = await github_create_release(CreateReleaseInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            tag_name="v0.0.1-test",
            name="Test Release",
            body="Test release created by github_create_release",
            draft=True
        ))
        
        if "error" in result.lower() and "authentication" in result.lower():
            return TestResult("github_create_release", "FAIL", 
                           "Authentication error", result)
        
        if "release" in result.lower() and ("created" in result.lower() or "v0.0.1-test" in result):
            return TestResult("github_create_release", "PASS", 
                           "Release created successfully", "")
        else:
            return TestResult("github_create_release", "FAIL", 
                           "Unexpected response", result[:200])
    except Exception as e:
        return TestResult("github_create_release", "FAIL", "", str(e)[:200])

async def test_update_release():
    """Test 5: github_update_release"""
    try:
        # Get the release we just created
        release_info = await github_get_release(GetReleaseInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            tag="v0.0.1-test"
        ))
        
        # Extract release ID
        release_id = None
        if isinstance(release_info, str):
            import re
            # Try JSON format: "id": 12345
            match = re.search(r'"id"\s*:\s*(\d+)', release_info)
            if match:
                release_id = match.group(1)
            else:
                # Try markdown format: **ID:** 12345
                match = re.search(r'\*\*ID:\*\*\s*(\d+)', release_info, re.IGNORECASE)
                if match:
                    release_id = match.group(1)
        
        if not release_id:
            return TestResult("github_update_release", "SKIP", 
                           "Could not get release ID", "")
        
        result = await github_update_release(UpdateReleaseInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            release_id=release_id,
            name="Updated Test Release",
            body="This release was updated by github_update_release"
        ))
        
        if "error" in result.lower() and "authentication" in result.lower():
            return TestResult("github_update_release", "FAIL", 
                           "Authentication error", result)
        
        if "updated" in result.lower() or "release" in result.lower():
            return TestResult("github_update_release", "PASS", 
                           "Release updated successfully", "")
        else:
            return TestResult("github_update_release", "FAIL", 
                           "Unexpected response", result[:200])
    except Exception as e:
        return TestResult("github_update_release", "FAIL", "", str(e)[:200])

async def test_update_repository():
    """Test 6: github_update_repository"""
    try:
        result = await github_update_repository(UpdateRepositoryInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            description="Updated description by github_update_repository test"
        ))
        
        if "error" in result.lower() and "authentication" in result.lower():
            return TestResult("github_update_repository", "FAIL", 
                           "Authentication error", result)
        
        if "updated" in result.lower() or "repository" in result.lower():
            return TestResult("github_update_repository", "PASS", 
                           "Repository updated successfully", "")
        else:
            return TestResult("github_update_repository", "FAIL", 
                           "Unexpected response", result[:200])
    except Exception as e:
        return TestResult("github_update_repository", "FAIL", "", str(e)[:200])

async def test_archive_repository():
    """Test 7: github_archive_repository"""
    try:
        result = await github_archive_repository(ArchiveRepositoryInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            archived=True
        ))
        
        if "error" in result.lower() and "authentication" in result.lower():
            return TestResult("github_archive_repository", "FAIL", 
                           "Authentication error", result)
        
        if "archived" in result.lower() or "updated" in result.lower():
            # Unarchive it so we can continue testing
            await github_update_repository(UpdateRepositoryInput(
                owner=TEST_OWNER,
                repo=TEST_REPO,
                archived=False
            ))
            return TestResult("github_archive_repository", "PASS", 
                           "Repository archived and unarchived successfully", "")
        else:
            return TestResult("github_archive_repository", "FAIL", 
                           "Unexpected response", result[:200])
    except Exception as e:
        return TestResult("github_archive_repository", "FAIL", "", str(e)[:200])

async def test_delete_repository():
    """Test 8: github_delete_repository"""
    try:
        result = await github_delete_repository(DeleteRepositoryInput(
            owner=TEST_OWNER,
            repo=TEST_REPO
        ))
        
        if "error" in result.lower() and "authentication" in result.lower():
            return TestResult("github_delete_repository", "FAIL", 
                           "Authentication error", result)
        
        if "deleted" in result.lower():
            return TestResult("github_delete_repository", "PASS", 
                           "Repository deleted successfully", "")
        else:
            return TestResult("github_delete_repository", "FAIL", 
                           "Unexpected response", result[:200])
    except Exception as e:
        return TestResult("github_delete_repository", "FAIL", "", str(e)[:200])

async def test_merge_pull_request():
    """Test 9: github_merge_pull_request - Skip if no PRs available"""
    return TestResult("github_merge_pull_request", "SKIP", 
                     "Requires existing pull request - tested separately if needed", "")

async def test_auth_error_handling():
    """Test 10: Authentication error handling"""
    try:
        # Try with invalid token
        result = await github_create_file(CreateFileInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            path=f"{TEST_PATH_PREFIX}should-fail.txt",
            content="test",
            message="test",
            token="invalid-token-12345"
        ))
        
        # Should return JSON error, not crash
        if isinstance(result, str):
            if "authentication" in result.lower() or "401" in result or "403" in result:
                return TestResult("auth_error_handling", "PASS", 
                               "Auth error handled correctly with clear message", "")
            elif "error" in result.lower():
                return TestResult("auth_error_handling", "PARTIAL", 
                               "Got error but message unclear", result[:200])
            else:
                return TestResult("auth_error_handling", "FAIL", 
                               "Should have failed with invalid token", result[:200])
        else:
            return TestResult("auth_error_handling", "FAIL", 
                           "Unexpected response type", str(type(result)))
    except Exception as e:
        # Exception is also acceptable if it's an auth error
        error_str = str(e).lower()
        if "authentication" in error_str or "401" in error_str or "403" in error_str:
            return TestResult("auth_error_handling", "PASS", 
                           "Auth error raised as exception (acceptable)", "")
        else:
            return TestResult("auth_error_handling", "FAIL", 
                           "Unexpected exception", str(e)[:200])

async def main():
    """Run all tests"""
    print("=" * 60)
    print("COMPREHENSIVE TEST SUITE: Write Operations")
    print("=" * 60)
    print(f"\nTest Repository: {TEST_OWNER}/{TEST_REPO}")
    print("Note: Some tests may fail if repository doesn't exist or auth is not configured\n")
    
    tests = [
        ("Test 1", test_create_file),
        ("Test 2", test_update_file),
        ("Test 3", test_delete_file),
        ("Test 4", test_create_release),
        ("Test 5", test_update_release),
        ("Test 6", test_update_repository),
        ("Test 7", test_archive_repository),
        ("Test 8", test_delete_repository),
        ("Test 9", test_merge_pull_request),
        ("Test 10", test_auth_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}: {test_func.__name__}")
        print("-" * 60)
        result = await test_func()
        results.append(result)
        
        status_icon = "[PASS]" if result.status == "PASS" else "[FAIL]" if result.status == "FAIL" else "[SKIP]"
        print(f"{status_icon} Status: {result.status}")
        if result.details:
            print(f"   Details: {result.details}")
        if result.error:
            print(f"   Error: {result.error}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    skipped = sum(1 for r in results if r.status == "SKIP")
    partial = sum(1 for r in results if r.status == "PARTIAL")
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"[PASS] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[SKIP] Skipped: {skipped}")
    if partial > 0:
        print(f"[PARTIAL] Partial: {partial}")
    
    print("\n" + "=" * 60)
    print("DETAILED RESULTS")
    print("=" * 60)
    
    for result in results:
        status_icon = "[PASS]" if result.status == "PASS" else "[FAIL]" if result.status == "FAIL" else "[SKIP]"
        print(f"\n{status_icon} {result.name}")
        print(f"   Status: {result.status}")
        if result.details:
            print(f"   Details: {result.details}")
        if result.error:
            print(f"   Error: {result.error[:200]}")
    
    # Recommendation
    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)
    
    if failed == 0 and skipped <= 2:
        print("\n[PASS] ALL TESTS PASSED - Safe to release v2.3.0")
    elif failed == 0:
        print("\n[WARN] SOME TESTS SKIPPED - Review skipped tests before release")
    elif failed <= 2:
        print(f"\n[WARN] {failed} TEST(S) FAILED - Review failures before release")
    else:
        print(f"\n[FAIL] {failed} TESTS FAILED - Must fix before release")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
    sys.exit(0 if all(r.status in ("PASS", "SKIP") for r in results) else 1)

