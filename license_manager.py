#!/usr/bin/env python3
"""
License Manager for GitHub MCP Server

Handles license verification for commercial use of the GitHub MCP Server.
Supports online verification with offline caching.

License Tiers:
- Free (AGPL v3): Open source projects only
- Startup: Up to 10 developers (£399/year)
- Business: Up to 50 developers (£1,599/year)
- Enterprise: Unlimited developers (£3,999/year)

For commercial licensing:
Website: https://mcplabs.co.uk
Email: licensing@mcplabs.co.uk
"""

import os
import httpx
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

# Configuration
LICENSE_API_URL = "https://lwbqfgdwmavycgmntevn.supabase.co/functions/v1/verify-license"
LICENSE_CHECK_INTERVAL = 86400  # 24 hours in seconds
LICENSE_CACHE_FILE = Path.home() / ".github_mcp_license_cache.json"

# License tier information
LICENSE_TIERS = {
    "free": {
        "name": "Open Source (AGPL v3)",
        "max_developers": None,
        "features": ["all"],
        "requires_key": False,
        "url": "https://github.com/crypto-ninja/github-mcp-server"
    },
    "startup": {
        "name": "Startup License",
        "max_developers": 10,
        "features": ["all"],
        "requires_key": True,
        "url": "https://mcplabs.co.uk/pricing"
    },
    "business": {
        "name": "Business License",
        "max_developers": 50,
        "features": ["all"],
        "requires_key": True,
        "url": "https://mcplabs.co.uk/pricing"
    },
    "enterprise": {
        "name": "Enterprise License",
        "max_developers": None,  # Unlimited
        "features": ["all"],
        "requires_key": True,
        "url": "https://mcplabs.co.uk/pricing"
    }
}


