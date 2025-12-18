"""Workspace tools for GitHub MCP Server.

These tools operate on local files within the workspace root directory,
enabling efficient local file operations without requiring GitHub API calls.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from ..models.inputs import (
    WorkspaceGrepInput,
    StrReplaceInput,
    ReadFileChunkInput,
)
from ..models.enums import ResponseFormat
from ..utils.errors import _handle_api_error
from ..utils.formatting import _truncate_response

# Workspace Configuration - supports user projects!
# Set MCP_WORKSPACE_ROOT env var to your project root, or defaults to current directory
WORKSPACE_ROOT = Path(os.getenv("MCP_WORKSPACE_ROOT", Path.cwd()))


def _validate_search_path(repo_path: str) -> Path:
    """Validate and normalize search path, ensuring it's within workspace."""
    base_dir = WORKSPACE_ROOT  # Use configurable workspace, not hardcoded REPO_ROOT
    norm_path = Path(repo_path).as_posix() if repo_path else ""

    # Normalize path
    if norm_path:
        # Remove leading slashes
        norm_path = norm_path.lstrip("/")
        # Check for parent traversal
        if ".." in norm_path or norm_path.startswith(".."):
            raise ValueError(
                "Path traversal detected: parent directory access not allowed"
            )
        search_path = (base_dir / norm_path).resolve()
    else:
        search_path = base_dir

    # Ensure it's within repo root
    try:
        search_path.relative_to(base_dir)
    except ValueError:
        raise ValueError(f"Path outside workspace root: {repo_path}")

    if not search_path.exists():
        raise ValueError(f"Search path does not exist: {repo_path}")

    return search_path


