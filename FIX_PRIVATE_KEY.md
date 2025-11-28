# Fix GitHub App Private Key Configuration

## Problem Identified

Your GitHub App authentication is failing because:

1. **Private key file not found**: The path `C:\Users\bicyc\Desktop\MCP auth\mcp-server-for-github-by-mcp-labs.2025-11-20.private-key.pem` doesn't exist
2. **Truncated private key**: The `GITHUB_APP_PRIVATE_KEY` environment variable only has 65 characters (should be 1600+)

## Solution Options

### Option 1: Use File Path (Recommended)

1. **Find your private key file** - It should be a `.pem` file you downloaded from GitHub
2. **Update `.env` file** - Use one of these approaches:

   **If key is in a different location:**
   ```bash
   GITHUB_APP_PRIVATE_KEY_PATH=C:\actual\path\to\your\private-key.pem
   # Remove or comment out GITHUB_APP_PRIVATE_KEY
   # GITHUB_APP_PRIVATE_KEY=...
   ```

   **If key is in project directory:**
   ```bash
   GITHUB_APP_PRIVATE_KEY_PATH=./private-key.pem
   # Or just the filename if in same directory
   GITHUB_APP_PRIVATE_KEY_PATH=private-key.pem
   ```

### Option 2: Use Environment Variable (If file is hard to access)

1. **Get the full private key content** from your `.pem` file
2. **Copy the ENTIRE key** including:
   ```
   -----BEGIN RSA PRIVATE KEY-----
   [many lines of base64 encoded data]
   -----END RSA PRIVATE KEY-----
   ```
3. **Update `.env` file**:
   ```bash
   GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
   ```
   - Use double quotes
   - Use `\n` for line breaks
   - Include the BEGIN and END lines

## How to Get Your Private Key

1. Go to: https://github.com/settings/apps
2. Click on your app (ID: 2324956)
3. Scroll to "Private keys" section
4. If you see a key listed, you can regenerate it (old one will stop working)
5. Click "Generate a private key"
6. Download the `.pem` file
7. Save it somewhere secure (NOT in git!)

## Verify Fix

After updating your `.env` file, run:

```bash
python debug_app_auth.py
```

You should see:
- ✅ Private key loaded successfully
- ✅ JWT token generated
- ✅ Installation token obtained

## Security Note

**NEVER commit private keys to git!**

Make sure `.env` is in `.gitignore`:
```bash
echo ".env" >> .gitignore
```

