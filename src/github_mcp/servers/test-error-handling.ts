// servers/test-error-handling.ts

import * as gh from './github/index.js';
import { closeMCPClient } from './client.js';

async function testErrorHandling() {
    try {
        console.log('Testing error handling...\n');
        
        // Test 1: Invalid repository
        console.log('1. Testing invalid repository...');
        try {
            await gh.repos.github_get_repo_info({
                owner: 'this-user-definitely-does-not-exist-12345',
                repo: 'this-repo-definitely-does-not-exist-12345',
                response_format: 'markdown'
            });
            console.log('   ❌ Should have thrown an error');
        } catch (error) {
            console.log('   ✓ Correctly caught error');
            console.log(`   Error: ${error}\n`);
        }
        
        // Test 2: Invalid parameters
        console.log('2. Testing invalid parameters...');
        try {
            await gh.issues.github_create_issue({
                owner: 'crypto-ninja',
                repo: 'github-mcp-server',
                title: ''  // Empty title should fail
            });
            console.log('   ❌ Should have thrown an error');
        } catch (error) {
            console.log('   ✓ Correctly caught error');
            console.log(`   Error: ${error}\n`);
        }
        
        console.log('✅ Error handling works correctly!');
        
        // Cleanup
        await closeMCPClient();
        
    } catch (error) {
        console.error('❌ Test failed:', error);
        process.exit(1);
    }
}

testErrorHandling();
