#!/usr/bin/env python3
"""
Fix remaining incorrect mock paths in test_individual_tools.py.

Many tests are using releases._make_github_request but should be using
the correct module based on the tool being tested.
"""

import re
from pathlib import Path

# Map test function names to correct modules
TEST_TO_MODULE = {
    'test_github_create_issue_permission_denied': 'issues',
    'test_github_get_file_content_not_found': 'files',
    'test_github_search_code_empty_results': 'search',
    'test_github_list_releases': 'releases',
    'test_github_get_release': 'releases',
    'test_github_create_release': 'releases',
    'test_github_list_workflows': 'actions',
    'test_github_get_workflow_runs': 'actions',
    'test_github_list_releases_with_pagination': 'releases',
    'test_github_list_releases_empty': 'releases',
    'test_github_get_release_by_tag': 'releases',
    'test_github_get_release_not_found': 'releases',
    'test_github_update_release_draft': 'releases',
}


def fix_file(filepath):
    """Fix incorrect mock paths."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # Find all @patch lines followed by test functions
    pattern = r"@patch\('src\.github_mcp\.tools\.releases\._make_github_request'\)\s*\n\s*async def (test_\w+)"
    matches = list(re.finditer(pattern, content))
    
    for match in matches:
        test_name = match.group(1)
        module = TEST_TO_MODULE.get(test_name, 'releases')  # Default to releases if not found
        
        if module != 'releases':
            old_patch = match.group(0)
            new_patch = old_patch.replace(
                'src.github_mcp.tools.releases._make_github_request',
                f'src.github_mcp.tools.{module}._make_github_request'
            )
            content = content.replace(old_patch, new_patch)
            changes.append(f"{test_name} -> {module}")
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    return []


def main():
    """Fix remaining mock paths."""
    filepath = Path('tests/test_individual_tools.py')
    changes = fix_file(filepath)
    if changes:
        print(f"\n✅ Fixed {len(changes)} mock paths:")
        for change in changes:
            print(f"   • {change}")
    else:
        print(f"ℹ️  No changes needed: {filepath.name}")


if __name__ == '__main__':
    main()

