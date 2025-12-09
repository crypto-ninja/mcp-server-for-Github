#!/usr/bin/env python3
"""Auto-update TypeScript tool definitions from Python models."""

import sys
import re
import ast
from pathlib import Path
from typing import Dict, Optional

project_root = Path(__file__).parent.parent

def parse_python_model_fields(model_name: str) -> Optional[Dict[str, Dict]]:
    """Parse fields from a Python Pydantic model."""
    inputs_file = project_root / "src" / "github_mcp" / "models" / "inputs.py"
    
    with open(inputs_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the model class
    model_pattern = rf'class {model_name}\(BaseModel\):'
    match = re.search(model_pattern, content)
    
    if not match:
        return None
    
    # Parse the class using AST
    tree = ast.parse(content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == model_name:
            fields = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign):
                    # Field with annotation: field_name: type = Field(...)
                    field_name = item.target.id if isinstance(item.target, ast.Name) else None
                    if field_name:
                        # Check if it has a default (Field(...))
                        is_required = item.value is None
                        if item.value:
                            # Check if Field has default parameter
                            if isinstance(item.value, ast.Call):
                                if isinstance(item.value.func, ast.Name) and item.value.func.id == 'Field':
                                    # Check for ... (required) or default=...
                                    is_required = True
                                    for keyword in item.value.keywords:
                                        if keyword.arg == 'default':
                                            if isinstance(keyword.value, ast.Constant) and keyword.value.value is None:
                                                is_required = False
                                            elif isinstance(keyword.value, ast.NameConstant) and keyword.value.value is None:
                                                is_required = False
                                            else:
                                                is_required = False
                                        elif keyword.arg is None:  # Positional ... argument
                                            is_required = True
                            
                            # Check for Field(..., ...) pattern
                            if isinstance(item.value, ast.Call):
                                if len(item.value.args) > 0:
                                    if isinstance(item.value.args[0], ast.Constant) and item.value.args[0].value == Ellipsis:
                                        is_required = True
                                    elif isinstance(item.value.args[0], ast.Ellipsis):
                                        is_required = True
                        
                        # Get type annotation
                        field_type = 'string'  # default
                        if item.annotation:
                            if isinstance(item.annotation, ast.Name):
                                type_name = item.annotation.id
                                if type_name in ['str', 'string']:
                                    field_type = 'string'
                                elif type_name in ['int', 'float']:
                                    field_type = 'number'
                                elif type_name == 'bool':
                                    field_type = 'boolean'
                                elif type_name == 'List':
                                    field_type = 'array'
                            elif isinstance(item.annotation, ast.Subscript):
                                # Optional[str], List[str], etc.
                                if isinstance(item.annotation.value, ast.Name):
                                    if item.annotation.value.id == 'Optional':
                                        # Get inner type
                                        if isinstance(item.annotation.slice, ast.Name):
                                            inner_type = item.annotation.slice.id
                                            if inner_type in ['str', 'string']:
                                                field_type = 'string'
                                            elif inner_type in ['int', 'float']:
                                                field_type = 'number'
                                            elif inner_type == 'bool':
                                                field_type = 'boolean'
                                    elif item.annotation.value.id == 'List':
                                        field_type = 'array'
                        
                        fields[field_name] = {
                            'required': is_required,
                            'type': field_type
                        }
            
            return fields
    
    return None

def get_model_name_from_tool(tool_name: str) -> str:
    """Convert tool name to model name."""
    name = tool_name.replace("github_", "")
    parts = name.split('_')
    pascal = ''.join(word.capitalize() for word in parts)
    return pascal + "Input"

def update_tool_definition(ts_content: str, tool_name: str, fields: Dict[str, Dict]) -> str:
    """Update a single tool definition in TypeScript content."""
    # Find the tool definition
    tool_pattern = rf'name:\s*"{re.escape(tool_name)}",'
    match = re.search(tool_pattern, ts_content)
    
    if not match:
        return ts_content
    
    # Find the parameters block
    start_pos = match.start()
    param_start = ts_content.find('parameters: {', start_pos)
    
    if param_start == -1:
        return ts_content
    
    # Find matching closing brace
    brace_count = 0
    param_end = param_start
    for i in range(param_start, len(ts_content)):
        if ts_content[i] == '{':
            brace_count += 1
        elif ts_content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                param_end = i + 1
                break
    
    # Build new parameters block
    param_lines = ['      parameters: {']
    for field_name, field_info in sorted(fields.items()):
        param_type = field_info['type']
        required = field_info['required']
        param_lines.append(f'        {field_name}: {{ type: "{param_type}", required: {str(required).lower()}, description: "{field_name}" }},')
    
    param_lines.append('      },')
    new_params = '\n'.join(param_lines)
    
    # Replace the parameters block
    return ts_content[:param_start] + new_params + ts_content[param_end:]

if __name__ == "__main__":
    print("This script would auto-update tool definitions.")
    print("For now, we'll focus on fixing the most critical ones manually.")
    print("\nThe check script found 80 tools with missing parameters.")
    print("Would you like me to:")
    print("1. Fix all tools automatically (risky - may break formatting)")
    print("2. Fix only tools with missing REQUIRED parameters")
    print("3. Fix the most commonly used tools (repos, issues, PRs, files, workflows)")
    
    # For now, let's just report what needs to be fixed
    sys.exit(0)

