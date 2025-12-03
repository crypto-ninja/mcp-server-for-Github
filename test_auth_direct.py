#!/usr/bin/env python3
"""Direct auth test - bypasses MCP layer"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_auth():
    print("=" * 70)
    print("DIRECT GITHUB AUTH TEST")
    print("=" * 70)
    
    # Step 1: Check if token is in environment
    token = os.getenv("GITHUB_TOKEN")
    print(f"\n1. GITHUB_TOKEN in environment: {'YES' if token else 'NO'}")
    if token:
        print(f"   Token length: {len(token)}")
        print(f"   Token prefix: {token[:7]}...")
    else:
        print("   ❌ NO TOKEN FOUND!")
        return
    
    # Step 2: Check GitHub App configuration
    app_id = os.getenv("GITHUB_APP_ID")
    app_installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
    app_key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
    app_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
    
    print("\n2. GitHub App Configuration:")
    print(f"   GITHUB_APP_ID: {'YES' if app_id else 'NO'}")
    print(f"   GITHUB_APP_INSTALLATION_ID: {'YES' if app_installation_id else 'NO'}")
    print(f"   GITHUB_APP_PRIVATE_KEY_PATH: {'YES' if app_key_path else 'NO'}")
    print(f"   GITHUB_APP_PRIVATE_KEY: {'YES' if app_key else 'NO'}")
    
    # Step 3: Test token with GitHub API
    print("\n3. Testing token with GitHub API...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    async with httpx.AsyncClient() as client:
        # Test 1: Get authenticated user (should work with any valid token)
        print("\n   Test 1: GET /user (verify token works)")
        try:
            response = await client.get(
                "https://api.github.com/user",
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! Authenticated as: {data['login']}")
            else:
                print(f"   ❌ FAILED: {response.text}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Test 2: List branches (read operation)
        print("\n   Test 2: GET /repos/crypto-ninja/github-mcp-server/branches")
        try:
            response = await client.get(
                "https://api.github.com/repos/crypto-ninja/github-mcp-server/branches",
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! Found {len(data)} branches")
            else:
                print(f"   ❌ FAILED: {response.text}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        # Test 3: Create branch (write operation)
        print("\n   Test 3: POST /repos/.../git/refs (create branch)")
        try:
            # First get main branch SHA
            ref_response = await client.get(
                "https://api.github.com/repos/crypto-ninja/github-mcp-server/git/ref/heads/main",
                headers=headers
            )
            
            if ref_response.status_code == 200:
                sha = ref_response.json()["object"]["sha"]
                print(f"   Main SHA: {sha[:7]}...")
                
                # Try to create branch
                import time
                branch_name = f"test/direct-auth-{int(time.time())}"
                
                create_response = await client.post(
                    "https://api.github.com/repos/crypto-ninja/github-mcp-server/git/refs",
                    headers=headers,
                    json={
                        "ref": f"refs/heads/{branch_name}",
                        "sha": sha
                    }
                )
                
                print(f"   Status: {create_response.status_code}")
                if create_response.status_code == 201:
                    print(f"   ✅ SUCCESS! Created branch: {branch_name}")
                    
                    # Clean up - delete it
                    await client.delete(
                        f"https://api.github.com/repos/crypto-ninja/github-mcp-server/git/refs/heads/{branch_name}",
                        headers=headers
                    )
                    print("   ✅ Cleanup: Branch deleted")
                else:
                    print(f"   ❌ FAILED: {create_response.text}")
            else:
                print(f"   ❌ Could not get main SHA: {ref_response.text}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    # Step 4: Test auth through the actual code
    print("\n4. Testing auth through get_auth_token() function...")
    try:
        from auth.github_app import get_auth_token
        auth_token = await get_auth_token()
        if auth_token:
            print(f"   ✅ get_auth_token() returned token (prefix: {auth_token[:10]}...)")
            print(f"   Token type: {'App' if auth_token.startswith('ghs_') else 'PAT' if auth_token.startswith('ghp_') else 'Unknown'}")
        else:
            print("   ❌ get_auth_token() returned None")
    except Exception as e:
        print(f"   ❌ ERROR importing/getting auth token: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_auth())

