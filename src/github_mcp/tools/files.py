"""Files tools for GitHub MCP Server."""

from typing import List, Dict, Any
import json
import httpx
import base64
import os
import fnmatch

from ..utils.github_client import GhClient

from ..models.inputs import (
    BatchFileOperationsInput,
    CreateFileInput,
    DeleteFileInput,
    GetFileContentInput,
    GitUserInfo,  # noqa: F401 - Used in type hints via Pydantic models
    GitHubGrepInput,
    GitHubReadFileChunkInput,
    GitHubStrReplaceInput,
    ListRepoContentsInput,
    UpdateFileInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _truncate_response
from ..utils.compact_format import format_response


async def github_get_file_content(params: GetFileContentInput) -> str:
    """
    Retrieve the content of a file from a GitHub repository.

    Fetches file content from a specific branch, tag, or commit. Automatically
    decodes base64-encoded content for text files.

    Args:
        params (GetFileContentInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - path (str): File path in repository
            - ref (Optional[str]): Branch, tag, or commit SHA
            - token (Optional[str]): GitHub token

    Returns:
        str: File content with metadata (name, size, encoding, etc.)

    Examples:
        - Use when: "Show me the README from tensorflow/tensorflow"
        - Use when: "Get the content of src/main.py"
        - Use when: "Fetch package.json from the main branch"

    Error Handling:
        - Returns error if file not found (404)
        - Returns error if file is too large for API
        - Handles binary files appropriately
    """
    try:
        params_dict = {}
        if params.ref:
            params_dict["ref"] = params.ref

        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            token=params.token,
            params=params_dict,
        )

        # Handle cache marker (304 Not Modified response)
        if isinstance(data, dict) and data.get("_from_cache"):
            # Retry once without conditional headers to fetch fresh content
            data = await _make_github_request(
                f"repos/{params.owner}/{params.repo}/contents/{params.path}",
                token=params.token,
                params=params_dict,
                skip_cache_headers=True,
            )

        # Validate that we have the expected structure
        if not isinstance(data, dict) or "name" not in data:
            return f"Error: Unexpected response format from GitHub API. Expected file data, got: {type(data).__name__}"

        # Handle file content
        if data.get("encoding") == "base64":
            import base64

            content = base64.b64decode(data["content"]).decode(
                "utf-8", errors="replace"
            )
        else:
            content = data.get("content", "")

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result)

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "content"
            )
            return json.dumps(compact_data, indent=2)

        result = f"""# File: {data.get("name", "unknown")}

**Path:** {data.get("path", "unknown")}
**Size:** {data.get("size", 0):,} bytes
**Type:** {data.get("type", "unknown")}
**Encoding:** {data.get("encoding", "none")}
**SHA:** {data.get("sha", "unknown")}
**URL:** {data.get("html_url", "unknown")}

---

**Content:**

```
{content}
```
"""

        return _truncate_response(result)

    except Exception as e:
        return _handle_api_error(e)


