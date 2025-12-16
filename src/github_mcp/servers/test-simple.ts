// servers/test-simple.ts

import { initializeMCPClient, callMCPTool, closeMCPClient } from './client.js';

async function testSimple() {
    try {
        console.log('Testing simple tool call (no parameters)...\n');
        
        await initializeMCPClient();
        
        // Test license_info which takes no parameters
        console.log('Calling github_license_info...');
        const result = await callMCPTool('github_license_info', {});
        console.log('✓ Success!');
        console.log('Result preview:', result.substring(0, 300));
        
        await closeMCPClient();
        
    } catch (error) {
        console.error('❌ Error:', error);
        process.exit(1);
    }
}

testSimple();

