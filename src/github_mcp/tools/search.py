"""Search tools for GitHub MCP Server."""

import json
from typing import Dict, Any, List, Union, cast

from ..models.inputs import (
    SearchCodeInput,
    SearchIssuesInput,
    SearchRepositoriesInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request
from ..utils.errors import _handle_api_error
from ..utils.formatting import (
    _format_timestamp,
    _truncate_response,
    _slim_search_response,
)
from ..utils.compact_format import format_response


async def github_search_code(params: SearchCodeInput) -> str:
    """
    Search for code snippets across GitHub repositories.

    Powerful code search with language filtering, repository targeting, and
    advanced qualifiers. Essential for finding patterns, TODOs, and specific functions.

    Args:
        params (SearchCodeInput): Validated input parameters containing:
            - query (str): Code search query with optional qualifiers
            - sort (Optional[str]): Sort by 'indexed' (default)
            - order (SortOrder): Sort order ('asc' or 'desc')
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Code search results with file locations and context

    Examples:
        - Use when: "Find all TODOs in Python repositories"
          query="TODO language:python"
        - Use when: "Search for authentication functions"
          query="function authenticate"
        - Use when: "Find security vulnerabilities"
          query="password language:javascript"
        - Use when: "Find API endpoints in specific repo"
          query="@RequestMapping repo:spring-projects/spring-framework"

    Query Qualifiers:
        - language:python - Code in Python
        - repo:owner/repo - Search specific repository
        - user:username - Search user's repositories
        - org:organization - Search organization's repositories
        - path:src/main - Search specific path
        - extension:js - Files with specific extension
        - size:>1000 - Files larger than 1000 bytes

    Error Handling:
        - Returns error if query syntax is invalid
        - Handles rate limiting for search API
        - Provides clear guidance for complex queries
    """
    try:
        order_value = (
            params.order.value
            if params.order is not None and hasattr(params.order, "value")
            else params.order
        )
        sort_value = (
            params.sort.value
            if params.sort is not None and hasattr(params.sort, "value")
            else params.sort
        )
        params_dict = {"q": params.query, "per_page": params.limit, "page": params.page}
        if order_value is not None:
            params_dict["order"] = order_value
        if sort_value is not None:
            params_dict["sort"] = sort_value

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            "search/code", token=params.token, params=params_dict
        )

        # Search API returns dict with 'items' list
        search_result: Dict[str, Any] = (
            cast(Dict[str, Any], data)
            if isinstance(data, dict)
            else {"total_count": 0, "items": []}
        )
        items: List[Dict[str, Any]] = search_result.get("items", [])
        total_count: int = search_result.get("total_count", 0)

        if params.response_format == ResponseFormat.COMPACT:
            compact_items = format_response(
                items, ResponseFormat.COMPACT.value, "search_code"
            )
            result = json.dumps(
                {"total_count": total_count, "items": compact_items}, indent=2
            )
            return _truncate_response(result, total_count)

        if params.response_format == ResponseFormat.JSON:
            slim_result = _slim_search_response(search_result, "code")
            result = json.dumps(slim_result, indent=2)
            return _truncate_response(result, total_count)

        # Markdown format
        markdown = "# Code Search Results\n\n"
        markdown += f"**Query:** `{params.query}`\n"
        markdown += f"**Total Results:** {total_count:,}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(items)} files\n\n"

        if not items:
            markdown += "No code found matching your query.\n"
        else:
            for item in items:
                # Extract repository info
                repo_name = item["repository"]["full_name"]
                file_path = item["path"]
                file_name = file_path.split("/")[-1]

                markdown += f"## 📄 {file_name}\n"
                markdown += (
                    f"**Repository:** [{repo_name}]({item['repository']['html_url']})\n"
                )
                markdown += f"**Path:** `{file_path}`\n"
                markdown += f"**Language:** {item.get('language', 'Unknown')}\n"
                markdown += f"**Size:** {item['size']:,} bytes\n"
                markdown += f"**URL:** [{item['html_url']}]({item['html_url']})\n\n"

                # Show code snippets if available
                if "text_matches" in item and item["text_matches"]:
                    markdown += "**Code Snippets:**\n"
                    for match in item["text_matches"][:3]:  # Limit to first 3 matches
                        if match.get("fragment"):
                            # Clean up the fragment
                            fragment = match["fragment"].replace("\n", " ").strip()
                            if len(fragment) > 200:
                                fragment = fragment[:200] + "..."
                            markdown += f"```\n{fragment}\n```\n"
                    markdown += "\n"

                markdown += "---\n\n"

        return _truncate_response(markdown, total_count)

    except Exception as e:
        # Return JSON error if response_format is JSON
        if params.response_format == ResponseFormat.JSON:
            error_data = {
                "error": True,
                "message": _handle_api_error(e),
                "query": params.query,
            }
            return json.dumps(error_data, indent=2)
        return _handle_api_error(e)


