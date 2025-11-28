#!/usr/bin/env python3
"""Direct test of .env loading"""

import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 70)
print("DIRECT .env LOADING TEST")
print("=" * 70)

# Get script directory
script_dir = Path(__file__).parent
print(f"\nScript directory: {script_dir}")
print(f"Script file: {__file__}")

# Check if .env exists
env_path = script_dir / ".env"
print(f"\n.env path: {env_path}")
print(f".env exists: {env_path.exists()}")

if env_path.exists():
    print(f".env is a file: {env_path.is_file()}")
    print(f".env size: {env_path.stat().st_size} bytes")

# Try to load it
print("\nLoading .env...")
load_dotenv(env_path)

# Check if GITHUB_TOKEN is now in environment
token = os.getenv("GITHUB_TOKEN")
print(f"\nGITHUB_TOKEN loaded: {token is not None}")

if token:
    print(f"Token length: {len(token)}")
    print(f"Token prefix: {token[:7]}...")
    print(f"Token format valid: {token.startswith('ghp_')}")
else:
    print("\n❌ NO TOKEN LOADED!")
    print("Available environment variables:")
    for key in sorted(os.environ.keys())[:20]:
        print(f"  - {key}")

print("\n" + "=" * 70)

