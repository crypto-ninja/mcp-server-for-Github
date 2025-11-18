#!/usr/bin/env python3
"""
Automatic TypeScript wrapper generator for MCP tools.

This script scans github_mcp.py for @mcp.tool() decorators and generates:
1. TypeScript interfaces for inputs (from Pydantic models)
2. TypeScript interfaces for outputs
3. Typed wrapper functions
4. JSDoc documentation
5. Proper directory structure

Usage:
    python codegen/generate_ts_wrappers.py [--output-dir servers]
"""

import ast
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class FieldInfo:
    """Information about a Pydantic field."""
    name: str
    python_type: str
    typescript_type: str
    optional: bool
    description: str
    default: Optional[str] = None


@dataclass
class ToolInfo:
    """Information about an MCP tool."""
    name: str
    function_name: str
    description: str
    category: str
    input_model: str
    fields: List[FieldInfo]
    annotations: Dict[str, any]
    examples: List[str]


class MCPToolExtractor:
    """Extract tool definitions from Python MCP server."""
    
    PYTHON_TO_TS_TYPE_MAP = {
        'str': 'string',
        'int': 'number',
        'float': 'number',
        'bool': 'boolean',
        'List[str]': 'string[]',
        'List[int]': 'number[]',
        'Dict': 'Record<string, any>',
        'Any': 'any',
        'Optional[str]': 'string | undefined',
        'Optional[int]': 'number | undefined',
        'Optional[bool]': 'boolean | undefined',
        'Optional[List[str]]': 'string[] | undefined',
        'Optional[List[int]]': 'number[] | undefined',
    }
    
    CATEGORY_MAP = {
        # Issue operations
        'github_list_issues': 'issues',
        'github_create_issue': 'issues',
        'github_update_issue': 'issues',
        'github_search_issues': 'issues',
        
        # Pull request operations
        'github_list_pull_requests': 'pulls',
        'github_create_pull_request': 'pulls',
        'github_get_pr_details': 'pulls',
        'github_get_pr_overview_graphql': 'pulls',
        'github_merge_pull_request': 'pulls',
        'github_close_pull_request': 'pulls',
        'github_create_pr_review': 'pulls',
        
        # File operations
        'github_get_file_content': 'files',
        'github_create_file': 'files',
        'github_update_file': 'files',
        'github_delete_file': 'files',
        'github_batch_file_operations': 'files',
        
        # Search operations
        'github_search_code': 'search',
        'github_search_repositories': 'search',
        
        # Workspace operations (local)
        'workspace_grep': 'workspace',
        'str_replace': 'workspace',
        'repo_read_file_chunk': 'workspace',
        
        # Remote operations (GitHub remote)
        'github_grep': 'remote',
        'github_read_file_chunk': 'remote',
        'github_str_replace': 'remote',
        
        # Repository management
        'github_get_repo_info': 'repos',
        'github_create_repository': 'repos',
        'github_update_repository': 'repos',
        'github_delete_repository': 'repos',
        'github_transfer_repository': 'repos',
        'github_archive_repository': 'repos',
        'github_list_repo_contents': 'repos',
        
        # Commit operations
        'github_list_commits': 'commits',
        
        # Workflow operations
        'github_list_workflows': 'workflows',
        'github_get_workflow_runs': 'workflows',
        
        # GraphQL operations
        'github_graphql_query': 'graphql',
        
        # User/Organization operations
        'github_get_user_info': 'users',
        
        # Release operations
        'github_list_releases': 'releases',
        'github_get_release': 'releases',
        'github_create_release': 'releases',
        'github_update_release': 'releases',
        
        # Workflow advisor
        'github_suggest_workflow': 'advisor',
        
        # License info
        'github_license_info': 'license',
    }
    
    def __init__(self, source_file: Path):
        self.source_file = source_file
        self.tools: List[ToolInfo] = []
        self.source_code = source_file.read_text(encoding='utf-8')
        self.ast_tree = ast.parse(self.source_code)
        self.pydantic_models: Dict[str, List[FieldInfo]] = {}
    
    def extract_all(self) -> List[ToolInfo]:
        """Extract all tools from the source file."""
        # First pass: Extract Pydantic models
        self._extract_pydantic_models()
        
        # Second pass: Extract tools
        self._extract_tools()
        
        return self.tools
    
    def _extract_pydantic_models(self):
        """Extract Pydantic model definitions and their fields."""
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a BaseModel subclass
                # BaseModel is imported directly from pydantic, so check for ast.Name
                is_basemodel = any(
                    isinstance(base, ast.Name) and base.id == 'BaseModel'
                    for base in node.bases
                )
                
                if is_basemodel:
                    model_name = node.name
                    fields = self._extract_model_fields(node)
                    self.pydantic_models[model_name] = fields
    
    def _extract_model_fields(self, class_node: ast.ClassDef) -> List[FieldInfo]:
        """Extract fields from a Pydantic model."""
        fields = []
        
        for item in class_node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                
                # Skip model_config and other non-field attributes
                if field_name in ['model_config', '__annotations__']:
                    continue
                
                # Get type annotation
                type_str = ast.unparse(item.annotation)
                
                # Check if optional
                optional = 'Optional' in type_str
                
                # Convert to TypeScript type
                ts_type = self._python_type_to_typescript(type_str)
                
                # Extract description from Field()
                description = self._extract_field_description(item.value)
                
                # Extract default value
                default = self._extract_default_value(item.value)
                
                fields.append(FieldInfo(
                    name=field_name,
                    python_type=type_str,
                    typescript_type=ts_type,
                    optional=optional,
                    description=description,
                    default=default
                ))
        
        return fields
    
    def _extract_field_description(self, value_node) -> str:
        """Extract description from Field() call."""
        if isinstance(value_node, ast.Call):
            for keyword in value_node.keywords:
                if keyword.arg == 'description':
                    if isinstance(keyword.value, ast.Constant):
                        return keyword.value.value
        return ""
    
    def _extract_default_value(self, value_node) -> Optional[str]:
        """Extract default value if present."""
        if isinstance(value_node, ast.Call):
            # Check for Field(default=...)
            for keyword in value_node.keywords:
                if keyword.arg == 'default':
                    return ast.unparse(keyword.value)
        elif isinstance(value_node, ast.Constant):
            return str(value_node.value)
        return None
    
    def _python_type_to_typescript(self, python_type: str) -> str:
        """Convert Python type annotation to TypeScript type."""
        # Direct mapping
        if python_type in self.PYTHON_TO_TS_TYPE_MAP:
            return self.PYTHON_TO_TS_TYPE_MAP[python_type]
        
        # Handle enums - convert to string literal union types
        enum_mappings = {
            'ResponseFormat': "'markdown' | 'json'",
            'IssueState': "'open' | 'closed' | 'all'",
            'PullRequestState': "'open' | 'closed' | 'all'",
            'SortOrder': "'asc' | 'desc'",
            'WorkflowRunStatus': "'queued' | 'in_progress' | 'completed' | 'waiting' | 'requested' | 'pending'",
            'WorkflowRunConclusion': "'success' | 'failure' | 'neutral' | 'cancelled' | 'skipped' | 'timed_out' | 'action_required'",
            'PRMergeMethod': "'merge' | 'squash' | 'rebase'",
            'PRReviewState': "'APPROVED' | 'CHANGES_REQUESTED' | 'COMMENTED' | 'DISMISSED' | 'PENDING'",
        }
        
        if python_type in enum_mappings:
            return enum_mappings[python_type]
        
        # Handle generics
        if python_type.startswith('Optional['):
            inner = python_type[9:-1]
            return f"{self._python_type_to_typescript(inner)} | undefined"
        
        if python_type.startswith('List['):
            inner = python_type[5:-1]
            return f"{self._python_type_to_typescript(inner)}[]"
        
        if python_type.startswith('Dict['):
            return "Record<string, any>"
        
        # Default to any
        return "any"
    
    def _extract_tools(self):
        """Extract all @mcp.tool() decorated functions."""
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.AsyncFunctionDef):
                # Check for @mcp.tool() decorator
                for decorator in node.decorator_list:
                    if self._is_mcp_tool_decorator(decorator):
                        tool = self._extract_tool_info(node, decorator)
                        if tool:
                            self.tools.append(tool)
    
    def _is_mcp_tool_decorator(self, decorator) -> bool:
        """Check if decorator is @mcp.tool()."""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return (decorator.func.attr == 'tool' and 
                        isinstance(decorator.func.value, ast.Name) and 
                        decorator.func.value.id == 'mcp')
        return False
    
    def _extract_tool_info(self, node: ast.AsyncFunctionDef, decorator) -> Optional[ToolInfo]:
        """Extract comprehensive tool information."""
        function_name = node.name
        
        # Extract tool name from decorator
        tool_name = function_name  # default
        annotations = {}
        
        if isinstance(decorator, ast.Call):
            for keyword in decorator.keywords:
                if keyword.arg == 'name':
                    if isinstance(keyword.value, ast.Constant):
                        tool_name = keyword.value.value
                    elif isinstance(keyword.value, ast.Str):  # Python < 3.8 compatibility
                        tool_name = keyword.value.s
                elif keyword.arg == 'annotations':
                    # Extract annotations dict
                    if isinstance(keyword.value, ast.Dict):
                        for k, v in zip(keyword.value.keys, keyword.value.values):
                            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                                annotations[k.value] = v.value
                            elif isinstance(k, ast.Str) and isinstance(v, ast.Str):  # Python < 3.8
                                annotations[k.s] = v.s
        
        # Extract docstring
        docstring = ast.get_docstring(node) or ""
        
        # Extract description (first paragraph of docstring)
        description = docstring.split('\n\n')[0].strip()
        
        # Extract examples from docstring
        examples = self._extract_examples_from_docstring(docstring)
        
        # Determine category
        category = self.CATEGORY_MAP.get(tool_name, 'misc')
        
        # Extract input model from function parameters
        input_model = None
        fields = []
        
        if node.args.args:
            for arg in node.args.args:
                if arg.arg != 'self' and arg.annotation:
                    input_model = ast.unparse(arg.annotation)
                    # Look up fields from Pydantic models
                    if input_model in self.pydantic_models:
                        fields = self.pydantic_models[input_model]
                    break
        
        return ToolInfo(
            name=tool_name,
            function_name=function_name,
            description=description,
            category=category,
            input_model=input_model or "any",
            fields=fields,
            annotations=annotations,
            examples=examples
        )
    
    def _extract_examples_from_docstring(self, docstring: str) -> List[str]:
        """Extract usage examples from docstring."""
        examples = []
        lines = docstring.split('\n')
        
        in_examples = False
        for line in lines:
            line = line.strip()
            if 'Examples:' in line or 'Use when:' in line:
                in_examples = True
                continue
            
            if in_examples:
                if line.startswith('- '):
                    examples.append(line[2:])
                elif line.startswith('*'):
                    examples.append(line[1:].strip())
                elif not line or ':' in line:
                    # End of examples section
                    break
        
        return examples


