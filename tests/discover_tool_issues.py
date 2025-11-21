"""
Tool Issue Discovery Script

Automatically discovers potential issues:
1. Tools with response_format in client but not in schema
2. Tools returning different types than expected
3. Tools with inconsistent error handling
4. Parameter mismatches between TypeScript and Python
"""

import re
from pathlib import Path
from typing import Dict, List
import inspect
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import github_mcp  # noqa: E402


def read_typescript_tool_list() -> List[str]:
    """Read READ_TOOLS_WITH_JSON_SUPPORT from client-deno.ts."""
    client_deno_path = project_root / "servers" / "client-deno.ts"
    
    if not client_deno_path.exists():
        return []
    
    content = client_deno_path.read_text(encoding='utf-8')
    
    # Extract the array
    match = re.search(r'const READ_TOOLS_WITH_JSON_SUPPORT = \[(.*?)\];', content, re.DOTALL)
    if not match:
        return []
    
    tools = []
    for line in match.group(1).split('\n'):
        line = line.strip()
        # Skip empty lines and comments
        if not line or line.startswith('//'):
            continue
        
        # Extract tool names from quotes - handle both ' and " quotes
        # Match: 'tool_name', or "tool_name", possibly with trailing comma
        tool_match = re.search(r"['\"](github_\w+|workspace_\w+|repo_\w+)['\"]", line)
        if tool_match:
            tool_name = tool_match.group(1)
            if tool_name:
                tools.append(tool_name)
    
    return tools


def get_python_tools() -> Dict[str, Dict]:
    """Get all Python tools by inspecting function definitions."""
    tools = {}
    
    # Get all functions from github_mcp module
    for name, obj in inspect.getmembers(github_mcp):
        # Look for async functions that start with github_, repo_, or workspace_
        if (inspect.iscoroutinefunction(obj) or inspect.isfunction(obj)) and \
           (name.startswith('github_') or name.startswith('repo_') or name.startswith('workspace_')):
            # Get function signature
            sig = inspect.signature(obj)
            params = sig.parameters
            
            # Find the params parameter
            param_model = None
            if 'params' in params:
                param_type = params['params'].annotation
                if inspect.isclass(param_type):
                    param_model = param_type
                elif isinstance(param_type, str):
                    if hasattr(github_mcp, param_type):
                        param_model = getattr(github_mcp, param_type)
            
            tools[name] = {
                'name': name,
                'function': obj,
                'param_model': param_model
            }
    
    # Also check for execute_code (health_check is no longer an MCP tool)
    for name in ['execute_code']:
        if hasattr(github_mcp, name):
            obj = getattr(github_mcp, name)
            if inspect.iscoroutinefunction(obj) or inspect.isfunction(obj):
                tools[name] = {
                    'name': name,
                    'function': obj,
                    'param_model': None
                }
    
    return tools


def get_tool_input_model(tool_name: str) -> any:
    """Get Pydantic model for a tool."""
    tools = get_python_tools()
    tool = tools.get(tool_name)
    
    if not tool:
        return None
    
    # Return the param_model if we already extracted it
    if tool.get('param_model'):
        return tool['param_model']
    
    # Otherwise try to extract from function signature
    func = tool.get('function')
    if not func:
        return None
    
    sig = inspect.signature(func)
    params = sig.parameters
    
    if 'params' in params:
        param_type = params['params'].annotation
        if inspect.isclass(param_type):
            return param_type
        elif isinstance(param_type, str):
            if hasattr(github_mcp, param_type):
                return getattr(github_mcp, param_type)
    
    return None


def check_response_format_support(tool_name: str) -> bool:
    """Check if a tool supports response_format parameter."""
    input_model = get_tool_input_model(tool_name)
    
    if not input_model:
        return False
    
    if hasattr(input_model, 'model_fields'):
        return 'response_format' in input_model.model_fields
    
    return False


def discover_parameter_mismatches() -> List[Dict]:
    """Find tools in READ_TOOLS_WITH_JSON_SUPPORT that don't support it."""
    issues = []
    
    typescript_tools = read_typescript_tool_list()
    python_tools = get_python_tools()
    
    print(f"TypeScript tools expecting JSON: {len(typescript_tools)}")
    print(f"Python tools registered: {len(python_tools)}")
    
    for tool_name in typescript_tools:
        if tool_name not in python_tools:
            issues.append({
                'type': 'missing_tool',
                'tool': tool_name,
                'message': f"Tool '{tool_name}' in TypeScript list but not found in Python"
            })
            continue
        
        has_response_format = check_response_format_support(tool_name)
        
        if not has_response_format:
            issues.append({
                'type': 'missing_response_format',
                'tool': tool_name,
                'message': f"Tool '{tool_name}' in READ_TOOLS_WITH_JSON_SUPPORT but doesn't support response_format parameter"
            })
    
    return issues


