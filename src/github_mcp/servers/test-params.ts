// servers/test-params.ts

import { initializeMCPClient, callMCPTool, closeMCPClient } from './client.js';

async function testParams() {
    try {
        console.log('Testing tool with parameters...\n');
        
        await initializeMCPClient();
        
        // Test with explicit params structure
        console.log('Test 1: Direct params...');
        try {
            const result1 = await callMCPTool('github_get_repo_info', {
                owner: 'crypto-ninja',
                repo: 'github-mcp-server',
                response_format: 'markdown'
            });
            console.log('✓ Success!');
            console.log('Result preview:', result1.substring(0, 200));
        } catch (e: any) {
            console.log('✗ Failed:', e.message?.substring(0, 200));
        }
        
        console.log('\nTest 2: Wrapped in params...');
        try {
            const result2 = await callMCPTool('github_get_repo_info', {
                params: {
                    owner: 'crypto-ninja',
                    repo: 'github-mcp-server',
                    response_format: 'markdown'
                }
            });
            console.log('✓ Success!');
            console.log('Result preview:', result2.substring(0, 200));
        } catch (e: any) {
            console.log('✗ Failed:', e.message?.substring(0, 200));
        }
        
        await closeMCPClient();
        
    } catch (error) {
        console.error('❌ Error:', error);
        process.exit(1);
    }
}

testParams();