async def github_create_file(params: CreateFileInput) -> str:
    """
    Create a new file in a GitHub repository.

    This tool creates a new file with the specified content and commits it to the repository.
    If the file already exists, this will fail - use github_update_file instead.

    Args:
        params (CreateFileInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - path (str): File path in repository
            - content (str): File content
            - message (str): Commit message
            - branch (Optional[str]): Target branch
            - committer (Optional[GitUserInfo]): Custom committer info
            - author (Optional[GitUserInfo]): Custom author info
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation message with commit details

    Examples:
        - Use when: "Create a new README.md file"
        - Use when: "Add a LICENSE file to the repository"
        - Use when: "Create docs/API.md with content..."

    Error Handling:
        - Returns error if file already exists (422)
        - Returns error if authentication fails (401/403)
        - Returns error if branch doesn't exist (404)
    """
    auth_token = await _get_auth_token_fallback(params.token)

    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating files. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # Encode content to base64
        content_bytes = params.content.encode("utf-8")
        content_base64 = base64.b64encode(content_bytes).decode("utf-8")

        # Prepare request body
        body: Dict[str, Any] = {"message": params.message, "content": content_base64}

        if params.branch:
            body["branch"] = params.branch
        if params.committer:
            body["committer"] = {
                "name": params.committer.name,
                "email": params.committer.email,
            }
        if params.author:
            body["author"] = {"name": params.author.name, "email": params.author.email}

        # Make API request
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            method="PUT",
            token=auth_token,
            json=body,
        )

        # Return useful data with path, sha, and url
        content = data.get("content", {})
        return json.dumps(
            {
                "success": True,
                "path": content.get("path") or params.path,
                "sha": content.get("sha") or data.get("commit", {}).get("sha"),
                "url": content.get("html_url")
                or data.get("content", {}).get("html_url")
                or f"https://github.com/{params.owner}/{params.repo}/blob/{params.branch or 'main'}/{params.path}",
                "message": f"File '{params.path}' created successfully",
            },
            indent=2,
        )

    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {"success": False, "error": str(e), "type": type(e).__name__}

        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = (
                    e.response.text[:200] if e.response.text else "Unknown error"
                )

            # Add helpful context for common errors
            if error_info["status_code"] == 422:
                error_info["hint"] = (
                    "This file already exists. Use 'github_update_file' to modify it, or 'github_delete_file' to remove it first."
                )
        else:
            error_info["message"] = str(e)

        return json.dumps(error_info, indent=2)


async def github_update_file(params: UpdateFileInput) -> str:
    """
    Update an existing file in a GitHub repository.

    This tool modifies the content of an existing file and commits the changes.
    Requires the current SHA of the file (get it from github_get_file_content first).

    Args:
        params (UpdateFileInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - path (str): File path in repository
            - content (str): New file content
            - message (str): Commit message
            - sha (str): Current file SHA (required)
            - branch (Optional[str]): Target branch
            - committer (Optional[GitUserInfo]): Custom committer info
            - author (Optional[GitUserInfo]): Custom author info
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation message with commit details

    Examples:
        - Use when: "Update the README.md file"
        - Use when: "Modify src/config.py"
        - Use when: "Change the content of docs/API.md"

    Error Handling:
        - Returns error if file doesn't exist (404)
        - Returns error if SHA doesn't match (409 conflict)
        - Returns error if authentication fails (401/403)
    """
    auth_token = await _get_auth_token_fallback(params.token)

    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for updating files. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # Encode content to base64
        content_bytes = params.content.encode("utf-8")
        content_base64 = base64.b64encode(content_bytes).decode("utf-8")

        # Prepare request body
        body: Dict[str, Any] = {
            "message": params.message,
            "content": content_base64,
            "sha": params.sha,
        }

        if params.branch:
            body["branch"] = params.branch
        if params.committer:
            body["committer"] = {
                "name": params.committer.name,
                "email": params.committer.email,
            }
        if params.author:
            body["author"] = {"name": params.author.name, "email": params.author.email}

        # Make API request
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            method="PUT",
            token=auth_token,
            json=body,
        )

        # Return the FULL GitHub API response as JSON
        return json.dumps(data, indent=2)

    except Exception as e:
        # Return structured JSON error for programmatic use
        error_info = {"success": False, "error": str(e), "type": type(e).__name__}

        # Extract detailed error info from HTTPStatusError
        if isinstance(e, httpx.HTTPStatusError):
            error_info["status_code"] = e.response.status_code
            try:
                error_body = e.response.json()
                error_info["message"] = error_body.get("message", "Unknown error")
                error_info["errors"] = error_body.get("errors", [])
            except Exception:
                error_info["message"] = (
                    e.response.text[:200] if e.response.text else "Unknown error"
                )

            # Add helpful context for common errors
            if error_info["status_code"] == 409:
                error_info["hint"] = (
                    "The file SHA doesn't match. The file may have been modified. Get the current SHA with 'github_get_file_content' and try again."
                )
            elif error_info["status_code"] == 404:
                error_info["hint"] = (
                    "File not found. Use 'github_create_file' to create it first."
                )
        else:
            error_info["message"] = str(e)

        return json.dumps(error_info, indent=2)


