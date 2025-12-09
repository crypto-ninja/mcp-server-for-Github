"""Discussions tools for GitHub MCP Server."""

import json
from typing import Dict, Any, List, Union, cast

from ..models.inputs import (
    GetDiscussionInput, ListDiscussionCategoriesInput, ListDiscussionCommentsInput, ListDiscussionsInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response


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
        params_dict = {
            "per_page": params.per_page,
            "page": params.page
        }
        if params.category:
            params_dict["category"] = params.category
        
        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/discussions",
            token=params.token,
            params=params_dict
        )
        
        # GitHub API returns a list for discussions endpoint
        discussions_list: List[Dict[str, Any]] = cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(discussions_list, indent=2)
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
                markdown += f"- **Created:** {_format_timestamp(discussion['created_at'])}\n"
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
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/discussions/{params.discussion_number}",
            token=params.token
        )
        
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
        
        if data.get('body'):
            markdown += f"\n### Content\n{data['body'][:500]}{'...' if len(data.get('body', '')) > 500 else ''}\n"
        
        markdown += f"\n- **URL:** {data['html_url']}\n"
        
        return markdown
        
    except Exception as e:
        return _handle_api_error(e)


async def github_list_discussion_categories(params: ListDiscussionCategoriesInput) -> str:
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
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/discussions/categories",
            token=params.token
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        markdown = f"# Discussion Categories for {params.owner}/{params.repo}\n\n"
        markdown += f"**Total Categories:** {len(data)}\n\n"
        
        if not data:
            markdown += "No discussion categories found.\n"
        else:
            for category in data:
                markdown += f"## {category['name']}\n"
                markdown += f"- **Slug:** {category.get('slug', 'N/A')}\n"
                markdown += f"- **Description:** {category.get('description', 'N/A')}\n"
                markdown += f"- **Emoji:** {category.get('emoji', 'N/A')}\n\n"
        
        return _truncate_response(markdown, len(data))
        
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
        params_dict = {
            "per_page": params.per_page,
            "page": params.page
        }
        
        data = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/discussions/{params.discussion_number}/comments",
            token=params.token,
            params=params_dict
        )
        
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result, len(data))
        
        markdown = f"# Comments for Discussion #{params.discussion_number}\n\n"
        markdown += f"**Total Comments:** {len(data)}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(data)} comments\n\n"
        
        if not data:
            markdown += "No comments found.\n"
        else:
            for comment in data:
                markdown += f"## Comment by {comment['user']['login']}\n"
                markdown += f"- **ID:** {comment['id']}\n"
                markdown += f"- **Created:** {_format_timestamp(comment['created_at'])}\n"
                markdown += f"- **Updated:** {_format_timestamp(comment['updated_at'])}\n"
                if comment.get('body'):
                    markdown += f"- **Content:** {comment['body'][:200]}{'...' if len(comment.get('body', '')) > 200 else ''}\n"
                markdown += f"- **URL:** {comment['html_url']}\n\n"
        
        return _truncate_response(markdown, len(data))
        
    except Exception as e:
        return _handle_api_error(e)

# ============================================================================
# Notifications Tools (Phase 2 - Batch 5)
# ============================================================================
