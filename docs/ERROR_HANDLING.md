# Error Handling Guide

## Response Format

All code execution responses use a standardized format for consistent error handling.

### Success Response

```json
{
  "error": false,
  "data": {
    // Result data here - whatever your code returns
  }
}
```

### Error Response

```json
{
  "error": true,
  "message": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {
    // Optional additional context
    "stack": "Stack trace (if available)",
    "validationErrors": ["Error 1", "Error 2"]
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Code failed validation (blocked patterns, too long, etc.) |
| `CODE_TOO_LONG` | Code exceeds maximum length (100KB) |
| `CODE_EMPTY` | Empty code submitted |
| `UNBALANCED_BRACKETS` | Mismatched brackets/braces detected |
| `SECURITY_VIOLATION` | Code contains blocked security patterns |
| `BLOCKED_PATTERN` | Specific dangerous pattern detected |
| `EXECUTION_ERROR` | Runtime error during code execution |
| `TIMEOUT` | Code execution exceeded time limit (60s) |
| `TOOL_ERROR` | Error calling an MCP tool |
| `TOOL_NOT_FOUND` | Requested tool does not exist |
| `INVALID_PARAMS` | Invalid parameters passed to tool |
| `MCP_CONNECTION_ERROR` | Failed to connect to MCP server |
| `MCP_TIMEOUT` | MCP operation timed out |
| `NO_OUTPUT` | No output from Deno execution |
| `NO_JSON_OUTPUT` | Output was not valid JSON |
| `PARSE_ERROR` | Error parsing execution output |
| `EXECUTION_FAILED` | Execution failed with non-zero exit code |
| `DENO_NOT_FOUND` | Deno runtime not found |

## Handling Errors in TypeScript

### Basic Error Handling

```typescript
const result = await callMCPTool("github_get_repo_info", {
  owner: "nonexistent",
  repo: "repo"
});

// Check if result is an error response
if (typeof result === 'object' && result !== null && result.error === true) {
  console.error(`Error: ${result.message}`);
  if (result.code) {
    console.error(`Error code: ${result.code}`);
  }
  if (result.details) {
    console.error(`Details:`, result.details);
  }
} else {
  // Handle success
  console.log(result);
}
```

### Error Handling with Try/Catch

```typescript
try {
  const repoInfo = await callMCPTool("github_get_repo_info", {
    owner: "facebook",
    repo: "react"
  });
  
  // If callMCPTool throws, it means the tool call itself failed
  // The result might still be an error response object
  if (typeof repoInfo === 'object' && repoInfo.error) {
    throw new Error(repoInfo.message);
  }
  
  return { data: repoInfo };
} catch (error) {
  // Handle both thrown errors and error response objects
  return {
    error: true,
    message: error instanceof Error ? error.message : String(error)
  };
}
```

### Programmatic Error Handling by Code

```typescript
const result = await callMCPTool("github_create_issue", {
  owner: "myorg",
  repo: "myrepo",
  title: "Test"
});

if (result.error) {
  switch (result.code) {
    case "TOOL_NOT_FOUND":
      console.error("Tool does not exist");
      break;
    case "INVALID_PARAMS":
      console.error("Invalid parameters:", result.details);
      break;
    case "TOOL_ERROR":
      console.error("Tool execution failed:", result.message);
      break;
    default:
      console.error("Unknown error:", result.message);
  }
}
```

## Validation Errors

When code validation fails, the error response includes validation details:

```json
{
  "error": true,
  "message": "Code validation failed: Security violation: eval() is not allowed",
  "code": "VALIDATION_ERROR",
  "details": {
    "validationErrors": [
      "Security violation: eval() is not allowed",
      "Security violation: Deno.run() is not allowed"
    ]
  }
}
```

## Execution Errors

When code execution fails, the error response includes stack traces:

```json
{
  "error": true,
  "message": "ReferenceError: undefinedVariable is not defined",
  "code": "EXECUTION_ERROR",
  "details": {
    "stack": "ReferenceError: undefinedVariable is not defined\n    at ..."
  }
}
```

## Best Practices

1. **Always check for errors**: Don't assume execution succeeded
2. **Use error codes**: Check `result.code` for programmatic handling
3. **Log details**: Include `result.details` in error logs for debugging
4. **Handle validation errors separately**: They indicate code issues, not runtime problems
5. **Provide user-friendly messages**: Use `result.message` for user-facing errors

## Example: Complete Error Handling

```typescript
async function safeToolCall(toolName: string, params: any) {
  try {
    const result = await callMCPTool(toolName, params);
    
    // Check for error response
    if (typeof result === 'object' && result !== null && result.error === true) {
      // Handle different error types
      if (result.code === "TOOL_NOT_FOUND") {
        throw new Error(`Tool "${toolName}" not found`);
      } else if (result.code === "INVALID_PARAMS") {
        throw new Error(`Invalid parameters: ${result.message}`);
      } else {
        throw new Error(result.message);
      }
    }
    
    return result;
  } catch (error) {
    // Handle thrown errors (network, connection, etc.)
    console.error(`Tool call failed: ${error.message}`);
    throw error;
  }
}

// Usage
try {
  const repoInfo = await safeToolCall("github_get_repo_info", {
    owner: "facebook",
    repo: "react"
  });
  console.log("Success:", repoInfo);
} catch (error) {
  console.error("Failed:", error.message);
}
```

