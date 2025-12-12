# Quick Start: Running CI Locally

## Step 1: Start Docker Desktop

1. Open **Docker Desktop** from Start Menu
2. Wait for it to fully start (whale icon in system tray should be steady)
3. **Restart your PowerShell/terminal** (important - Docker needs to be in PATH)

## Step 2: Verify Docker Works

After restarting terminal, run:
```powershell
docker --version
docker ps
```

If you see version info and an empty container list, Docker is working! ✅

## Step 3: Install `act`

Choose the easiest option for you:

### Option A: Scoop (Recommended - Easiest)
```powershell
# Install Scoop (if you don't have it)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# Install act
scoop install act
```

### Option B: Manual Download
1. Go to: https://github.com/nektos/act/releases/latest
2. Download `act_windows_amd64.zip` (or `act_windows_arm64.zip` for ARM)
3. Extract to a folder (e.g., `C:\tools\act\`)
4. Add to PATH:
   ```powershell
   # Add to PATH permanently
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\tools\act", [EnvironmentVariableTarget]::User)
   ```
5. **Restart terminal** after adding to PATH

## Step 4: Test `act`

```powershell
act --version
```

Should show version number (e.g., `act version 0.2.XX`)

## Step 5: Run CI Locally

```powershell
# List available jobs
act -l

# Run full CI workflow (simulates push to main)
act push

# Or just run the build job (faster)
act -j build
```

**Note:** First run will download Docker images (~2GB). This is normal and only happens once.

## Troubleshooting

### "docker: command not found"
- Make sure Docker Desktop is running
- **Restart your terminal** after starting Docker Desktop
- Check Docker Desktop → Settings → General → "Use the WSL 2 based engine" (if using WSL)

### "act: command not found"
- If using manual download, make sure you added to PATH
- **Restart terminal** after installation
- Verify: `$env:Path -split ';' | Select-String act`

### Docker Desktop won't start
- Check Windows requirements: https://docs.docker.com/desktop/install/windows-install/
- May need WSL 2: `wsl --install`
- Check virtualization is enabled in BIOS

## Next Steps

Once `act` is working, you can:
- Run `act push` before every commit to catch CI issues
- Test specific Python versions: `act -j build --matrix python-version:3.12`
- Use secrets file for GitHub token (see `docs/LOCAL_CI_TESTING.md`)
