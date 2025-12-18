"""Pull Requests tools for GitHub MCP Server."""

from typing import Dict, Any, List, Union, cast
import json
import httpx

from ..utils.graphql_client import GraphQLClient
from ..models.inputs import (
    ClosePullRequestInput,
    CreatePRReviewInput,
    CreatePullRequestInput,
    GetPullRequestDetailsInput,
    GraphQLPROverviewInput,
    ListPullRequestsInput,
    MergePullRequestInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response
from ..utils.compact_format import format_response


async def github_list_pull_requests(params: ListPullRequestsInput) -> str:
    """
    List pull requests from a GitHub repository.

    Retrieves pull requests with state filtering and pagination support.
    Shows PR metadata including author, status, and review information.

    Args:
        params (ListPullRequestsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - state (PullRequestState): Filter by 'open', 'closed', or 'all'
            - limit (int): Maximum results (1-100, default 20)
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of pull requests with details and pagination info

    Examples:
        - Use when: "Show open PRs in react repository"
        - Use when: "List all merged pull requests"
        - Use when: "Get recent PRs for microsoft/typescript"

    Error Handling:
        - Returns error if repository not accessible
        - Handles pagination for large result sets
        - Provides clear status for each PR
    """
    try:
        params_dict = {
            "state": params.state.value,
            "per_page": params.limit,
            "page": params.page,
        }

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls",
            token=params.token,
            params=params_dict,
        )

        # GitHub API returns a list for pulls endpoint; tests may mock dict with "items"
        if isinstance(data, list):
            prs_list: List[Dict[str, Any]] = cast(List[Dict[str, Any]], data)
        elif isinstance(data, dict):
            prs_list = cast(List[Dict[str, Any]], data.get("items", []))
        else:
            prs_list = []

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(prs_list, ResponseFormat.COMPACT.value, "pr")
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(prs_list))

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(prs_list, indent=2)
            return _truncate_response(result, len(prs_list))

        # Markdown format
        markdown = f"# Pull Requests for {params.owner}/{params.repo}\n\n"
        markdown += f"**State:** {params.state.value} | **Page:** {params.page} | **Showing:** {len(prs_list)} PRs\n\n"

        if not prs_list:
            markdown += f"No {params.state.value} pull requests found.\n"
        else:
            for pr in prs_list:
                markdown += f"## #{pr['number']}: {pr['title']}\n"
                markdown += f"- **State:** {pr['state']}\n"
                markdown += f"- **Author:** @{pr['user']['login']}\n"
                markdown += f"- **Created:** {_format_timestamp(pr['created_at'])}\n"
                markdown += f"- **Updated:** {_format_timestamp(pr['updated_at'])}\n"
                markdown += f"- **Base:** `{pr['base']['ref']}` ← **Head:** `{pr['head']['ref']}`\n"

                if pr.get("draft"):
                    markdown += "- **Draft:** Yes\n"

                if pr.get("merged"):
                    markdown += "- **Merged:** Yes\n"
                    if pr.get("merged_at"):
                        markdown += (
                            f"- **Merged At:** {_format_timestamp(pr['merged_at'])}\n"
                        )

                markdown += f"- **URL:** {pr['html_url']}\n\n"

                if pr.get("body"):
                    body_preview = (
                        pr["body"][:200] + "..."
                        if len(pr["body"]) > 200
                        else pr["body"]
                    )
                    markdown += f"**Preview:** {body_preview}\n\n"

                markdown += "---\n\n"

        return _truncate_response(markdown, len(prs_list))

    except Exception as e:
        return _handle_api_error(e)