def _is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary."""
    # Check by extension
    binary_extensions = {
        ".pyc",
        ".pyo",
        ".pyd",
        ".so",
        ".dll",
        ".exe",
        ".bin",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".otf",
        ".mp3",
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
    }
    if file_path.suffix.lower() in binary_extensions:
        return True

    # Check by content (first 512 bytes)
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(512)
            # Check for null bytes (common in binary files)
            if b"\x00" in chunk:
                return True
            # Check if it's valid UTF-8
            try:
                chunk.decode("utf-8")
            except UnicodeDecodeError:
                return True
    except Exception:
        return True

    return False


def _load_gitignore(base_dir: Path) -> List[re.Pattern]:
    """Load and parse .gitignore patterns."""
    gitignore_path = base_dir / ".gitignore"
    patterns = []

    # Always ignore .git directory
    patterns.append(re.compile(r"^\.git(/|$)"))

    if not gitignore_path.exists():
        return patterns

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Convert gitignore pattern to regex
                pattern = line.replace(".", r"\.").replace("*", ".*").replace("?", ".")
                if pattern.startswith("/"):
                    pattern = pattern[1:]
                else:
                    pattern = f".*{pattern}"
                patterns.append(re.compile(pattern))
    except Exception:
        pass

    return patterns


def _should_ignore_file(
    file_path: Path, base_dir: Path, gitignore_patterns: List[re.Pattern]
) -> bool:
    """Check if a file should be ignored based on .gitignore patterns."""
    rel_path = file_path.relative_to(base_dir).as_posix()

    for pattern in gitignore_patterns:
        if pattern.search(rel_path):
            return True

    return False


def _python_grep_search(
    search_path: Path,
    pattern: str,
    file_pattern: str,
    case_sensitive: bool,
    max_results: int,
    context_lines: int,
    gitignore_patterns: List[re.Pattern],
    base_dir: Path,
) -> List[Dict[str, Any]]:
    """Python-based grep search as fallback."""
    matches: List[Dict[str, Any]] = []
    compiled_pattern = re.compile(pattern, re.IGNORECASE if not case_sensitive else 0)

    # Convert file_pattern glob to regex
    if file_pattern == "*":
        file_regex = re.compile(r".*")
    else:
        # Simple glob to regex conversion
        file_regex_str = (
            file_pattern.replace(".", r"\.").replace("*", ".*").replace("?", ".")
        )
        file_regex = re.compile(file_regex_str, re.IGNORECASE)

    try:
        for root, dirs, files in os.walk(search_path):
            # Skip .git directory
            if ".git" in dirs:
                dirs.remove(".git")

            for file_name in files:
                file_path = Path(root) / file_name

                # Check if file matches pattern
                if not file_regex.search(file_name):
                    continue

                # Check if binary
                if _is_binary_file(file_path):
                    continue

                # Check gitignore
                if _should_ignore_file(file_path, base_dir, gitignore_patterns):
                    continue

                if len(matches) >= max_results:
                    break

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                        for line_num, line in enumerate(lines, start=1):
                            if len(matches) >= max_results:
                                break
                            if compiled_pattern.search(line):
                                # Get context
                                start_line = max(1, line_num - context_lines)
                                end_line = min(len(lines), line_num + context_lines)
                                context_before = [
                                    line.rstrip("\n\r")
                                    for line in lines[start_line - 1 : line_num - 1]
                                ]
                                context_after = [
                                    line.rstrip("\n\r")
                                    for line in lines[line_num:end_line]
                                ]

                                matches.append(
                                    {
                                        "file": str(file_path.relative_to(base_dir)),
                                        "line_number": line_num,
                                        "line": line.rstrip("\n\r"),
                                        "context_before": context_before,
                                        "context_after": context_after,
                                    }
                                )
                except Exception:
                    continue
    except Exception:
        pass

    return matches


async def workspace_grep(params: WorkspaceGrepInput) -> str:
    """
    Search for patterns in workspace files using grep.

    **Workspace Configuration**: Set MCP_WORKSPACE_ROOT environment variable
    to your project directory. Defaults to current working directory.

    This tool efficiently searches through files in the repository,
    returning only matching lines with context instead of full files.
    Ideal for finding functions, errors, TODOs, or any code pattern.

    Security: Repository-rooted, no parent traversal allowed.

    Args:
        params (WorkspaceGrepInput): Validated input parameters containing:
            - pattern (str): Regex pattern to search for
            - repo_path (str): Optional subdirectory to search within
            - context_lines (int): Number of lines before/after match (0-5)
            - max_results (int): Maximum matches to return (1-500)
            - file_pattern (str): Glob pattern for files (e.g., '*.py', '*.md')
            - case_sensitive (bool): Whether search is case-sensitive
            - response_format (ResponseFormat): Output format (markdown or json)

    Returns:
        str: Formatted search results with file paths, line numbers, and matches

    Examples:
        - Use when: "Find all KeyError occurrences"
        - Use when: "Search for function definitions matching github_*"
        - Use when: "Find all TODOs in Python files"
        - Use when: "Search for import statements in src directory"

    Error Handling:
        - Returns error if pattern is invalid
        - Returns error if path traversal detected
        - Handles binary files gracefully
        - Respects .gitignore patterns
    """
    try:
        # Validate inputs
        if not params.pattern:
            return "Error: Pattern cannot be empty"

        # Validate and get search path
        try:
            search_path = _validate_search_path(params.repo_path)
            base_dir = WORKSPACE_ROOT  # Use configurable workspace
        except ValueError as e:
            return f"Error: {str(e)}"

        # Load gitignore patterns
        gitignore_patterns = _load_gitignore(base_dir)

        # Try ripgrep first, then grep, then Python fallback
        matches: List[Dict[str, Any]] = []
        files_searched = 0

        # Try ripgrep
        try:
            cmd = ["rg", "--json", "--no-heading", "--with-filename", "--line-number"]
            if params.context_lines > 0:
                cmd.extend(["-C", str(params.context_lines)])
            if not params.case_sensitive:
                cmd.append("--ignore-case")
            if params.file_pattern != "*":
                cmd.extend(["--glob", params.file_pattern])
            cmd.extend([params.pattern, str(search_path)])

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if proc.returncode == 0:
                # Parse ripgrep JSON output
                for line in proc.stdout.strip().split("\n"):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("type") == "match":
                            file_path_str = data["data"]["path"]["text"]
                            file_path = Path(file_path_str)
                            line_num = data["data"]["line_number"]
                            line_text = data["data"]["lines"]["text"].rstrip("\n\r")

                            # Convert to relative path if absolute
                            try:
                                rel_path = file_path.relative_to(base_dir)
                            except ValueError:
                                # If it's already relative or outside base_dir, use as-is
                                rel_path = file_path

                            # Get context - ripgrep JSON doesn't include context directly
                            # We'll read it from the file if needed
                            context_before = []
                            context_after = []
                            if params.context_lines > 0:
                                try:
                                    full_path = (
                                        base_dir / rel_path
                                        if not rel_path.is_absolute()
                                        else rel_path
                                    )
                                    if full_path.exists() and full_path.is_file():
                                        with open(
                                            full_path,
                                            "r",
                                            encoding="utf-8",
                                            errors="replace",
                                        ) as f:
                                            all_lines = f.readlines()
                                            if line_num <= len(all_lines):
                                                start_idx = max(
                                                    0,
                                                    line_num - 1 - params.context_lines,
                                                )
                                                end_idx = min(
                                                    len(all_lines),
                                                    line_num + params.context_lines,
                                                )
                                                context_before = [
                                                    line.rstrip("\n\r")
                                                    for line in all_lines[
                                                        start_idx : line_num - 1
                                                    ]
                                                ]
                                                context_after = [
                                                    line.rstrip("\n\r")
                                                    for line in all_lines[
                                                        line_num:end_idx
                                                    ]
                                                ]
                                except Exception:
                                    pass

                            matches.append(
                                {
                                    "file": str(rel_path),
                                    "line_number": line_num,
                                    "line": line_text,
                                    "context_before": context_before,
                                    "context_after": context_after,
                                }
                            )
                        elif data.get("type") == "summary":
                            files_searched = (
                                data.get("data", {}).get("stats", {}).get("searched", 0)
                            )
                    except (json.JSONDecodeError, KeyError):
                        continue
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            # Fallback to Python-based search
            matches = _python_grep_search(
                search_path,
                params.pattern,
                params.file_pattern,
                params.case_sensitive,
                params.max_results,
                params.context_lines,
                gitignore_patterns,
                base_dir,
            )
            files_searched = len(set(m["file"] for m in matches))

        # Limit results
        matches = matches[: params.max_results]

        # Format response
        files_with_matches = len(set(m["file"] for m in matches))

        if params.response_format == ResponseFormat.COMPACT:
            compact_matches = [
                {
                    "file": m["file"],
                    "line_number": m["line_number"],
                    "line": m["line"],
                }
                for m in matches
            ]
            result = {
                "pattern": params.pattern,
                "files_searched": files_searched or files_with_matches,
                "total_matches": len(matches),
                "matches": compact_matches,
                "truncated": len(matches) >= params.max_results,
            }
            return json.dumps(result, indent=2)

        if params.response_format == ResponseFormat.JSON:
            result = {
                "pattern": params.pattern,
                "files_searched": files_searched or files_with_matches,
                "total_matches": len(matches),
                "matches": matches,
                "truncated": len(matches) >= params.max_results,
            }
            return json.dumps(result, indent=2)

        # Markdown format
        markdown = "# Grep Results\n\n"
        markdown += f"**Pattern:** `{params.pattern}`\n"
        markdown += f"**Files Searched:** {files_searched or files_with_matches}\n"
        markdown += f"**Total Matches:** {len(matches)}\n"
        markdown += f"**Showing:** {len(matches)} matches\n\n"

        if not matches:
            markdown += "No matches found.\n"
        else:
            # Group by file
            by_file: Dict[str, List[Dict[str, Any]]] = {}
            for match in matches:
                file_key = match["file"]
                if file_key not in by_file:
                    by_file[file_key] = []
                by_file[file_key].append(match)

            for file_key, file_matches in by_file.items():
                markdown += f"## {file_key}\n\n"
                for match in file_matches:
                    line_num = match["line_number"]
                    line_text = match["line"]
                    context_before = match.get("context_before", [])
                    context_after = match.get("context_after", [])

                    markdown += f"**Line {line_num}:**\n"
                    markdown += "```\n"

                    # Show context before
                    for i, ctx_line in enumerate(context_before):
                        ctx_line_num = line_num - len(context_before) + i
                        markdown += f"{ctx_line_num}: {ctx_line}\n"

                    # Show matching line
                    markdown += f"{line_num}: {line_text}\n"

                    # Show context after
                    for i, ctx_line in enumerate(context_after):
                        ctx_line_num = line_num + 1 + i
                        markdown += f"{ctx_line_num}: {ctx_line}\n"

                    markdown += "```\n\n"

                markdown += "---\n\n"

        markdown += "\n**Summary:**\n"
        if matches:
            files_with_matches_set = {match["file"] for match in matches}
            markdown += f"- {len(files_with_matches_set)} files with matches\n"
        else:
            markdown += "- 0 files with matches\n"
        markdown += f"- {len(matches)} total occurrences\n"
        markdown += f"- Pattern: `{params.pattern}`\n"

        return _truncate_response(markdown, len(matches))

    except Exception as e:
        return _handle_api_error(e)


async def workspace_str_replace(params: StrReplaceInput) -> str:
    """
    [LOCAL] Replace an exact string match in a local workspace file.

    For editing files on GitHub remote, use github_str_replace instead.

    **Workspace Configuration**: Set MCP_WORKSPACE_ROOT environment variable
    to your project directory. Defaults to current working directory.

    This tool finds an exact match of old_str in the file and replaces it with new_str.
    The match must be unique (exactly one occurrence) to prevent accidental replacements.

    Security: Repository-rooted, no parent traversal allowed.

    Args:
        params (StrReplaceInput): Validated input parameters containing:
            - path (str): Relative path to file under repository root
            - old_str (str): Exact string to find and replace (must be unique)
            - new_str (str): Replacement string
            - description (Optional[str]): Optional description of the change

    Returns:
        str: Confirmation message with details of the replacement

    Examples:
        - Use when: "Replace function name in file"
        - Use when: "Update configuration value"
        - Use when: "Fix typo in documentation"
        - Use when: "Update version number"

    Error Handling:
        - Returns error if file not found
        - Returns error if old_str not found
        - Returns error if multiple matches found (must be unique)
        - Returns error if path traversal detected
    """
    try:
        # Validate and normalize path
        base_dir = WORKSPACE_ROOT  # Use configurable workspace
        norm_path = Path(params.path).as_posix()

        # Check for path traversal
        if ".." in norm_path or norm_path.startswith("..") or os.path.isabs(norm_path):
            return "Error: Path traversal is not allowed."

        abs_path = (base_dir / norm_path).resolve()

        # Ensure it's within repo root
        try:
            abs_path.relative_to(base_dir)
        except ValueError:
            return f"Error: Access outside workspace root ({WORKSPACE_ROOT}) is not allowed."

        if not abs_path.exists():
            return f"Error: File does not exist: {params.path}"

        if abs_path.is_dir():
            return f"Error: Path is a directory, not a file: {params.path}"

        # Read file content
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return f"Error: Could not read file: {str(e)}"

        # Count occurrences
        count = content.count(params.old_str)

        if count == 0:
            return f"Error: String not found in file '{params.path}'. The exact string '{params.old_str[:50]}{'...' if len(params.old_str) > 50 else ''}' was not found."

        if count > 1:
            return f"Error: Multiple matches found ({count} occurrences). The string must appear exactly once for safety. Found at {count} locations in '{params.path}'."

        # Perform replacement
        new_content = content.replace(params.old_str, params.new_str, 1)

        # Write back to file
        try:
            with open(abs_path, "w", encoding="utf-8", newline="") as f:
                f.write(new_content)
        except Exception as e:
            return f"Error: Could not write to file: {str(e)}"

        # Build confirmation message
        result = "✅ String replacement successful!\n\n"
        result += f"**File:** `{params.path}`\n"
        if params.description:
            result += f"**Description:** {params.description}\n"
        result += "**Occurrences:** 1 (unique match)\n"
        result += f"**Replaced:** `{params.old_str[:100]}{'...' if len(params.old_str) > 100 else ''}`\n"
        result += f"**With:** `{params.new_str[:100]}{'...' if len(params.new_str) > 100 else ''}`\n"

        return result

    except Exception as e:
        return _handle_api_error(e)


async def workspace_read_file(params: ReadFileChunkInput) -> str:
    """
    [LOCAL] Read a specific range of lines from a local workspace file.

    For reading files from GitHub remote, use github_get_file_content instead.

    **Workspace Configuration**: Set MCP_WORKSPACE_ROOT environment variable
    to your project directory. Defaults to current working directory.

    Security:
    - Normalizes path
    - Denies parent traversal (..)
    - Enforces repo-root constraint
    - Caps lines read
    """
    try:
        base_dir = WORKSPACE_ROOT.resolve()  # Use configurable workspace
        norm_path = os.path.normpath(params.path)

        if norm_path.startswith("..") or os.path.isabs(norm_path):
            return "Error: Path traversal is not allowed."

        abs_path = os.path.abspath(os.path.join(str(base_dir), norm_path))
        if not abs_path.startswith(str(base_dir) + os.sep) and abs_path != str(
            base_dir
        ):
            return "Error: Access outside workspace root is not allowed."

        if not os.path.exists(abs_path):
            return "Error: File does not exist."
        if os.path.isdir(abs_path):
            return "Error: Path is a directory."

        start = max(1, params.start_line)
        end = start + params.num_lines - 1

        lines: List[str] = []
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            for current_idx, line in enumerate(f, start=1):
                if current_idx < start:
                    continue
                if current_idx > end:
                    break
                lines.append(line.rstrip("\n"))

        header = f"# {norm_path}\n\nLines {start}-{end} (max {params.num_lines})\n\n"
        content = "\n".join(lines) if lines else "(no content in range)"
        return _truncate_response(header + "```\n" + content + "\n```")
    except Exception as e:
        return _handle_api_error(e)
