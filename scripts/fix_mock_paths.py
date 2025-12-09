#!/usr/bin/env python3
"""
Fix mock paths in test files to patch at the tool module level instead of utils level.

This is needed because tools import _make_github_request from utils, so we need to
patch where it's used (in the tool module), not where it's defined.
"""

import re
from pathlib import Path

# Map test files to their corresponding tool modules
TEST_TO_MODULE = {
    'test_actions_tools.py': 'actions',
    'test_discussions_tools.py': 'discussions',
    'test_notifications_collaborators_tools.py': 'notifications',
    'test_projects_tools.py': 'projects',
    'test_security_tools.py': 'security',
    'test_individual_tools.py': 'repositories',  # Main test file uses multiple modules
    'test_response_formatting.py': 'repositories',  # Uses repo tools
    'test_write_operations_auth.py': 'files',  # Uses file operations
}

# For files that test multiple modules, we'll need to patch at utils level
# or update each test individually
MULTI_MODULE_TESTS = ['test_individual_tools.py', 'test_response_formatting.py', 'test_write_operations_auth.py']


def fix_mock_paths(filepath):
    """Fix mock paths in a test file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    filename = Path(filepath).name
    
    # Determine the module to patch
    if filename in MULTI_MODULE_TESTS:
        # For multi-module tests, patch at utils level (works for all)
        # Actually, let's keep utils level for these since they test multiple modules
        pass
    elif filename in TEST_TO_MODULE:
        module = TEST_TO_MODULE[filename]
        # Replace utils.requests with tools.{module}
        content = re.sub(
            r"@patch\('src\.github_mcp\.utils\.requests\._make_github_request'\)",
            f"@patch('src.github_mcp.tools.{module}._make_github_request')",
            content
        )
        content = re.sub(
            r"@patch\('src\.github_mcp\.utils\.requests\._get_auth_token_fallback'\)",
            f"@patch('src.github_mcp.tools.{module}._get_auth_token_fallback')",
            content
        )
        content = re.sub(
            r"@patch\.object\(github_mcp, '_make_github_request'\)",
            f"@patch('src.github_mcp.tools.{module}._make_github_request')",
            content
        )
        content = re.sub(
            r"@patch\.object\(github_mcp, '_get_auth_token_fallback'\)",
            f"@patch('src.github_mcp.tools.{module}._get_auth_token_fallback')",
            content
        )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """Fix mock paths in all test files."""
    test_dir = Path('tests')
    updated = []
    
    for filepath in test_dir.glob('test_*.py'):
        if fix_mock_paths(filepath):
            updated.append(filepath.name)
            print(f"✅ Updated: {filepath.name}")
    
    print(f"\n📊 Total files updated: {len(updated)}")


if __name__ == '__main__':
    main()