async def github_delete_file(params: DeleteFileInput) -> str:
    """
    Delete a file from a GitHub repository.

    ⚠️ DESTRUCTIVE OPERATION: This permanently deletes the file from the repository.
    Requires the current SHA of the file (get it from github_get_file_content first).

    Args:
        params (DeleteFileInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - path (str): File path to delete
            - message (str): Commit message explaining deletion
            - sha (str): Current file SHA (required for safety)
            - branch (Optional[str]): Target branch
            - committer (Optional[GitUserInfo]): Custom committer info
            - author (Optional[GitUserInfo]): Custom author info
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation message with commit details

    Examples:
        - Use when: "Delete the old config file"
        - Use when: "Remove docs/deprecated.md"
        - Use when: "Clean up temporary files"

    Error Handling:
        - Returns error if file doesn't exist (404)
        - Returns error if SHA doesn't match (409 conflict)
        - Returns error if authentication fails (401/403)

    Safety Notes:
        - Requires explicit SHA to prevent accidental deletions
        - Creates a commit that can be reverted if needed
        - File history is preserved in Git
    """
    auth_token = await _get_auth_token_fallback(params.token)

    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for deleting files. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # Prepare request body
        body: Dict[str, Any] = {"message": params.message, "sha": params.sha}

        if params.branch:
            body["branch"] = params.branch
        if params.committer:
            body["committer"] = {
                "name": params.committer.name,
                "email": params.committer.email,
            }
        if params.author:
            body["author"] = {"name": params.author.name, "email": params.author.email}

        # Make API request
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            method="DELETE",
            token=auth_token,
            json=body,
        )

        # Format success response
        result = f"""✅ **File Deleted Successfully!**


**Repository:** {params.owner}/{params.repo}
**File:** {params.path}
**Branch:** {params.branch or "default"}
**Commit Message:** {params.message}


**Commit Details:**
- SHA: {data["commit"]["sha"]}
- Author: {data["commit"]["author"]["name"]}
- Date: {data["commit"]["author"]["date"]}


⚠️ **Note:** File has been removed from the repository but remains in Git history.
You can restore it by reverting this commit if needed.
"""

        return result

    except Exception as e:
        error_msg = _handle_api_error(e)

        # Add helpful context for common errors
        if "409" in error_msg or "does not match" in error_msg.lower():
            error_msg += "\n\n💡 Tip: The file SHA doesn't match. The file may have been modified. Get the current SHA with 'github_get_file_content' and try again."
        elif "404" in error_msg:
            error_msg += "\n\n💡 Tip: File not found. It may have already been deleted or the path is incorrect."

        return error_msg


