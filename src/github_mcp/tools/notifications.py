"""Notifications tools for GitHub MCP Server."""

import json
from typing import Dict, Any, List, Union, cast

from ..models.inputs import (
    GetThreadInput,
    GetThreadSubscriptionInput,
    ListNotificationsInput,
    MarkNotificationsReadInput,
    MarkThreadReadInput,
    SetThreadSubscriptionInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response
from ..utils.compact_format import format_response


async def github_list_notifications(params: ListNotificationsInput) -> str:
    """
    List notifications for the authenticated user.

    Retrieves all notifications for the authenticated user. Requires
    User Access Token (UAT) - installation tokens won't work.

    Args:
        params (ListNotificationsInput): Validated input parameters containing:
            - all (bool): Show all notifications (including read)
            - participating (bool): Show only participating notifications
            - since (Optional[str]): Filter by update time
            - before (Optional[str]): Filter by update time
            - per_page (int): Results per page
            - page (int): Page number
            - token (Optional[str]): GitHub token (required - UAT only)
            - response_format (ResponseFormat): Output format

    Returns:
        str: List of notifications

    Examples:
        - Use when: "Show me my notifications"
        - Use when: "List unread notifications"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub User Access Token (UAT) required for notifications. Installation tokens won't work.",
                "success": False,
            },
            indent=2,
        )

    try:
        params_dict: Dict[str, Any] = {"per_page": params.limit, "page": params.page}
        if params.all:
            params_dict["all"] = "true"
        if params.participating:
            params_dict["participating"] = "true"
        if params.since:
            params_dict["since"] = params.since
        if params.before:
            params_dict["before"] = params.before

        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            "notifications", token=auth_token, params=params_dict
        )

        # GitHub API returns a list for notifications endpoint
        # Type assertion needed because _make_github_request is typed as Dict but can return List
        notifications_list: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(notifications_list, indent=2)
            return _truncate_response(result, len(notifications_list))

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                notifications_list, ResponseFormat.COMPACT.value, "notification"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(notifications_list))

        markdown = "# Notifications\n\n"
        markdown += f"**Total Notifications:** {len(notifications_list)}\n"
        markdown += f"**Page:** {params.page} | **Showing:** {len(notifications_list)} notifications\n\n"

        if not notifications_list:
            markdown += "No notifications found.\n"
        else:
            for notification in notifications_list:
                unread_emoji = "🔔" if notification.get("unread", False) else "✓"
                markdown += f"## {unread_emoji} {notification.get('subject', {}).get('title', 'N/A')}\n"
                markdown += f"- **Type:** {notification.get('subject', {}).get('type', 'N/A')}\n"
                markdown += f"- **Repository:** {notification.get('repository', {}).get('full_name', 'N/A')}\n"
                markdown += f"- **Unread:** {notification.get('unread', False)}\n"
                markdown += (
                    f"- **Updated:** {_format_timestamp(notification['updated_at'])}\n"
                )
                markdown += f"- **URL:** {notification.get('url', 'N/A')}\n\n"

        return _truncate_response(markdown, len(notifications_list))

    except Exception as e:
        return _handle_api_error(e)


async def github_get_thread(params: GetThreadInput) -> str:
    """
    Get details about a notification thread.

    Retrieves complete thread information including subject, reason,
    and repository details. Requires User Access Token (UAT).

    Args:
        params (GetThreadInput): Validated input parameters containing:
            - thread_id (str): Thread ID
            - token (Optional[str]): GitHub token (required - UAT only)
            - response_format (ResponseFormat): Output format

    Returns:
        str: Detailed thread information

    Examples:
        - Use when: "Show me details about notification thread 123"
        - Use when: "Get information about thread 456"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub User Access Token (UAT) required for notifications. Installation tokens won't work.",
                "success": False,
            },
            indent=2,
        )

    try:
        data = await _make_github_request(
            f"notifications/threads/{params.thread_id}", token=auth_token
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(data, ResponseFormat.COMPACT.value, "thread")
            return json.dumps(compact_data, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        markdown = "# Notification Thread\n\n"
        markdown += f"- **ID:** {data.get('id', 'N/A')}\n"
        markdown += f"- **Unread:** {data.get('unread', False)}\n"
        markdown += f"- **Reason:** {data.get('reason', 'N/A')}\n"
        markdown += (
            f"- **Repository:** {data.get('repository', {}).get('full_name', 'N/A')}\n"
        )
        markdown += f"- **Subject:** {data.get('subject', {}).get('title', 'N/A')}\n"
        markdown += f"- **Updated:** {_format_timestamp(data['updated_at'])}\n"
        markdown += f"- **URL:** {data.get('url', 'N/A')}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_mark_thread_read(params: MarkThreadReadInput) -> str:
    """
    Mark a notification thread as read.

    Marks a specific thread as read. Requires User Access Token (UAT).

    Args:
        params (MarkThreadReadInput): Validated input parameters containing:
            - thread_id (str): Thread ID
            - token (Optional[str]): GitHub token (required - UAT only)

    Returns:
        str: Success confirmation

    Examples:
        - Use when: "Mark thread 123 as read"
        - Use when: "Mark notification as read"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub User Access Token (UAT) required for notifications. Installation tokens won't work.",
                "success": False,
            },
            indent=2,
        )

    try:
        await _make_github_request(
            f"notifications/threads/{params.thread_id}",
            method="PATCH",
            token=auth_token,
        )

        return json.dumps(
            {
                "success": True,
                "message": f"Thread {params.thread_id} marked as read",
                "thread_id": params.thread_id,
            },
            indent=2,
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_mark_notifications_read(params: MarkNotificationsReadInput) -> str:
    """
    Mark notifications as read.

    Marks all notifications or notifications up to a specific time as read.
    Requires User Access Token (UAT).

    Args:
        params (MarkNotificationsReadInput): Validated input parameters containing:
            - last_read_at (Optional[str]): Timestamp to mark as read up to
            - read (bool): Mark as read (default: true)
            - token (Optional[str]): GitHub token (required - UAT only)

    Returns:
        str: Success confirmation

    Examples:
        - Use when: "Mark all notifications as read"
        - Use when: "Mark notifications up to yesterday as read"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub User Access Token (UAT) required for notifications. Installation tokens won't work.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload: Dict[str, Any] = {}
        if params.last_read_at:
            payload["last_read_at"] = params.last_read_at
        if params.read is not None:
            payload["read"] = params.read

        await _make_github_request(
            "notifications", method="PUT", token=auth_token, json=payload
        )

        return json.dumps(
            {"success": True, "message": "Notifications marked as read"}, indent=2
        )

    except Exception as e:
        return _handle_api_error(e)


async def github_get_thread_subscription(params: GetThreadSubscriptionInput) -> str:
    """
    Get subscription status for a notification thread.

    Checks whether the authenticated user is subscribed to a thread.
    Requires User Access Token (UAT).

    Args:
        params (GetThreadSubscriptionInput): Validated input parameters containing:
            - thread_id (str): Thread ID
            - token (Optional[str]): GitHub token (required - UAT only)
            - response_format (ResponseFormat): Output format

    Returns:
        str: Subscription status

    Examples:
        - Use when: "Check if I'm subscribed to thread 123"
        - Use when: "Get subscription status for this thread"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub User Access Token (UAT) required for notifications. Installation tokens won't work.",
                "success": False,
            },
            indent=2,
        )

    try:
        data = await _make_github_request(
            f"notifications/threads/{params.thread_id}/subscription", token=auth_token
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact = {
                "subscribed": data.get("subscribed", False),
                "ignored": data.get("ignored", False),
            }
            return json.dumps(compact, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        markdown = "# Thread Subscription Status\n\n"
        markdown += f"- **Subscribed:** {data.get('subscribed', False)}\n"
        markdown += f"- **Ignored:** {data.get('ignored', False)}\n"
        markdown += f"- **Reason:** {data.get('reason', 'N/A')}\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at']) if data.get('created_at') else 'N/A'}\n"

        return markdown

    except Exception as e:
        return _handle_api_error(e)


async def github_set_thread_subscription(params: SetThreadSubscriptionInput) -> str:
    """
    Set subscription status for a notification thread.

    Subscribes or unsubscribes from a thread, or marks it as ignored.
    Requires User Access Token (UAT).

    Args:
        params (SetThreadSubscriptionInput): Validated input parameters containing:
            - thread_id (str): Thread ID
            - ignored (bool): Whether to ignore the thread
            - token (Optional[str]): GitHub token (required - UAT only)

    Returns:
        str: Updated subscription status

    Examples:
        - Use when: "Ignore thread 123"
        - Use when: "Unsubscribe from this notification thread"
    """
    auth_token = await _get_auth_token_fallback(params.token)
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub User Access Token (UAT) required for notifications. Installation tokens won't work.",
                "success": False,
            },
            indent=2,
        )

    try:
        payload = {"ignored": params.ignored}

        data = await _make_github_request(
            f"notifications/threads/{params.thread_id}/subscription",
            method="PUT",
            token=auth_token,
            json=payload,
        )

        return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# Collaborators & Teams Tools (Phase 2 - Batch 6)
# ============================================================================
