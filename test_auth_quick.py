import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from script directory (same as github_mcp.py does)
script_dir = Path(__file__).parent
env_path = script_dir / ".env"
load_dotenv(env_path)

# Set debug flag
os.environ['GITHUB_MCP_DEBUG_AUTH'] = 'true'

from auth.github_app import get_auth_token, clear_token_cache  # noqa: E402

clear_token_cache()  # Force fresh token
token = asyncio.run(get_auth_token())

print(f'Token type: {"App" if token and token.startswith("ghs_") else "PAT"}')
print(f'Token prefix: {token[:15] if token else "None"}...')
