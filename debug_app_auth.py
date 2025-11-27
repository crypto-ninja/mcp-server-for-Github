#!/usr/bin/env python3
"""
Comprehensive GitHub App Authentication Diagnostic Script

This script helps debug why GitHub App authentication might be failing.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import httpx
import jwt
import time

# Load .env file
script_dir = Path(__file__).parent
env_path = script_dir / ".env"
load_dotenv(env_path)

print("=" * 70)
print("GITHUB APP AUTHENTICATION DIAGNOSTIC")
print("=" * 70)
print()

# Step 1: Check environment variables
print("Step 1: Checking Environment Variables")
print("-" * 70)

app_id = os.getenv("GITHUB_APP_ID")
installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
key_content = os.getenv("GITHUB_APP_PRIVATE_KEY")
auth_mode = os.getenv("GITHUB_AUTH_MODE", "not set")

print(f"GITHUB_APP_ID: {app_id if app_id else '❌ NOT SET'}")
print(f"GITHUB_APP_INSTALLATION_ID: {installation_id if installation_id else '❌ NOT SET'}")
print(f"GITHUB_APP_PRIVATE_KEY_PATH: {key_path if key_path else '❌ NOT SET'}")
print(f"GITHUB_APP_PRIVATE_KEY: {'✅ SET' if key_content else '❌ NOT SET (checking file path...)'}")
print(f"GITHUB_AUTH_MODE: {auth_mode}")
print()

if not app_id or not installation_id:
    print("❌ ERROR: Missing required App ID or Installation ID")
    sys.exit(1)

# Step 2: Load private key
print("Step 2: Loading Private Key")
print("-" * 70)

private_key = None

# Try from environment variable first
if key_content:
    print("✅ Found private key in GITHUB_APP_PRIVATE_KEY")
    private_key = key_content
else:
    # Try loading from file
    if key_path:
        key_file = Path(key_path)
        if not key_file.is_absolute():
            key_file = Path.cwd() / key_path
        
        print(f"📁 Attempting to load from: {key_file}")
        print(f"   Exists: {key_file.exists()}")
        
        if key_file.exists():
            try:
                with open(key_file, 'r', encoding='utf-8') as f:
                    private_key = f.read()
                print("✅ Successfully loaded private key from file")
            except Exception as e:
                print(f"❌ ERROR loading key file: {e}")
        else:
            print(f"❌ ERROR: Key file not found at {key_file}")
    else:
        print("❌ ERROR: No private key found (neither in env var nor file path)")

if not private_key:
    print("\n❌ FATAL: Cannot proceed without private key")
    sys.exit(1)

# Validate key format
print("\n📋 Key format check:")
print(f"   Starts with '-----BEGIN': {private_key.strip().startswith('-----BEGIN')}")
print(f"   Contains 'PRIVATE KEY': {'PRIVATE KEY' in private_key}")
print(f"   Key length: {len(private_key)} characters")
print()

# Step 3: Generate JWT token
print("Step 3: Generating JWT Token")
print("-" * 70)

try:
    now = int(time.time())
    payload = {
        "iat": now - 60,  # Issued at time (60 seconds ago to account for clock skew)
        "exp": now + (10 * 60),  # Expires in 10 minutes
        "iss": app_id  # Issuer is the App ID
    }
    
    jwt_token = jwt.encode(payload, private_key, algorithm="RS256")
    print("✅ JWT token generated successfully")
    print(f"   Token length: {len(jwt_token)} characters")
    print(f"   Token preview: {jwt_token[:50]}...")
except Exception as e:
    print(f"❌ ERROR generating JWT: {type(e).__name__}: {e}")
    sys.exit(1)

print()

# Step 4: Test JWT with GitHub API
print("Step 4: Testing JWT with GitHub API")
print("-" * 70)

async def test_jwt():
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        # Test 1: Get app info
        try:
            response = await client.get(
                "https://api.github.com/app",
                headers=headers
            )
            print(f"GET /app: Status {response.status_code}")
            if response.status_code == 200:
                app_data = response.json()
                print(f"✅ App verified: {app_data.get('name', 'Unknown')}")
                print(f"   App ID matches: {app_data.get('id') == int(app_id)}")
            else:
                print(f"❌ Failed: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            return False
        
        # Test 2: Get installation token
        print(f"\n📥 Requesting installation token for installation {installation_id}...")
        try:
            response = await client.post(
                f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                headers=headers
            )
            print(f"POST /app/installations/{installation_id}/access_tokens: Status {response.status_code}")
            
            if response.status_code == 201:
                token_data = response.json()
                installation_token = token_data.get("token")
                expires_at = token_data.get("expires_at")
                print("✅ Installation token obtained!")
                print(f"   Token prefix: {installation_token[:15]}...")
                print(f"   Expires at: {expires_at}")
                print(f"   Token type: {'App' if installation_token.startswith('ghs_') else 'Unknown'}")
                return True
            else:
                print("❌ Failed to get installation token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                
                # Try to parse error
                try:
                    error_data = response.json()
                    print(f"   Error message: {error_data.get('message', 'Unknown')}")
                    if 'errors' in error_data:
                        for err in error_data['errors']:
                            print(f"   - {err}")
                except Exception:
                    pass
                
                return False
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            return False

result = asyncio.run(test_jwt())

print()
print("=" * 70)
if result:
    print("✅ SUCCESS: GitHub App authentication is working!")
    print("\nIf the main script still fails, check:")
    print("  - GITHUB_AUTH_MODE setting")
    print("  - Token caching issues (try clear_token_cache())")
else:
    print("❌ FAILURE: GitHub App authentication is not working")
    print("\nCommon issues:")
    print("  1. Installation ID is incorrect")
    print("  2. App is not installed on the target repository")
    print("  3. App permissions are insufficient")
    print("  4. Private key format is incorrect")
print("=" * 70)

