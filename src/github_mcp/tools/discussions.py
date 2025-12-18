"""Discussions tools for GitHub MCP Server."""

import json
from typing import Dict, Any, List, Union, cast

from ..utils.graphql_client import GraphQLClient

from ..models.inputs import (
    AddDiscussionCommentInput,
    CreateDiscussionInput,
    GetDiscussionInput,
    ListDiscussionCategoriesInput,
    ListDiscussionCommentsInput,
    ListDiscussionsInput,
    UpdateDiscussionInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response
from ..utils.compact_format import format_response


async def github_list_discussions(params: ListDiscussionsInput) -> str:
    """
    List discussions for a repository.

    Retrieves all discussions in a repository. Supports filtering by category.
    Discussions are community conversations separate from issues.

    Args:
        params (ListDiscussionsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - category (Optional[str]): Filter by category slug
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of discussions with details

    Examples:
        - Use when: "Show me all discussions"
        - Use when: "List discussions in the Q&A category"
    """
    try:
        params_dict: Dict[str, Any] = {"per_page": params.limit, "page": params.page}
        if params.category:
            params_dict["category"] = params.category

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/discussions",
            token=params.token,
            params=params_dict,
        )

        # GitHub API returns a list for discussions endpoint
        discussions_list: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(discussions_list, indent=2)
            return _truncate_response(result, len(discussions_list))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                discussions_list, ResponseFormat.COMPACT.value, "discussion"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(discussions_list))

        markdown = f"# Discussions for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Discussions:** {len(discussions_list)}\n\n"

        if not discussions_list:
            markdown += "No discussions found.\n"
        else:
            for discussion in discussions_list:
                markdown += f"## {discussion['title']}\n"
                markdown += f"- **Number:** {discussion['number']}\n"
                markdown += f"- **Category:** {discussion.get('category', {}).get('name', 'N/A')}\n"
                markdown += f"- **Author:** {discussion['user']['login']}\n"
                markdown += f"- **State:** {discussion.get('state', 'N/A')}\n"
                markdown += (
                    f"- **Created:** {_format_timestamp(discussion['created_at'])}\n"
                )
                markdown += f"- **URL:** {discussion['html_url']}\n\n"

        return _truncate_response(markdown, len(discussions_list))

    except Exception as e:
        return _handle_api_error(e)


async def github_get_discussion(params: GetDiscussionInput) -> str:
    """
    Get details about a specific discussion.

    Retrieves complete discussion information including title, body,
    category, author, and comments count.

    Args:
        params (GetDiscussionInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - discussion_number (int): Discussion number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed discussion information

    Examples:
        - Use when: "Show me details about discussion 123"
        - Use when: "Get information about discussion 456"
    """
    try:
        data: Dict[str, Any] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/discussions/{params.discussion_number}",
            token=params.token,
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "discussion"
            )
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        markdown = f"# Discussion: {data['title']}\n\n"
        markdown += f"- **Number:** {data['number']}\n"
        markdown += f"- **Category:** {data.get('category', {}).get('name', 'N/A')}\n"
        markdown += f"- **Author:** {data['user']['login']}\n"
        markdown += f"- **State:** {data.get('state', 'N/A')}\n"
        markdown += f"- **Comments:** {data.get('comments', 0)}\n"
        markdown += f"- **Upvotes:** {data.get('upvote_count', 0)}\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **Updated:** {_format_timestamp(data['updated_at'])}\n"

        if data.get("body"):
            markdown += f"\n### Content\n{data['body'][:500]}{'...' if len(data.get('body', '')) > 500 else ''}\n"

        markdown += f"\n- **URL:** {data['html_url']}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_list_discussion_categories(
    params: ListDiscussionCategoriesInput,
) -> str:
    """
    List discussion categories for a repository.

    Retrieves all available discussion categories (e.g., "General", "Q&A",
    "Ideas", "Announcements") configured for the repository.

    Args:
        params (ListDiscussionCategoriesInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of discussion categories

    Examples:
        - Use when: "Show me all discussion categories"
        - Use when: "List available discussion types"
    """
    try:
        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/discussions/categories",
            token=params.token,
        )

        # GitHub API returns a list for categories endpoint
        categories_list: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(categories_list, indent=2)

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                categories_list, ResponseFormat.COMPACT.value, "discussion"
            )
            return json.dumps(compact_data, indent=2)

        markdown = f"# Discussion Categories for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Categories:** {len(categories_list)}\n\n"

        if not categories_list:
            markdown += "No discussion categories found.\n"
        else:
            for category in categories_list:
                markdown += f"## {category['name']}\n"
                markdown += f"- **Slug:** {category.get('slug', 'N/A')}\n"
                markdown += f"- **Description:** {category.get('description', 'N/A')}\n"
                markdown += f"- **Emoji:** {category.get('emoji', 'N/A')}\n\n"

        return _truncate_response(markdown, len(categories_list))

    except Exception as e:
        return _handle_api_error(e)