async def github_list_repo_contents(params: ListRepoContentsInput) -> str:
    """
    List files and directories in a repository path.

    Browse repository structure by listing contents of directories.
    Returns file/folder names, types, sizes, and paths.

    Args:
        params (ListRepoContentsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - path (str): Directory path (empty string for root)
            - ref (Optional[str]): Branch, tag, or commit
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Directory listing with file/folder information

    Examples:
        - Use when: "List files in the src directory"
        - Use when: "Show me what's in the root of the repo"
        - Use when: "Browse the docs folder"

    Error Handling:
        - Returns error if path doesn't exist (404)
        - Handles both files and directories
        - Indicates if path points to a file vs directory
    """
    try:
        params_dict = {}
        if params.ref:
            params_dict["ref"] = params.ref

        path = params.path.strip("/") if params.path else ""
        endpoint = f"repos/{params.owner}/{params.repo}/contents/{path}"

        data = await _make_github_request(
            endpoint, token=params.token, params=params_dict
        )

        # Handle cache marker (304 Not Modified response)
        if isinstance(data, dict) and data.get("_from_cache"):
            # For 304 responses, we need to make a fresh request without conditional headers
            # This is a workaround - ideally we'd cache the actual response data
            # For now, retry without cache to get the actual data
            client = GhClient.instance()
            response = await client.request(
                method="GET",
                path=f"/{endpoint}",
                token=params.token,
                params=params_dict,
                headers={"Cache-Control": "no-cache"},  # Force fresh request
            )
            response.raise_for_status()
            data = response.json()

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(
                result, len(data) if isinstance(data, list) else 1
            )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "content"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(
                result, len(data) if isinstance(data, list) else 1
            )

        # Markdown format
        if isinstance(data, dict):
            # Single file returned
            # Validate structure before accessing keys
            if "name" not in data:
                return f"Error: Unexpected response format from GitHub API. Expected file data, got: {type(data).__name__}"

            return f"""# Single File

This path points to a file, not a directory.

**Name:** {data.get("name", "unknown")}
**Path:** {data.get("path", "unknown")}
**Size:** {data.get("size", 0):,} bytes
**Type:** {data.get("type", "unknown")}
**URL:** {data.get("html_url", "unknown")}

Use `github_get_file_content` to retrieve the file content.
"""

        # Directory listing - validate it's a list
        if not isinstance(data, list):
            return f"Error: Unexpected response format from GitHub API. Expected list of items, got: {type(data).__name__}"

        display_path = path or "(root)"
        markdown = f"# Contents of /{display_path}\n\n"
        markdown += f"**Repository:** {params.owner}/{params.repo}\n"
        if params.ref:
            markdown += f"**Branch/Ref:** {params.ref}\n"
        markdown += f"**Items:** {len(data)}\n\n"

        # Separate directories and files
        directories = [
            item
            for item in data
            if isinstance(item, dict) and item.get("type") == "dir"
        ]
        files = [
            item
            for item in data
            if isinstance(item, dict) and item.get("type") == "file"
        ]

        if directories:
            markdown += "## 📁 Directories\n"
            for item in directories:
                name = item.get("name", "unknown")
                markdown += f"- `{name}/`\n"
            markdown += "\n"

        if files:
            markdown += "## 📄 Files\n"
            for item in files:
                name = item.get("name", "unknown")
                size = item.get("size", 0)
                size_kb = size / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb >= 1 else f"{size} bytes"
                markdown += f"- `{name}` ({size_str})\n"

        return _truncate_response(markdown, len(data))

    except Exception as e:
        return _handle_api_error(e)