async def github_create_pull_request(params: CreatePullRequestInput) -> str:
    """
    Create a new pull request in a GitHub repository.

    Creates a pull request from a source branch to a target branch with optional
    draft status, description, and maintainer modification permissions.

    Args:
        params (CreatePullRequestInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - title (str): Pull request title (required)
            - head (str): Source branch name (required)
            - base (str): Target branch name (required)
            - body (Optional[str]): PR description in Markdown
            - draft (bool): Create as draft PR (default: False)
            - maintainer_can_modify (bool): Allow maintainer modifications (default: True)
            - token (Optional[str]): GitHub token (optional - uses GITHUB_TOKEN env var if not provided)

    Returns:
        str: Created pull request details including number and URL

    Examples:
        - Use when: "Create a PR from feature-branch to main"
        - Use when: "Open a draft PR for review"
        - Use when: "Create a pull request for this feature"

    Error Handling:
        - Returns error if branches don't exist
        - Returns error if authentication fails
        - Returns error if insufficient permissions
        - Validates branch names and repository access
    """

    # Get token (try param, then GitHub App, then PAT)
    auth_token = await _get_auth_token_fallback(params.token)

    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating pull requests. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload = {
            "title": params.title,
            "head": params.head,
            "base": params.base,
            "draft": params.draft,
            "maintainer_can_modify": params.maintainer_can_modify,
        }

        if params.body:
            payload["body"] = params.body

        data: Dict[str, Any] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls",
            method="POST",
            token=auth_token,
            json=payload,
        )

        # Return useful data with number, url, title, state, head, base
        return json.dumps(
            {
                "success": True,
                "number": data.get("number"),
                "url": data.get("html_url"),
                "title": data.get("title"),
                "state": data.get("state"),
                "head": data.get("head", {}).get("ref"),
                "base": data.get("base", {}).get("ref"),
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
        else:
            error_info["message"] = _handle_api_error(e)

        return json.dumps(error_info, indent=2)


async def github_get_pr_details(params: GetPullRequestDetailsInput) -> str:
    """
    Get comprehensive details about a specific pull request.

    Retrieves detailed information including reviews, commits, status checks,
    and optionally changed files. Essential for PR review workflows.

    Args:
        params (GetPullRequestDetailsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pull_number (int): Pull request number
            - include_reviews (bool): Include review information (default: True)
            - include_commits (bool): Include commit information (default: True)
            - include_files (bool): Include changed files (default: False)
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Comprehensive PR details with reviews, commits, and status

    Examples:
        - Use when: "Show me details for PR #42"
        - Use when: "What's blocking PR #123?"
        - Use when: "Get review status for this pull request"
        - Use when: "Show me all commits in PR #456"

    Error Handling:
        - Returns error if PR not found (404)
        - Handles private repository access requirements
        - Provides clear status for merge conflicts and checks
    """
    try:
        # Get PR details
        pr_data: Dict[str, Any] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}",
            token=params.token,
        )

        if params.response_format == ResponseFormat.JSON:
            result: Dict[str, Any] = {"pr": pr_data}

            # Add additional data if requested
            if params.include_reviews:
                try:
                    reviews = await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/reviews",
                        token=params.token,
                    )
                    result["reviews"] = reviews
                except Exception:
                    result["reviews"] = "Error fetching reviews"

            if params.include_commits:
                try:
                    commits = await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/commits",
                        token=params.token,
                    )
                    result["commits"] = commits
                except Exception:
                    result["commits"] = "Error fetching commits"

            if params.include_files:
                try:
                    files = await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/files",
                        token=params.token,
                    )
                    result["files"] = files
                except Exception:
                    result["files"] = "Error fetching files"

            return json.dumps(result, indent=2)

        if params.response_format == ResponseFormat.COMPACT:
            compact_pr = format_response(pr_data, ResponseFormat.COMPACT.value, "pr")
            return json.dumps({"pr": compact_pr}, indent=2)

        # Markdown format
        status_emoji = "🔀" if not pr_data["draft"] else "📝"
        merge_emoji = (
            "✅"
            if pr_data.get("mergeable")
            else "❌"
            if pr_data.get("mergeable") is False
            else "⏳"
        )

        markdown = f"""# {status_emoji} Pull Request #{pr_data["number"]}: {pr_data["title"]}

**State:** {pr_data["state"]} | **Draft:** {"Yes" if pr_data["draft"] else "No"}
**Base:** `{pr_data["base"]["ref"]}` ← **Head:** `{pr_data["head"]["ref"]}`
**Mergeable:** {merge_emoji} {pr_data.get("mergeable", "Unknown")}
**Created:** {_format_timestamp(pr_data["created_at"])}
**Updated:** {_format_timestamp(pr_data["updated_at"])}
**Author:** @{pr_data["user"]["login"]}
**URL:** {pr_data["html_url"]}

"""

        if pr_data.get("body"):
            body_preview = (
                pr_data["body"][:300] + "..."
                if len(pr_data["body"]) > 300
                else pr_data["body"]
            )
            markdown += f"## Description\n\n{body_preview}\n\n"

        # Additions/Deletions
        markdown += "## Changes\n"
        markdown += f"- **Additions:** +{pr_data['additions']:,} lines\n"
        markdown += f"- **Deletions:** -{pr_data['deletions']:,} lines\n"
        markdown += f"- **Changed Files:** {pr_data['changed_files']:,}\n\n"

        # Reviews section
        if params.include_reviews:
            try:
                reviews = await _make_github_request(
                    f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/reviews",
                    token=params.token,
                )

                markdown += f"## Reviews ({len(reviews)})\n\n"

                if not reviews:
                    markdown += "No reviews yet.\n\n"
                else:
                    for review in reviews:
                        review_emoji = (
                            "✅"
                            if review["state"] == "APPROVED"
                            else "❌"
                            if review["state"] == "CHANGES_REQUESTED"
                            else "💬"
                        )
                        markdown += f"- {review_emoji} **@{review['user']['login']}** - {review['state']}\n"
                        if review.get("body"):
                            body_preview = (
                                review["body"][:100] + "..."
                                if len(review["body"]) > 100
                                else review["body"]
                            )
                            markdown += f"  _{body_preview}_\n"
                        markdown += (
                            f"  _{_format_timestamp(review['submitted_at'])}_\n\n"
                        )
            except Exception:
                markdown += "## Reviews\n\nError fetching reviews.\n\n"

        # Commits section
        if params.include_commits:
            try:
                commits = await _make_github_request(
                    f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/commits",
                    token=params.token,
                )

                markdown += f"## Commits ({len(commits)})\n\n"

                for commit in commits[:10]:  # Limit to first 10 commits
                    commit_msg = commit["commit"]["message"].split("\n")[
                        0
                    ]  # First line only
                    markdown += f"- **{commit['sha'][:8]}** - {commit_msg}\n"
                    markdown += f"  _by @{commit['author']['login']} on {_format_timestamp(commit['commit']['author']['date'])}_\n"

                if len(commits) > 10:
                    markdown += f"\n... and {len(commits) - 10} more commits\n"

                markdown += "\n"
            except Exception:
                markdown += "## Commits\n\nError fetching commits.\n\n"

        # Files section (optional, can be large)
        if params.include_files:
            try:
                files = await _make_github_request(
                    f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/files",
                    token=params.token,
                )

                markdown += f"## Changed Files ({len(files)})\n\n"

                for file in files[:20]:  # Limit to first 20 files
                    status_icon = (
                        "📝"
                        if file["status"] == "modified"
                        else "➕"
                        if file["status"] == "added"
                        else "➖"
                        if file["status"] == "removed"
                        else "🔄"
                    )
                    markdown += f"- {status_icon} `{file['filename']}` (+{file['additions']}, -{file['deletions']})\n"

                if len(files) > 20:
                    markdown += f"\n... and {len(files) - 20} more files\n"

                markdown += "\n"
            except Exception:
                markdown += "## Changed Files\n\nError fetching files.\n\n"

        return _truncate_response(markdown)

    except Exception as e:
        return _handle_api_error(e)