async def github_list_discussion_comments(params: ListDiscussionCommentsInput) -> str:
    """
    List comments in a discussion.

    Retrieves all comments for a specific discussion, including replies
    and reactions.

    Args:
        params (ListDiscussionCommentsInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - discussion_number (int): Discussion number
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of discussion comments

    Examples:
        - Use when: "Show me all comments in discussion 123"
        - Use when: "List replies to this discussion"
    """
    try:
        params_dict = {"per_page": params.limit, "page": params.page}

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/discussions/{params.discussion_number}/comments",
            token=params.token,
            params=params_dict,
        )

        # GitHub API returns a list for comments endpoint
        comments_list: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                comments_list, ResponseFormat.COMPACT.value, "comment"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(comments_list))

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(comments_list, indent=2)
            return _truncate_response(result, len(comments_list))

        markdown = f"# Comments for Discussion #{params.discussion_number}\n\n"
        markdown += f"**Total Comments:** {len(comments_list)}\n"
        markdown += (
            f"**Page:** {params.page} | **Showing:** {len(comments_list)} comments\n\n"
        )

        if not comments_list:
            markdown += "No comments found.\n"
        else:
            for comment in comments_list:
                markdown += f"## Comment by {comment['user']['login']}\n"
                markdown += f"- **ID:** {comment['id']}\n"
                markdown += (
                    f"- **Created:** {_format_timestamp(comment['created_at'])}\n"
                )
                markdown += (
                    f"- **Updated:** {_format_timestamp(comment['updated_at'])}\n"
                )
                if comment.get("body"):
                    markdown += f"- **Content:** {comment['body'][:200]}{'...' if len(comment.get('body', '')) > 200 else ''}\n"
                markdown += f"- **URL:** {comment['html_url']}\n\n"

        return _truncate_response(markdown, len(comments_list))

    except Exception as e:
        return _handle_api_error(e)


async def _get_repository_id(token: str, owner: str, repo: str) -> str:
    """Get repository node_id for GraphQL mutations."""
    gql = GraphQLClient()
    query = """
    query($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) {
            id
        }
    }
    """
    result = await gql.query(token, query, {"owner": owner, "repo": repo})
    if "errors" in result:
        raise Exception(f"GraphQL error: {result['errors']}")
    return result["data"]["repository"]["id"]