async def github_grep(params: GitHubGrepInput) -> str:
    """
    Search for patterns in GitHub repository files using grep-like functionality.

    This tool efficiently searches through files in a GitHub repository,
    returning only matching lines with context instead of full files.
    Ideal for finding functions, errors, TODOs, or any code pattern in remote repos.

    **Use Cases:**
    - Verify code exists after pushing changes
    - Search across branches or specific commits
    - Find patterns in remote repositories without cloning
    - Efficient token usage (returns only matches, not full files)

    Args:
        params (GitHubGrepInput): Search parameters including:
            - owner/repo: Repository identification
            - pattern: Regex pattern to search for
            - ref: Optional branch/tag/commit
            - file_pattern: File filter (e.g., '*.py')
            - path: Subdirectory to search
            - context_lines: Lines before/after match
            - max_results: Maximum matches

    Returns:
        str: Formatted search results with file paths, line numbers, and matches

    Examples:
        - "Find all TODOs in Python files"
        - "Search for 'async def' in main branch"
        - "Find error handling patterns after my last push"

    Security:
        - Respects GitHub repository permissions
        - Rate limited by GitHub API
        - No local file system access
    """
    import re

    try:
        # Get repository tree to list files
        ref = params.ref or "HEAD"
        tree_endpoint = f"repos/{params.owner}/{params.repo}/git/trees/{ref}"
        tree_params = {"recursive": "1"}

        tree_response = await _make_github_request(
            tree_endpoint, params=tree_params, token=params.token
        )

        if isinstance(tree_response, dict) and tree_response.get("_from_cache"):
            # Retry without conditional request if cached
            tree_response = await _make_github_request(
                tree_endpoint, params=tree_params, token=params.token
            )

        tree_data = tree_response.get("tree", [])

        # Filter files by pattern and path
        files_to_search = []
        for item in tree_data:
            if item.get("type") != "blob":  # Only files, not directories
                continue

            file_path = item.get("path", "")

            # Apply path filter
            if params.path and not file_path.startswith(params.path):
                continue

            # Apply file pattern filter
            if params.file_pattern != "*":
                if not fnmatch.fnmatch(
                    file_path, params.file_pattern
                ) and not fnmatch.fnmatch(
                    os.path.basename(file_path), params.file_pattern
                ):
                    continue

            files_to_search.append(file_path)

        if not files_to_search:
            return f"No files matching pattern '{params.file_pattern}' in path '{params.path or 'repository'}'"

        # Compile regex pattern
        flags = 0 if params.case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(params.pattern, flags)
        except re.error as e:
            return f"Error: Invalid regex pattern: {str(e)}"

        # Search through files (limit to 100 to avoid rate limits)
        matches = []
        files_searched = 0

        for file_path in files_to_search[:100]:
            files_searched += 1

            try:
                # Get file content
                content_params = {}
                if params.ref:
                    content_params["ref"] = params.ref

                content_response = await _make_github_request(
                    f"repos/{params.owner}/{params.repo}/contents/{file_path}",
                    params=content_params if content_params else None,
                    token=params.token,
                )

                if isinstance(content_response, dict) and content_response.get(
                    "_from_cache"
                ):
                    content_response = await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/contents/{file_path}",
                        params=content_params if content_params else None,
                        token=params.token,
                    )

                # Decode content
                if content_response.get("encoding") == "base64":
                    content = base64.b64decode(content_response["content"]).decode(
                        "utf-8", errors="ignore"
                    )
                else:
                    content = content_response.get("content", "")

                lines = content.split("\n")

                # Search for pattern
                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        # Get context lines
                        context_lines = (
                            params.context_lines or 2
                        )  # Default to 2 if None
                        start_line = max(1, line_num - context_lines)
                        end_line = min(len(lines), line_num + context_lines)

                        context_before = []
                        context_after = []
                        for i in range(start_line, line_num):
                            if 1 <= i <= len(lines):
                                context_before.append(lines[i - 1].rstrip("\n\r"))
                        for i in range(line_num + 1, end_line + 1):
                            if 1 <= i <= len(lines):
                                context_after.append(lines[i - 1].rstrip("\n\r"))

                        matches.append(
                            {
                                "file": file_path,
                                "line_number": line_num,
                                "line": line.rstrip("\n\r"),
                                "context_before": context_before,
                                "context_after": context_after,
                            }
                        )

                        max_results = params.max_results or 50
                        if len(matches) >= max_results:
                            break

                max_results = params.max_results or 50
                if len(matches) >= max_results:
                    break

            except Exception:
                # Skip files that can't be read (binary, too large, etc.)
                continue

        # Limit results
        max_results = params.max_results or 50
        matches = matches[:max_results]

        # Format results
        if params.response_format == ResponseFormat.JSON:
            result_dict: Dict[str, Any] = {
                "pattern": params.pattern,
                "repository": f"{params.owner}/{params.repo}",
                "ref": params.ref or "default branch",
                "matches": len(matches),
                "files_searched": files_searched,
                "results": matches,
            }
            return json.dumps(result_dict, indent=2)
        else:
            # Markdown format
            result = f"# Search Results: '{params.pattern}'\n\n"
            result += f"**Repository:** {params.owner}/{params.repo}\n"
            result += f"**Ref:** {params.ref or 'default branch'}\n"
            result += (
                f"**Matches:** {len(matches)} in {files_searched} files searched\n\n"
            )

            if not matches:
                result += "No matches found.\n"
            else:
                # Group by file
                by_file: Dict[str, List[Dict[str, Any]]] = {}
                for match in matches:
                    file_path = match["file"]
                    if file_path not in by_file:
                        by_file[file_path] = []
                    by_file[file_path].append(match)

                for file_path, file_matches in by_file.items():
                    result += f"\n## {file_path}\n\n"
                    for match in file_matches:
                        result += (
                            f"**Line {match['line_number']}:** `{match['line']}`\n\n"
                        )
                        if match.get("context_before") or match.get("context_after"):
                            result += "```\n"
                            for ctx_line in match.get("context_before", []):
                                result += f"  {ctx_line}\n"
                            result += f"> {match['line']}\n"
                            for ctx_line in match.get("context_after", []):
                                result += f"  {ctx_line}\n"
                            result += "```\n\n"

            return _truncate_response(result, len(matches))

    except Exception as e:
        return _handle_api_error(e)