async def github_search_repositories(params: SearchRepositoriesInput) -> str:
    """
    Search for repositories on GitHub with advanced filtering.

    Supports GitHub's full search syntax including language, stars, topics, and more.
    Returns sorted and paginated results.

    Args:
        params (SearchRepositoriesInput): Validated input parameters containing:
            - query (str): Search query with optional qualifiers
            - sort (Optional[str]): Sort by 'stars', 'forks', 'updated', etc.
            - order (SortOrder): Sort order ('asc' or 'desc')
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Search results with repository details and pagination info

    Examples:
        - Use when: "Find Python machine learning repositories"
          query="machine learning language:python"
        - Use when: "Search for React repositories with >10k stars"
          query="react stars:>10000"
        - Use when: "Find trending JavaScript projects"
          query="language:javascript" sort="stars"

    Query Qualifiers:
        - language:python - Repositories in Python
        - stars:>1000 - More than 1000 stars
        - topics:machine-learning - Tagged with topic
        - created:>2023-01-01 - Created after date
        - fork:false - Exclude forks

    Error Handling:
        - Returns error if query syntax is invalid
        - Handles rate limiting for search API
        - Provides clear error messages for all failures
    """
    try:
        order_value = (
            params.order.value
            if params.order is not None and hasattr(params.order, "value")
            else params.order
        )
        sort_value = (
            params.sort.value
            if params.sort is not None and hasattr(params.sort, "value")
            else params.sort
        )
        params_dict = {"q": params.query, "per_page": params.limit, "page": params.page}

        if order_value is not None:
            params_dict["order"] = order_value
        if sort_value is not None:
            params_dict["sort"] = sort_value

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            "search/repositories", token=params.token, params=params_dict
        )

        # Search API returns dict with 'items' list
        search_result: Dict[str, Any] = (
            cast(Dict[str, Any], data)
            if isinstance(data, dict)
            else {"total_count": 0, "items": []}
        )
        items: List[Dict[str, Any]] = search_result.get("items", [])
        total_count: int = search_result.get("total_count", 0)

        if params.response_format == ResponseFormat.COMPACT:
            compact_items = format_response(items, ResponseFormat.COMPACT.value, "repo")
            result = json.dumps(
                {"total_count": total_count, "items": compact_items}, indent=2
            )
            return _truncate_response(result, total_count)

        if params.response_format == ResponseFormat.JSON:
            slim_result = _slim_search_response(search_result, "repository")
            result = json.dumps(slim_result, indent=2)
            return _truncate_response(result, total_count)

        # Markdown format
        markdown = "# Repository Search Results\n\n"
        markdown += f"**Query:** {params.query}\n"
        markdown += f"**Total Results:** {total_count:,}\n"
        markdown += (
            f"**Page:** {params.page} | **Showing:** {len(items)} repositories\n\n"
        )

        if not items:
            markdown += "No repositories found matching your query.\n"
        else:
            for repo in items:
                markdown += f"## {repo['full_name']}\n"
                markdown += f"{repo['description'] or 'No description'}\n\n"
                markdown += f"- ⭐ **Stars:** {repo['stargazers_count']:,}\n"
                markdown += f"- 🍴 **Forks:** {repo['forks_count']:,}\n"
                markdown += f"- **Language:** {repo['language'] or 'Not specified'}\n"
                markdown += f"- **Updated:** {_format_timestamp(repo['updated_at'])}\n"

                if repo.get("topics"):
                    topics = ", ".join([f"`{t}`" for t in repo["topics"][:5]])
                    markdown += f"- **Topics:** {topics}\n"

                markdown += f"- **URL:** {repo['html_url']}\n\n"
                markdown += "---\n\n"

        return _truncate_response(markdown, total_count)

    except Exception as e:
        return _handle_api_error(e)


