# Deno Executor

Runtime executor for GitHub MCP Server's code-first execution feature.

## Files

- `mod.ts` - Main entry point for code execution
- `test_runtime.ts` - Test suite for runtime functionality

## How It Works

1. Claude writes TypeScript code
2. Python MCP server receives code via `execute_code` tool
3. Deno runtime spawns and executes code
4. Code calls GitHub MCP tools via `callMCPTool()`
5. Results return to Claude

## Testing

```bash
# Test runtime directly
cd deno_executor
deno run --allow-read --allow-run --allow-env --allow-net test_runtime.ts

# Test Python integration
cd ..
python test_deno_runtime.py
```

## Security

- Runs in isolated Deno sandbox
- Limited permissions (read, run, env, net)
- 60-second execution timeout
- No file system write access

## Development

When updating:

1. Test with `test_runtime.ts` first
2. Test Python integration
3. Test in Claude Desktop

## Troubleshooting

See [CODE_EXECUTION_GUIDE.md](../CODE_EXECUTION_GUIDE.md#troubleshooting)

