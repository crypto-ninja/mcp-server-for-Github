/**
 * Code Validator for TypeScript Execution Security
 * 
 * Validates user-submitted TypeScript code before execution to prevent:
 * - Sandbox escape attempts
 * - Dangerous global access
 * - Prototype pollution
 * - Malicious patterns
 */

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

// Patterns that are ALWAYS blocked (security critical)
const BLOCKED_PATTERNS: Array<{ pattern: RegExp; reason: string }> = [
  // Direct eval and Function constructors
  { pattern: /\beval\s*\(/gi, reason: "eval() is not allowed" },
  { pattern: /\bnew\s+Function\s*\(/gi, reason: "new Function() is not allowed" },
  { pattern: /\bFunction\s*\(/gi, reason: "Function() constructor is not allowed" },
  
  // Dynamic code execution via setTimeout/setInterval with strings
  { pattern: /\bsetTimeout\s*\(\s*["'`]/gi, reason: "setTimeout with string argument is not allowed" },
  { pattern: /\bsetInterval\s*\(\s*["'`]/gi, reason: "setInterval with string argument is not allowed" },
  
  // Deno-specific dangerous APIs
  { pattern: /\bDeno\s*\.\s*run\b/gi, reason: "Deno.run() is not allowed" },
  { pattern: /\bDeno\s*\.\s*Command\b/gi, reason: "Deno.Command() is not allowed" },
  { pattern: /\bDeno\s*\.\s*exec\b/gi, reason: "Deno.exec() is not allowed" },
  { pattern: /\bDeno\s*\.\s*writeFile\b/gi, reason: "Deno.writeFile() is not allowed" },
  { pattern: /\bDeno\s*\.\s*writeTextFile\b/gi, reason: "Deno.writeTextFile() is not allowed" },
  { pattern: /\bDeno\s*\.\s*remove\b/gi, reason: "Deno.remove() is not allowed" },
  { pattern: /\bDeno\s*\.\s*rename\b/gi, reason: "Deno.rename() is not allowed" },
  { pattern: /\bDeno\s*\.\s*mkdir\b/gi, reason: "Deno.mkdir() is not allowed" },
  { pattern: /\bDeno\s*\.\s*chmod\b/gi, reason: "Deno.chmod() is not allowed" },
  { pattern: /\bDeno\s*\.\s*chown\b/gi, reason: "Deno.chown() is not allowed" },
  { pattern: /\bDeno\s*\.\s*link\b/gi, reason: "Deno.link() is not allowed" },
  { pattern: /\bDeno\s*\.\s*symlink\b/gi, reason: "Deno.symlink() is not allowed" },
  { pattern: /\bDeno\s*\.\s*truncate\b/gi, reason: "Deno.truncate() is not allowed" },
  { pattern: /\bDeno\s*\.\s*kill\b/gi, reason: "Deno.kill() is not allowed" },
  { pattern: /\bDeno\s*\.\s*exit\b/gi, reason: "Deno.exit() is not allowed" },
  { pattern: /\bDeno\s*\.\s*env\s*\.\s*set\b/gi, reason: "Deno.env.set() is not allowed" },
  { pattern: /\bDeno\s*\.\s*env\s*\.\s*delete\b/gi, reason: "Deno.env.delete() is not allowed" },
  
  // Prototype pollution attempts
  { pattern: /__proto__/gi, reason: "__proto__ access is not allowed" },
  { pattern: /\bconstructor\s*\.\s*prototype\b/gi, reason: "constructor.prototype access is not allowed" },
  { pattern: /Object\s*\.\s*setPrototypeOf\b/gi, reason: "Object.setPrototypeOf() is not allowed" },
  { pattern: /Object\s*\.\s*defineProperty\b/gi, reason: "Object.defineProperty() is not allowed (potential prototype pollution)" },
  { pattern: /Object\s*\.\s*defineProperties\b/gi, reason: "Object.defineProperties() is not allowed" },
  
  // Global object manipulation
  { pattern: /\bglobalThis\s*\[/gi, reason: "Dynamic globalThis access is not allowed" },
  { pattern: /\bwindow\s*\[/gi, reason: "Dynamic window access is not allowed" },
  { pattern: /\bglobal\s*\[/gi, reason: "Dynamic global access is not allowed" },
  
  // Process/system access
  { pattern: /\bprocess\s*\./gi, reason: "process object access is not allowed" },
  { pattern: /\brequire\s*\(/gi, reason: "require() is not allowed (use ES modules)" },
  
  // Network bypass attempts (outside our controlled fetch)
  { pattern: /\bWebSocket\b/gi, reason: "WebSocket is not allowed" },
  { pattern: /\bnew\s+Worker\b/gi, reason: "Web Workers are not allowed" },
  { pattern: /\bSharedArrayBuffer\b/gi, reason: "SharedArrayBuffer is not allowed" },
  
  // Import with dynamic strings (potential for code injection)
  { pattern: /import\s*\(\s*[^"'`\s]/gi, reason: "Dynamic import() with variables is not allowed" },
];

// Patterns that generate warnings but are allowed
const WARNING_PATTERNS: Array<{ pattern: RegExp; reason: string }> = [
  { pattern: /\bJSON\s*\.\s*parse\s*\(/gi, reason: "JSON.parse() - ensure input is trusted" },
  { pattern: /\bfetch\s*\(/gi, reason: "fetch() - only GitHub API calls are permitted" },
  { pattern: /\bDeno\s*\.\s*readFile\b/gi, reason: "Deno.readFile() - read access may be restricted" },
  { pattern: /\bDeno\s*\.\s*readTextFile\b/gi, reason: "Deno.readTextFile() - read access may be restricted" },
];

// Maximum code length (prevent DoS via huge code blocks)
const MAX_CODE_LENGTH = 100000; // 100KB

// Maximum nesting depth for brackets/braces (prevent stack overflow)
const MAX_NESTING_DEPTH = 50;

/**
 * Validates TypeScript code for security issues before execution
 */
export function validateCode(code: string): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check code length
  if (code.length > MAX_CODE_LENGTH) {
    errors.push(`Code exceeds maximum length of ${MAX_CODE_LENGTH} characters (got ${code.length})`);
    return { valid: false, errors, warnings };
  }

  // Check for empty code
  if (!code.trim()) {
    errors.push("Code cannot be empty");
    return { valid: false, errors, warnings };
  }

  // Check blocked patterns
  for (const { pattern, reason } of BLOCKED_PATTERNS) {
    // Reset regex lastIndex for global patterns
    pattern.lastIndex = 0;
    if (pattern.test(code)) {
      errors.push(`Security violation: ${reason}`);
    }
  }

  // Check warning patterns
  for (const { pattern, reason } of WARNING_PATTERNS) {
    pattern.lastIndex = 0;
    if (pattern.test(code)) {
      warnings.push(`Warning: ${reason}`);
    }
  }

  // Check nesting depth
  const nestingError = checkNestingDepth(code);
  if (nestingError) {
    errors.push(nestingError);
  }

  // Check for suspicious string concatenation that might build dangerous code
  if (detectCodeConstruction(code)) {
    warnings.push("Warning: Detected string concatenation patterns that may be building code dynamically");
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Check for excessive nesting depth (potential DoS or obfuscation)
 */
function checkNestingDepth(code: string): string | null {
  let depth = 0;
  let maxDepth = 0;
  
  for (const char of code) {
    if (char === '{' || char === '(' || char === '[') {
      depth++;
      maxDepth = Math.max(maxDepth, depth);
    } else if (char === '}' || char === ')' || char === ']') {
      depth--;
    }
    
    if (maxDepth > MAX_NESTING_DEPTH) {
      return `Code exceeds maximum nesting depth of ${MAX_NESTING_DEPTH}`;
    }
  }
  
  if (depth !== 0) {
    return "Unbalanced brackets/braces detected";
  }
  
  return null;
}

/**
 * Detect patterns that suggest dynamic code construction
 */
function detectCodeConstruction(code: string): boolean {
  // Patterns that suggest building code as strings
  const suspiciousPatterns = [
    /["'`]\s*\+\s*["'`].*\+\s*["'`]/g,  // Multiple string concatenations
    /\.join\s*\(\s*["'`]["'`]\s*\)/g,    // Array joining to build strings
    /String\s*\.\s*fromCharCode/gi,       // Building strings from char codes
    /\\x[0-9a-f]{2}/gi,                   // Hex escape sequences (potential obfuscation)
    /\\u[0-9a-f]{4}/gi,                   // Unicode escapes (if excessive)
  ];
  
  let suspiciousCount = 0;
  for (const pattern of suspiciousPatterns) {
    const matches = code.match(pattern);
    if (matches) {
      suspiciousCount += matches.length;
    }
  }
  
  // Only flag if there are multiple suspicious patterns
  return suspiciousCount >= 3;
}

/**
 * Sanitize error messages to prevent information leakage
 */
export function sanitizeErrorMessage(error: string): string {
  // Remove file paths that might leak server structure
  let sanitized = error.replace(/\/[^\s:]+\//g, '/[path]/');
  
  // Remove potential stack traces with sensitive info
  sanitized = sanitized.replace(/at\s+[^\n]+/g, 'at [redacted]');
  
  return sanitized;
}

