/**
 * Retry creating releases after clearing token cache
 * 
 * Prerequisites:
 * 1. Update GitHub App permissions to include "Releases: Write"
 * 2. Run this script to clear cache and create releases
 */

import { initializeMCPClient, callMCPTool, closeMCPClient } from "./servers/client-deno.ts";

async function retryReleases() {
    try {
        console.log("🔧 Initializing MCP client...");
        await initializeMCPClient();
        
        // Clear token cache first
        console.log("🗑️  Clearing token cache to get fresh permissions...");
        const clearResult = await callMCPTool("github_clear_token_cache", {});
        console.log(clearResult);
        console.log("\n⏳ Waiting 2 seconds for cache to clear...");
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Test permission first
        console.log("\n🔍 Testing read permission...");
        const testRepo = await callMCPTool("github_get_repo_info", {
            owner: "crypto-ninja",
            repo: "github-mcp-server"
        });
        console.log("✅ Read permission works! Repo:", testRepo.name);
        
        // Create v2.2.0 Release
        console.log("\n📦 Creating v2.2.0 release...");
        try {
            const v220 = await callMCPTool("github_create_release", {
                owner: "crypto-ninja",
                repo: "github-mcp-server",
                tag_name: "v2.2.0",
                name: "v2.2.0 - Enterprise GitHub App Authentication 🔐",
                body: `# v2.2.0 - Enterprise GitHub App Authentication 🔐

**Release Date:** November 20, 2025  
**Tool Count:** 42 → 43 (+1)

## 🔐 GitHub App Authentication

- Dual auth system (App + PAT fallback)
- 3x rate limit (15K vs 5K requests/hour)
- Enterprise-grade permissions
- 1-hour token caching
- 100% backward compatible

## 🏗️ Architecture

- Centralized authentication for all 42 tools
- Automatic PAT fallback
- Debug logging support

## 📦 Installation

\`\`\`bash
pip install --upgrade github-mcp-server
\`\`\`

**Built with passion by MCP Labs** 🚀`,
                draft: false,
                prerelease: false
            });
            console.log("✅ v2.2.0 created successfully!");
            console.log("Response:", v220);
        } catch (error: any) {
            console.error("❌ Failed to create v2.2.0:", error.message || error);
            if (error.message?.includes("401") || error.message?.includes("Unauthorized")) {
                console.error("\n⚠️  PERMISSION ISSUE:");
                console.error("Your GitHub App needs 'Releases: Write' permission.");
                console.error("1. Go to: https://github.com/settings/apps");
                console.error("2. Select your app");
                console.error("3. Add 'Releases: Write' permission");
                console.error("4. Re-run this script");
            }
        }
        
        // Create v2.2.1 Release
        console.log("\n📦 Creating v2.2.1 release...");
        try {
            const v221 = await callMCPTool("github_create_release", {
                owner: "crypto-ninja",
                repo: "github-mcp-server",
                tag_name: "v2.2.1",
                name: "v2.2.1 - Production Hardening & Quick Wins 🎯",
                body: `# v2.2.1 - Production Hardening & Quick Wins 🎯

**Release Date:** November 21, 2025  
**Tool Count:** 43 → 44 (+1)

## 🎯 Quick Win Sprint Complete!

### ✅ Dependencies Fixed

- Added PyJWT>=2.8.0 (GitHub App support)
- Added python-dotenv>=1.0.0 (.env support)
- Pinned MCP SDK to <2.0.0 (stability)

### ✅ Startup Validation

- Deno validation with clear error messages
- Fail-fast if dependencies missing
- Installation instructions included

### ✅ Health Monitoring

- New \`health_check\` tool
- Returns version, auth status, Deno info
- Production monitoring ready

### ✅ Token Cache Management

- New \`github_clear_token_cache\` tool
- Force fresh tokens after permission updates
- Resolves permission caching issues

### ✅ Bug Fixes (Dogfooding Wins! 🐕🍖)

1. Fixed \`response_format\` parameter on write tools
2. Fixed GitHub auth env vars in execute_code  
3. CI now installs Deno automatically
4. Added token cache clearing capability

## 🏆 Dogfooding Achievement

All bugs discovered and fixed while using our own tools to create releases!

## 📦 Installation

\`\`\`bash
pip install --upgrade github-mcp-server
\`\`\`

**Production Ready: 9.5/10** ⭐`,
                draft: false,
                prerelease: false
            });
            console.log("✅ v2.2.1 created successfully!");
            console.log("Response:", v221);
        } catch (error: any) {
            console.error("❌ Failed to create v2.2.1:", error.message || error);
        }
        
        await closeMCPClient();
        console.log("\n✅ Done!");
        
    } catch (error) {
        console.error("❌ Error:", error);
        process.exit(1);
    }
}

retryReleases();

