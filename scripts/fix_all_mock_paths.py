#!/usr/bin/env python3
"""
Fix all mock paths in test files to use tool module level patching.
"""

import re
from pathlib import Path

# Map tool names to their modules
TOOL_TO_MODULE = {
    'github_get_repo_info': 'repositories',
    'github_create_repository': 'repositories',
    'github_delete_repository': 'repositories',
    'github_update_repository': 'repositories',
    'github_transfer_repository': 'repositories',
    'github_archive_repository': 'repositories',
    'github_list_user_repos': 'repositories',
    'github_list_org_repos': 'repositories',
    'github_list_issues': 'issues',
    'github_create_issue': 'issues',
    'github_update_issue': 'issues',
    'github_add_issue_comment': 'comments',
    'github_get_file_content': 'files',
    'github_create_file': 'files',
    'github_update_file': 'files',
    'github_delete_file': 'files',
    'github_list_repo_contents': 'files',
    'github_batch_file_operations': 'files',
    'github_list_pull_requests': 'pull_requests',
    'github_create_pull_request': 'pull_requests',
    'github_get_pr_details': 'pull_requests',
    'github_merge_pull_request': 'pull_requests',
    'github_close_pull_request': 'pull_requests',
    'github_list_releases': 'releases',
    'github_get_release': 'releases',
    'github_create_release': 'releases',
    'github_update_release': 'releases',
    'github_search_code': 'search',
    'github_search_repositories': 'search',
    'github_search_issues': 'search',
    'github_list_commits': 'commits',
    'github_get_user_info': 'users',
    'github_get_authenticated_user': 'users',
    'github_list_branches': 'branches',
    'github_create_branch': 'branches',
    'github_get_branch': 'branches',
    'github_delete_branch': 'branches',
    'github_compare_branches': 'branches',
}


def fix_file(filepath):
    """Fix mock paths in a test file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a test function
        test_match = re.search(r'async def (test_github_\w+)', line)
        if test_match:
            test_name = test_match.group(1)
            # Extract tool name from test name
            tool_match = re.search(r'test_github_(\w+)', test_name)
            if tool_match:
                tool_name = f"github_{tool_match.group(1)}"
                module = TOOL_TO_MODULE.get(tool_name)
                
                if module:
                    # Look ahead for @patch decorators and update them
                    j = i - 1
                    while j >= 0 and (lines[j].strip().startswith('@patch') or lines[j].strip().startswith('@pytest')):
                        if 'src.github_mcp.utils.requests._make_github_request' in lines[j]:
                            lines[j] = lines[j].replace(
                                'src.github_mcp.utils.requests._make_github_request',
                                f'src.github_mcp.tools.{module}._make_github_request'
                            )
                        if 'src.github_mcp.utils.requests._get_auth_token_fallback' in lines[j]:
                            lines[j] = lines[j].replace(
                                'src.github_mcp.utils.requests._get_auth_token_fallback',
                                f'src.github_mcp.tools.{module}._get_auth_token_fallback'
                            )
                        j -= 1
        
        new_lines.append(line)
        i += 1
    
    new_content = ''.join(new_lines)
    
    # Also do general replacements for any remaining utils.requests patterns
    new_content = re.sub(
        r"@patch\('src\.github_mcp\.utils\.requests\._make_github_request'\)",
        lambda m: m.group(0),  # Keep as is for now, will be fixed by tool-specific logic
        new_content
    )
    
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    if new_content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def fix_file_simple(filepath):
    """Simple approach: replace based on test function name."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Find all test functions
    test_pattern = r'(async def (test_github_\w+).*?)(?=\n    async def|\nclass|\Z)'
    tests = re.finditer(test_pattern, content, re.DOTALL)
    
    for test_match in tests:
        test_block = test_match.group(1)
        test_name = test_match.group(2)
        
        # Extract tool name
        tool_match = re.search(r'test_github_(\w+)', test_name)
        if tool_match:
            tool_name = f"github_{tool_match.group(1)}"
            module = TOOL_TO_MODULE.get(tool_name)
            
            if module:
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
                
                if new_block != test_block:
                    content = content.replace(test_block, new_block)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """Fix mock paths in test files."""
    test_files = [
        'tests/test_write_operations_auth.py',
        'tests/test_response_formatting.py',
    ]
    
    updated = []
    for filepath in test_files:
        path = Path(filepath)
        if path.exists() and fix_file_simple(path):
            updated.append(path.name)
            print(f"✅ Updated: {path.name}")
    
    print(f"\n📊 Total files updated: {len(updated)}")


if __name__ == '__main__':
    main()


