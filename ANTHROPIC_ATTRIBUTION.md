# Attribution to Anthropic Research

This project implements the **code-first MCP architecture** described in Anthropic's research blog post:

**["Code execution with MCP: building more efficient AI agents"](https://www.anthropic.com/engineering/code-execution-with-mcp)**

**Authors:** Adam Jones, Conor Kelly  
**Research Team:** Jeremy Fox, Jerome Swannack, Stuart Ritchie, Molly Vorwerck, Matt Samuels, Maggie Vo  
**Published:** November 2025

## Our Implementation

We followed their recommended architecture:

- File tree structure for tool discovery
- TypeScript wrappers calling MCP tools via `callMCPTool()`
- On-demand tool loading instead of upfront definitions
- Secure Deno runtime for code execution

## Results

Their blog predicted: **98.7% token reduction** (150,000 → 2,000 tokens)  
Our production results: **98% token reduction** (70,000 → 800 tokens)

This validates their research in a real-world production environment.

## Contribution

As they encouraged: *"If you implement this approach, we encourage you to share your findings with the MCP community."*

We shared our findings: (https://github.com/orgs/modelcontextprotocol/discussions/629)

Thank you to the Anthropic team for documenting this revolutionary pattern!

