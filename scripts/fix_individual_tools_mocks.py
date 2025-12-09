#!/usr/bin/env python3
"""
Fix all mock paths in test_individual_tools.py based on tool being tested.
"""

import re
from pathlib import Path

# Map tool names to their modules
TOOL_TO_MODULE = {
    'github_get_repo_info': 'repositories',
    'github_list_issues': 'issues',
    'github_create_issue': 'issues',
    'github_get_file_content': 'files',
    'github_search_code': 'search',
    'github_list_commits': 'commits',
    'github_get_pr_details': 'pull_requests',
    'github_get_release': 'releases',
    'github_list_releases': 'releases',
    'github_create_release': 'releases',
    'github_get_user_info': 'users',
    'github_list_workflows': 'actions',
    'github_get_workflow_runs': 'actions',
    'github_create_pull_request': 'pull_requests',
    'github_merge_pull_request': 'pull_requests',
    'github_update_issue': 'issues',
    'github_str_replace': 'files',
    'github_batch_file_operations': 'files',
    'github_list_branches': 'branches',
    'github_create_branch': 'branches',
    'github_get_branch': 'branches',
    'github_delete_branch': 'branches',
    'github_compare_branches': 'branches',
    'github_close_pull_request': 'pull_requests',
    'github_create_pr_review': 'pull_requests',
    'github_update_release': 'releases',
    'github_search_issues': 'search',
    'github_search_repositories': 'search',
    'github_list_repo_contents': 'files',
    'github_read_file_chunk': 'files',
}


def fix_file(filepath):
    """Fix mock paths in test_individual_tools.py."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Find all test functions and their corresponding tools
    # Pattern: async def test_github_<tool_name>(...)
    test_pattern = r'async def (test_github_\w+)'
    tests = list(re.finditer(test_pattern, content))
    
    for test_match in tests:
        test_name = test_match.group(1)
        # Extract tool name: test_github_get_repo_info -> github_get_repo_info
        tool_match = re.search(r'test_github_(\w+)', test_name)
        if tool_match:
            tool_name = f"github_{tool_match.group(1)}"
            module = TOOL_TO_MODULE.get(tool_name)
            
            if module:
                # Find the test function block (from decorators to next function/class)
                test_start = test_match.start()
                # Look backwards for decorators
                decorator_start = test_start
                while decorator_start > 0:
                    if content[decorator_start:decorator_start+7] == '    @':
                        decorator_start = content.rfind('\n', 0, decorator_start) + 1
                        break
                    decorator_start -= 1
                
                # Look forwards for next function/class
                test_end = content.find('\n    async def ', test_start + 1)
                if test_end == -1:
                    test_end = content.find('\nclass ', test_start + 1)
                if test_end == -1:
                    test_end = len(content)
                
                test_block = content[decorator_start:test_end]
                
                # Replace mock paths in this test block
                new_block = test_block
                new_block = re.sub(
                    r"@patch\('src\.github_mcp\.utils\.requests\._make_github_request'\)",
                    f"@patch('src.github_mcp.tools.{module}._make_github_request')",
                    new_block
                )
                new_block = re.sub(
                    r"@patch\('src\.github_mcp\.utils\.requests\._get_auth_token_fallback'\)",
                    f"@patch('src.github_mcp.tools.{module}._get_auth_token_fallback')",
                    new_block
                )
                new_block = re.sub(
                    r"@patch\.object\(github_mcp, '_make_github_request'\)",
                    f"@patch('src.github_mcp.tools.{module}._make_github_request')",
                    new_block
                )
                new_block = re.sub(
                    r"@patch\.object\(github_mcp, '_get_auth_token_fallback'\)",
                    f"@patch('src.github_mcp.tools.{module}._get_auth_token_fallback')",
                    new_block
                )
                
                if new_block != test_block:
                    content = content[:decorator_start] + new_block + content[test_end:]
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """Fix mock paths in test_individual_tools.py."""
    filepath = Path('tests/test_individual_tools.py')
    if fix_file(filepath):
        print(f"✅ Updated: {filepath.name}")
    else:
        print(f"ℹ️  No changes needed: {filepath.name}")


if __name__ == '__main__':
    main()


