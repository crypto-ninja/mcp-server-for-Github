"""Releases tools for GitHub MCP Server."""

import json
import httpx
from typing import Dict, Any, List, Union, cast

from ..models.inputs import (
    CreateReleaseInput,
    GetReleaseInput,
    ListReleasesInput,
    UpdateReleaseInput,
    DeleteReleaseInput,
)
from ..models.enums import (
    ResponseFormat,
)
from ..utils.requests import _make_github_request, _get_auth_token_fallback
from ..utils.errors import _handle_api_error
from ..utils.formatting import _format_timestamp, _truncate_response
from ..utils.compact_format import format_response


async def github_list_releases(params: ListReleasesInput) -> str:
    """
    List all releases from a GitHub repository.
    """
    try:
        params_dict = {
            "per_page": params.limit,
            "page": params.page,
        }
        data: Union[Dict[str, Any], List[Dict[str, Any]]] = await _make_github_request(
            f"repos/{params.owner}/{params.repo}/releases",
            token=params.token,
            params=params_dict,
        )
        # GitHub API returns a list for releases endpoint
        releases_list: List[Dict[str, Any]] = (
            cast(List[Dict[str, Any]], data) if isinstance(data, list) else []
        )

        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                releases_list, ResponseFormat.COMPACT.value, "release"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result, len(releases_list))

        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(releases_list, indent=2)
            return _truncate_response(result, len(releases_list))
        markdown = f"# Releases for {params.owner}/{params.repo}\n\n"
        markdown += (
            f"**Page:** {params.page} | **Showing:** {len(releases_list)} releases\n\n"
        )
        if not releases_list:
            markdown += "No releases found.\n"
        else:
            for release in releases_list:
                status = []
                if release.get("draft"):
                    status.append("🚧 Draft")
                if release.get("prerelease"):
                    status.append("🔬 Pre-release")
                status_str = " | ".join(status) if status else "📦 Release"
                markdown += (
                    f"## {release['name'] or release['tag_name']} {status_str}\n\n"
                )
                markdown += f"- **Tag:** `{release['tag_name']}`\n"
                markdown += f"- **Published:** {_format_timestamp(release['published_at']) if release.get('published_at') else 'Draft'}\n"
                markdown += f"- **Author:** {release['author']['login']}\n"
                asset_count = len(release.get("assets", []))
                if asset_count > 0:
                    markdown += f"- **Assets:** {asset_count} file(s)\n"
                if release.get("assets"):
                    total_downloads = sum(
                        asset.get("download_count", 0) for asset in release["assets"]
                    )
                    if total_downloads > 0:
                        markdown += f"- **Downloads:** {total_downloads:,}\n"
                markdown += f"- **URL:** {release['html_url']}\n\n"
                if release.get("body"):
                    body_preview = release["body"][:300]
                    if len(release["body"]) > 300:
                        body_preview += "..."
                    markdown += f"{body_preview}\n\n"
                markdown += "---\n\n"
            if len(releases_list) == (params.limit or 0):
                current_page = params.page or 1
                markdown += f"*Showing page {current_page}. Use `page: {current_page + 1}` to see more.*\n"
        return _truncate_response(markdown, len(releases_list))
    except Exception as e:
        return _handle_api_error(e)


async def github_get_release(params: GetReleaseInput) -> str:
    """
    Get detailed information about a specific release or the latest release.
    """
    try:
        if params.tag == "latest":
            endpoint = f"repos/{params.owner}/{params.repo}/releases/latest"
        else:
            endpoint = f"repos/{params.owner}/{params.repo}/releases/tags/{params.tag}"
        data: Dict[str, Any] = await _make_github_request(endpoint, token=params.token)
        if params.response_format == ResponseFormat.COMPACT:
            compact_data = format_response(
                data, ResponseFormat.COMPACT.value, "release"
            )
            result = json.dumps(compact_data, indent=2)
            return _truncate_response(result)
        if params.response_format == ResponseFormat.JSON:
            result = json.dumps(data, indent=2)
            return _truncate_response(result)
        status = []
        if data.get("draft"):
            status.append("🚧 Draft")
        if data.get("prerelease"):
            status.append("🔬 Pre-release")
        status_str = " | ".join(status) if status else "📦 Release"
        markdown = f"# {data['name'] or data['tag_name']}\n\n"
        markdown += f"**Status:** {status_str}\n\n"
        markdown += "## Release Information\n\n"
        markdown += f"- **Tag:** `{data['tag_name']}`\n"
        markdown += f"- **Published:** {_format_timestamp(data['published_at']) if data.get('published_at') else 'Draft (not published)'}\n"
        markdown += f"- **Created:** {_format_timestamp(data['created_at'])}\n"
        markdown += f"- **Author:** {data['author']['login']}\n"
        markdown += f"- **URL:** {data['html_url']}\n\n"
        if data.get("assets"):
            markdown += "## Assets\n\n"
            total_downloads = 0
            for asset in data["assets"]:
                downloads = asset.get("download_count", 0)
                total_downloads += downloads
                size_mb = asset["size"] / (1024 * 1024)
                markdown += f"- **{asset['name']}**\n"
                markdown += f"  - Size: {size_mb:.2f} MB\n"
                markdown += f"  - Downloads: {downloads:,}\n"
                markdown += f"  - [Download]({asset['browser_download_url']})\n\n"
            markdown += f"**Total Downloads:** {total_downloads:,}\n\n"
        if data.get("body"):
            markdown += "## Release Notes\n\n"
            markdown += data["body"]
            markdown += "\n\n"
        if data.get("target_commitish"):
            markdown += f"**Target:** `{data['target_commitish']}`\n"
        return _truncate_response(markdown)
    except Exception as e:
        return _handle_api_error(e)


