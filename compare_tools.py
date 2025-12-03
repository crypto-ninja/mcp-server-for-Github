import re

# Read both files
with open('github_mcp.py', 'r', encoding='utf-8') as f:
    py_content = f.read()

with open('deno_executor/tool-definitions.ts', 'r', encoding='utf-8') as f:
    ts_content = f.read()

# Extract tool names
py_tools = set(re.findall(r'name="(github_\w+)"', py_content))
ts_tools = set(re.findall(r'name: "(github_\w+)"', ts_content))

# Also check for github_license_info (no name= in decorator)
if 'github_license_info' in py_content and 'async def github_license_info' in py_content:
    py_tools.add('github_license_info')

print(f'Python GitHub tools: {len(py_tools)}')
print(f'TypeScript GitHub tools: {len(ts_tools)}')
print()

missing_from_ts = py_tools - ts_tools
extra_in_ts = ts_tools - py_tools

if missing_from_ts:
    print(f'❌ Missing from TypeScript ({len(missing_from_ts)}):')
    for tool in sorted(missing_from_ts):
        print(f'  - {tool}')

if extra_in_ts:
    print(f'⚠️  Extra in TypeScript ({len(extra_in_ts)}):')
    for tool in sorted(extra_in_ts):
        print(f'  - {tool}')

if not missing_from_ts and not extra_in_ts:
    print('✅ All tools match!')