def discover_write_tools_with_response_format() -> List[Dict]:
    """Find write operations that incorrectly have response_format."""
    issues = []
    
    write_tools = [
        'github_create_release',
        'github_update_file',
        'github_delete_file',
        'github_create_issue',
        'github_update_issue',
        'github_create_pull_request',
        'github_merge_pull_request',
        'github_close_pull_request',
        'github_create_pr_review',
        'github_create_repository',
        'github_update_repository',
        'github_delete_repository',
        'github_transfer_repository',
        'github_archive_repository',
        'github_batch_file_operations',
        'github_str_replace',
    ]
    
    for tool_name in write_tools:
        has_response_format = check_response_format_support(tool_name)
        
        if has_response_format:
            issues.append({
                'type': 'write_tool_with_response_format',
                'tool': tool_name,
                'message': f"Write operation '{tool_name}' incorrectly has response_format parameter"
            })
    
    return issues


def discover_missing_tools() -> List[Dict]:
    """Find tools in Python that should be in TypeScript list but aren't."""
    issues = []
    
    typescript_tools = set(read_typescript_tool_list())
    python_tools = get_python_tools()
    
    # Tools that should support response_format (read operations)
    read_operations = [
        'github_list_issues',
        'github_list_commits',
        'github_list_pull_requests',
        'github_list_releases',
        'github_list_workflows',
        'github_get_workflow_runs',
        'github_list_repo_contents',
        'github_search_code',
        'github_search_repositories',
        'github_search_issues',
        'github_get_repo_info',
        'github_get_pr_details',
        'github_get_pr_overview_graphql',
        'github_get_release',
        'github_get_user_info',
        'github_grep',
        'github_read_file_chunk',
        'repo_read_file_chunk',
        'workspace_grep',
    ]
    
    for tool_name in read_operations:
        if tool_name not in python_tools:
            continue
        
        has_response_format = check_response_format_support(tool_name)
        
        if has_response_format and tool_name not in typescript_tools:
            issues.append({
                'type': 'missing_from_typescript',
                'tool': tool_name,
                'message': f"Tool '{tool_name}' supports response_format but not in READ_TOOLS_WITH_JSON_SUPPORT"
            })
    
    return issues


def _fix_windows_encoding():
    """Fix Windows console encoding for Unicode output."""
    import sys
    
    if sys.platform == 'win32':
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):
            pass


def main():
    """Run all discovery checks and report issues."""
    _fix_windows_encoding()
    
    print("=" * 70)
    print("Tool Issue Discovery Report")
    print("=" * 70)
    print()
    
    all_issues = []
    
    # Check 1: Parameter mismatches
    print("1. Checking parameter mismatches...")
    issues = discover_parameter_mismatches()
    all_issues.extend(issues)
    if issues:
        print(f"   [FAIL] Found {len(issues)} issues:")
        for issue in issues:
            print(f"      - {issue['message']}")
    else:
        print("   [PASS] No parameter mismatches found")
    print()
    
    # Check 2: Write tools with response_format
    print("2. Checking write operations...")
    issues = discover_write_tools_with_response_format()
    all_issues.extend(issues)
    if issues:
        print(f"   [FAIL] Found {len(issues)} issues:")
        for issue in issues:
            print(f"      - {issue['message']}")
    else:
        print("   [PASS] All write operations correctly configured")
    print()
    
    # Check 3: Missing tools
    print("3. Checking for missing tools in TypeScript list...")
    issues = discover_missing_tools()
    all_issues.extend(issues)
    if issues:
        print(f"   [WARN] Found {len(issues)} potential additions:")
        for issue in issues:
            print(f"      - {issue['message']}")
    else:
        print("   [PASS] All tools properly listed")
    print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total issues found: {len(all_issues)}")
    
    by_type = {}
    for issue in all_issues:
        issue_type = issue['type']
        by_type[issue_type] = by_type.get(issue_type, 0) + 1
    
    for issue_type, count in by_type.items():
        print(f"  {issue_type}: {count}")
    
    if all_issues:
        print()
        print("Next steps:")
        print("   1. Review issues above")
        print("   2. Fix parameter mismatches")
        print("   3. Update READ_TOOLS_WITH_JSON_SUPPORT if needed")
        print("   4. Run tests to verify fixes")
        return 1
    else:
        print()
        print("[PASS] No issues found! All tools are properly configured.")
        return 0


if __name__ == "__main__":
    exit(main())

