# Running GitHub Actions Locally with `act`

This guide explains how to test your CI/CD pipeline locally before pushing to GitHub.

## Prerequisites

### 1. Install Docker Desktop

`act` requires Docker to run GitHub Actions workflows locally.

**Windows:**
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Install and start Docker Desktop
3. Verify installation:
   ```powershell
   docker --version
   ```

### 2. Install `act`

**Option A: Using Scoop (Recommended for Windows)**
```powershell
# Install Scoop if you don't have it
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# Install act
scoop install act
```

**Option B: Using Chocolatey**
```powershell
# Install Chocolatey if you don't have it (run as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install act
choco install act-cli
```

**Option C: Manual Download**
1. Download from: https://github.com/nektos/act/releases
2. Extract and add to PATH

## Usage

### Run Full CI Workflow

Simulates a `push` event (what happens when you push to main):

```powershell
act push
```

### Run Specific Job

Run just the build/test job:

```powershell
act -j build
```

### Run with Specific Python Version

Test a specific Python version from the matrix:

```powershell
act -j build --matrix python-version:3.12
```

### List Available Jobs

See what jobs are available:

```powershell
act -l
```

### Dry Run (See What Would Run)

Preview without executing:

```powershell
act push --dryrun
```

## Common Issues

### Docker Not Running

If you see Docker errors:
1. Start Docker Desktop
2. Wait for it to fully start (whale icon in system tray)
3. Verify: `docker ps`

### Large Docker Images

First run will download large images (~2GB). Subsequent runs are faster.

### Secrets/Environment Variables

`act` can't access GitHub secrets. For local testing:

1. Create `.secrets` file in repo root:
   ```
   GITHUB_TOKEN=your_token_here
   ```

2. Run with secrets:
   ```powershell
   act push --secret-file .secrets
   ```

**⚠️ Never commit `.secrets` to git!** Add to `.gitignore`.

### Platform Differences

Some actions may behave differently on Windows vs Linux. The CI runs on `ubuntu-latest`, so `act` uses Linux containers.

## Example Workflow

```powershell
# 1. Make your changes
git add .
git commit -m "feat: Add new feature"

# 2. Test locally before pushing
act push

# 3. If tests pass, push to GitHub
git push origin main
```

## CI Workflow Overview

Our `.github/workflows/ci.yml` runs:

1. **Lint (ruff)** - Code style checks
2. **Type Check (mypy)** - Type safety verification
3. **Security Audit (pip-audit)** - Dependency vulnerability scan
4. **Tests (pytest)** - Full test suite across Python 3.10, 3.11, 3.12
5. **Coverage Report** - Code coverage metrics

## Tips

- Run `act push` before every push to catch issues early
- Use `act -j build` for faster iteration (just tests)
- Check Docker has enough resources (Settings → Resources in Docker Desktop)
- First run takes longer (image downloads), subsequent runs are faster

## Troubleshooting

### "act: command not found"
- Ensure `act` is in your PATH
- Restart terminal after installation

### "Cannot connect to Docker daemon"
- Start Docker Desktop
- Verify Docker is running: `docker ps`

### "Image pull failed"
- Check internet connection
- Try: `docker pull node:16-buster-slim` manually

### Tests fail locally but pass in CI
- Check Python version matches (CI uses 3.10, 3.11, 3.12)
- Verify environment variables are set correctly
- Some tests may require GitHub API access (use `.secrets` file)
