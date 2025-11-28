// Debug test for github_create_pull_request
console.log("=== Testing github_create_pull_request ===\n");

const owner = "crypto-ninja";
const repo = "github-mcp-server";

// Test 1: Try with invalid branch (should fail)
console.log("Test 1: Creating PR with invalid branch (should fail)...\n");
try {
  const badPR = await callMCPTool("github_create_pull_request", {
    owner,
    repo,
    title: "Test PR",
    head: "NONEXISTENT_BRANCH_12345",
    base: "main",
    body: "This should fail"
  });
  
  console.log("Response type:", typeof badPR);
  console.log("Response length:", badPR.length);
  console.log("\nFull response:");
  console.log(badPR);
  console.log("\n---\n");
  
  // Try to parse as JSON
  try {
    const parsed = JSON.parse(badPR);
    console.log("Parsed as JSON:", JSON.stringify(parsed, null, 2));
    if (parsed.success === true) {
      console.log("❌ FALSE POSITIVE: Returned success:true but should have failed!");
    }
  } catch {
    console.log("Not valid JSON (expected for error messages)");
  }
} catch (error) {
  console.error("Exception thrown:", error);
}

// Test 2: Try with valid branch (should succeed)
console.log("\nTest 2: Creating PR with valid branch (should succeed)...\n");
try {
  const goodPR = await callMCPTool("github_create_pull_request", {
    owner,
    repo,
    title: "Test PR - Debug",
    head: "feature/branch-management-tools",
    base: "main",
    body: "Testing PR creation"
  });
  
  console.log("Response type:", typeof goodPR);
  console.log("Response length:", goodPR.length);
  console.log("\nFull response:");
  console.log(goodPR);
  console.log("\n---\n");
  
  // Try to parse as JSON
  try {
    const parsed = JSON.parse(goodPR);
    console.log("Parsed as JSON:", JSON.stringify(parsed, null, 2));
  } catch {
    console.log("Not valid JSON (formatted string response)");
    // Try to extract PR number
    const match = goodPR.match(/#(\d+)/);
    if (match) {
      console.log("✅ Extracted PR number:", match[1]);
    } else {
      console.log("❌ Could not extract PR number");
    }
  }
} catch (error) {
  console.error("Exception thrown:", error);
}

return {
  test1_complete: true,
  test2_complete: true
};