async def github_create_release(params: CreateReleaseInput) -> str:
    """
    Create a new release in a GitHub repository.

    This tool creates a GitHub release with a tag, title, and release notes.
    Can create draft or pre-release versions. Requires write access to the repository.

    Note:
        GitHub Apps currently cannot create releases that involve tagging commits,
        because there is no dedicated "releases" permission scope for Apps in
        the GitHub API. For this reason, authentication for this tool will
        automatically fall back to Personal Access Token (PAT) when a GitHub
        App token is not sufficient. This behavior is implemented in
        `get_auth_token()` and `_get_auth_token_fallback()`.

    Args:
        params (CreateReleaseInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - tag_name (str): Git tag for the release (e.g., 'v1.2.0')
            - name (Optional[str]): Release title
            - body (Optional[str]): Release notes in Markdown
            - draft (Optional[bool]): Create as draft
            - prerelease (Optional[bool]): Mark as pre-release
            - target_commitish (Optional[str]): Commit/branch to release from
            - generate_release_notes (bool): Auto-generate release notes from PRs and commits
            - discussion_category_name (Optional[str]): Create linked discussion in category
            - make_latest (Optional[str]): Control 'Latest' badge ('true', 'false', or 'legacy')
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation message with release details and URL

    Examples:
        - Use when: "Create a v1.2.0 release"
        - Use when: "Tag and release the current version"
        - Use when: "Create a pre-release for testing"

    Error Handling:
        - Returns error if tag already exists (422)
        - Returns error if authentication fails (401/403)
        - Returns error if invalid parameters (422)
    """
    # Get token (try param, then GitHub App, then PAT with automatic PAT fallback
    # for operations like releases where GitHub Apps lack permissions)
    # See: auth/github_app.get_auth_token for details.
    auth_token = await _get_auth_token_fallback(params.token)

    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for creating releases. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # Get default branch and commit SHA if target_commitish not provided
        target_commitish = params.target_commitish
        if not target_commitish:
            repo_info = await _make_github_request(
                f"repos/{params.owner}/{params.repo}", token=auth_token
            )
            target_commitish = repo_info["default_branch"]

        # Get commit SHA from target_commitish (could be branch name or SHA)
        # If it's a branch name, get the SHA; if it's already a SHA, use it
        if len(target_commitish) == 40 and all(
            c in "0123456789abcdef" for c in target_commitish.lower()
        ):
            # It's already a SHA
            commit_sha = target_commitish
        else:
            # It's a branch name, get the SHA
            branch_ref = await _make_github_request(
                f"repos/{params.owner}/{params.repo}/git/ref/heads/{target_commitish}",
                token=auth_token,
            )
            commit_sha = branch_ref["object"]["sha"]

        # CRITICAL: Create the Git tag FIRST using Git References API
        # This ensures the tag exists before creating the release
        # Without this, GitHub creates "untagged" releases
        try:
            # Check if tag already exists
            await _make_github_request(
                f"repos/{params.owner}/{params.repo}/git/refs/tags/{params.tag_name}",
                method="GET",
                token=auth_token,
            )
            # Tag exists, that's fine - continue to create release
        except httpx.HTTPStatusError as tag_check_error:
            # Only create tag if it's a 404 (not found) error
            # If it's an auth error (401/403), we should fail immediately
            status_code = tag_check_error.response.status_code

            # If it's an auth error (401/403), re-raise it immediately
            if status_code in (401, 403):
                raise tag_check_error

            # Only create tag if it's a 404 (tag doesn't exist)
            if status_code == 404:
                tag_ref_data = {
                    "ref": f"refs/tags/{params.tag_name}",
                    "sha": commit_sha,
                }
                try:
                    await _make_github_request(
                        f"repos/{params.owner}/{params.repo}/git/refs",
                        method="POST",
                        token=auth_token,
                        json=tag_ref_data,
                    )
                    # Tag created successfully - continue to create release
                except Exception as tag_create_error:
                    # If tag creation fails, raise the error (don't silently continue)
                    raise tag_create_error
            else:
                # Other HTTP errors (500, etc.) - re-raise
                raise tag_check_error
        except Exception as tag_check_error:
            # Non-HTTP errors (network, timeout, etc.) - re-raise
            raise tag_check_error

        # Now create the release (tag already exists)
        endpoint = f"repos/{params.owner}/{params.repo}/releases"
        body_data = {
            "tag_name": params.tag_name,
            "name": params.name or params.tag_name,
            "draft": params.draft or False,
            "prerelease": params.prerelease or False,
            "target_commitish": target_commitish,
        }

        # Add optional fields
        if params.body:
            body_data["body"] = params.body

        # Add new optional parameters
        if params.generate_release_notes:
            body_data["generate_release_notes"] = True

        if params.discussion_category_name:
            body_data["discussion_category_name"] = params.discussion_category_name

        if params.make_latest:
            body_data["make_latest"] = params.make_latest

        # Create the release
        data: Dict[str, Any] = await _make_github_request(
            endpoint, method="POST", token=auth_token, json=body_data
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
        else:
            error_info["message"] = str(e)

        return json.dumps(error_info, indent=2)


async def github_update_release(params: UpdateReleaseInput) -> str:
    """
    Update an existing GitHub release.

    This tool modifies release information including title, notes, and status.
    Only provided fields will be updated - others remain unchanged.

    Args:
        params (UpdateReleaseInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - release_id (Union[int, str]): Release ID (numeric) or tag name (e.g., 'v1.2.0')
            - tag_name (Optional[str]): New tag name
            - name (Optional[str]): New title
            - body (Optional[str]): New release notes
            - draft (Optional[bool]): Draft status
            - prerelease (Optional[bool]): Pre-release status
            - generate_release_notes (Optional[bool]): Auto-generate release notes
            - discussion_category_name (Optional[str]): Create linked discussion
            - make_latest (Optional[str]): Control 'Latest' badge ('true', 'false', 'legacy')
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation message with updated release details

    Examples:
        - Use when: "Update the v1.2.0 release notes"
        - Use when: "Change release from draft to published"
        - Use when: "Add more details to the latest release"

    Error Handling:
        - Returns error if release not found (404)
        - Returns error if authentication fails (401/403)
        - Returns error if invalid parameters (422)
    """
    auth_token = await _get_auth_token_fallback(params.token)

    # Ensure we have a valid token before proceeding
    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for updating releases. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        # Convert release_id to string for processing
        release_id_str = str(params.release_id)

        # First, get the release to find its ID if tag name was provided
        if isinstance(params.release_id, str) and (
            release_id_str.startswith("v") or "." in release_id_str
        ):
            # Looks like a tag name, need to get release ID
            get_endpoint = (
                f"repos/{params.owner}/{params.repo}/releases/tags/{release_id_str}"
            )
            release_data: Dict[str, Any] = await _make_github_request(
                get_endpoint, method="GET", token=auth_token
            )
            release_id = release_data["id"]
        else:
            # It's a numeric ID (int or numeric string)
            release_id = (
                int(params.release_id)
                if isinstance(params.release_id, str)
                else params.release_id
            )

        endpoint = f"repos/{params.owner}/{params.repo}/releases/{release_id}"

        # Build request body with only provided fields
        body_data: Dict[str, Any] = {}

        if params.tag_name is not None:
            body_data["tag_name"] = params.tag_name
        if params.name is not None:
            body_data["name"] = params.name
        if params.body is not None:
            body_data["body"] = params.body
        if params.draft is not None:
            body_data["draft"] = params.draft
        if params.prerelease is not None:
            body_data["prerelease"] = params.prerelease
        if params.generate_release_notes is not None:
            body_data["generate_release_notes"] = params.generate_release_notes
        if params.discussion_category_name is not None:
            body_data["discussion_category_name"] = params.discussion_category_name
        if params.make_latest is not None:
            body_data["make_latest"] = params.make_latest

        # Update the release
        data: Dict[str, Any] = await _make_github_request(
            endpoint, method="PATCH", token=auth_token, json=body_data
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
        else:
            error_info["message"] = str(e)

        return json.dumps(error_info, indent=2)


async def github_delete_release(params: DeleteReleaseInput) -> str:
    """
    Delete a release from a GitHub repository.

    Args:
        params (DeleteReleaseInput): Validated input parameters containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - release_id (int): Release ID to delete
            - token (Optional[str]): GitHub token

    Returns:
        str: Confirmation message

    Examples:
        - Use when: "Delete release 12345"
        - Use when: "Remove the v1.0.0 release"

    Error Handling:
        - Returns error if release not found (404)
        - Returns error if authentication fails (401/403)
    """
    auth_token = await _get_auth_token_fallback(params.token)

    if not auth_token:
        return json.dumps(
            {
                "error": "Authentication required",
                "message": "GitHub token required for deleting releases. Set GITHUB_TOKEN or configure GitHub App authentication.",
                "success": False,
            },
            indent=2,
        )

    try:
        await _make_github_request(
            f"repos/{params.owner}/{params.repo}/releases/{params.release_id}",
            method="DELETE",
            token=auth_token,
        )
        return json.dumps(
            {
                "success": True,
                "message": f"Release {params.release_id} deleted successfully",
            },
            indent=2,
        )
    except Exception as e:
        return _handle_api_error(e)


# Phase 2.1: File Management Tools
