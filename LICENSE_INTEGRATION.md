# License Verification Integration Guide

This guide explains how to integrate the license verification system into `github_mcp.py`.

## Quick Start

The license verification system is now available in `license_manager.py`. Here's how to integrate it:

### 1. Add Import to github_mcp.py

Add this import at the top of `github_mcp.py` (after the existing imports):

```python
from license_manager import check_license_on_startup, get_license_manager
```

### 2. Check License on Startup

In the `main()` function or server startup code, add:

```python
async def main():
    """Main entry point for the MCP server."""
    
    # Check license on startup
    await check_license_on_startup()
    
    # Rest of your existing main() code...
    # (server initialization, etc.)
```

### 3. Add License Info Tool (Optional)

Add a new tool to let users check their license status:

```python
@mcp.tool()
async def github_license_info() -> str:
    """
    Display current license information and status.
    
    Returns license tier, expiration date, and feature access.
    For commercial licensing information, visit https://mcplabs.co.uk
    """
    license_manager = get_license_manager()
    license_info = await license_manager.verify_license()
    
    if license_info.get("valid"):
        tier = license_info.get("tier", "free")
        tier_info = license_manager.get_tier_info(tier)
        
        response = f"""# GitHub MCP Server License

**Status:** ✅ Valid
**Tier:** {tier_info['name']}
**License Type:** {tier.upper()}
"""
        if tier != "free":
            response += f"""
**Expires:** {license_info.get('expires_at', 'N/A').split('T')[0]}
**Max Developers:** {license_info.get('max_developers') or 'Unlimited'}
**Status:** {license_info.get('status', 'unknown').upper()}
"""
        else:
            response += """
**License:** AGPL v3 (Open Source)
**Commercial Use:** Requires commercial license
**Purchase:** https://mcplabs.co.uk/pricing
"""
        
        return response
    else:
        return f"""# License Verification Failed

**Error:** {license_info.get('error', 'Unknown')}
**Message:** {license_info.get('message', '')}

Contact: licensing@mcplabs.co.uk
"""
```

## Configuration

### For Users

Users need to set the `GITHUB_MCP_LICENSE_KEY` environment variable:

**Option 1: Environment Variable**
```bash
export GITHUB_MCP_LICENSE_KEY="MCP-1.0-STAR-XLQVbEM3A3dB-U8XK6A"
```

**Option 2: Claude Desktop Config**
```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["/path/to/github_mcp.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_github_token",
        "GITHUB_MCP_LICENSE_KEY": "MCP-1.0-STAR-XLQVbEM3A3dB-U8XK6A"
      }
    }
  }
}
```

## How It Works

### License Verification Flow

1. **Startup Check**: When the MCP server starts, it checks the license
2. **Online Verification**: Calls https://mcplabs.co.uk API to validate
3. **Caching**: Saves valid licenses locally (valid for 24 hours)
4. **Offline Fallback**: Uses cache if API unreachable
5. **AGPL Fallback**: If no license key provided, runs under AGPL v3

### License Tiers

- **Free (AGPL v3)**: Open source projects only, must share source code
- **Startup (£399/year)**: Up to 10 developers, commercial use
- **Business (£1,599/year)**: Up to 50 developers, priority support
- **Enterprise (£3,999/year)**: Unlimited developers, 24/7 support

### Security Features

- ✅ Verifies license key + product ID match
- ✅ Checks expiration dates
- ✅ Validates license status (active/expired/cancelled)
- ✅ Caches results to minimize API calls
- ✅ Graceful degradation if API unavailable

## Testing

### Test with Valid License

```bash
export GITHUB_MCP_LICENSE_KEY="MCP-1.0-STAR-XLQVbEM3A3dB-U8XK6A"
python github_mcp.py
```

Expected output:
```
============================================================
✅ GitHub MCP Server - License Valid
============================================================
License: Startup License
Tier: STARTUP
Status: ACTIVE
Expires: 2026-11-05
Max Developers: 10
============================================================
```

### Test without License (AGPL)

```bash
unset GITHUB_MCP_LICENSE_KEY
python github_mcp.py
```

Expected output:
```
============================================================
✅ GitHub MCP Server - License Valid
============================================================
License: Open Source (AGPL v3)
Tier: FREE
License: AGPL v3 (Open Source)
⚠️  For commercial use, purchase a license at https://mcplabs.co.uk
============================================================
```

### Test with Invalid License

```bash
export GITHUB_MCP_LICENSE_KEY="INVALID-KEY"
python github_mcp.py
```

Expected output:
```
============================================================
⚠️  LICENSE VERIFICATION FAILED
============================================================
Error: License not found
Message: Invalid license key. Purchase at https://mcplabs.co.uk

Options:
1. Get free AGPL license: https://github.com/crypto-ninja/github-mcp-server
2. Purchase commercial license: https://mcplabs.co.uk/pricing
3. Contact support: licensing@mcplabs.co.uk
============================================================
```

## API Endpoint

The license verification uses the MCP Labs API:

**URL:** `https://lwbqfgdwmavycgmntevn.supabase.co/functions/v1/verify-license`

**Request:**
```json
{
  "license_key": "MCP-1.0-STAR-XLQVbEM3A3dB-U8XK6A",
  "product_id": "github"
}
```

**Response (Valid):**
```json
{
  "valid": true,
  "tier": "startup",
  "tier_name": "Startup License",
  "product_id": "github",
  "expires_at": "2026-11-05T17:04:04.228+00:00",
  "status": "active",
  "max_developers": 10,
  "features": ["all"],
  "checked_at": "2025-11-05T17:43:29.957Z"
}
```

## Support

For licensing questions or support:

- **Website:** https://mcplabs.co.uk
- **Email:** licensing@mcplabs.co.uk
- **GitHub Issues:** https://github.com/crypto-ninja/github-mcp-server/issues

## License

The license verification system itself is part of the GitHub MCP Server and follows the same dual-licensing model (AGPL v3 / Commercial).