async def github_get_pr_overview_graphql(params: GraphQLPROverviewInput) -> str:
    """
    Fetch PR title, author, review states, commits count, and files changed in one GraphQL query.
    """
    try:
        token = await _get_auth_token_fallback(params.token)
        if not token:
            return "Error: Authentication required for GraphQL. Set GITHUB_TOKEN or configure GitHub App authentication."

        gql = GraphQLClient()
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              number
              title
              author { login }
              state
              additions
              deletions
              changedFiles
              reviews(last: 20) { nodes { author { login } state submittedAt } }
              commits(last: 1) { totalCount }
              files(first: 20) { totalCount nodes { path additions deletions } }
              url
              createdAt
              merged
            }
          }
        }
        """
        variables = {
            "owner": params.owner,
            "repo": params.repo,
            "number": params.pull_number,
        }
        data = await gql.query(token, query, variables)
        pr = (((data or {}).get("data") or {}).get("repository") or {}).get(
            "pullRequest"
        )
        if not pr:
            return "Error: PR not found."

        if params.response_format == ResponseFormat.JSON:
            return _truncate_response(json.dumps(pr, indent=2))

        if params.response_format == ResponseFormat.COMPACT:
            compact_pr = format_response(pr, ResponseFormat.COMPACT.value, "pr")
            return _truncate_response(json.dumps(compact_pr, indent=2))

        md = [
            f"# PR #{pr['number']}: {pr['title']}",
            f"Author: @{pr['author']['login']} | State: {pr['state']}",
            f"Additions: +{pr['additions']} | Deletions: -{pr['deletions']} | Files: {pr['changedFiles']}",
            f"Commits: {pr['commits']['totalCount']} | URL: {pr['url']}",
            "",
            "## Recent Reviews",
        ]
        reviews = (pr.get("reviews") or {}).get("nodes") or []
        if not reviews:
            md.append("(no reviews)")
        else:
            for rv in reviews:
                md.append(
                    f"- {rv['state']} by @{rv['author']['login']} at {rv.get('submittedAt', '')} "
                )
        files = (pr.get("files") or {}).get("nodes") or []
        if files:
            md.append("\n## Changed Files (first 20)")
            for f in files:
                md.append(f"- {f['path']} (+{f['additions']}, -{f['deletions']})")
        return _truncate_response("\n".join(md))
    except Exception as e:
        return _handle_api_error(e)


async def github_merge_pull_request(params: MergePullRequestInput) -> str:
    """
    Merge a pull request using the specified merge method.

    This tool merges an open pull request into its base branch. Supports
    merge commits, squash merging, and rebase merging.

    Args:
        params (MergePullRequestInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pull_number (int): Pull request number
            - merge_method (Optional[str]): 'merge', 'squash', or 'rebase' (default: squash)
            - commit_title (Optional[str]): Custom commit title
            - commit_message (Optional[str]): Custom commit message
            - sha (Optional[str]): SHA of head commit that must match (prevents race conditions)
            - token (Optional[str]): GitHub token

    Returns:
        str: Merge confirmation with commit details

    Examples:
        - Use when: "Merge PR #8"
        - Use when: "Squash and merge this pull request"
        - Use when: "Merge the feature branch"

    Error Handling:
        - Returns error if PR not found (404)
        - Returns error if not mergeable (405)
        - Returns error if insufficient permissions (403)
        - Returns error if conflicts exist (409)
    """
    # Get token (try param, then GitHub App, then PAT)
    token = await _get_auth_token_fallback(params.token)

    # Ensure we have a valid token before proceeding
    if not token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for merging pull requests. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # Build merge data
        merge_data = {"merge_method": params.merge_method or "squash"}

        if params.commit_title:
            merge_data["commit_title"] = params.commit_title
        if params.commit_message:
            merge_data["commit_message"] = params.commit_message
        if params.sha:
            merge_data["sha"] = params.sha

        # Merge the pull request
        result = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/merge",
            method="PUT",
            token=token,
            json=merge_data,
        )

        # Return the FULL GitHub API response as JSON
        return json.dumps(result, indent=2)

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
        else:
            error_info["message"] = str(e)

        return json.dumps(error_info, indent=2)


async def github_close_pull_request(params: ClosePullRequestInput) -> str:
    """
    Close a pull request without merging.

    This tool closes a PR and optionally adds a closing comment explaining why.
    Useful for stale PRs, superseded PRs, or PRs that won't be merged.

    Args:
        params (ClosePullRequestInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pull_number (int): Pull request number
            - comment (Optional[str]): Closing comment/explanation
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation with PR details

    Examples:
        - Use when: "Close PR #11"
        - Use when: "Close stale pull request"
        - Use when: "Close superseded PR with comment"

    Error Handling:
        - Returns error if PR not found (404)
        - Returns error if authentication fails (401/403)
        - Returns error if PR already closed (422)
    """

    # Get token (try param, then GitHub App, then PAT)
    token = await _get_auth_token_fallback(params.token)
    if not token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for closing pull requests. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # Add comment if provided
        if params.comment:
            await _make_github_request(
                f"repos/{params.owner}/{params.repo}/issues/{params.pull_number}/comments",
                method="POST",
                token=token,
                json={"body": params.comment},
            )

        # Close the PR
        pr = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}",
            method="PATCH",
            token=token,
            json={"state": "closed"},
        )

        # Return the FULL GitHub API response as JSON
        return json.dumps(pr, indent=2)

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
        else:
            error_info["message"] = str(e)

        return json.dumps(error_info, indent=2)


async def github_create_pr_review(params: CreatePRReviewInput) -> str:
    """
    Create a review on a pull request with optional line-specific comments.

    This tool allows you to review pull requests by:
    - Adding general review comments
    - Adding line-specific comments to code
    - Approving the PR
    - Requesting changes to the PR

    Args:
        params (CreatePRReviewInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pull_number (int): Pull request number
            - event (str): 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'
            - body (Optional[str]): General review comment
            - comments (Optional[List[PRReviewComment]]): Line-specific comments
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation with review details

    Examples:
        - Use when: "Approve PR #42"
        - Use when: "Request changes on line 15 of main.py"
        - Use when: "Add review comment suggesting improvements"

    Error Handling:
        - Returns error if PR not found (404)
        - Returns error if already reviewed (422)
        - Returns error if insufficient permissions (403)
    """
    try:
        token = await _get_auth_token_fallback(params.token)
        if not token:
            return json.dumps(
                {
                    "error": "Authentication required",
                    "message": "GitHub token required for creating PR reviews. Set GITHUB_TOKEN or configure GitHub App authentication.",
                    "success": False,
                },
                indent=2,
            )

        review_data: Dict[str, Any] = {"event": params.event}
        if params.body:
            review_data["body"] = params.body
        if params.comments:
            review_data["comments"] = []
            for comment in params.comments:
                comment_data: Dict[str, Any] = {
                    "path": comment.path,
                    "body": comment.body,
                    "side": comment.side,
                }
                if comment.line:
                    comment_data["line"] = comment.line
                elif comment.position:
                    comment_data["position"] = comment.position
                else:
                    return f"Error: Comment on {comment.path} must specify either 'line' or 'position'"
                review_data["comments"].append(comment_data)

        review = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/pulls/{params.pull_number}/reviews",
            method="POST",
            token=token,
            json=review_data,
        )

        # Return the FULL GitHub API response as JSON
        return json.dumps(review, indent=2)

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
        else:
            error_info["message"] = str(e)

        return json.dumps(error_info, indent=2)


# ============================================================================
# CODE-FIRST EXECUTION TOOL (The Only Tool Exposed to Claude)
# ============================================================================
# This is the ONLY tool Claude Desktop sees, providing 98% token reduction
# All 108 GitHub tools above are accessed via this tool through TypeScript code
# ============================================================================
