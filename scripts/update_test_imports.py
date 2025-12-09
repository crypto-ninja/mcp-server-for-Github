#!/usr/bin/env python3
"""
Script to update test imports for new module structure.

This script updates all test files to use the new modular import structure:
- Tools: from src.github_mcp.tools import ...
- Models: from src.github_mcp.models import ...
- Utils: from src.github_mcp.utils.requests import ...
"""

import re
from pathlib import Path

# Mapping of old imports to new imports
IMPORT_REPLACEMENTS = [
    # Tool imports - match individual tool imports
    (r'from github_mcp import\s+((?:github_\w+,\s*)+github_\w+)', 
     lambda m: f'from src.github_mcp.tools import {m.group(1)}'),
    
    # Model imports - match Input models
    (r'from github_mcp import\s+((?:\w+Input,\s*)+\w+Input)',
     lambda m: f'from src.github_mcp.models import {m.group(1)}'),
    
    # Mixed imports - need to split them
    (r'from github_mcp import\s+((?:github_\w+|\w+Input|ResponseFormat)(?:,\s*(?:github_\w+|\w+Input|ResponseFormat))*)',
     lambda m: f'from src.github_mcp import {m.group(1)}'),  # Will be handled by __init__.py
    
    # Utility function imports
    (r'from github_mcp import _make_github_request',
     r'from src.github_mcp.utils.requests import _make_github_request'),
    (r'from github_mcp import _get_auth_token_fallback',
     r'from src.github_mcp.utils.requests import _get_auth_token_fallback'),
    (r'from github_mcp import _handle_api_error',
     r'from src.github_mcp.utils.errors import _handle_api_error'),
    
    # Module imports - keep github_mcp for backward compat but update mocks
    # (r'^import github_mcp$', r'import src.github_mcp.tools as github_mcp'),
    
    # Mock decorators - patch at the source (simpler)
    (r"@patch\.object\(github_mcp, '_make_github_request'\)",
     r"@patch('src.github_mcp.utils.requests._make_github_request')"),
    (r"@patch\.object\(github_mcp, '_get_auth_token_fallback'\)",
     r"@patch('src.github_mcp.utils.requests._get_auth_token_fallback')"),
    (r"@patch\('github_mcp\._make_github_request'\)",
     r"@patch('src.github_mcp.utils.requests._make_github_request')"),
    (r"@patch\('github_mcp\._get_auth_token_fallback'\)",
     r"@patch('src.github_mcp.utils.requests._get_auth_token_fallback')"),
]


def update_file(filepath):
    """Update imports in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Apply replacements
    for pattern, replacement in IMPORT_REPLACEMENTS:
        if callable(replacement):
            content = re.sub(pattern, replacement, content)
        else:
            content = re.sub(pattern, replacement, content)
    
    # Special handling for mixed imports - split them properly
    # Match: from github_mcp import (tool1, tool2, ModelInput, ResponseFormat)
    def split_mixed_imports(match):
        imports = match.group(1)
        tools = []
        models = []
        enums = []
        
        for item in imports.split(','):
            item = item.strip()
            if item.startswith('github_'):
                tools.append(item)
            elif item.endswith('Input'):
                models.append(item)
            elif item in ['ResponseFormat', 'IssueState', 'PullRequestState', 'SortOrder']:
                enums.append(item)
        
        result = []
        if tools:
            result.append(f'from src.github_mcp.tools import {", ".join(tools)}')
        if models:
            result.append(f'from src.github_mcp.models import {", ".join(models)}')
        if enums:
            result.append(f'from src.github_mcp.models import {", ".join(enums)}')
        
        return '\n'.join(result) if result else match.group(0)
    
    # Match multi-line imports
    content = re.sub(
        r'from github_mcp import\s*\(((?:[^)]|\n)+)\)',
        split_mixed_imports,
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """Update all test files."""
    test_dir = Path('tests')
    updated = []
    
    for filepath in test_dir.glob('test_*.py'):
        if update_file(filepath):
            updated.append(filepath.name)
            print(f"✅ Updated: {filepath.name}")
    
    print(f"\n📊 Total files updated: {len(updated)}")
    if updated:
        print("\nFiles updated:")
        for f in updated:
            print(f"  - {f}")


if __name__ == '__main__':
    main()

