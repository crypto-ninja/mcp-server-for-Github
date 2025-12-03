#!/usr/bin/env python3
"""
Audit all GitHub MCP tools to check response formats.
Identifies tools that return formatted strings vs JSON.
"""
import re
from pathlib import Path

def audit_tools():
    """Audit all tools in github_mcp.py"""
    github_mcp = Path("github_mcp.py")
    content = github_mcp.read_text()
    
    # Find all tool functions
    lines = content.split('\n')
    tool_locations = {}
    tool_pattern = r'async def (github_\w+|workspace_\w+|repo_\w+|str_replace)\([^)]*\) -> str:'
    
    for i, line in enumerate(lines, 1):
        match = re.search(tool_pattern, line)
        if match:
            tool_name = match.group(1)
            tool_locations[tool_name] = i
    
    # Check return statements for each tool
    results = {
        'json': [],
        'formatted_string': [],
        'mixed': [],
        'error_string': []
    }
    
    for tool_name, start_line in tool_locations.items():
        # Find the end of this function (next async def or @conditional_tool/@mcp.tool)
        end_line = len(lines)
        for i in range(start_line, len(lines)):
            if i > start_line and (lines[i].strip().startswith('async def ') or 
                                   lines[i].strip().startswith('@conditional_tool') or
                                   lines[i].strip().startswith('@mcp.tool')):
                end_line = i
                break
        
        # Extract function body
        func_body = '\n'.join(lines[start_line-1:end_line])
        
        # Check return statements
        has_json = bool(re.search(r'return\s+json\.dumps\(', func_body))
        has_formatted = bool(re.search(r'return\s+f["\']', func_body) or 
                            re.search(r'return\s+f"""', func_body) or
                            re.search(r'return\s+result\s*$', func_body, re.MULTILINE))
        
        # Categorize
        if has_json and not has_formatted:
            results['json'].append((tool_name, start_line))
        elif has_formatted and not has_json:
            results['formatted_string'].append((tool_name, start_line))
        elif has_json and has_formatted:
            results['mixed'].append((tool_name, start_line))
        else:
            results['error_string'].append((tool_name, start_line))
    
    return results, tool_locations

if __name__ == '__main__':
    results, locations = audit_tools()
    
    print("=" * 70)
    print("TOOL RESPONSE FORMAT AUDIT")
    print("=" * 70)
    print(f"\nTotal tools found: {sum(len(v) for v in results.values())}")
    print(f"\n✅ JSON only: {len(results['json'])}")
    print(f"❌ Formatted strings: {len(results['formatted_string'])}")
    print(f"⚠️  Mixed (JSON + strings): {len(results['mixed'])}")
    print(f"🔧 Error strings only: {len(results['error_string'])}")
    
    print("\n" + "=" * 70)
    print("TOOLS RETURNING FORMATTED STRINGS (NEED FIX)")
    print("=" * 70)
    for tool, line in sorted(results['formatted_string'], key=lambda x: x[1]):
        print(f"  ❌ {tool:40} (line {line})")
    
    print("\n" + "=" * 70)
    print("TOOLS WITH MIXED RESPONSES")
    print("=" * 70)
    for tool, line in sorted(results['mixed'], key=lambda x: x[1]):
        print(f"  ⚠️  {tool:40} (line {line})")
    
    print("\n" + "=" * 70)
    print("TOOLS RETURNING JSON (GOOD)")
    print("=" * 70)
    for tool, line in sorted(results['json'], key=lambda x: x[1]):
        print(f"  ✅ {tool:40} (line {line})")

