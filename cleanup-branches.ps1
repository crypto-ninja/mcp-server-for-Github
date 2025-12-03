# Branch Cleanup Script for GitHub MCP Server
# Safe cleanup of merged and stale branches

Write-Output "🧹 GitHub MCP Server - Branch Cleanup"
Write-Output "=====================================`n"

# SAFE TO DELETE (fully merged)
Write-Output "✅ SAFE TO DELETE (fully merged):"
Write-Output "  - hungry-darwin`n"

# LIKELY SAFE TO DELETE (work is in main, branches just diverged)
Write-Output "✅ LIKELY SAFE (feature work already in main):"
Write-Output "  - feat/phase-2.3-competitive-analysis"
Write-Output "  - feature/license-verification"
Write-Output "  - phase-2.2-repo-management`n"

# REMOTE BRANCHES TO DELETE
Write-Output "✅ REMOTE BRANCHES TO DELETE:"
Write-Output "  - origin/feat/mcp-vnext-phase0-1"
Write-Output "  - origin/feat/phase-2.3-competitive-analysis"
Write-Output "  - origin/feature/license-verification"
Write-Output "  - origin/phase-2.2-repo-management`n"

Write-Output "⚠️  REVIEW ABOVE - All feature work appears to be in main already"
Write-Output "`nPress Ctrl+C to cancel, or any key to proceed with cleanup..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Delete local branches
Write-Output "`n🗑️  Deleting local branches...`n"

$localBranches = @(
    "hungry-darwin",
    "feat/phase-2.3-competitive-analysis",
    "feature/license-verification",
    "phase-2.2-repo-management"
)

foreach ($branch in $localBranches) {
    Write-Output "  Deleting local: $branch"
    git branch -D $branch 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Output "    ✅ Deleted"
    } else {
        Write-Output "    ⚠️  Failed (may not exist)"
    }
}

# Delete remote branches
Write-Output "`n🗑️  Deleting remote branches...`n"

$remoteBranches = @(
    "feat/mcp-vnext-phase0-1",
    "feat/phase-2.3-competitive-analysis",
    "feature/license-verification",
    "phase-2.2-repo-management"
)

foreach ($branch in $remoteBranches) {
    Write-Output "  Deleting remote: origin/$branch"
    git push origin --delete $branch 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Output "    ✅ Deleted"
    } else {
        Write-Output "    ⚠️  Failed (may not exist or already deleted)"
    }
}

# Prune stale remote references
Write-Output "`n🧹 Pruning stale remote references...`n"
git remote prune origin
Write-Output "    ✅ Complete`n"

# Final status
Write-Output "`n✅ Cleanup Complete!`n"
Write-Output "Remaining branches:"
git branch -a

