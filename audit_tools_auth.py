#!/usr/bin/env python3
"""
Systematic audit of all GitHub MCP tools for authentication and error handling.
"""
import re
from typing import Dict, List, Tuple

def extract_tool_functions(file_path: str) -> List[Dict]:
    """Extract all tool functions and their authentication patterns."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    tools = []
    i = 0
    
    while i < len(lines):
        # Look for @conditional_tool decorator
        if '@conditional_tool' in lines[i]:
            # Find the function definition
            func_start = None
            func_name = None
            
            for j in range(i, min(i + 20, len(lines))):
                if 'async def github_' in lines[j]:
                    func_start = j
                    match = re.search(r'async def (github_\w+)', lines[j])
                    if match:
                        func_name = match.group(1)
                    break
            
            if func_name and func_start:
                # Extract function body (until next @conditional_tool or end of function)
                func_end = func_start + 1
                indent_level = len(lines[func_start]) - len(lines[func_start].lstrip())
                
                for j in range(func_start + 1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith(' ' * (indent_level + 1)) and not lines[j].startswith('\t'):
                        if lines[j].strip().startswith('@') or lines[j].strip().startswith('async def') or lines[j].strip().startswith('def '):
                            func_end = j
                            break
                else:
                    func_end = len(lines)
                
                func_body = '\n'.join(lines[func_start:func_end])
                
                # Analyze authentication patterns
                has_token_retrieval = '_get_auth_token_fallback' in func_body
                has_token_validation = 'if not auth_token' in func_body or 'if not token' in func_body
                has_token_in_request = 'token=auth_token' in func_body or 'token=token' in func_body
                
                # Determine risk level
                risk_level = "LOW"
                if any(op in func_name for op in ['create', 'update', 'delete', 'merge', 'close', 'add', 'remove', 'transfer', 'archive']):
                    risk_level = "HIGH"
                elif any(op in func_name for op in ['get', 'list', 'search']):
                    risk_level = "MEDIUM"
                
                # Check if it's a write operation
                is_write = any(op in func_name for op in ['create', 'update', 'delete', 'merge', 'close', 'add', 'remove', 'transfer', 'archive'])
                
                tools.append({
                    'name': func_name,
                    'line': func_start + 1,
                    'risk_level': risk_level,
                    'is_write': is_write,
                    'has_token_retrieval': has_token_retrieval,
                    'has_token_validation': has_token_validation,
                    'has_token_in_request': has_token_in_request,
                    'func_body_preview': func_body[:500]  # First 500 chars for context
                })
            
            i = func_start if func_start else i + 1
        else:
            i += 1
    
    return tools

def categorize_issues(tools: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Categorize tools by issues found."""
    critical = []
    high_priority = []
    low_priority = []
    
    for tool in tools:
        issues = []
        
        # Critical: High-risk write operations missing validation
        if tool['is_write'] and tool['risk_level'] == 'HIGH':
            if not tool['has_token_retrieval']:
                issues.append("Missing token retrieval fallback")
            if not tool['has_token_validation']:
                issues.append("Missing token validation (CRITICAL for write operations)")
            if not tool['has_token_in_request']:
                issues.append("Token not passed to API request")
        
        # High priority: Medium-risk operations with issues
        elif tool['risk_level'] == 'MEDIUM':
            if not tool['has_token_retrieval'] and tool['has_token_in_request']:
                issues.append("Inconsistent token handling")
            if not tool['has_token_validation']:
                issues.append("Missing token validation")
        
        # Low priority: Low-risk read operations
        else:
            if not tool['has_token_retrieval']:
                issues.append("Could benefit from token fallback")
        
        if issues:
            tool['issues'] = issues
            if tool['is_write'] and tool['risk_level'] == 'HIGH' and not tool['has_token_validation']:
                critical.append(tool)
            elif tool['risk_level'] == 'HIGH' or (tool['risk_level'] == 'MEDIUM' and issues):
                high_priority.append(tool)
            else:
                low_priority.append(tool)
    
    return critical, high_priority, low_priority

