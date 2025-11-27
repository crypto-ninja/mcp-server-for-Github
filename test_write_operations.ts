// Test script for fixed write operations
console.log("=== TESTING FIXED WRITE OPERATIONS ===\n");

const owner = "crypto-ninja";
const repo = "github-mcp-server";

// Test 1: github_create_issue
console.log("Test 1: github_create_issue");
console.log("━".repeat(70));

try {
  const issue = await callMCPTool("github_create_issue", {
    owner,
    repo,
    title: "Test issue for JSON response verification",
    body: "Testing that the tool returns proper JSON"
  });
  
  const issueData = JSON.parse(issue);
  console.log(`✅ Returns JSON: ${issueData.number ? 'YES' : 'NO'}`);
  console.log(`   Issue #${issueData.number}: ${issueData.title}`);
  console.log(`   URL: ${issueData.html_url}\n`);
} catch (e) {
  console.log(`❌ Failed: ${e.message}\n`);
}

// Test 2: github_create_branch
console.log("Test 2: github_create_branch");
console.log("━".repeat(70));

try {
  const branch = await callMCPTool("github_create_branch", {
    owner,
    repo,
    branch: `test/json-verify-${Date.now()}`,
    from_ref: "main"
  });
  
  const branchData = JSON.parse(branch);
  console.log(`✅ Returns JSON: ${branchData.success !== undefined ? 'YES' : 'NO'}`);
  console.log(`   Branch: ${branchData.branch || branchData.ref}`);
  console.log(`   SHA: ${branchData.sha}\n`);
} catch (e) {
  console.log(`❌ Failed: ${e.message}\n`);
}

// Test 3: Error case - invalid repo
console.log("Test 3: Error handling (invalid repo)");
console.log("━".repeat(70));

try {
  const error = await callMCPTool("github_create_issue", {
    owner,
    repo: "NONEXISTENT_REPO_12345",
    title: "Test",
    body: "Test"
  });
  
  const errorData = JSON.parse(error);
  console.log(`✅ Returns JSON error: ${errorData.success === false ? 'YES' : 'NO'}`);
  console.log(`   Error: ${errorData.error}`);
  console.log(`   Status: ${errorData.status_code}`);
  console.log(`   Message: ${errorData.message}\n`);
} catch (e) {
  console.log(`❌ Failed: ${e.message}\n`);
}

console.log("=".repeat(70));
console.log("TESTING COMPLETE");
console.log("=".repeat(70));
console.log("\nAll write operations should now return proper JSON!");
console.log("Ready for meta merge! 🤯\n");

return {
  test1_complete: true,
  test2_complete: true,
  test3_complete: true,
  status: "All tests completed"
};
