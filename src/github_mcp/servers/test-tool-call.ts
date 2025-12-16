// servers/test-tool-call.ts

import * as gh from './github/index.js';
import { closeMCPClient } from './client.js';

async function testToolCalls() {
    try {
        console.log('Testing MCP tool calls...\n');
        
        // Test 1: Get repository info
        console.log('1. Testing github_get_repo_info...');
        const repoInfo = await gh.repos.github_get_repo_info({
            owner: 'crypto-ninja',
            repo: 'github-mcp-server',
            response_format: 'markdown' as 'markdown' | 'json'
        });
        console.log('   ✓ Success');
        console.log('   Response preview:', repoInfo.substring(0, 100) + '...\n');
        
        // Test 2: List issues
        console.log('2. Testing github_list_issues...');
        const issues = await gh.issues.github_list_issues({
            owner: 'crypto-ninja',
            repo: 'github-mcp-server',
            state: 'open',
            limit: 5,
            response_format: 'markdown'
        });
        console.log('   ✓ Success');
        console.log('   Response preview:', issues.substring(0, 100) + '...\n');
        
        // Test 3: Search code
        console.log('3. Testing github_search_code...');
        const searchResults = await gh.search.github_search_code({
            query: 'mcp.tool language:python repo:crypto-ninja/github-mcp-server',
            limit: 3,
            response_format: 'markdown'
        });
        console.log('   ✓ Success');
        console.log('   Response preview:', searchResults.substring(0, 100) + '...\n');
        
        console.log('✅ All tool calls successful!');
        
        // Cleanup
        await closeMCPClient();
        
    } catch (error) {
        console.error('❌ Tool call failed:', error);
        process.exit(1);
    }
}

testToolCalls();

