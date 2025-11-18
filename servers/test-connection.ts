// servers/test-connection.ts

import { initializeMCPClient, listAvailableTools, closeMCPClient } from './client.js';

async function testConnection() {
    try {
        console.log('Testing MCP Bridge connection...\n');
        
        // Initialize connection
        console.log('1. Initializing connection...');
        await initializeMCPClient();
        console.log('   ✓ Connected\n');
        
        // List tools
        console.log('2. Listing available tools...');
        const tools = await listAvailableTools();
        console.log(`   ✓ Found ${tools.length} tools\n`);
        
        console.log('Available tools:');
        tools.forEach((tool, i) => {
            console.log(`   ${i + 1}. ${tool}`);
        });
        
        // Cleanup
        console.log('\n3. Closing connection...');
        await closeMCPClient();
        console.log('   ✓ Closed\n');
        
        console.log('✅ All tests passed!');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
        process.exit(1);
    }
}

testConnection();

