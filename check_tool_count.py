import re

with open('deno_executor/tool-definitions.ts', 'r', encoding='utf-8') as f:
    content = f.read()

tools = re.findall(r'name: "(github_\w+)"', content)
print(f'Total GitHub tools in TypeScript: {len(tools)}')
branch_tools = [t for t in tools if 'branch' in t]
print(f'Branch tools found: {len(branch_tools)}')
if branch_tools:
    print('Branch tools:', branch_tools)
else:
    print('❌ Branch tools are MISSING from TypeScript definitions!')

