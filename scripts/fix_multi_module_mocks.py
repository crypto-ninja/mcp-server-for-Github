#!/usr/bin/env python3
"""
Fix mock paths in multi-module test files.

These tests use tools from multiple modules, so we need to patch at the
tool module level based on which tool is being tested.
"""

import re
from pathlib import Path

# Map tool names to their modules
TOOL_TO_MODULE = {
    # Repositories
    'github_get_repo_info': 'repositories',
    'github_create_repository': 'repositories',
    'github_delete_repository': 'repositories',
    'github_update_repository': 'repositories',
    'github_transfer_repository': 'repositories',
    'github_archive_repository': 'repositories',
    'github_list_user_repos': 'repositories',
    'github_list_org_repos': 'repositories',
    
    # Issues
    'github_list_issues': 'issues',
    'github_create_issue': 'issues',
    'github_update_issue': 'issues',
    'github_add_issue_comment': 'comments',
    
    # Files
    'github_get_file_content': 'files',
    'github_create_file': 'files',
    'github_update_file': 'files',
    'github_delete_file': 'files',
    'github_list_repo_contents': 'files',
    'github_batch_file_operations': 'files',
    
    # Pull Requests
    'github_list_pull_requests': 'pull_requests',
    'github_create_pull_request': 'pull_requests',
    'github_get_pr_details': 'pull_requests',
    'github_merge_pull_request': 'pull_requests',
    'github_close_pull_request': 'pull_requests',
    
    # Releases
    'github_list_releases': 'releases',
    'github_get_release': 'releases',
    'github_create_release': 'releases',
    'github_update_release': 'releases',
    
    # Search
    'github_search_code': 'search',
    'github_search_repositories': 'search',
    'github_search_issues': 'search',
    
    # Commits
    'github_list_commits': 'commits',
    
    # Users
    'github_get_user_info': 'users',
    'github_get_authenticated_user': 'users',
    
    # Branches
    'github_list_branches': 'branches',
    'github_create_branch': 'branches',
    'github_get_branch': 'branches',
    'github_delete_branch': 'branches',
    'github_compare_branches': 'branches',
}


def get_tool_from_test(test_function):
    """Extract tool name from test function name."""
    match = re.search(r'test_github_(\w+)', test_function)
    if match:
        tool_name = f"github_{match.group(1)}"
        return tool_name
    return None


def fix_file(filepath):
    """Fix mock paths in a test file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Find all test functions and their tools
    test_functions = re.findall(r'async def (test_\w+)', content)
    
    # For each test, find the tool it uses and update mocks
    for test_func in test_functions:
        tool_name = get_tool_from_test(test_func)
        if tool_name and tool_name in TOOL_TO_MODULE:
            module = TOOL_TO_MODULE[tool_name]
            
            # Find the test function block
            test_block = re.search(
                rf'(async def {re.escape(test_func)}.*?)(?=\n    async def|\nclass|\Z)',
                content,
                re.DOTALL
            )
            
            if test_block:
                test_content = test_block.group(1)
                
                # Replace mock paths in this test
                new_test_content = re.sub(
                    r"@patch\('src\.github_mcp\.utils\.requests\._make_github_request'\)",
                    f"@patch('src.github_mcp.tools.{module}._make_github_request')",
                    test_content
                )
                new_test_content = re.sub(
                    r"@patch\('src\.github_mcp\.utils\.requests\._get_auth_token_fallback'\)",
                    f"@patch('src.github_mcp.tools.{module}._get_auth_token_fallback')",
                    new_test_content
                )
                
                if new_test_content != test_content:
                    content = content.replace(test_content, new_test_content)
    
    # Also do a general replacement for utils.requests patterns
    # (fallback for tests that don't match the pattern above)
    content = re.sub(
        r"@patch\('src\.github_mcp\.utils\.requests\._make_github_request'\)",
        r"@patch('src.github_mcp.utils.requests._make_github_request')",  # Keep utils for now
        content
    )
    content = re.sub(
        r"@patch\('src\.github_mcp\.utils\.requests\._get_auth_token_fallback'\)",
        r"@patch('src.github_mcp.utils.requests._get_auth_token_fallback')",  # Keep utils for now
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """Fix mock paths in multi-module test files."""
    test_files = [
        'tests/test_individual_tools.py',
        'tests/test_response_formatting.py',
        'tests/test_write_operations_auth.py',
    ]
    
    updated = []
    for filepath in test_files:
        path = Path(filepath)
        if path.exists() and fix_file(path):
            updated.append(path.name)
            print(f"✅ Updated: {path.name}")
    
    print(f"\n📊 Total files updated: {len(updated)}")


if __name__ == '__main__':
    main()


