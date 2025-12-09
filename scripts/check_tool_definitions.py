#!/usr/bin/env python3
"""Check tool definitions against Python input models for missing parameters."""

import sys
import re
from pathlib import Path
from typing import Dict, Optional

project_root = Path(__file__).parent.parent

def parse_python_model(model_name: str) -> Optional[Dict[str, Dict]]:
    """Parse a Python Pydantic model from inputs.py."""
    inputs_file = project_root / "src" / "github_mcp" / "models" / "inputs.py"
    
    if not inputs_file.exists():
        return None
    
    with open(inputs_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the model class
    model_pattern = rf'class {model_name}\(BaseModel\):'
    match = re.search(model_pattern, content)
    
    if not match:
        return None
    
    # Find the class body
    start_pos = match.end()
    indent_level = len(match.group(0)) - len(match.group(0).lstrip())
    
    # Find the end of the class
    lines = content[start_pos:].split('\n')
    class_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            continue  # Skip the class definition line
        if line.strip() == '':
            continue
        if line.strip().startswith('class ') and not line.strip().startswith('class ' + model_name):
            # Next class found
            break
        if line.strip() and not line.startswith(' ' * (indent_level + 1)) and not line.startswith('\t'):
            # Different indentation level
            if i > 0:
                break
        class_lines.append(line)
    
    class_body = '\n'.join(class_lines)
    
    # Extract field definitions
    fields = {}
    # Pattern: field_name: type = Field(...)
    field_pattern = r'(\w+):\s*(?:Optional\[)?([\w\[\]]+)(?:\])?\s*=\s*Field\([^)]*description[^)]*\)'
    
    for field_match in re.finditer(field_pattern, class_body):
        field_name = field_match.group(1)
        field_type = field_match.group(2)
        
        # Check if it's required (Field(...) vs Field(default=...))
        is_required = 'default=' not in field_match.group(0) and 'default=None' not in field_match.group(0)
        
        fields[field_name] = {
            'required': is_required,
            'type': field_type
        }
    
    # Also check for Field(..., description=...) pattern (required fields)
    required_pattern = r'(\w+):\s*[^=]+\s*=\s*Field\(\.\.\.[^)]*description[^)]*\)'
    for req_match in re.finditer(required_pattern, class_body):
        field_name = req_match.group(1)
        if field_name not in fields:
            fields[field_name] = {
                'required': True,
                'type': 'str'  # Default
            }
    
    return fields

def parse_typescript_tool_definitions() -> Dict[str, Dict]:
    """Parse tool definitions from TypeScript file."""
    ts_file = project_root / "deno_executor" / "tool-definitions.ts"
    
    if not ts_file.exists():
        return {}
    
    tools = {}
    
    with open(ts_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all tool definitions - look for name: "tool_name"
    tool_blocks = re.split(r'},\s*\n\s*\{', content)
    
    for block in tool_blocks:
        # Extract tool name
        name_match = re.search(r'name:\s*"([^"]+)"', block)
        if not name_match:
            continue
        
        tool_name = name_match.group(1)
        
        # Extract parameters
        params = {}
        param_section = re.search(r'parameters:\s*\{([^}]+)\}', block, re.DOTALL)
        
        if param_section:
            param_content = param_section.group(1)
            # Find each parameter
            param_pattern = r'(\w+):\s*\{\s*type:\s*"([^"]+)",\s*required:\s*(true|false)'
            for param_match in re.finditer(param_pattern, param_content):
                param_name = param_match.group(1)
                param_type = param_match.group(2)
                param_required = param_match.group(3) == 'true'
                params[param_name] = {
                    'type': param_type,
                    'required': param_required
                }
        
        tools[tool_name] = {
            'parameters': params
        }
    
    return tools

def get_model_name_from_tool(tool_name: str) -> str:
    """Convert tool name to model name."""
    # github_get_repo_info -> RepoInfoInput
    # github_list_issues -> ListIssuesInput
    # github_create_issue -> CreateIssueInput
    
    # Remove github_ prefix
    name = tool_name.replace("github_", "")
    
    # Convert snake_case to PascalCase
    parts = name.split('_')
    pascal = ''.join(word.capitalize() for word in parts)
    
    return pascal + "Input"

def compare_tools():
    """Compare TypeScript definitions with Python models."""
    ts_tools = parse_typescript_tool_definitions()
    
    issues = []
    
    for tool_name, ts_def in ts_tools.items():
        model_name = get_model_name_from_tool(tool_name)
        python_fields = parse_python_model(model_name)
        
        if python_fields is None:
            # Tool might not have a model (e.g., github_license_info, execute_code)
            continue
        
        ts_params = set(ts_def['parameters'].keys())
        python_params = set(python_fields.keys())
        
        # Check for missing parameters in TS definition
        missing_in_ts = python_params - ts_params
        if missing_in_ts:
            issues.append({
                'tool': tool_name,
                'model': model_name,
                'type': 'missing_in_ts',
                'missing': missing_in_ts,
                'python_fields': {k: python_fields[k] for k in missing_in_ts}
            })
    
    return issues

if __name__ == "__main__":
    print("Checking tool definitions against Python models...\n")
    
    issues = compare_tools()
    
    if not issues:
        print("✅ All tool definitions match their Python models!")
        sys.exit(0)
    
    print(f"Found {len(issues)} tools with missing parameters in TS definitions:\n")
    
    for issue in issues:
        print(f"🔴 {issue['tool']} (model: {issue['model']})")
        print(f"   Missing: {', '.join(sorted(issue['missing']))}")
        for param in sorted(issue['missing']):
            field_info = issue['python_fields'][param]
            req_str = "required" if field_info['required'] else "optional"
            print(f"      - {param}: {field_info['type']} ({req_str})")
        print()
    
    sys.exit(1)
