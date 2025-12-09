#!/usr/bin/env python3
"""
Fix all remaining mock paths in test_individual_tools.py that still use utils.requests.
"""

import re
from pathlib import Path

# Map tool names to their modules
TOOL_TO_MODULE = {
    'github_get_repo_info': 'repositories',
    'github_list_issues': 'issues',
    'github_create_issue': 'issues',
    'github_update_issue': 'issues',
    'github_get_file_content': 'files',
    'github_search_code': 'search',
    'github_list_commits': 'commits',
    'github_get_pr_details': 'pull_requests',
    'github_list_pull_requests': 'pull_requests',
    'github_get_release': 'releases',
    'github_list_releases': 'releases',
    'github_create_release': 'releases',
    'github_update_release': 'releases',
    'github_get_user_info': 'users',
    'github_list_workflows': 'actions',
    'github_get_workflow_runs': 'actions',
    'github_create_pull_request': 'pull_requests',
    'github_merge_pull_request': 'pull_requests',
    'github_close_pull_request': 'pull_requests',
    'github_create_pr_review': 'pull_requests',
    'github_str_replace': 'files',
    'github_search_issues': 'search',
    'github_search_repositories': 'search',
    'github_batch_file_operations': 'files',
    'github_list_repo_contents': 'files',
    'github_create_file': 'files',
    'github_update_file': 'files',
    'github_delete_file': 'files',
    'github_transfer_repository': 'repositories',
    'github_archive_repository': 'repositories',
    'github_create_repository': 'repositories',
    'github_delete_repository': 'repositories',
    'github_update_repository': 'repositories',
    'github_suggest_workflow': 'actions',
    'github_license_info': 'misc',
    'github_grep': 'files',
    'github_read_file_chunk': 'files',
}


def fix_file(filepath):
    """Fix all remaining mock paths in test_individual_tools.py."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Find all test functions with utils.requests mock
    pattern = r"@patch\('src\.github_mcp\.utils\.requests\._make_github_request'\)\s*\n\s*async def (test_github_\w+)"
    matches = list(re.finditer(pattern, content))
    
    for match in matches:
        test_name = match.group(1)
        # Extract tool name from test name
        tool_match = re.search(r'test_github_(\w+)', test_name)
        if tool_match:
            tool_name = f"github_{tool_match.group(1)}"
            module = TOOL_TO_MODULE.get(tool_name)
            
            if module:
                # Replace the mock path
                old_patch = match.group(0)
                new_patch = old_patch.replace(
                    "src.github_mcp.utils.requests._make_github_request",
                    f"src.github_mcp.tools.{module}._make_github_request"
                )
                content = content.replace(old_patch, new_patch)
            else:
                print(f"⚠️  No module mapping for {tool_name} in test {test_name}")
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """Fix all remaining mock paths."""
    filepath = Path('tests/test_individual_tools.py')
    if fix_file(filepath):
        print(f"✅ Updated: {filepath.name}")
        print("📊 Fixed all remaining mock paths")
    else:
        print(f"ℹ️  No changes needed: {filepath.name}")


if __name__ == '__main__':
    main()

