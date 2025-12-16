/**
 * Standard error codes for the GitHub MCP Server
 * Used for programmatic error handling and debugging
 */

export const ErrorCodes = {
  // Validation errors
  VALIDATION_ERROR: "VALIDATION_ERROR",
  CODE_TOO_LONG: "CODE_TOO_LONG",
  CODE_EMPTY: "CODE_EMPTY",
  UNBALANCED_BRACKETS: "UNBALANCED_BRACKETS",
  
  // Security errors
  SECURITY_VIOLATION: "SECURITY_VIOLATION",
  BLOCKED_PATTERN: "BLOCKED_PATTERN",
  
  // Execution errors
  EXECUTION_ERROR: "EXECUTION_ERROR",
  TIMEOUT: "TIMEOUT",
  
  // Tool errors
  TOOL_ERROR: "TOOL_ERROR",
  TOOL_NOT_FOUND: "TOOL_NOT_FOUND",
  INVALID_PARAMS: "INVALID_PARAMS",
  
  // MCP errors
  MCP_CONNECTION_ERROR: "MCP_CONNECTION_ERROR",
  MCP_TIMEOUT: "MCP_TIMEOUT",
} as const;

export type ErrorCode = typeof ErrorCodes[keyof typeof ErrorCodes];