class TypeScriptGenerator:
    """Generate TypeScript wrapper code from tool definitions."""
    
    def __init__(self, tools: List[ToolInfo]):
        self.tools = tools
    
    def generate_interface(self, tool: ToolInfo) -> str:
        """Generate TypeScript interface from Pydantic model fields."""
        if not tool.fields:
            return ""
        
        interface_name = f"{self._to_pascal_case(tool.function_name)}Input"
        
        lines = [f"export interface {interface_name} {{"]
        
        for field in tool.fields:
            comment = f"  /** {field.description} */" if field.description else ""
            if comment:
                lines.append(comment)
            
            optional_marker = "?" if field.optional else ""
            lines.append(f"  {field.name}{optional_marker}: {field.typescript_type};")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_wrapper(self, tool: ToolInfo) -> str:
        """Generate typed wrapper function."""
        interface_name = f"{self._to_pascal_case(tool.function_name)}Input" if tool.fields else "any"
        
        # Generate examples section
        examples_section = ""
        if tool.examples:
            examples_section = "\n * \n * Examples:\n"
            for example in tool.examples[:3]:  # Limit to 3 examples
                examples_section += f" * - {example}\n"
        
        # Calculate relative path to client.js from the tool file location
        # Tool file: servers/github/{category}/{tool_name}.ts
        # Client file: servers/client.ts
        # Relative path: ../../client.js
        return f'''// servers/github/{tool.category}/{self._to_kebab_case(tool.function_name)}.ts
import {{ callMCPTool }} from '../../client.js';

{self.generate_interface(tool)}

/**
 * {tool.description}
 {examples_section}
 * @param input - Tool parameters
 * @returns Tool execution result
 */
export async function {tool.function_name}(
    input: {interface_name}
): Promise<string> {{
    return callMCPTool<string>(
        '{tool.name}',
        input
    );
}}
'''
    
    def generate_category_index(self, category: str, tools: List[ToolInfo]) -> str:
        """Generate index.ts for a category."""
        exports = [f"export * from './{self._to_kebab_case(tool.function_name)}.js';" 
                   for tool in tools]
        
        return "\n".join(exports) + "\n"
    
    def generate_main_index(self, categories: Dict[str, List[ToolInfo]]) -> str:
        """Generate main index.ts that exports all categories."""
        exports = [f"export * as {category} from './{category}/index.js';" 
                   for category in sorted(categories.keys())]
        
        return "\n".join(exports) + "\n"
    
    def generate_all(self, output_dir: Path):
        """Generate complete servers/ directory structure."""
        # Group tools by category
        categories = self._group_by_category(self.tools)
        
        github_dir = output_dir / 'github'
        
        # Generate each category
        for category, tools in categories.items():
            category_dir = github_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate individual tool files
            for tool in tools:
                file_path = category_dir / f"{self._to_kebab_case(tool.function_name)}.ts"
                file_path.write_text(self.generate_wrapper(tool))
                print(f"[OK] Generated {file_path.relative_to(output_dir)}")
            
            # Generate category index
            index_path = category_dir / "index.ts"
            index_path.write_text(self.generate_category_index(category, tools))
            print(f"[OK] Generated {index_path.relative_to(output_dir)}")
        
        # Generate main index
        main_index = github_dir / "index.ts"
        main_index.write_text(self.generate_main_index(categories))
        print(f"[OK] Generated {main_index.relative_to(output_dir)}")
        
        print(f"\n[SUCCESS] Generated wrappers for {len(self.tools)} tools across {len(categories)} categories!")
    
    def _group_by_category(self, tools: List[ToolInfo]) -> Dict[str, List[ToolInfo]]:
        """Group tools by category."""
        categories: Dict[str, List[ToolInfo]] = {}
        
        for tool in tools:
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool)
        
        return categories
    
    @staticmethod
    def _to_pascal_case(snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        return ''.join(word.capitalize() for word in snake_str.split('_'))
    
    @staticmethod
    def _to_kebab_case(snake_str: str) -> str:
        """Convert snake_case to kebab-case."""
        return snake_str.replace('_', '-')


def main():
    parser = argparse.ArgumentParser(description='Generate TypeScript wrappers for MCP tools')
    parser.add_argument('--source', default='github_mcp.py', help='Source Python file')
    parser.add_argument('--output-dir', default='servers', help='Output directory for generated files')
    
    args = parser.parse_args()
    
    source_file = Path(args.source)
    output_dir = Path(args.output_dir)
    
    if not source_file.exists():
        print(f"[ERROR] Source file not found: {source_file}")
        return 1
    
    try:
        # Set UTF-8 encoding for Windows console
        import sys
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        
        print(f"[INFO] Reading {source_file}...")
        
        # Extract tools
        extractor = MCPToolExtractor(source_file)
        tools = extractor.extract_all()
        
        print(f"[OK] Found {len(tools)} tools")
        print(f"[OK] Found {len(extractor.pydantic_models)} Pydantic models")
        
        if len(tools) == 0:
            print("[WARNING] No tools found! Check if @mcp.tool() decorators are present.")
            return 1
        
        # List all tools found
        print(f"\nTools found:")
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.name} ({tool.category})")
        
        # Generate TypeScript wrappers
        print(f"\n[INFO] Generating TypeScript wrappers...")
        generator = TypeScriptGenerator(tools)
        generator.generate_all(output_dir)
        
        print(f"\n[SUCCESS] Done! Wrappers generated in {output_dir}/github/")
        print(f"\nNext steps:")
        print(f"1. cd {output_dir}")
        print(f"2. npm install")
        print(f"3. npm run build")
        
        return 0
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())