async def _get_discussion_id(token: str, owner: str, repo: str, number: int) -> str:
    """Get discussion node_id for GraphQL mutations."""
    gql = GraphQLClient()
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
        repository(owner: $owner, name: $repo) {
            discussion(number: $number) {
                id
            }
        }
    }
    """
    result = await gql.query(
        token, query, {"owner": owner, "repo": repo, "number": number}
    )
    if "errors" in result:
        raise Exception(f"GraphQL error: {result['errors']}")
    discussion = result["data"]["repository"].get("discussion")
    if not discussion:
        raise Exception(f"Discussion #{number} not found")
    return discussion["id"]


async def github_create_discussion(params: CreateDiscussionInput) -> str:
    """
    Create a new discussion in a repository using GraphQL.

    This tool creates a new discussion in the specified category. Requires
    the category node_id which can be obtained from github_list_discussion_categories.

    Args:
        params (CreateDiscussionInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - category_id (str): Discussion category node_id
            - title (str): Discussion title
            - body (str): Discussion body (markdown)
            - token (Optional[str]): GitHub token

    Returns:
        str: Created discussion details with number and URL

    Examples:
        - Use when: "Create a new Q&A discussion"
        - Use when: "Start a discussion in the Announcements category"

    Error Handling:
        - Returns error if category not found
        - Returns error if authentication fails (401/403)
        - Returns error if repository doesn't have discussions enabled
    """
    token = await _get_auth_token_fallback(params.token)
    if not token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating discussions. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # Get repository ID
        repo_id = await _get_repository_id(token, params.owner, params.repo)

        # Create discussion mutation
        gql = GraphQLClient()
        mutation = """
        mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
            createDiscussion(input: {
                repositoryId: $repositoryId
                categoryId: $categoryId
                title: $title
                body: $body
            }) {
                discussion {
                    id
                    number
                    title
                    url
                    body
                }
            }
        }
        """

        variables = {
            "repositoryId": repo_id,
            "categoryId": params.category_id,
            "title": params.title,
            "body": params.body,
        }

        result = await gql.query(token, mutation, variables)

        if "errors" in result:
            error_msg = result["errors"][0].get("message", "Unknown GraphQL error")
            return json.dumps(
                {"error": "GraphQL error", "message": error_msg, "success": False},
                indent=2,
            )

        discussion = result["data"]["createDiscussion"]["discussion"]
        return json.dumps(
            {
                "success": True,
                "number": discussion["number"],
                "title": discussion["title"],
                "url": discussion["url"],
                "node_id": discussion["id"],
                "body_preview": (
                    discussion["body"][:200] + "..."
                    if len(discussion.get("body", "")) > 200
                    else discussion.get("body", "")
                ),
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_update_discussion(params: UpdateDiscussionInput) -> str:
    """
    Update an existing discussion using GraphQL.

    This tool modifies discussion information including title, body, and category.
    Only provided fields will be updated - others remain unchanged.

    Args:
        params (UpdateDiscussionInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - discussion_number (int): Discussion number
            - title (Optional[str]): New title
            - body (Optional[str]): New body (markdown)
            - category_id (Optional[str]): Move to different category (node_id)
            - token (Optional[str]): GitHub token

    Returns:
        str: Updated discussion details

    Examples:
        - Use when: "Update discussion 123 title"
        - Use when: "Change discussion 456 category"
        - Use when: "Edit discussion 789 body"

    Error Handling:
        - Returns error if discussion not found (404)
        - Returns error if authentication fails (401/403)
        - Returns error if category not found
    """
    token = await _get_auth_token_fallback(params.token)
    if not token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for updating discussions. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # Get discussion ID
        discussion_id = await _get_discussion_id(
            token, params.owner, params.repo, params.discussion_number
        )

        # Update discussion mutation
        gql = GraphQLClient()
        mutation = """
        mutation($discussionId: ID!, $title: String, $body: String, $categoryId: ID) {
            updateDiscussion(input: {
                discussionId: $discussionId
                title: $title
                body: $body
                categoryId: $categoryId
            }) {
                discussion {
                    id
                    number
                    title
                    url
                    body
                }
            }
        }
        """

        variables: Dict[str, Any] = {"discussionId": discussion_id}
        if params.title is not None:
            variables["title"] = params.title
        if params.body is not None:
            variables["body"] = params.body
        if params.category_id is not None:
            variables["categoryId"] = params.category_id

        result = await gql.query(token, mutation, variables)

        if "errors" in result:
            error_msg = result["errors"][0].get("message", "Unknown GraphQL error")
            return json.dumps(
                {"error": "GraphQL error", "message": error_msg, "success": False},
                indent=2,
            )

        discussion = result["data"]["updateDiscussion"]["discussion"]
        return json.dumps(
            {
                "success": True,
                "number": discussion["number"],
                "title": discussion["title"],
                "url": discussion["url"],
                "body_preview": (
                    discussion["body"][:500] + "..."
                    if len(discussion.get("body", "")) > 500
                    else discussion.get("body", "")
                ),
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_add_discussion_comment(params: AddDiscussionCommentInput) -> str:
    """
    Add a comment to a discussion using GraphQL.

    This tool adds a comment to an existing discussion. Can optionally reply
    to a specific comment by providing the reply_to_id (comment node_id).

    Args:
        params (AddDiscussionCommentInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - discussion_number (int): Discussion number
            - body (str): Comment body (markdown)
            - reply_to_id (Optional[str]): Reply to a specific comment (comment node_id)
            - token (Optional[str]): GitHub token

    Returns:
        str: Created comment details with ID and URL

    Examples:
        - Use when: "Add a comment to discussion 123"
        - Use when: "Reply to comment in discussion 456"
        - Use when: "Post a response to this discussion"

    Error Handling:
        - Returns error if discussion not found (404)
        - Returns error if reply_to_id not found
        - Returns error if authentication fails (401/403)
    """
    token = await _get_auth_token_fallback(params.token)
    if not token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for adding discussion comments. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # Get discussion ID
        discussion_id = await _get_discussion_id(
            token, params.owner, params.repo, params.discussion_number
        )

        # Add comment mutation
        gql = GraphQLClient()
        mutation = """
        mutation($discussionId: ID!, $body: String!, $replyToId: ID) {
            addDiscussionComment(input: {
                discussionId: $discussionId
                body: $body
                replyToId: $replyToId
            }) {
                comment {
                    id
                    body
                    url
                }
            }
        }
        """

        variables: Dict[str, Any] = {
            "discussionId": discussion_id,
            "body": params.body,
        }
        if params.reply_to_id:
            variables["replyToId"] = params.reply_to_id

        result = await gql.query(token, mutation, variables)

        if "errors" in result:
            error_msg = result["errors"][0].get("message", "Unknown GraphQL error")
            return json.dumps(
                {"error": "GraphQL error", "message": error_msg, "success": False},
                indent=2,
            )

        comment = result["data"]["addDiscussionComment"]["comment"]
        return json.dumps(
            {
                "success": True,
                "comment_id": comment["id"],
                "url": comment["url"],
                "body_preview": (
                    comment["body"][:200] + "..."
                    if len(comment.get("body", "")) > 200
                    else comment.get("body", "")
                ),
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# Notifications Tools (Phase 2 - Batch 5)
# ============================================================================