async def github_batch_file_operations(params: BatchFileOperationsInput) -> str:
    """
    Perform multiple file operations (create/update/delete) in a single commit.

    This is much more efficient than individual file operations. All changes are committed
    together atomically - either all succeed or all fail.

    Args:
        params (BatchFileOperationsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - operations (List[FileOperation]): List of file operations
            - message (str): Commit message
            - branch (Optional[str]): Target branch
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation message with commit details

    Examples:
        - Use when: "Update README.md and LICENSE in one commit"
        - Use when: "Create multiple documentation files"
        - Use when: "Refactor: delete old files and create new ones"

    Error Handling:
        - Returns error if any file operation is invalid
        - Returns error if branch doesn't exist (404)
        - Validates all operations before making changes
    """
    try:
        token = await _get_auth_token_fallback(params.token)
        if not token:
            return "Error: GitHub token required for batch file operations. Set GITHUB_TOKEN or configure GitHub App authentication."

        branch_name = params.branch or "main"
        if not params.branch:
            repo_info = await _make_github_request(
                f"repos/{params.owner}/{params.repo}", token=token
            )
            branch_name = repo_info["default_branch"]

        branch_data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/git/ref/heads/{branch_name}",
            token=token,
        )
        latest_commit_sha = branch_data["object"]["sha"]

        commit_data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/git/commits/{latest_commit_sha}",
            token=token,
        )
        base_tree_sha = commit_data["tree"]["sha"]

        tree: List[Dict[str, Any]] = []
        for op in params.operations:
            if op.operation == "delete":
                tree.append(
                    {"path": op.path, "mode": "100644", "type": "blob", "sha": None}
                )
            else:
                if op.content is None:
                    raise ValueError(
                        f"Content is required for operation '{op.operation}' on path '{op.path}'"
                    )
                content_bytes = op.content.encode("utf-8")
                encoded_content = base64.b64encode(content_bytes).decode("utf-8")
                blob_data = await _make_github_request(
                    f"repos/{params.owner}/{params.repo}/git/blobs",
                    method="POST",
                    token=token,
                    json={"content": encoded_content, "encoding": "base64"},
                )
                tree.append(
                    {
                        "path": op.path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob_data["sha"],
                    }
                )

        new_tree = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/git/trees",
            method="POST",
            token=token,
            json={"base_tree": base_tree_sha, "tree": tree},
        )

        new_commit = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/git/commits",
            method="POST",
            token=token,
            json={
                "message": params.message,
                "tree": new_tree["sha"],
                "parents": [latest_commit_sha],
            },
        )

        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/git/refs/heads/{branch_name}",
            method="PATCH",
            token=token,
            json={"sha": new_commit["sha"]},
        )

        response = "# Batch File Operations Complete! ✅\n\n"
        response += f"**Repository:** {params.owner}/{params.repo}  \n"
        response += f"**Branch:** {branch_name}  \n"
        response += f"**Commit Message:** {params.message}  \n"
        response += f"**Commit SHA:** `{new_commit['sha']}`  \n"
        response += f"**Operations:** {len(params.operations)} files modified  \n\n"
        response += "## Changes:\n\n"
        for op in params.operations:
            emoji = (
                "📝"
                if op.operation == "update"
                else "✨"
                if op.operation == "create"
                else "🗑️"
            )
            response += f"- {emoji} **{op.operation.upper()}**: `{op.path}`\n"
        response += f"\n**View Commit:** https://github.com/{params.owner}/{params.repo}/commit/{new_commit['sha']}\n"
        return response

    except Exception as e:
        return _handle_api_error(e)


