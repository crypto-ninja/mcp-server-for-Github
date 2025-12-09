#!/usr/bin/env python3
"""Live integration tests against real GitHub API."""

import asyncio
import time
import sys
import os
from typing import Tuple

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    token_status = "SET" if os.environ.get("GITHUB_TOKEN") else "NOT SET"
    app_status = "SET" if os.environ.get("GITHUB_APP_ID") else "NOT SET"
    print(f"Environment loaded - GITHUB_TOKEN: {token_status}, GITHUB_APP_ID: {app_status}")
except ImportError:
    print("Warning: python-dotenv not installed")

# Test configuration
TEST_OWNER = "crypto-ninja"
TEST_REPO = "mcp-test-repo"

# Track results
results = []


def log_result(test_name: str, passed: bool, duration_ms: float, details: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    results.append((test_name, passed, duration_ms))
    print(f"  {status} {test_name} ({duration_ms:.0f}ms) {details}")


def _response_ok(result) -> Tuple[bool, str]:
    """Helper to decide if a string response is OK (no 'error')."""
    if isinstance(result, str):
        low = result.lower()
        if "error" in low:
            return False, result
        return True, result
    return False, str(result)


async def test_get_repo_info():
    """Test getting repository information."""
    from src.github_mcp.tools.repositories import github_get_repo_info
    from src.github_mcp.models.enums import ResponseFormat
    from src.github_mcp.models.inputs import RepoInfoInput

    start = time.perf_counter()
    try:
        params = RepoInfoInput(owner=TEST_OWNER, repo=TEST_REPO, response_format=ResponseFormat.JSON)
        result = await github_get_repo_info(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_get_repo_info", ok, duration, detail[:100])
        return ok
    except Exception as e:  # pragma: no cover - live network errors
        duration = (time.perf_counter() - start) * 1000
        log_result("github_get_repo_info", False, duration, str(e)[:100])
        return False


async def test_list_branches():
    """Test listing branches."""
    from src.github_mcp.tools.branches import github_list_branches
    from src.github_mcp.models.enums import ResponseFormat
    from src.github_mcp.models.inputs import ListBranchesInput

    start = time.perf_counter()
    try:
        params = ListBranchesInput(owner=TEST_OWNER, repo=TEST_REPO, response_format=ResponseFormat.JSON)
        result = await github_list_branches(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_list_branches", ok, duration, detail[:100])
        return ok
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("github_list_branches", False, duration, str(e)[:100])
        return False


async def test_list_issues():
    """Test listing issues."""
    from src.github_mcp.tools.issues import github_list_issues
    from src.github_mcp.models.enums import ResponseFormat
    from src.github_mcp.models.inputs import ListIssuesInput

    start = time.perf_counter()
    try:
        params = ListIssuesInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            state="all",
            limit=10,
            page=1,
            response_format=ResponseFormat.JSON,
        )
        result = await github_list_issues(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_list_issues", ok, duration, detail[:100])
        return ok
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("github_list_issues", False, duration, str(e)[:100])
        return False


async def test_list_pull_requests():
    """Test listing pull requests."""
    from src.github_mcp.tools.pull_requests import github_list_pull_requests
    from src.github_mcp.models.enums import ResponseFormat
    from src.github_mcp.models.inputs import ListPullRequestsInput

    start = time.perf_counter()
    try:
        params = ListPullRequestsInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            state="all",
            limit=10,
            page=1,
            response_format=ResponseFormat.JSON,
        )
        result = await github_list_pull_requests(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_list_pull_requests", ok, duration, detail[:100])
        return ok
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("github_list_pull_requests", False, duration, str(e)[:100])
        return False


async def test_get_file_content():
    """Test getting file content."""
    from src.github_mcp.tools.files import github_get_file_content
    from src.github_mcp.models.inputs import GetFileContentInput

    start = time.perf_counter()
    try:
        params = GetFileContentInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            path="README.md",
        )
        result = await github_get_file_content(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_get_file_content", ok, duration, detail[:100])
        return ok
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("github_get_file_content", False, duration, str(e)[:100])
        return False


async def test_list_commits():
    """Test listing commits."""
    from src.github_mcp.tools.commits import github_list_commits
    from src.github_mcp.models.enums import ResponseFormat
    from src.github_mcp.models.inputs import ListCommitsInput

    start = time.perf_counter()
    try:
        params = ListCommitsInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            limit=5,
            page=1,
            response_format=ResponseFormat.JSON,
        )
        result = await github_list_commits(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_list_commits", ok, duration, detail[:100])
        return ok
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("github_list_commits", False, duration, str(e)[:100])
        return False


async def test_list_releases():
    """Test listing releases."""
    from src.github_mcp.tools.releases import github_list_releases
    from src.github_mcp.models.enums import ResponseFormat
    from src.github_mcp.models.inputs import ListReleasesInput

    start = time.perf_counter()
    try:
        params = ListReleasesInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            limit=5,
            page=1,
            response_format=ResponseFormat.JSON,
        )
        result = await github_list_releases(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_list_releases", ok, duration, detail[:100])
        return ok
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("github_list_releases", False, duration, str(e)[:100])
        return False


async def test_search_repositories():
    """Test repository search."""
    from src.github_mcp.tools.search import github_search_repositories
    from src.github_mcp.models.enums import ResponseFormat
    from src.github_mcp.models.inputs import SearchRepositoriesInput

    start = time.perf_counter()
    try:
        params = SearchRepositoriesInput(
            query="mcp server language:python",
            limit=5,
            page=1,
            response_format=ResponseFormat.JSON,
        )
        result = await github_search_repositories(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_search_repositories", ok, duration, detail[:100])
        return ok
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("github_search_repositories", False, duration, str(e)[:100])
        return False


async def test_get_user_info():
    """Test getting user info."""
    from src.github_mcp.tools.users import github_get_user_info
    from src.github_mcp.models.enums import ResponseFormat
    from src.github_mcp.models.inputs import GetUserInfoInput

    start = time.perf_counter()
    try:
        params = GetUserInfoInput(username="crypto-ninja", response_format=ResponseFormat.JSON)
        result = await github_get_user_info(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_get_user_info", ok, duration, detail[:100])
        return ok
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("github_get_user_info", False, duration, str(e)[:100])
        return False


async def test_list_workflows():
    """Test listing workflows (Actions)."""
    from src.github_mcp.tools.actions import github_list_workflows
    from src.github_mcp.models.enums import ResponseFormat
    from src.github_mcp.models.inputs import ListWorkflowsInput

    start = time.perf_counter()
    try:
        params = ListWorkflowsInput(owner=TEST_OWNER, repo=TEST_REPO, response_format=ResponseFormat.JSON)
        result = await github_list_workflows(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_list_workflows", ok, duration, detail[:100])
        return ok
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("github_list_workflows", False, duration, str(e)[:100])
        return False


async def test_list_labels():
    """Test listing labels."""
    from src.github_mcp.tools.labels import github_list_labels
    from src.github_mcp.models.inputs import ListLabelsInput

    start = time.perf_counter()
    try:
        params = ListLabelsInput(owner=TEST_OWNER, repo=TEST_REPO)
        result = await github_list_labels(params)
        duration = (time.perf_counter() - start) * 1000

        ok, detail = _response_ok(result)
        log_result("github_list_labels", ok, duration, detail[:100])
        return ok
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("github_list_labels", False, duration, str(e)[:100])
        return False


async def test_execute_code_list_tools():
    """Test the execute_code function - list tools."""
    from src.github_mcp.deno_runtime import DenoRuntime

    start = time.perf_counter()
    try:
        runtime = DenoRuntime()
        result = await runtime.execute_code_async(
            """
            const tools = listAvailableTools();
            return { toolCount: tools.totalTools, categories: Object.keys(tools.byCategory).length };
            """
        )
        duration = (time.perf_counter() - start) * 1000

        if isinstance(result, dict) and result.get("error") is not True:
            data = result.get("data", result)
            tool_count = data.get("toolCount", 0) if isinstance(data, dict) else 0
            categories = data.get("categories", 0) if isinstance(data, dict) else 0
            log_result(
                "execute_code (list tools)", True, duration, f"{tool_count} tools, {categories} categories"
            )
            return True
        else:
            log_result("execute_code (list tools)", False, duration, str(result)[:100])
            return False
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("execute_code (list tools)", False, duration, str(e)[:100])
        return False


async def test_execute_code_api_call():
    """Test execute_code making actual API call."""
    from src.github_mcp.deno_runtime import DenoRuntime

    start = time.perf_counter()
    try:
        runtime = DenoRuntime()
        result = await runtime.execute_code_async(
            f"""
            const repo = await callMCPTool("github_get_repo_info", {{
                owner: "{TEST_OWNER}",
                repo: "{TEST_REPO}",
                response_format: "json"
            }});
            return repo;
            """
        )
        duration = (time.perf_counter() - start) * 1000

        if isinstance(result, dict) and result.get("error") is not True:
            log_result("execute_code (API call)", True, duration)
            return True
        else:
            log_result("execute_code (API call)", False, duration, str(result)[:100])
            return False
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("execute_code (API call)", False, duration, str(e)[:100])
        return False


async def test_connection_pooling():
    """Test that connection pooling provides speedup."""
    from src.github_mcp.deno_runtime import DenoRuntime

    print("\n  Testing connection pooling (5 rapid calls)...")

    runtime = DenoRuntime()
    times = []

    for i in range(5):
        start = time.perf_counter()
        try:
            result = await runtime.execute_code_async("return 1 + 1;")
            duration = (time.perf_counter() - start) * 1000
            times.append(duration)
            status = "[OK]" if result.get("error") is not True else "[ERR]"
            print(f"    Call {i+1}: {duration:.0f}ms {status}")
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            times.append(duration)
            print(f"    Call {i+1}: {duration:.0f}ms [ERR] {str(e)[:50]}")

    if times:
        avg = sum(times) / len(times)
        first = times[0]
        rest_avg = sum(times[1:]) / len(times[1:]) if len(times) > 1 else first

        # Pooling is working if subsequent calls are faster
        pooling_effective = rest_avg < first * 0.5 or rest_avg < 200

        log_result(
            "connection_pooling",
            pooling_effective,
            avg,
            f"First: {first:.0f}ms, Rest avg: {rest_avg:.0f}ms",
        )
        return pooling_effective
    return False


async def test_create_and_close_issue():
    """Test creating and closing an issue (write operations)."""
    from src.github_mcp.tools.issues import github_create_issue, github_update_issue
    import json

    print("\n  Testing write operations (create/close issue)...")

    # Create issue
    start = time.perf_counter()
    try:
        from src.github_mcp.models.inputs import CreateIssueInput, UpdateIssueInput

        create_params = CreateIssueInput(
            owner=TEST_OWNER,
            repo=TEST_REPO,
            title="[TEST] Live integration test - auto-close",
            body="Automated test issue from live integration tests. Will be closed immediately.",
            labels=["test"],
        )
        create_result = await github_create_issue(create_params)
        create_duration = (time.perf_counter() - start) * 1000

        if isinstance(create_result, str) and "error" not in create_result.lower():
            # Parse to get issue number
            try:
                data = json.loads(create_result)
                issue_number = data.get("number")
                print(f"    Created issue #{issue_number} ({create_duration:.0f}ms)")

                # Close the issue
                start = time.perf_counter()
                close_params = UpdateIssueInput(
                    owner=TEST_OWNER,
                    repo=TEST_REPO,
                    issue_number=issue_number,
                    state="closed",
                )
                close_result = await github_update_issue(close_params)
                close_duration = (time.perf_counter() - start) * 1000

                if isinstance(close_result, str) and "error" not in close_result.lower():
                    print(f"    Closed issue #{issue_number} ({close_duration:.0f}ms)")
                    log_result(
                        "create_and_close_issue",
                        True,
                        create_duration + close_duration,
                        f"Issue #{issue_number}",
                    )
                    return True
                else:
                    log_result(
                        "create_and_close_issue",
                        False,
                        create_duration + close_duration,
                        f"Close failed: {close_result[:50]}",
                    )
                    return False
            except json.JSONDecodeError:
                log_result("create_and_close_issue", False, create_duration, "Failed to parse response")
                return False
        else:
            log_result("create_and_close_issue", False, create_duration, str(create_result)[:100])
            return False
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        log_result("create_and_close_issue", False, duration, str(e)[:100])
        return False


async def main():
    print("=" * 70)
    print("GitHub MCP Server - Live Integration Tests")
    print(f"Test Repo: {TEST_OWNER}/{TEST_REPO}")
    print("=" * 70)

    # Read operations
    print("\n[READ OPERATIONS]")
    await test_get_repo_info()
    await test_list_branches()
    await test_list_issues()
    await test_list_pull_requests()
    await test_get_file_content()
    await test_list_commits()
    await test_list_releases()
    await test_list_labels()

    # Search operations
    print("\n[SEARCH OPERATIONS]")
    await test_search_repositories()

    # User operations
    print("\n[USER OPERATIONS]")
    await test_get_user_info()

    # Actions
    print("\n[ACTIONS]")
    await test_list_workflows()

    # Code-first architecture
    print("\n[CODE-FIRST ARCHITECTURE]")
    await test_execute_code_list_tools()
    await test_execute_code_api_call()

    # Connection pooling
    print("\n[CONNECTION POOLING]")
    await test_connection_pooling()

    # Write operations (creates real issue, then closes it)
    print("\n[WRITE OPERATIONS]")
    await test_create_and_close_issue()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)
    avg_time = sum(t for _, _, t in results) / total if total > 0 else 0

    print(f"\n  Total:     {total}")
    print(f"  Passed:    {passed}")
    print(f"  Failed:    {failed}")
    print(f"  Avg Time:  {avg_time:.0f}ms")
    print(f"\n  Pass Rate: {passed/total*100:.1f}%")

    if failed > 0:
        print("\n  Failed Tests:")
        for name, p, _ in results:
            if not p:
                print(f"    - {name}")

    print("\n" + "=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    raise SystemExit(0 if success else 1)

