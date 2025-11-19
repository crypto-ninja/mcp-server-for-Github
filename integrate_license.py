#!/usr/bin/env python3
"""
Integration Script for License Verification

This script shows the exact changes needed to integrate license verification
into github_mcp.py. For manual integration, follow these steps:

1. Add import at top of github_mcp.py (after existing imports):
   from license_manager import check_license_on_startup, get_license_manager

2. Add startup check in main() or server initialization

3. Optionally add the license_info tool

For full instructions, see LICENSE_INTEGRATION.md
"""


def show_integration_instructions():
    """Display integration instructions."""
    print("="*70)
    print("LICENSE VERIFICATION INTEGRATION")
    print("="*70)
    print()
    print("To integrate license verification into github_mcp.py:")
    print()
    print("STEP 1: Add Import (after existing imports)")
    print("-" * 70)
    print("from license_manager import check_license_on_startup, get_license_manager")
    print()
    print("STEP 2: Check License on Startup (in main() or startup code)")
    print("-" * 70)
    print("async def main():")
    print("    # Check license on startup")
    print("    await check_license_on_startup()")
    print("    ")
    print("    # Rest of existing code...")
    print()
    print("STEP 3: Optional - Add License Info Tool")
    print("-" * 70)
    print("@mcp.tool()")
    print("async def github_license_info() -> str:")
    print('    """Display current license information and status."""')
    print("    license_manager = get_license_manager()")
    print("    license_info = await license_manager.verify_license()")
    print("    ")
    print("    if license_info.get('valid'):")
    print("        tier = license_info.get('tier', 'free')")
    print("        tier_info = license_manager.get_tier_info(tier)")
    print("        ")
    print("        response = f'''# GitHub MCP Server License")
    print("")
    print("**Status:** ✅ Valid")
    print("**Tier:** {tier_info['name']}")
    print("**License Type:** {tier.upper()}")
    print("'''")
    print("        if tier != 'free':")
    print("            response += f'''")
    print("**Expires:** {license_info.get('expires_at', 'N/A').split('T')[0]}")
    print("**Max Developers:** {license_info.get('max_developers') or 'Unlimited'}")
    print("**Status:** {license_info.get('status', 'unknown').upper()}")
    print("'''")
    print("        else:")
    print("            response += '''")
    print("**License:** AGPL v3 (Open Source)")
    print("**Commercial Use:** Requires commercial license")
    print("**Purchase:** https://mcplabs.co.uk/pricing")
    print("'''")
    print("        return response")
    print("    else:")
    print("        return f'''# License Verification Failed")
    print("")
    print("**Error:** {license_info.get('error', 'Unknown')}")
    print("**Message:** {license_info.get('message', '')}")
    print("")
    print("Contact: licensing@mcplabs.co.uk")
    print("'''")
    print()
    print("="*70)
    print("For detailed instructions, see: LICENSE_INTEGRATION.md")
    print("="*70)

if __name__ == "__main__":
    show_integration_instructions()