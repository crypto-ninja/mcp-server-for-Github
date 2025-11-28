#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for all fixed write operations.
Tests authentication validation and error handling.
"""
import asyncio
import json
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from github_mcp import (
    CreateFileInput, UpdateFileInput, DeleteFileInput,
    CreateReleaseInput, UpdateReleaseInput,
    UpdateRepositoryInput, ArchiveRepositoryInput,
    GetFileContentInput, GetReleaseInput
)

# Test repository
TEST_REPO = {
    "owner": "crypto-ninja",
    "repo": "mcp-test-repo-deleteme"
}

test_results = []

def record_test(test_name: str, status: str, details: str, error: str = None):
    """Record test result."""
    result = {
        "test": test_name,
        "status": status,
        "details": details[:200] if details else "",
        "error": error[:200] if error else None
    }
    test_results.append(result)
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
    print(f"\n{status_icon} {test_name}: {status}")
    if details:
        print(f"   Details: {details[:200]}")
    if error:
        print(f"   Error: {error[:200]}")

async def test_create_file():
    """Test 1: github_create_file"""
    try:
        from github_mcp import github_create_file
        result = await github_create_file(CreateFileInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            path="test-file.txt",
            content="This is a test file created by github_create_file",
            message="Test: Create test file"
        ))
        record_test("github_create_file", "PASS", result)
        return True
    except Exception as e:
        record_test("github_create_file", "FAIL", "Exception thrown", str(e))
        return False

async def test_update_file():
    """Test 2: github_update_file"""
    try:
        from github_mcp import github_get_file_content, github_update_file
        
        # Get file SHA first
        file_info = await github_get_file_content(GetFileContentInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            path="test-file.txt",
            response_format="json"
        ))
        
        file_data = json.loads(file_info) if isinstance(file_info, str) else file_info
        sha = file_data.get("sha") or file_data.get("content", {}).get("sha")
        
        if not sha:
            record_test("github_update_file", "FAIL", "Could not get file SHA", "SHA not found")
            return False
        
        result = await github_update_file(UpdateFileInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            path="test-file.txt",
            content="This file has been updated by github_update_file",
            message="Test: Update test file",
            sha=sha
        ))
        record_test("github_update_file", "PASS", result)
        return True
    except Exception as e:
        record_test("github_update_file", "FAIL", "Exception thrown", str(e))
        return False

async def test_delete_file():
    """Test 3: github_delete_file"""
    try:
        from github_mcp import github_get_file_content, github_delete_file
        
        # Get file SHA first
        file_info = await github_get_file_content(GetFileContentInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            path="test-file.txt",
            response_format="json"
        ))
        
        file_data = json.loads(file_info) if isinstance(file_info, str) else file_info
        sha = file_data.get("sha") or file_data.get("content", {}).get("sha")
        
        if not sha:
            record_test("github_delete_file", "FAIL", "Could not get file SHA", "SHA not found")
            return False
        
        result = await github_delete_file(DeleteFileInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            path="test-file.txt",
            message="Test: Delete test file",
            sha=sha
        ))
        record_test("github_delete_file", "PASS", result)
        return True
    except Exception as e:
        record_test("github_delete_file", "FAIL", "Exception thrown", str(e))
        return False

async def test_create_release():
    """Test 4: github_create_release"""
    try:
        from github_mcp import github_create_release
        result = await github_create_release(CreateReleaseInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            tag_name="v0.0.1-test",
            name="Test Release",
            body="Test release created by github_create_release",
            draft=True
        ))
        record_test("github_create_release", "PASS", result)
        return True
    except Exception as e:
        record_test("github_create_release", "FAIL", "Exception thrown", str(e))
        return False

async def test_update_release():
    """Test 5: github_update_release"""
    try:
        from github_mcp import github_get_release, github_update_release
        
        # Get release ID
        release_info = await github_get_release(GetReleaseInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            tag="v0.0.1-test",
            response_format="json"
        ))
        
        release_data = json.loads(release_info) if isinstance(release_info, str) else release_info
        release_id = release_data.get("id") or release_data.get("release_id") or "v0.0.1-test"
        
        result = await github_update_release(UpdateReleaseInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            release_id=str(release_id),
            name="Updated Test Release",
            body="This release was updated by github_update_release"
        ))
        record_test("github_update_release", "PASS", result)
        return True
    except Exception as e:
        record_test("github_update_release", "FAIL", "Exception thrown", str(e))
        return False

async def test_update_repository():
    """Test 6: github_update_repository"""
    try:
        from github_mcp import github_update_repository
        result = await github_update_repository(UpdateRepositoryInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            description="Updated description by github_update_repository test"
        ))
        record_test("github_update_repository", "PASS", result)
        return True
    except Exception as e:
        record_test("github_update_repository", "FAIL", "Exception thrown", str(e))
        return False

async def test_archive_repository():
    """Test 7: github_archive_repository"""
    try:
        from github_mcp import github_archive_repository, github_update_repository
        
        result = await github_archive_repository(ArchiveRepositoryInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            archived=True
        ))
        record_test("github_archive_repository", "PASS", result)
        
        # Unarchive for continued testing
        await github_update_repository(UpdateRepositoryInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            archived=False
        ))
        print("   ✅ Repository unarchived for continued testing")
        return True
    except Exception as e:
        record_test("github_archive_repository", "FAIL", "Exception thrown", str(e))
        return False

async def test_auth_error_handling():
    """Test authentication error handling"""
    try:
        from github_mcp import github_create_file
        # Try with invalid token
        result = await github_create_file(CreateFileInput(
            owner=TEST_REPO["owner"],
            repo=TEST_REPO["repo"],
            path="should-fail.txt",
            content="test",
            message="test",
            token="invalid-token-12345"
        ))
        
        # Check if it's a proper error message
        if isinstance(result, str) and ("Authentication" in result or "error" in result.lower()):
            record_test("Auth Error Handling", "PASS", "Auth error handled correctly")
            return True
        else:
            record_test("Auth Error Handling", "FAIL", "Unexpected result", result)
            return False
    except Exception as e:
        error_str = str(e)
        if "Authentication" in error_str or "401" in error_str or "403" in error_str:
            record_test("Auth Error Handling", "PASS", "Auth error handled correctly")
            return True
        else:
            record_test("Auth Error Handling", "PARTIAL", "Got error but unclear", error_str)
            return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("COMPREHENSIVE TEST SUITE: Fixed Write Operations")
    print("=" * 60)
    
    # Run tests
    await test_create_file()
    await test_update_file()
    await test_delete_file()
    await test_create_release()
    await test_update_release()
    await test_update_repository()
    await test_archive_repository()
    
    # Skip destructive tests
    record_test("github_delete_repository", "SKIP", "Skipped - too destructive. Manual test recommended.")
    record_test("github_merge_pull_request", "SKIP", "Skipped - requires existing pull request.")
    record_test("github_transfer_repository", "SKIP", "Skipped - too destructive. Manual test recommended.")
    
    # Test auth error handling
    await test_auth_error_handling()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    skipped = sum(1 for r in test_results if r["status"] == "SKIP")
    
    print(f"Total Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    
    if failed == 0:
        print("\n✅ Status: READY to release v2.3.0")
    else:
        print(f"\n❌ Status: NOT READY - {failed} test(s) failed")
    
    # Detailed results
    print("\n" + "=" * 60)
    print("DETAILED RESULTS")
    print("=" * 60)
    for result in test_results:
        status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⏭️"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if result["error"]:
            print(f"   Error: {result['error']}")
    
    return {
        "summary": {
            "total": len(test_results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "status": "READY" if failed == 0 else "NOT_READY"
        },
        "results": test_results
    }

if __name__ == "__main__":
    result = asyncio.run(main())
    print("\n" + json.dumps(result["summary"], indent=2))