def generate_report(tools: List[Dict], critical: List[Dict], high_priority: List[Dict], low_priority: List[Dict]) -> str:
    """Generate comprehensive audit report."""
    report = []
    report.append("# 🔍 GitHub MCP Tools Authentication Audit Report\n")
    report.append(f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n\n")
    
    # Executive Summary
    report.append("## 1. Executive Summary\n\n")
    total_tools = len(tools)
    tools_with_issues = len(critical) + len(high_priority) + len(low_priority)
    write_ops = sum(1 for t in tools if t['is_write'])
    write_ops_with_validation = sum(1 for t in tools if t['is_write'] and t['has_token_validation'])
    
    report.append(f"- **Total Tools Audited:** {total_tools}\n")
    report.append(f"- **Write Operations:** {write_ops}\n")
    report.append(f"- **Write Ops with Validation:** {write_ops_with_validation}\n")
    report.append(f"- **Tools with Issues:** {tools_with_issues}\n")
    report.append(f"- **🔴 Critical Issues:** {len(critical)}\n")
    report.append(f"- **🟡 High Priority Issues:** {len(high_priority)}\n")
    report.append(f"- **🟢 Low Priority Issues:** {len(low_priority)}\n\n")
    
    if len(critical) == 0 and len(high_priority) == 0:
        report.append("**Status:** ✅ **SAFE to release v2.3.0** - No critical issues found\n\n")
    elif len(critical) > 0:
        report.append(f"**Status:** ❌ **HOLD v2.3.0** - {len(critical)} critical issues must be fixed first\n\n")
    else:
        report.append(f"**Status:** ⚠️ **CONSIDER fixes** - {len(high_priority)} high-priority issues found\n\n")
    
    report.append("---\n\n")
    
    # Critical Issues
    if critical:
        report.append("## 2. 🔴 CRITICAL Issues (Must Fix Before v2.3.0)\n\n")
        for tool in critical:
            report.append(f"### {tool['name']}\n\n")
            report.append(f"- **Line:** {tool['line']}\n")
            report.append(f"- **Risk Level:** {tool['risk_level']} - Write Operation\n")
            report.append("- **Issues Found:**\n")
            for issue in tool['issues']:
                report.append(f"  - ❌ {issue}\n")
            report.append("- **Priority:** CRITICAL\n")
            report.append("- **Recommendation:** Add explicit token validation before API call\n\n")
        report.append("---\n\n")
    
    # High Priority Issues
    if high_priority:
        report.append("## 3. 🟡 HIGH Priority Issues (Should Fix Before v2.3.0)\n\n")
        for tool in high_priority:
            report.append(f"### {tool['name']}\n\n")
            report.append(f"- **Line:** {tool['line']}\n")
            report.append(f"- **Risk Level:** {tool['risk_level']}\n")
            report.append("- **Issues Found:**\n")
            for issue in tool['issues']:
                report.append(f"  - ⚠️ {issue}\n")
            report.append("- **Priority:** HIGH\n\n")
        report.append("---\n\n")
    
    # Low Priority Issues
    if low_priority:
        report.append("## 4. 🟢 LOW Priority Issues (Can Fix in v2.3.1)\n\n")
        for tool in low_priority:
            report.append(f"- **{tool['name']}** (line {tool['line']}): {', '.join(tool['issues'])}\n")
        report.append("\n---\n\n")
    
    # Quick Fix List
    report.append("## 5. Quick Fix List\n\n")
    fix_num = 1
    for tool in critical + high_priority:
        if not tool['has_token_validation'] and tool['is_write']:
            report.append(f"{fix_num}. **{tool['name']}** (line {tool['line']}): Add `if not auth_token:` validation check\n")
            fix_num += 1
    
    report.append("\n---\n\n")
    
    # All Tools Status
    report.append("## 6. Complete Tool Status\n\n")
    report.append("| Tool Name | Risk | Write | Token Retrieval | Token Validation | Token in Request | Status |\n")
    report.append("|-----------|------|-------|------------------|-------------------|------------------|--------|\n")
    
    for tool in sorted(tools, key=lambda x: (x['is_write'], x['name']), reverse=True):
        status = "✅ PASS"
        if tool['name'] in [t['name'] for t in critical]:
            status = "🔴 CRITICAL"
        elif tool['name'] in [t['name'] for t in high_priority]:
            status = "🟡 HIGH"
        elif tool['name'] in [t['name'] for t in low_priority]:
            status = "🟢 LOW"
        
        token_ret = "✅" if tool['has_token_retrieval'] else "❌"
        token_val = "✅" if tool['has_token_validation'] else "❌"
        token_req = "✅" if tool['has_token_in_request'] else "❌"
        is_write = "✅" if tool['is_write'] else "❌"
        
        report.append(f"| {tool['name']} | {tool['risk_level']} | {is_write} | {token_ret} | {token_val} | {token_req} | {status} |\n")
    
    return ''.join(report)

if __name__ == '__main__':
    tools = extract_tool_functions('github_mcp.py')
    critical, high_priority, low_priority = categorize_issues(tools)
    report = generate_report(tools, critical, high_priority, low_priority)
    
    # Save to file
    with open('AUTH_AUDIT_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Print summary (safe for Windows console)
    print("\nAudit complete! Report saved to AUTH_AUDIT_REPORT.md")
    print(f"   Found {len(critical)} critical, {len(high_priority)} high, {len(low_priority)} low priority issues")

