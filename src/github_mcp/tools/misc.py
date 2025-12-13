"""Miscellaneous tools for GitHub MCP Server."""

from ..utils.license_manager import get_license_manager


async def github_license_info() -> str:
    """
    Display current license information and status for the GitHub MCP Server.

    Returns:
        Formatted license information including tier, expiration, and status
    """
    license_manager = get_license_manager()
    license_info = await license_manager.verify_license()

    if license_info.get("valid"):
        tier = license_info.get("tier", "free")
        tier_info = license_manager.get_tier_info(tier)

        response = f"""# GitHub MCP Server License


**Status:** ✅ Valid
**Tier:** {tier_info["name"]}
**License Type:** {tier.upper()}
"""
        if tier != "free":
            response += f"""
**Expires:** {license_info.get("expires_at", "N/A").split("T")[0]}
**Max Developers:** {license_info.get("max_developers") or "Unlimited"}
**Status:** {license_info.get("status", "unknown").upper()}
"""
        else:
            response += """
**License:** AGPL v3 (Open Source)
**Commercial Use:** Requires commercial license
**Purchase:** https://mcplabs.co.uk/pricing
**Contact:** licensing@mcplabs.co.uk
"""
        return response
    else:
        return f"""# License Verification Failed


**Error:** {license_info.get("error", "Unknown")}
**Message:** {license_info.get("message", "")}


**Options:**
1. Get free AGPL license: https://github.com/crypto-ninja/mcp-server-for-Github
2. Purchase commercial license: https://mcplabs.co.uk/pricing
3. Contact support: licensing@mcplabs.co.uk
"""
