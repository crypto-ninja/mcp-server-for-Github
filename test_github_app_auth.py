#!/usr/bin/env python3
"""
Test GitHub App authentication configuration.

This script verifies:
1. Environment variables are set correctly
2. GitHub App token can be obtained
3. Rate limits confirm App auth is working (15,000/hour)

Run with: python test_github_app_auth.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Load .env from script directory (not working directory)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    print("Note: python-dotenv not installed, using environment variables only")


async def test_app_auth():
    """Test GitHub App authentication."""
    print("=" * 70)
    print("GITHUB APP AUTH TEST")
    print("=" * 70)
    
    # Check environment variables
    app_id = os.getenv("GITHUB_APP_ID")
    installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
    key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
    pat_token = os.getenv("GITHUB_TOKEN")
    auth_mode = os.getenv("GITHUB_AUTH_MODE", "app")
    
    print("\nEnvironment Configuration:")
    print(f"  GITHUB_APP_ID: {'✅ Set' if app_id else '❌ Not set'}")
    print(f"  GITHUB_APP_INSTALLATION_ID: {'✅ Set' if installation_id else '❌ Not set'}")
    print(f"  GITHUB_APP_PRIVATE_KEY_PATH: {'✅ Set' if key_path else '❌ Not set'}")
    print(f"  GITHUB_TOKEN (PAT fallback): {'✅ Set' if pat_token else '❌ Not set'}")
    print(f"  GITHUB_AUTH_MODE: {auth_mode}")
    
    # Check if private key file exists
    if key_path:
        key_exists = Path(key_path).exists()
        print(f"  Private key file exists: {'✅ Yes' if key_exists else '❌ No'}")
    
    # Try to import and use the auth module
    print("\n" + "-" * 70)
    print("Testing GitHub App Authentication...")
    print("-" * 70)
    
    if not all([app_id, installation_id, key_path]):
        print("\n⚠️  GitHub App not fully configured")
        print("   Required: GITHUB_APP_ID, GITHUB_APP_INSTALLATION_ID, GITHUB_APP_PRIVATE_KEY_PATH")
        
        if pat_token:
            print("\n✅ PAT fallback available (GITHUB_TOKEN is set)")
            print("   Rate limit: 5,000 requests/hour")
        else:
            print("\n❌ No authentication configured!")
            return False
        return True
    
    try:
        from auth.github_app import get_installation_token_from_env
        
        print("🔧 Getting GitHub App token...")
        token = await get_installation_token_from_env()
        
        if token:
            print(f"✅ Token obtained (length: {len(token)})")
            
            # Test with GitHub API to check rate limit
            try:
                import httpx
                
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                }
                
                async with httpx.AsyncClient() as client:
                    # Check rate limit
                    response = await client.get(
                        "https://api.github.com/rate_limit",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        rate = response.json()['resources']['core']
                        limit = rate['limit']
                        remaining = rate['remaining']
                        
                        print("\n📊 Rate Limit Status:")
                        print(f"   Limit: {limit}/hour")
                        print(f"   Remaining: {remaining}")
                        
                        if limit == 15000:
                            print("\n✅ Using GitHub App rate limits (15,000/hour)")
                        elif limit == 5000:
                            print("\n⚠️  Using PAT rate limits (5,000/hour)")
                            print("   GitHub App auth may not be working correctly")
                        else:
                            print(f"\n❓ Unexpected rate limit: {limit}")
                    else:
                        print(f"\n⚠️  Rate limit check failed: {response.status_code}")
                        print(f"   Response: {response.text[:200]}")
                        
            except ImportError:
                print("\n⚠️  httpx not installed, skipping rate limit check")
                print("   Install with: pip install httpx")
                
        else:
            print("❌ Failed to obtain token")
            print("   Check your GitHub App configuration")
            return False
            
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
        return False
        
    except Exception as e:
        print(f"\n❌ Error during auth test: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    return True


async def test_branch_tools():
    """Test branch tools with current auth (bonus test)."""
    print("\n" + "-" * 70)
    print("Testing Branch Tools (Optional)...")
    print("-" * 70)
    
    try:
        # This would require the full MCP server setup
        # For now, just indicate the test is available
        print("\n💡 To test branch tools, use the MCP server with:")
        print('   github_list_branches(owner="crypto-ninja", repo="github-mcp-server")')
        print("\n   If using GitHub App auth, branch operations should work without PAT fallback")
        
    except Exception as e:
        print(f"   Note: {e}")


def main():
    """Run all tests."""
    print("\n🧪 GitHub MCP Server - Authentication Test Suite\n")
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(test_app_auth())
    loop.run_until_complete(test_branch_tools())
    
    print()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()