async def github_search_issues(params: SearchIssuesInput) -> str:
    """
    Search for issues across GitHub repositories with advanced filtering.

    Powerful issue search with state, label, author, and repository filtering.
    Essential for finding specific problems, feature requests, and security issues.

    Args:
        params (SearchIssuesInput): Validated input parameters containing:
            - query (str): Issue search query with optional qualifiers
            - sort (Optional[str]): Sort by 'created', 'updated', 'comments'
            - order (SortOrder): Sort order ('asc' or 'desc')
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Issue search results with details and pagination info

    Examples:
        - Use when: "Find security issues in Python projects"
          query="security language:python"
        - Use when: "Search for bug reports"
          query="bug label:bug"
        - Use when: "Find feature requests in specific repo"
          query="feature request repo:microsoft/vscode"
        - Use when: "Find issues by specific user"
          query="author:torvalds"

    Query Qualifiers:
        - state:open - Open issues only
        - state:closed - Closed issues only
        - label:bug - Issues with specific label
        - author:username - Issues by specific author
        - assignee:username - Issues assigned to user
        - repo:owner/repo - Issues in specific repository
        - user:username - Issues in user's repositories
        - org:organization - Issues in organization's repositories
        - language:python - Issues in Python repositories
        - created:>2023-01-01 - Issues created after date
        - updated:>2023-01-01 - Issues updated after date
        - comments:>10 - Issues with more than 10 comments
        - in:title - Search in issue titles only
        - in:body - Search in issue bodies only

    Error Handling:
        - Returns error if query syntax is invalid
        - Handles rate limiting for search API
        - Provides clear guidance for complex queries
    """
    try:
        order_value = (
            params.order.value
            if params.order is not None and hasattr(params.order, "value")
            else params.order
        )
        sort_value = (
            params.sort.value
            if params.sort is not None and hasattr(params.sort, "value")
            else params.sort
        )
        params_dict = {"q": params.query, "per_page": params.limit, "page": params.page}

        if order_value is not None:
            params_dict["order"] = order_value
        if sort_value is not None:
            params_dict["sort"] = sort_value

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            "search/issues", token=params.token, params=params_dict
        )

        # Search API returns dict with 'items' list
        search_result: Dict[str, Any] = (
            cast(Dict[str, Any], data)
            if isinstance(data, dict)
            else {"total_count": 0, "items": []}
        )
        items: List[Dict[str, Any]] = search_result.get("items", [])
        total_count: int = search_result.get("total_count", 0)

        if params.response_format == ResponseFormat.COMPACT:
            compact_items = format_response(
                items, ResponseFormat.COMPACT.value, "issue"
            )
            result = json.dumps(
                {"total_count": total_count, "items": compact_items}, indent=2
            )
            return _truncate_response(result, total_count)

        if params.response_format == ResponseFormat.JSON:
            slim_result = _slim_search_response(search_result, "issue")
            result = json.dumps(slim_result, indent=2)
            return _truncate_response(result, total_count)

        # Markdown format
        markdown = "# Issue Search Results\n\n"
        markdown += f"**Query:** `{params.query}`\n"
        markdown += f"**Total Results:** {total_count:,}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(items)} issues\n\n"

        if not items:
            markdown += "No issues found matching your query.\n"
        else:
            for issue in items:
                # Status emoji
                status_emoji = "🟢" if issue["state"] == "open" else "🔴"

                markdown += f"## {status_emoji} #{issue['number']}: {issue['title']}\n"
                markdown += f"**Repository:** [{issue['repository_url'].split('/')[-2]}/{issue['repository_url'].split('/')[-1]}]({issue['html_url']})\n"
                markdown += f"**State:** {issue['state']}\n"
                markdown += f"**Author:** @{issue['user']['login']}\n"
                markdown += f"**Created:** {_format_timestamp(issue['created_at'])}\n"
                markdown += f"**Updated:** {_format_timestamp(issue['updated_at'])}\n"

                if issue.get("closed_at"):
                    markdown += f"**Closed:** {_format_timestamp(issue['closed_at'])}\n"

                if issue.get("labels"):
                    labels = ", ".join(
                        [f"`{label['name']}`" for label in issue["labels"][:5]]
                    )
                    markdown += f"**Labels:** {labels}\n"

                if issue.get("assignees"):
                    assignees = ", ".join(
                        [f"@{a['login']}" for a in issue["assignees"]]
                    )
                    markdown += f"**Assignees:** {assignees}\n"

                markdown += f"**Comments:** {issue['comments']}\n"
                markdown += f"**URL:** {issue['html_url']}\n\n"

                if issue.get("body"):
                    body_preview = (
                        issue["body"][:300] + "..."
                        if len(issue["body"]) > 300
                        else issue["body"]
                    )
                    markdown += f"**Description:** {body_preview}\n\n"

                markdown += "---\n\n"

        return _truncate_response(markdown, total_count)

    except Exception as e:
        return _handle_api_error(e)
