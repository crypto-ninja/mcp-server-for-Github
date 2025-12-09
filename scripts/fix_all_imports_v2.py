#!/usr/bin/env python3
"""
Comprehensive script to fix all import issues in test files.

Fixes:
1. 'from src.github_mcp import <Model>' -> 'from src.github_mcp.models import <Model>'
2. Missing tool imports
3. Inline imports within test functions
"""

import re
from pathlib import Path

# All model names that should be imported from models
MODEL_NAMES = [
    'RepoInfoInput', 'ListIssuesInput', 'CreateIssueInput', 'UpdateIssueInput',
    'GetFileContentInput', 'SearchCodeInput', 'ListCommitsInput', 
    'GetPullRequestDetailsInput', 'ListPullRequestsInput', 'GetReleaseInput', 
    'ListReleasesInput', 'CreateReleaseInput', 'UpdateReleaseInput', 
    'GetUserInfoInput', 'ListWorkflowsInput', 'GetWorkflowRunsInput',
    'CreatePullRequestInput', 'MergePullRequestInput', 'ClosePullRequestInput',
    'CreatePRReviewInput', 'GitHubStrReplaceInput', 'SearchIssuesInput', 
    'SearchRepositoriesInput', 'BatchFileOperationsInput', 'CreateFileInput', 
    'UpdateFileInput', 'DeleteFileInput', 'ListRepoContentsInput', 
    'TransferRepositoryInput', 'ArchiveRepositoryInput', 'CreateRepositoryInput',
    'DeleteRepositoryInput', 'UpdateRepositoryInput', 'GraphQLPROverviewInput', 
    'WorkflowSuggestionInput', 'GitHubGrepInput', 'GitHubReadFileChunkInput',
    'ListDiscussionsInput', 'GetDiscussionInput', 'ListDiscussionCategoriesInput',
    'ListDiscussionCommentsInput', 'ResponseFormat',
]


def fix_file_imports(filepath):
    """Fix all import issues in a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # Pattern 1: Single line imports
    # from src.github_mcp import Model1, Model2, Tool1
    pattern1 = r"from src\.github_mcp import\s+([A-Z][a-zA-Z0-9_]*(?:\s*,\s*[A-Z][a-zA-Z0-9_]*)*)"
    
    def replace_import(match):
        imports_str = match.group(1)
        imports = [imp.strip() for imp in imports_str.split(',')]
        
        # Separate models and tools
        models = [imp for imp in imports if any(model == imp for model in MODEL_NAMES)]
        tools = [imp for imp in imports if imp not in models]
        
        if models:
            # Create models import
            models_import = f"from src.github_mcp.models import {', '.join(models)}"
            changes.append(f"Fixed: {match.group(0).strip()} -> models import")
            
            if tools:
                # Keep tools import as is (or create separate tools import if needed)
                return models_import + "\n" + f"from src.github_mcp.tools import {', '.join(tools)}"
            else:
                return models_import
        return match.group(0)
    
    content = re.sub(pattern1, replace_import, content)
    
    # Pattern 2: Multi-line imports with parentheses
    # from src.github_mcp import (
    #     Model1,
    #     Model2,
    # )
    pattern2 = r"from src\.github_mcp import\s*\(([^)]+)\)"
    
    def replace_multiline_import(match):
        imports_str = match.group(1)
        imports = [imp.strip() for imp in re.split(r'[,\n]', imports_str) if imp.strip()]
        
        # Separate models and tools
        models = [imp for imp in imports if any(model == imp for model in MODEL_NAMES)]
        tools = [imp for imp in imports if imp not in models]
        
        if models:
            changes.append(f"Fixed multi-line import with {len(models)} models")
            
            if tools:
                # Split into two imports
                models_block = "from src.github_mcp.models import (\n    " + ",\n    ".join(models) + "\n)"
                tools_block = "from src.github_mcp.tools import (\n    " + ",\n    ".join(tools) + "\n)"
                return models_block + "\n" + tools_block
            else:
                return "from src.github_mcp.models import (\n    " + ",\n    ".join(models) + "\n)"
        return match.group(0)
    
    content = re.sub(pattern2, replace_multiline_import, content, flags=re.MULTILINE)
    
    # Pattern 3: Inline imports within functions
    # from src.github_mcp import Model
    pattern3 = r"(\s+)from src\.github_mcp import\s+([A-Z][a-zA-Z0-9_]*)"
    
    def replace_inline_import(match):
        indent = match.group(1)
        model_name = match.group(2)
        
        if any(model == model_name for model in MODEL_NAMES):
            changes.append(f"Fixed inline import: {model_name}")
            return f"{indent}from src.github_mcp.models import {model_name}"
        return match.group(0)
    
    content = re.sub(pattern3, replace_inline_import, content)
    
    # Special fix for discussions test
    if 'test_discussions_tools.py' in str(filepath):
        if 'github_list_discussions' not in content:
            # Find the tools import and add it
            pattern = r"(from src\.github_mcp\.tools import[^\n]*)"
            match = re.search(pattern, content)
            if match:
                old_line = match.group(1)
                if 'github_get_discussion' in old_line:
                    # Check if it's a multi-line import
                    if '(' in content[content.find(old_line):content.find(old_line)+200]:
                        # Multi-line import
                        pattern_ml = r"(from src\.github_mcp\.tools import\s*\([^)]*github_get_discussion[^)]*\))"
                        match_ml = re.search(pattern_ml, content, re.DOTALL)
                        if match_ml:
                            old_block = match_ml.group(1)
                            if 'github_list_discussions' not in old_block:
                                new_block = old_block.replace(
                                    'github_get_discussion,',
                                    'github_get_discussion,\n    github_list_discussions,'
                                )
                                content = content.replace(old_block, new_block)
                                changes.append("Added github_list_discussions to multi-line import")
                    else:
                        # Single line import
                        new_line = old_line.replace(
                            'github_get_discussion,',
                            'github_get_discussion, github_list_discussions,'
                        )
                        content = content.replace(old_line, new_line)
                        changes.append("Added github_list_discussions import")
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    return []


def main():
    """Fix imports in all test files."""
    test_files = [
        'tests/test_individual_tools.py',
        'tests/test_discussions_tools.py',
        'tests/test_actions_tools.py',
        'tests/test_security_tools.py',
        'tests/test_projects_tools.py',
        'tests/test_notifications_collaborators_tools.py',
    ]
    
    total_changes = 0
    for filepath_str in test_files:
        filepath = Path(filepath_str)
        if filepath.exists():
            changes = fix_file_imports(filepath)
            if changes:
                print(f"\n✅ Fixed {len(changes)} issues in {filepath.name}:")
                for change in changes[:10]:  # Show first 10
                    print(f"   • {change}")
                if len(changes) > 10:
                    print(f"   ... and {len(changes) - 10} more")
                total_changes += len(changes)
            else:
                print(f"ℹ️  {filepath.name}: No changes needed")
        else:
            print(f"⚠️  File not found: {filepath_str}")
    
    print(f"\n📊 Total: Fixed {total_changes} import issues across all files")


if __name__ == '__main__':
    main()

