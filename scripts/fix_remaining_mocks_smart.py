#!/usr/bin/env python3
"""
Fix remaining mock paths by analyzing test function names and tool calls.
"""

import re
from pathlib import Path

# Map patterns in test names to modules
TEST_PATTERN_TO_MODULE = {
    # Commits
    r'list_commits': 'commits',
    r'get.*commit': 'commits',
    
    # Issues
    r'list_issues': 'issues',
    r'create_issue': 'issues',
    r'update_issue': 'issues',
    r'issue.*label': 'issues',
    r'issue.*assignee': 'issues',
    r'issue.*milestone': 'issues',
    
    # Pull Requests
    r'list_pull_requests': 'pull_requests',
    r'get_pr_details': 'pull_requests',
    r'create.*pr': 'pull_requests',
    r'merge.*pr': 'pull_requests',
    r'close.*pr': 'pull_requests',
    r'pr.*review': 'pull_requests',
    
    # Releases
    r'list_releases': 'releases',
    r'get_release': 'releases',
    r'create_release': 'releases',
    r'update_release': 'releases',
    
    # Files
    r'list_repo_contents': 'files',
    r'get_file_content': 'files',
    r'batch_file': 'files',
    r'str_replace': 'files',
    r'grep': 'files',
    r'read_file_chunk': 'files',
    r'large_file': 'files',
    
    # Actions
    r'list_workflows': 'actions',
    r'get_workflow': 'actions',
    r'workflow.*run': 'actions',
    r'suggest_workflow': 'actions',
    
    # Search
    r'search_code': 'search',
    r'search_issues': 'search',
    r'search_repositories': 'search',
    
    # Users
    r'get_user_info': 'users',
    
    # Repositories
    r'get_repo_info': 'repositories',
    r'create_repository': 'repositories',
    r'delete_repository': 'repositories',
    r'update_repository': 'repositories',
    r'transfer_repository': 'repositories',
    r'archive_repository': 'repositories',
    r'empty_repo': 'repositories',
    
    # Error handling (use repositories as default)
    r'error': 'repositories',
    r'validation': 'repositories',
    r'gone': 'repositories',
    r'conflict': 'repositories',
    r'server_error': 'repositories',
    r'timeout': 'repositories',
    r'workflow': 'actions',  # More specific
    r'release_workflow': 'releases',
}


def get_module_for_test(test_name):
    """Determine module based on test name patterns."""
    for pattern, module in TEST_PATTERN_TO_MODULE.items():
        if re.search(pattern, test_name, re.IGNORECASE):
            return module
    return 'repositories'  # Default fallback


def fix_file(filepath):
    """Fix all remaining mock paths."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Find all @patch with utils.requests
    pattern = r"@patch\('src\.github_mcp\.utils\.requests\._make_github_request'\)\s*\n\s*async def (test_\w+)"
    matches = list(re.finditer(pattern, content))
    
    for match in matches:
        test_name = match.group(1)
        module = get_module_for_test(test_name)
        
        # Replace the mock path
        old_patch = match.group(0)
        new_patch = old_patch.replace(
            "src.github_mcp.utils.requests._make_github_request",
            f"src.github_mcp.tools.{module}._make_github_request"
        )
        content = content.replace(old_patch, new_patch)
        print(f"✅ Fixed {test_name} -> {module}")
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return len(matches)
    return 0


def main():
    """Fix all remaining mock paths."""
    filepath = Path('tests/test_individual_tools.py')
    count = fix_file(filepath)
    if count > 0:
        print(f"\n📊 Fixed {count} mock paths in {filepath.name}")
    else:
        print(f"ℹ️  No changes needed: {filepath.name}")


if __name__ == '__main__':
    main()

