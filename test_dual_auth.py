#!/usr/bin/env python3
"""Test dual auth fallback system"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_dual_auth():
    print("=" * 70)
    print("TESTING DUAL AUTH FALLBACK SYSTEM")
    print("=" * 70)
    
    # Import after loading env
    from auth.github_app import get_auth_token, _has_app_config
    
    # Test 1: Check current configuration
    print("\n1. Current Configuration:")
    print(f"   GITHUB_TOKEN present: {bool(os.getenv('GITHUB_TOKEN'))}")
    print(f"   GitHub App configured: {_has_app_config()}")
    print(f"   GITHUB_AUTH_MODE: {os.getenv('GITHUB_AUTH_MODE', 'not set')}")
    
    # Test 2: Test get_auth_token() with current config
    print("\n2. Testing get_auth_token() with current configuration:")
    try:
        token = await get_auth_token()
        if token:
            print(f"   ✅ SUCCESS! Token retrieved (length: {len(token)})")
            print(f"   Token prefix: {token[:10]}...")
            token_type = "App" if token.startswith("ghs_") else "PAT" if token.startswith("ghp_") else "Unknown"
            print(f"   Token type: {token_type}")
        else:
            print("   ❌ FAILED! get_auth_token() returned None")
            print("   This indicates the fallback chain is broken!")
    except Exception as e:
        print(f"   ❌ EXCEPTION: {type(e).__name__}: {e}")
        print("   This exception broke the fallback chain!")
    
    # Test 3: Test with explicit PAT mode
    print("\n3. Testing with GITHUB_AUTH_MODE=pat:")
    original_mode = os.getenv("GITHUB_AUTH_MODE")
    os.environ["GITHUB_AUTH_MODE"] = "pat"
    
    try:
        token = await get_auth_token()
        if token:
            print(f"   ✅ SUCCESS! PAT token retrieved (prefix: {token[:10]}...)")
        else:
            print("   ❌ FAILED! No PAT token found")
    except Exception as e:
        print(f"   ❌ EXCEPTION: {type(e).__name__}: {e}")
    finally:
        if original_mode:
            os.environ["GITHUB_AUTH_MODE"] = original_mode
        else:
            os.environ.pop("GITHUB_AUTH_MODE", None)
    
    # Test 4: Test fallback when App fails
    print("\n4. Testing fallback when GitHub App fails:")
    print("   (This simulates App configured but token retrieval fails)")
    
    # Temporarily break App config to test fallback
    original_app_id = os.getenv("GITHUB_APP_ID")
    if original_app_id:
        os.environ.pop("GITHUB_APP_ID", None)
        print("   Temporarily removed GITHUB_APP_ID to test fallback")
        
        try:
            token = await get_auth_token()
            if token:
                print(f"   ✅ SUCCESS! Fallback to PAT worked (prefix: {token[:10]}...)")
            else:
                print("   ❌ FAILED! Fallback did not work - no token returned")
        except Exception as e:
            print(f"   ❌ EXCEPTION: {type(e).__name__}: {e}")
        finally:
            if original_app_id:
                os.environ["GITHUB_APP_ID"] = original_app_id
    
    # Test 5: Direct PAT access
    print("\n5. Testing direct PAT access:")
    pat_token = os.getenv("GITHUB_TOKEN")
    if pat_token:
        print(f"   ✅ PAT available directly (length: {len(pat_token)})")
    else:
        print("   ❌ No PAT in environment")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    # Summary
    print("\n📊 SUMMARY:")
    print("   If all tests show ✅, the dual auth system is working correctly.")
    print("   If any test shows ❌, there's a bug in the fallback chain.")
    print("\n💡 TIP: Set GITHUB_MCP_DEBUG_AUTH=true to see detailed auth flow")

if __name__ == "__main__":
    asyncio.run(test_dual_auth())