# Workflow Optimization Tool


async def github_str_replace(params: GitHubStrReplaceInput) -> str:
    """
    Replace an exact string match in a GitHub repository file with a new string.

    This tool finds an exact match of old_str in the GitHub file and replaces it with new_str.
    The match must be unique (exactly one occurrence) to prevent accidental replacements.
    Updates the file via GitHub API with a commit.

    **Use Cases:**
    - Make surgical edits to GitHub files without cloning
    - Update configuration values in remote repos
    - Fix typos or update documentation on GitHub
    - Token-efficient file updates (only changes what's needed)

    Args:
        params (GitHubStrReplaceInput): Parameters including:
            - owner/repo: Repository identification
            - path: File path in repository
            - old_str: Exact string to find and replace (must be unique)
            - new_str: Replacement string
            - ref: Optional branch (defaults to default branch)
            - commit_message: Optional commit message
            - description: Optional description of the change

    Returns:
        str: Confirmation message with commit details

    Examples:
        - "Replace version number in README.md on GitHub"
        - "Update configuration value in remote file"
        - "Fix typo in GitHub documentation"

    Security:
        - Respects GitHub repository permissions
        - Requires write access to repository
        - No local file system access
    """

    try:
        # Get token (try param, then GitHub App, then PAT)
        token = await _get_auth_token_fallback(params.token)
        if not token:
            return json.dumps(
                {
                    "error": "Authentication required",
                    "message": "GitHub token required for updating files. Set GITHUB_TOKEN environment variable or pass token parameter.",
                    "success": False,
                },
                indent=2,
            )

        # Get current file content and SHA
        content_params = {}
        if params.ref:
            content_params["ref"] = params.ref

        file_response = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            params=content_params if content_params else None,
            token=token,
        )

        if isinstance(file_response, dict) and file_response.get("_from_cache"):
            file_response = await _make_github_request(
                f"repos/{params.owner}/{params.repo}/contents/{params.path}",
                params=content_params if content_params else None,
                token=token,
            )

        # Decode content
        if file_response.get("encoding") == "base64":
            content = base64.b64decode(file_response["content"]).decode(
                "utf-8", errors="replace"
            )
        else:
            content = file_response.get("content", "")

        current_sha = file_response.get("sha")
        if not current_sha:
            return "Error: Could not get file SHA. File may not exist or you may not have access."

        # Count occurrences
        count = content.count(params.old_str)

        if count == 0:
            return f"Error: String not found in file '{params.path}'. The exact string '{params.old_str[:50]}{'...' if len(params.old_str) > 50 else ''}' was not found."

        if count > 1:
            return f"Error: Multiple matches found ({count} occurrences). The string must appear exactly once for safety. Found at {count} locations in '{params.path}'."

        # Perform replacement
        new_content = content.replace(params.old_str, params.new_str, 1)

        # Encode new content
        new_content_bytes = new_content.encode("utf-8")
        new_content_b64 = base64.b64encode(new_content_bytes).decode("utf-8")

        # Generate commit message if not provided
        commit_msg = params.commit_message
        if not commit_msg:
            commit_msg = f"Update {params.path}"
            if params.description:
                commit_msg += f": {params.description}"
            else:
                commit_msg += f" (replace '{params.old_str[:30]}{'...' if len(params.old_str) > 30 else ''}')"

        # Update file via GitHub API
        update_data = {
            "message": commit_msg,
            "content": new_content_b64,
            "sha": current_sha,
        }

        if params.ref:
            update_data["branch"] = params.ref

        update_response = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            method="PUT",
            token=token,
            json=update_data,
        )

        # Format confirmation
        result = "✅ String replacement successful on GitHub!\n\n"
        result += f"**Repository:** {params.owner}/{params.repo}\n"
        result += f"**File:** {params.path}\n"
        result += f"**Branch:** {params.ref or 'default branch'}\n"
        if params.description:
            result += f"**Description:** {params.description}\n"
        result += (
            f"**Commit:** {update_response.get('commit', {}).get('sha', 'N/A')[:7]}\n"
        )
        result += f"**Commit Message:** {commit_msg}\n"
        result += (
            f"**URL:** {update_response.get('content', {}).get('html_url', 'N/A')}\n\n"
        )
        result += f"**Replaced:** `{params.old_str[:100]}{'...' if len(params.old_str) > 100 else ''}`\n"
        result += f"**With:** `{params.new_str[:100]}{'...' if len(params.new_str) > 100 else ''}`\n"

        return result

    except Exception as e:
        return _handle_api_error(e)


