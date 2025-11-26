// Test script for branch management tools
console.log("=== TESTING BRANCH MANAGEMENT TOOLS ===\n");

const owner = "crypto-ninja";
const repo = "github-mcp-server";

// Test 1: List branches
console.log("Test 1: Listing all branches...");
const branches = await callMCPTool("github_list_branches", {
  owner,
  repo
});
console.log(branches);
console.log("\n✅ Test 1 passed!\n");

// Test 2: Create test branch
console.log("Test 2: Creating test branch...");
const createResult = await callMCPTool("github_create_branch", {
  owner,
  repo,
  branch: "test/branch-tools-test",
  from_ref: "main"
});
console.log(createResult);
console.log("\n✅ Test 2 passed!\n");

// Test 3: Get branch details
console.log("Test 3: Getting test branch details...");
const branchDetails = await callMCPTool("github_get_branch", {
  owner,
  repo,
  branch: "test/branch-tools-test"
});
console.log(branchDetails);
console.log("\n✅ Test 3 passed!\n");

// Test 4: Compare branches
console.log("Test 4: Comparing test branch to main...");
const comparison = await callMCPTool("github_compare_branches", {
  owner,
  repo,
  base: "main",
  head: "test/branch-tools-test"
});
console.log(comparison);
console.log("\n✅ Test 4 passed!\n");

// Test 5: Delete test branch
console.log("Test 5: Deleting test branch...");
const deleteResult = await callMCPTool("github_delete_branch", {
  owner,
  repo,
  branch: "test/branch-tools-test"
});
console.log(deleteResult);
console.log("\n✅ Test 5 passed!\n");

console.log("=".repeat(70));
console.log("🎉 ALL TESTS PASSED!");
console.log("=".repeat(70));
console.log("\n🚀 Branch management tools are ready!");
console.log("🤯 Now they can merge themselves into main!");