class LicenseManager:
    """Manages license verification and caching for the GitHub MCP Server."""
    
    def __init__(self, license_key: Optional[str] = None, product_id: str = "github"):
        """
        Initialize the license manager.
        
        Args:
            license_key: Optional license key (reads from GITHUB_MCP_LICENSE_KEY env var if not provided)
            product_id: Product identifier (default: "github")
        """
        self.license_key = license_key or os.environ.get("GITHUB_MCP_LICENSE_KEY", "")
        self.product_id = product_id
        self.cache_file = LICENSE_CACHE_FILE
        self.api_url = LICENSE_API_URL
    
    async def verify_license(self, force_online: bool = False) -> Dict[str, Any]:
        """
        Verify the license key.
        
        Args:
            force_online: Force online verification even if cache is valid
            
        Returns:
            Dict with license info: {valid, tier, expires_at, status, max_developers}
        """
        # If no license key, assume AGPL (free tier)
        if not self.license_key:
            return {
                "valid": True,
                "tier": "free",
                "product_id": self.product_id,
                "status": "agpl",
                "message": "Running under AGPL v3 license. For commercial use, get a license at https://mcplabs.co.uk"
            }
        
        # Check cache first (if not forcing online)
        if not force_online:
            cached = self._load_cache()
            if cached and self._is_cache_valid(cached):
                return cached
        
        # Perform online verification
        try:
            verified = await self._verify_online()
            self._save_cache(verified)
            return verified
        except Exception as e:
            # If online fails, try cache as fallback
            cached = self._load_cache()
            if cached and cached.get("valid"):
                # Add warning that we're using cached data
                cached["warning"] = f"Using cached license (online check failed: {str(e)})"
                return cached
            
            # No cache, no online - return error
            return {
                "valid": False,
                "error": f"License verification failed: {str(e)}",
                "message": "Cannot verify license. Check your internet connection or license key."
            }
    
    async def _verify_online(self) -> Dict[str, Any]:
        """Verify license with online API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    json={
                        "license_key": self.license_key,
                        "product_id": self.product_id
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    data["checked_at"] = datetime.utcnow().isoformat()
                    return data
                elif response.status_code == 404:
                    return {
                        "valid": False,
                        "error": "License not found",
                        "message": "Invalid license key. Purchase at https://mcplabs.co.uk"
                    }
                elif response.status_code == 403:
                    try:
                        error_data = response.json()
                        return {
                            "valid": False,
                            "error": error_data.get("error", "License inactive"),
                            "message": error_data.get("message", "License is not active")
                        }
                    except:
                        return {
                            "valid": False,
                            "error": "License inactive",
                            "message": "Contact support@mcplabs.co.uk"
                        }
                else:
                    return {
                        "valid": False,
                        "error": f"API returned {response.status_code}",
                        "message": "License verification failed. Contact support@mcplabs.co.uk"
                    }
            except httpx.TimeoutException:
                raise Exception("License API timeout")
            except httpx.RequestError as e:
                raise Exception(f"Network error: {str(e)}")
    
    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Load cached license data."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None
    
    def _save_cache(self, license_data: Dict[str, Any]) -> None:
        """Save license data to cache."""
        try:
            # Ensure directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(license_data, f)
        except Exception:
            pass  # Silently fail - cache is optional
    
    def _is_cache_valid(self, cached: Dict[str, Any]) -> bool:
        """Check if cached license is still valid."""
        try:
            # Check if cached check is recent enough
            checked_at = datetime.fromisoformat(cached.get("checked_at", ""))
            if datetime.utcnow() - checked_at > timedelta(seconds=LICENSE_CHECK_INTERVAL):
                return False
            
            # Check if license hasn't expired
            if "expires_at" in cached:
                expires = datetime.fromisoformat(cached["expires_at"].replace('Z', '+00:00').replace('+00:00', ''))
                if datetime.utcnow() > expires:
                    return False
            
            # Check if license is active
            if cached.get("status") not in ["active", "agpl"]:
                return False
            
            return cached.get("valid", False)
        except Exception:
            return False
    
    def get_tier_info(self, tier: str) -> Dict[str, Any]:
        """Get information about a license tier."""
        return LICENSE_TIERS.get(tier, LICENSE_TIERS["free"])
    
    def print_license_status(self, license_info: Dict[str, Any]) -> None:
        """Print license status to console."""
        print("=" * 60)
        
        if not license_info.get("valid"):
            print("[!] LICENSE VERIFICATION FAILED")
            print("=" * 60)
            print(f"Error: {license_info.get('error', 'Unknown error')}")
            print(f"Message: {license_info.get('message', '')}")
            print()
            print("Options:")
            print("1. Get free AGPL license: https://github.com/crypto-ninja/github-mcp-server")
            print("2. Purchase commercial license: https://mcplabs.co.uk/pricing")
            print("3. Contact support: licensing@mcplabs.co.uk")
            print("=" * 60)
            return
        
        # Print valid license info
        tier = license_info.get("tier", "free")
        tier_info = self.get_tier_info(tier)
        
        print("[OK] GitHub MCP Server - License Valid")
        print("=" * 60)
        print(f"License: {tier_info['name']}")
        print(f"Tier: {tier.upper()}")
        
        if tier != "free":
            print(f"Status: {license_info.get('status', 'unknown').upper()}")
            if "expires_at" in license_info:
                expires = license_info['expires_at'].split('T')[0]
                print(f"Expires: {expires}")
            if "max_developers" in license_info:
                max_devs = license_info["max_developers"]
                if max_devs is None:
                    print("Max Developers: Unlimited")
                else:
                    print(f"Max Developers: {max_devs}")
        else:
            print("License: AGPL v3 (Open Source)")
            print("[!] For commercial use, purchase a license at https://mcplabs.co.uk")
        
        if "warning" in license_info:
            print(f"\n[!] Warning: {license_info['warning']}")
        
        print("=" * 60)
        print()


async def check_license_on_startup() -> bool:
    """
    Check license when MCP server starts.
    Print license status and return validity.
    
    Returns:
        bool: True if license is valid, False otherwise
    """
    license_manager = LicenseManager()
    license_info = await license_manager.verify_license()
    license_manager.print_license_status(license_info)
    return license_info.get("valid", False)


# Global license manager instance
_global_license_manager: Optional[LicenseManager] = None

def get_license_manager() -> LicenseManager:
    """Get or create the global license manager instance."""
    global _global_license_manager
    if _global_license_manager is None:
        _global_license_manager = LicenseManager()
    return _global_license_manager