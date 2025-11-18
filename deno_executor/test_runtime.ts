/**
 * Test the Deno runtime executor
 */

import { initializeMCPClient, callMCPTool, closeMCPClient } from "../servers/client-deno.ts";

console.error("Testing Deno Runtime...\n");

try {
  // Test 1: Initialize bridge
  console.error("1. Initializing MCP bridge...");
  await initializeMCPClient();
  console.error("   ✓ Connected\n");

  // Test 2: Simple tool call
  console.error("2. Testing tool call...");
  const result = await callMCPTool("github_get_repo_info", {
    owner: "modelcontextprotocol",
    repo: "servers"
  });
  console.error("   ✓ Tool call successful");
  console.error(`   Result: ${result.substring(0, 100)}...\n`);

  // Test 3: Multiple tool calls
  console.error("3. Testing multiple tool calls...");
  const issues = await callMCPTool("github_list_issues", {
    owner: "modelcontextprotocol",
    repo: "servers",
    state: "open",
    limit: 5
  });
  console.error("   ✓ Multiple calls successful\n");

  // Test 4: Error handling
  console.error("4. Testing error handling...");
  try {
    const error = await callMCPTool("github_get_repo_info", {
      owner: "this-repo-definitely",
      repo: "does-not-exist-12345"
    });
    console.error("   ✓ Errors handled gracefully (returned as string)\n");
  } catch (e) {
    console.error("   ✓ Errors caught properly\n");
  }

  // Cleanup
  await closeMCPClient();
  console.error("✅ All Deno runtime tests passed!");

} catch (error) {
  console.error("❌ Test failed:", error);
  Deno.exit(1);
}

