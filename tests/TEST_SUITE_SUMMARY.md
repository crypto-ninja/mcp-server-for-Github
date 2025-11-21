# Comprehensive Tool Testing Suite

## Overview

This test suite validates all aspects of the GitHub MCP Server's tool system, ensuring consistency between TypeScript client and Python server, proper parameter validation, and preventing regressions.

## Test Files

### Phase 1: Schema Validation (`test_tool_schemas.py`)
- **Purpose**: Validate tool parameters match their Pydantic schemas
- **Tests**:
  - All tools are registered
  - `response_format` parameter consistency
  - Write operations don't have `response_format`
  - Tools reject extra parameters
  - `response_format` enum values are correct

### Phase 2: Integration Tests (`test_tool_integration.py`)
- **Purpose**: Test tools working together
- **Tests**:
  - Tool chaining (search then read, create then update)
  - Execute code integration with tool calls
  - Data flow between tools
  - Error propagation

### Phase 3: Contract Tests (`test_contracts.py`)
- **Purpose**: Ensure TypeScript client and Python server agree
- **Tests**:
  - TypeScript client expectations match Python server
  - Response format parsing
  - Tool schemas match between client and server

### Phase 4: Regression Tests (`test_regressions.py`)
- **Purpose**: Prevent previously fixed bugs from returning
- **Tests**:
  - `response_format` only on supported tools
  - GitHub auth in `execute_code`
  - JSON error responses
  - Parameter validation

### Phase 5: Tool Discovery (`discover_tool_issues.py`)
- **Purpose**: Automatically discover potential issues
- **Checks**:
  - Tools in TypeScript list that don't support `response_format`
  - Write operations with `response_format`
  - Missing tools in TypeScript list

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Phase
```bash
# Schema validation
pytest tests/test_tool_schemas.py -v

# Integration tests
pytest tests/test_tool_integration.py -v

# Contract tests
pytest tests/test_contracts.py -v

# Regression tests
pytest tests/test_regressions.py -v
```

### Run Discovery Script
```bash
python tests/discover_tool_issues.py
```

### Run with Coverage
```bash
pip install pytest pytest-cov
pytest --cov=github_mcp --cov=auth --cov-report=html --cov-report=term
```

## Current Issues Found

The discovery script identified 2 issues:

1. **`github_read_file_chunk`** - In TypeScript list but doesn't support `response_format`
2. **`repo_read_file_chunk`** - In TypeScript list but doesn't support `response_format`

### Recommended Fix

Remove these tools from `READ_TOOLS_WITH_JSON_SUPPORT` in `servers/client-deno.ts` since they don't support the `response_format` parameter.

## Coverage Goals

- **Current**: ~25%
- **Phase 1 Target**: 40% (schema validation)
- **Phase 2 Target**: 55% (integration tests)
- **Phase 3 Target**: 70% (contract tests)
- **Phase 4 Target**: 80%+ (regression + edge cases)

## What These Tests Catch

✅ **Parameter mismatches** (like `response_format` on wrong tools)  
✅ **Type inconsistencies** (string vs object vs JSON string)  
✅ **Error handling bugs** (inconsistent error formats)  
✅ **Integration issues** (tools not working together)  
✅ **Regression bugs** (old issues coming back)  
✅ **Documentation errors** (code doesn't match docs)

## Next Steps

1. Fix the 2 issues found by discovery script
2. Run full test suite
3. Add CI checks for test coverage
4. Add tests for edge cases
5. Add performance tests for large responses

