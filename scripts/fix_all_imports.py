#!/usr/bin/env python3
"""
Fix all import issues in test files:
1. Change 'from src.github_mcp import' to 'from src.github_mcp.models import' for model imports
2. Add missing tool imports
3. Fix specific import issues
"""

import re
from pathlib import Path

# List of all model names (Pydantic input models)
MODEL_NAMES = [
    'RepoInfoInput', 'ListIssuesInput', 'CreateIssueInput', 'UpdateIssueInput',
    'GetFileContentInput', 'SearchCodeInput', 'ListCommitsInput', 'GetPullRequestDetailsInput',
    'ListPullRequestsInput', 'GetReleaseInput', 'ListReleasesInput', 'CreateReleaseInput',
    'UpdateReleaseInput', 'GetUserInfoInput', 'ListWorkflowsInput', 'GetWorkflowRunsInput',
    'CreatePullRequestInput', 'MergePullRequestInput', 'ClosePullRequestInput',
    'CreatePRReviewInput', 'GitHubStrReplaceInput', 'SearchIssuesInput', 'SearchRepositoriesInput',
    'BatchFileOperationsInput', 'CreateFileInput', 'UpdateFileInput', 'DeleteFileInput',
    'ListRepoContentsInput', 'TransferRepositoryInput', 'ArchiveRepositoryInput',
    'CreateRepositoryInput', 'DeleteRepositoryInput', 'UpdateRepositoryInput',
    'GraphQLPROverviewInput', 'WorkflowSuggestionInput', 'GitHubGrepInput',
    'GitHubReadFileChunkInput', 'ListDiscussionsInput', 'GetDiscussionInput',
    'ListDiscussionCategoriesInput', 'ListDiscussionCommentsInput', 'ResponseFormat',
]

# List of all tool names
TOOL_NAMES = [
    'github_get_repo_info', 'github_list_issues', 'github_create_issue', 'github_update_issue',
    'github_get_file_content', 'github_search_code', 'github_list_commits',
    'github_get_pr_details', 'github_list_pull_requests', 'github_get_release',
    'github_list_releases', 'github_create_release', 'github_update_release',
    'github_get_user_info', 'github_list_workflows', 'github_get_workflow_runs',
    'github_create_pull_request', 'github_merge_pull_request', 'github_close_pull_request',
    'github_create_pr_review', 'github_str_replace', 'github_search_issues',
    'github_search_repositories', 'github_batch_file_operations', 'github_create_file',
    'github_update_file', 'github_delete_file', 'github_list_repo_contents',
    'github_transfer_repository', 'github_archive_repository', 'github_create_repository',
    'github_delete_repository', 'github_update_repository', 'github_suggest_workflow',
    'github_license_info', 'github_list_discussions', 'github_get_discussion',
    'github_list_discussion_categories', 'github_list_discussion_comments',
]


def is_model_import(line):
    """Check if a line imports a model."""
    for model in MODEL_NAMES:
        if model in line:
            return True
    return False


def fix_imports_in_file(filepath):
    """Fix imports in a test file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    original = ''.join(lines)
    new_lines = []
    i = 0
    changes_made = []
    
    while i < len(lines):
        line = lines[i]
        
        # Fix: from src.github_mcp import <Model> -> from src.github_mcp.models import <Model>
        if re.match(r'\s*from src\.github_mcp import', line):
            # Check if this line or next lines contain model names
            import_line = line
            j = i
            while j < len(lines) and (lines[j].strip().endswith(',') or 
                                      (j == i and '(' in lines[j])):
                import_line += lines[j]
                j += 1
            
            if is_model_import(import_line):
                # Replace with models import
                new_line = line.replace('from src.github_mcp import', 'from src.github_mcp.models import')
                new_lines.append(new_line)
                if new_line != line:
                    changes_made.append(f"Fixed model import: {line.strip()}")
                # Skip continuation lines if any
                i = j
                continue
        
        # Fix: Missing github_list_discussions import in discussions test
        if 'test_discussions_tools.py' in str(filepath):
            if 'from src.github_mcp.tools import' in line and 'github_list_discussions' not in line:
                # Check if we need to add it
                if 'github_get_discussion' in line:
                    # Add github_list_discussions to the import
                    line = line.replace(
                        'github_get_discussion,',
                        'github_get_discussion, github_list_discussions,'
                    )
                    if line != lines[i]:
                        changes_made.append("Added github_list_discussions import")
        
        new_lines.append(line)
        i += 1
    
    new_content = ''.join(new_lines)
    
    if new_content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return changes_made
    return []


def fix_imports_simple(filepath):
    """Simpler approach: replace all 'from src.github_mcp import' with 'from src.github_mcp.models import'."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # Pattern: from src.github_mcp import <something>
    # We want to replace with from src.github_mcp.models import <something>
    # But only if it's importing a model
    
    # Find all import statements
    pattern = r"from src\.github_mcp import\s+([A-Z][a-zA-Z0-9_]*(?:\s*,\s*[A-Z][a-zA-Z0-9_]*)*)"
    matches = list(re.finditer(pattern, content))
    
    for match in matches:
        imports = match.group(1)
        # Check if any model names are in the imports
        has_models = any(model in imports for model in MODEL_NAMES)
        
        if has_models:
            # Replace with models import
            old_import = match.group(0)
            new_import = old_import.replace('from src.github_mcp import', 'from src.github_mcp.models import')
            content = content.replace(old_import, new_import)
            changes.append(f"Fixed: {old_import.strip()}")
    
    # Also handle multi-line imports
    pattern = r"from src\.github_mcp import\s*\(([^)]+)\)"
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    for match in matches:
        imports = match.group(1)
        # Check if any model names are in the imports
        has_models = any(model in imports for model in MODEL_NAMES)
        
        if has_models:
            # Replace with models import
            old_import = match.group(0)
            new_import = old_import.replace('from src.github_mcp import', 'from src.github_mcp.models import')
            content = content.replace(old_import, new_import)
            changes.append(f"Fixed multi-line: {old_import[:50]}...")
    
    # Fix discussions test - add missing import
    if 'test_discussions_tools.py' in str(filepath):
        if 'github_list_discussions' not in content and 'from src.github_mcp.tools import' in content:
            # Find the tools import line
            pattern = r"(from src\.github_mcp\.tools import[^\n]*)"
            match = re.search(pattern, content)
            if match:
                old_line = match.group(1)
                if 'github_get_discussion' in old_line and 'github_list_discussions' not in old_line:
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
            changes = fix_imports_simple(filepath)
            if changes:
                print(f"\n✅ Fixed {len(changes)} imports in {filepath.name}:")
                for change in changes[:5]:  # Show first 5
                    print(f"   {change}")
                if len(changes) > 5:
                    print(f"   ... and {len(changes) - 5} more")
                total_changes += len(changes)
            else:
                print(f"ℹ️  No changes needed: {filepath.name}")
        else:
            print(f"⚠️  File not found: {filepath_str}")
    
    print(f"\n📊 Total: Fixed {total_changes} import statements")


if __name__ == '__main__':
    main()

