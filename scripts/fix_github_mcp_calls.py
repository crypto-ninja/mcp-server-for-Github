#!/usr/bin/env python3
"""
Fix all 'github_mcp.github_*' calls to use direct function calls.

Since tools are imported at the top, we should use them directly instead of
going through the github_mcp module.
"""

import re
from pathlib import Path


def fix_file(filepath):
    """Fix all github_mcp.github_* calls in a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # Pattern: await github_mcp.github_<tool_name>(params)
    pattern = r'await github_mcp\.(github_\w+)\(([^)]+)\)'
    
    def replace_call(match):
        tool_name = match.group(1)
        params = match.group(2)
        new_call = f'await {tool_name}({params})'
        changes.append(f"{match.group(0)} -> {new_call}")
        return new_call
    
    content = re.sub(pattern, replace_call, content)
    
    # Also handle: result = await github_mcp.github_* without await
    pattern2 = r'github_mcp\.(github_\w+)\(([^)]+)\)'
    
    def replace_call2(match):
        tool_name = match.group(1)
        params = match.group(2)
        new_call = f'{tool_name}({params})'
        if match.group(0) not in [c.split(' -> ')[0] for c in changes]:
            changes.append(f"{match.group(0)} -> {new_call}")
        return new_call
    
    content = re.sub(pattern2, replace_call2, content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    return []


def main():
    """Fix github_mcp calls in test files."""
    test_files = [
        'tests/test_individual_tools.py',
    ]
    
    total_changes = 0
    for filepath_str in test_files:
        filepath = Path(filepath_str)
        if filepath.exists():
            changes = fix_file(filepath)
            if changes:
                print(f"\n✅ Fixed {len(changes)} calls in {filepath.name}:")
                for change in changes[:10]:  # Show first 10
                    print(f"   • {change}")
                if len(changes) > 10:
                    print(f"   ... and {len(changes) - 10} more")
                total_changes += len(changes)
            else:
                print(f"ℹ️  {filepath.name}: No changes needed")
        else:
            print(f"⚠️  File not found: {filepath_str}")
    
    print(f"\n📊 Total: Fixed {total_changes} function calls")


if __name__ == '__main__':
    main()