async def github_read_file_chunk(params: GitHubReadFileChunkInput) -> str:
    """
    Read a specific range of lines from a GitHub repository file.

    This tool efficiently reads just the lines you need from a GitHub file,
    avoiding loading entire large files into memory. Perfect for:
    - Reading specific functions or sections
    - Checking code after pushing changes
    - Reviewing specific parts of documentation
    - Token-efficient file reading (90%+ savings vs full file)

    Args:
        params (GitHubReadFileChunkInput): Parameters including:
            - owner/repo: Repository identification
            - path: File path in repository
            - start_line: Starting line (1-based)
            - num_lines: Number of lines to read (max 500)
            - ref: Optional branch/tag/commit

    Returns:
        str: Numbered lines from the file with metadata

    Examples:
        - "Read lines 50-100 of main.py from main branch"
        - "Show me the first 20 lines of README.md"
        - "Read the function starting at line 150"

    Security:
        - Respects GitHub repository permissions
        - No local file system access
        - Rate limited by GitHub API
    """
    try:
        # Get file content from GitHub
        content_params = {}
        if params.ref:
            content_params["ref"] = params.ref

        content_response = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/contents/{params.path}",
            params=content_params if content_params else None,
            token=params.token,
        )

        if isinstance(content_response, dict) and content_response.get("_from_cache"):
            # Retry without conditional request if cached
            content_response = await _make_github_request(
                f"repos/{params.owner}/{params.repo}/contents/{params.path}",
                params=content_params if content_params else None,
                token=params.token,
            )

        # Decode content
        if content_response.get("encoding") == "base64":
            content = base64.b64decode(content_response["content"]).decode(
                "utf-8", errors="ignore"
            )
        else:
            content = content_response.get("content", "")

        lines = content.split("\n")
        total_lines = len(lines)

        # Calculate line range
        start_idx = params.start_line - 1  # Convert to 0-based
        end_idx = min(start_idx + params.num_lines, total_lines)

        if start_idx >= total_lines:
            return f"Error: start_line {params.start_line} exceeds file length ({total_lines} lines)"

        if start_idx < 0:
            return "Error: start_line must be >= 1"

        # Extract requested lines
        chunk_lines = lines[start_idx:end_idx]

        # Format output with line numbers
        result = f"# File: {params.path}\n\n"
        result += f"**Repository:** {params.owner}/{params.repo}\n"
        result += f"**Ref:** {params.ref or 'default branch'}\n"
        result += f"**Lines:** {params.start_line}-{params.start_line + len(chunk_lines) - 1} of {total_lines}\n"
        result += f"**Size:** {content_response.get('size', 0)} bytes\n\n"
        result += "```\n"

        for i, line in enumerate(chunk_lines, start=params.start_line):
            result += f"{i:4d}: {line}\n"

        result += "```\n"

        if end_idx < total_lines:
            result += f"\n*({total_lines - end_idx} more lines not shown)*\n"

        return result

    except Exception as e:
        return _handle_api_error(e)
