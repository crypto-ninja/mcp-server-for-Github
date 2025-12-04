## GitHub MCP Server Architecture Analysis (v2.4.0)

**Project:** GitHub MCP Server (code-first reference implementation)  
**Version:** 2.4.0  
**Tools:** 62 total (1 exposed MCP tool, 61 internal GitHub/workspace tools)

---

## 1. Project Structure

### 1.1 Directory Layout & Organization

- **Root**
  - `github_mcp.py` – Main MCP server implementation in Python, defines all tools and the `execute_code` entrypoint.
  - `auth/` – Authentication helpers for GitHub App and PAT, including token caching and dual-auth logic.
    - `github_app.py` – GitHub App + PAT dual-auth implementation.
  - `deno_executor/` – TypeScript-based code execution engine used by the `execute_code` MCP tool.
    - `mod.ts` – Entrypoint for Deno execution; hosts the code-first execution environment.
    - `tool-definitions.ts` – TypeScript catalog of all 62 tools (schema for AI use).
  - `servers/` – Deno-side MCP client logic and lower-level GitHub client abstractions for the executor.
  - `src/github_mcp/` – CLI utilities and runtime helpers (e.g., `cli.py`, `deno_runtime.py`).
  - `tests/` – Comprehensive test suite (Python) validating tools, contracts, auth, and executor integration.
  - `.github/workflows/ci.yml` – CI pipeline (lint, type-check, security, tests, coverage).
  - `pyproject.toml` / `requirements.txt` – Packaging and Python dependencies.
  - `README.md` and additional docs – Human-facing documentation, architecture notes, auth guides, testing docs.

### 1.2 Key Files & Roles

- **`github_mcp.py`**
  - Initializes `FastMCP("github_mcp")` server.
  - Loads environment (`.env`) and validates Deno availability at startup.
  - Defines `CODE_FIRST_MODE` and conditionally registers tools via a `conditional_tool` decorator.
  - Implements all GitHub-related tools (repo, issues, PRs, workflows, releases, search, workspace tools, licensing) using Pydantic models.
  - Provides shared utilities: `_get_auth_token_fallback`, `_make_github_request`, `_handle_api_error`, formatting helpers, workspace path validation, etc.
  - Exposes the `execute_code` MCP tool which shells out to Deno (`deno_executor/mod.ts`).

- **`auth/github_app.py`**
  - `GitHubAppAuth` class: generates JWTs, fetches & caches installation tokens, and provides auth headers.
  - `get_installation_token_from_env()` – reads GitHub App config from env vars and returns installation token.
  - `get_auth_token()` – central dual-auth resolver: chooses GitHub App vs PAT based on config and `GITHUB_AUTH_MODE`.
  - `verify_installation_access()` – optional check that installation can access a given repo (diagnostics).
  - Global `_app_auth` instance provides process-wide token caching across requests.

- **`deno_executor/mod.ts`**
  - Deno entrypoint for executing user TypeScript code.
  - Imports `initializeMCPClient`, `callMCPTool`, `closeMCPClient` from `servers/client-deno.ts`.
  - Imports `GITHUB_TOOLS` and helpers from `deno_executor/tool-definitions.ts`.
  - Exposes AI-facing helpers inside the execution context:
    - `listAvailableTools()` – returns categorized catalog of all tools.
    - `searchTools(keyword)` – relevance-ranked search over tool names, descriptions, categories, parameters.
    - `getToolInfo(toolName)` – returns full metadata + usage hints for a single tool.
    - `getToolsInCategory(category)` – returns tools in a category.
    - `callMCPTool(name, params)` – calls Python-side MCP tools via the MCP bridge (`client-deno.ts`).
  - `executeUserCode(code)` – core executor that:
    - Initializes MCP client.
    - Constructs a new `Function` injecting the helpers.
    - Runs user-provided TypeScript asynchronously.
    - Returns `{ success: true, result }` or `{ success: false, error, stack }` and always prints JSON to stdout.
  - `import.meta.main` block:
    - Reads code from stdin (with timeout fallback to `Deno.args[0]`).
    - Calls `executeUserCode` and prints JSON result.

- **`deno_executor/tool-definitions.ts`**
  - TypeScript `ToolDefinition` / `ToolParameter` interfaces.
  - `GITHUB_TOOLS`: array of 61 tools, each with name, category, description, parameters, return description, and TypeScript usage example.
  - Helper functions `getToolsByCategory` and `getCategories` for discovery.
  - Includes the `execute_code` tool definition itself as a first-class tool in the catalog.

- **`README.md`**
  - High-level positioning, changelog excerpts, and code-first architecture explanation.
  - Explains code-first vs traditional MCP, token savings, and tool discovery APIs.
  - Documents dual authentication (GitHub App + PAT) and why PAT is required for release operations.
  - Describes testing philosophy, self-referential "dogfooding", and roadmap.

- **`tests/`**
  - `test_tool_schemas.py` – Pydantic schema validation and tool registration correctness.
  - `test_tool_integration.py` – higher-level workflows and tool chaining.
  - `test_contracts.py` – TS↔Python contract tests (schema, response format alignment).
  - `test_execute_code_mcp.py`, `test_execute_code.py`, `test_deno_runtime.py` – validate Deno executor, MCP bridge, error handling.
  - `test_auth.py` – GitHub App / PAT dual-auth logic, headers, caching.
  - `test_individual_tools.py`, `test_write_operations_auth.py`, `test_write_operations_integration.py` – per-tool and write-path tests.
  - `test_regressions.py` – regression coverage.
  - Guides/summary: `TEST_SUITE_GUIDE.md`, `TEST_SUITE_SUMMARY.md`, `INTEGRATION_TEST_REPORT.md` etc.

---

## 2. Core Architecture

### 2.1 Code-First MCP Approach

- **Traditional MCP**
  - Client loads 40+ tool definitions directly into model context.
  - Tool schemas consume ~70,000 tokens every session.
  - Tool discovery is static: the model must "see" all tool definitions ahead of time.

- **This Project's Code-First Design**
  - MCP client sees **exactly one** tool: **`execute_code`**.
  - All other tools (46 GitHub/workspace tools) are invoked **dynamically** by user-provided TypeScript code.
  - TypeScript code runs in Deno, using the MCP bridge to call back into Python tools as needed.
  - Tool schemas are not injected into the LLM context; instead, they are available **inside** the execution environment via discovery functions.
  - Result: ~800 tokens vs ~70,000 → **≈98% token reduction**.

### 2.2 High-Level Flow: User Request → Tool Execution → Response

1. **MCP Client** (Cursor, Claude Desktop, etc.)
   - Exposes a single server tool: `execute_code`.
   - The user (or AI agent) passes TypeScript source code as the `code` parameter.

2. **Python MCP Server (`github_mcp.py`)**
   - Registered `execute_code` MCP tool receives the `code` string.
   - Spawns Deno (via `deno` CLI) running `deno_executor/mod.ts`.
   - Passes the code string via stdin (safer on Windows) or args fallback.

3. **Deno Executor (`deno_executor/mod.ts`)**
   - Uses `initializeMCPClient` from `servers/client-deno.ts` to establish an MCP-client connection back to the Python server process.
   - Creates an execution sandbox via `new Function("callMCPTool", "listAvailableTools", ...)` which returns an async IIFE.
   - Executes user code with injected helpers:
     - `callMCPTool` – bridging to Python-registered tools.
     - `listAvailableTools`, `searchTools`, `getToolInfo`, `getToolsInCategory` – discovery APIs using `GITHUB_TOOLS` from `tool-definitions.ts`.
   - Collects the `result` (whatever the user returns) and wraps it in `{ success: true, result }`.
   - On error, catches and ensures a **JSON** error object is printed to stdout (not just stderr).
   - Ensures MCP client is closed gracefully in both success and failure paths.

4. **Python MCP Server**
   - Receives Deno subprocess's JSON on stdout.
   - Maps this to the MCP tool result payload for `execute_code`.
   - Returns the JSON result to the MCP client.

5. **MCP Client / LLM**
   - Receives a JSON object describing success/error and any nested tool call results.
   - The LLM can then use that JSON to generate natural language responses or additional tool calls.

### 2.3 Deno TypeScript Executor ↔ Python Integration

- **Bridge Design**
  - `servers/client-deno.ts` (not detailed here, but implied by imports) is a Deno-side MCP client that can call any Python MCP tool by name.
  - All GitHub operations (e.g. `github_create_issue`, `github_list_pull_requests`, etc.) are defined in Python in `github_mcp.py` and registered with `FastMCP`.
  - Deno invokes them through `callMCPTool(toolName, params)` which sends an MCP tool call over the established connection.

- **Execution Context**
  - The user's TypeScript has full access to:
    - **Tool discovery** (`listAvailableTools`, `searchTools`, `getToolInfo`, `getToolsInCategory`).
    - **Tool invocation** (`callMCPTool`).
    - Standard JS/TS logic (loops, conditionals, try/catch, composition).
  - This enables **multi-step workflows** in a single MCP call:
    - Example: read repo info → search issues → create a PR → update an issue → create a release.

### 2.4 Relationship Between `execute_code` and the Tool Set

- **Total Tools**: 62
  - 1 exposed to MCP clients: `execute_code`.
  - 61 internal GitHub/workspace tools (e.g. repo management, issues, PRs, files, search, workspace operations, licensing, gists, labels, stargazers, user context).
- **Public MCP Surface**
  - When `CODE_FIRST_MODE=true` (default), only `execute_code` is registered with MCP.
  - In **internal mode** (`CODE_FIRST_MODE=false`), all tools are registered: used by Deno and for internal tests/diagnostics.
- **Executor Role**
  - `execute_code` is the **only** gateway; every GitHub operation is reachable **only through code**.
  - AI agents are expected to:
    - Discover tools at runtime.
    - Compose them into workflows.
    - Handle errors and branching within their TypeScript code.

---

## 3. Authentication System

### 3.1 GitHub App Authentication (Advanced, 15k req/hour)

- Implemented in `auth/github_app.py`:
  - `GitHubAppAuth` maintains:
    - `_token` – current installation access token.
    - `_expires_at` – expiry timestamp.
    - `_lock` – `asyncio.Lock` for concurrency-safe refresh.
  - `get_installation_token(app_id, private_key_pem, installation_id, force_refresh)`:
    - If cached token is valid (`now < _expires_at - 60`), returns it.
    - Otherwise:
      - Generates a JWT via `_generate_jwt()` with 9-minute lifetime (GitHub max 10 minutes).
      - Calls `POST /app/installations/{installation_id}/access_tokens` to get new token.
      - Caches token for 55 minutes (safety margin vs 60 min expiry).
  - `get_installation_token_from_env()` wires env-based configuration:
    - Reads `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID`.
    - Loads private key from `GITHUB_APP_PRIVATE_KEY` or `GITHUB_APP_PRIVATE_KEY_PATH`.
    - Returns an installation token or `None`.

### 3.2 Personal Access Token (Simple Default, 5k req/hour)

- PATs are read from `GITHUB_TOKEN`.
- Recommended starting point for most users:
  - Easiest to configure (2‑minute setup).
  - Sufficient for personal projects and light automation.
- Also used when:
  - GitHub App is not configured.
  - App token acquisition fails.
  - App cannot perform certain operations (notably **releases** and tagging), so the server intentionally falls back to PAT.

### 3.3 Dual-Auth Resolution Logic (Behavior vs Recommendation)

- Key functions:
  - `_has_app_config()` – checks presence of App ID, Installation ID, and at least one key source.
  - `get_auth_token()` – core resolver, with optional `GITHUB_MCP_DEBUG_AUTH` logging.

- **Decision Order (Code Behavior)** (as implemented in `get_auth_token()`):

  1. **Explicit mode `GITHUB_AUTH_MODE=pat`**
     - Immediately returns `GITHUB_TOKEN` (if present).
  2. **Explicit mode `GITHUB_AUTH_MODE=app` and App configured**
     - Attempts `get_installation_token_from_env()`.
     - On success, returns App token.
     - On failure/exception, logs (if debug) and falls through to PAT fallback.
  3. **Default (no explicit mode)**
     - If `_has_app_config()`:
       - Try GitHub App first via `get_installation_token_from_env()`.
       - On success, return App token.
       - On failure, log and fall back to PAT.
     - Regardless, attempts PAT fallback:
       - `GITHUB_TOKEN` is returned if set.

### 3.4 Recommended Setup vs Runtime Behavior

- For **most users**:
  - Configure only `GITHUB_TOKEN` (PAT) to get started quickly.
- For **power users / CI / production**:
  - Add GitHub App configuration on top of PAT for higher rate limits.
- Docs (README, `ADVANCED_GITHUB_APP.md`, `AUTHENTICATION.md`) present PAT as the simple default with GitHub App as an **optional** optimization, while the runtime still follows the App‑first, PAT‑fallback resolution described above.

### 3.5 Usage in Tool Layer
  - `_get_auth_token_fallback(param_token)` in `github_mcp.py`:
    - If a tool receives a `token` parameter, it uses that directly.
    - Otherwise, calls `get_auth_token()` for dual-auth resolution.
  - `_make_github_request()` uses `GhClient.instance().request(...)` with the token, centralizing error handling and rate-limit-friendly behavior.

### 3.4 Token Caching & Refresh

- Install token cache lives in `GitHubAppAuth` instance `_app_auth`.
- Refresh rules:
  - Tokens are valid for 60 minutes.
  - Cache TTL is 55 minutes to avoid edge-time expiry.
  - Refresh is protected by an `asyncio.Lock` to prevent stampedes.
- Manual invalidation:
  - `clear_token_cache()` module-level function resets `_token` and `_expires_at`.
  - CLI utilities (e.g., `github-mcp-cli clear-cache`) can trigger this after permission or installation changes.

---

## 4. Tool System

### 4.1 Python Tool Definitions

- All tools are defined in `github_mcp.py` using Pydantic models and the `FastMCP` tooling.
- Core patterns:
  - Input Pydantic models (e.g., `RepoInfoInput`, `IssueInput`, etc.) ensure strict validation (`extra='forbid'`, stripped strings, etc.).
  - Decorators:
    - `@mcp.tool(...)` – registers tools normally.
    - `@conditional_tool(...)` – no-op in code-first mode (so tools aren't exposed to MCP), but active in internal mode.
  - Shared HTTP logic in `_make_github_request()` centralizes:
    - Endpoint construction.
    - Authentication.
    - Error handling mapping to user-friendly messages.
  - Tool types include:
    - GitHub Repo / Issues / PR / Workflow / Release / Search.
    - Workspace operations (`workspace_grep`, `repo_read_file_chunk`, `str_replace`).
    - Licensing meta-tool (`github_license_info`).

### 4.2 TypeScript Tool Exposure

- `deno_executor/tool-definitions.ts` is the **authoritative TS-side schema** used by AI agents.
- Each `ToolDefinition` includes:
  - `name`, `category`, `description`.
  - `parameters` (map of `ToolParameter` with `type`, `required`, `description`, `example`).
  - `returns` – plain-language description of the return value.
  - `example` – concrete usage with `callMCPTool`.
- Categories mirror human mental models: Repository Management, Issues, Pull Requests, File Operations, Branch Management, Commits, Users, Search, Releases, GitHub Actions, Workspace, Licensing, Advanced, Code Execution.

### 4.3 Discovery Helpers in Deno

- Implemented in `deno_executor/mod.ts`:

  - **`listAvailableTools()`**
    - Groups `GITHUB_TOOLS` by `category`.
    - Returns:
      - `totalTools`, `categories`, `tools` grouped, `usage` hint, and a small `quickReference` subset.

  - **`searchTools(keyword)`**
    - Case-insensitive search over:
      - Tool name (high weight).
      - Description.
      - Category.
      - Parameter names and parameter descriptions.
    - Returns array of matches:
      - `name`, `category`, `description`, `relevance`, `matchedIn[]`, and the full `tool` object.

  - **`getToolInfo(toolName)`**
    - Uses `listAvailableTools()` internally.
    - Scans all tools by category to find exact name match.
    - Returns:
      - Original tool fields plus `category`, `usage` string (`await callMCPTool("toolName", parameters)`), and `metadata` with `totalTools`, category count, etc.
    - On missing tool returns an error object with a suggestion to use `searchTools()`.

  - **`getToolsInCategory(category)`**
    - Thin wrapper around `getToolsByCategory()`.

### 4.4 How an AI Agent Discovers and Uses Tools

1. **Catalog**
   - Call `listAvailableTools()` to see all tools and categories.
2. **Search**
   - Use `searchTools("issue")`, `searchTools("pull request")`, etc., to find candidate tools ranked by relevance.
3. **Inspect**
   - For a chosen tool name, use `getToolInfo("github_create_issue")` to inspect parameters, examples, and metadata.
4. **Invoke**
   - Call `await callMCPTool("github_create_issue", { owner, repo, title, body })`.
5. **Compose**
   - Chain multiple tool calls inside the same `execute_code` script:
     - E.g., `github_get_repo_info` → `github_list_pull_requests` → `github_merge_pull_request`.

This design explicitly treats the **AI agent as the primary user** of the tool-discovery APIs.

---

## 5. Key Design Decisions

### 5.1 Code-First vs Traditional MCP

- **Motivation**
  - Traditional MCP loads the full tool set into context, incurring heavy token cost with each conversation.
  - Code-first avoids this by making tools part of an execution environment, not the initial prompt.
- **Benefits**
  - **Token efficiency**: ~70,000 → ~800 tokens (≈98% reduction).
  - **Speed**: 95% faster initialization (per README, ~45s → ~2s in some clients).
  - **Expressiveness**: Agents write code with loops, conditions, and composable workflows instead of one-shot tool calls.
  - **Scalability**: Adding more tools doesn't linearly increase token cost.
- **Trade-offs**
  - Requires Deno runtime on the host.
  - Errors can arise both in the tool layer and in user code, needing robust error handling.
  - Tool schemas are no longer visible in the LLM's initial context — discovery must be done via code.

### 5.2 Why Deno for TypeScript Execution

- **Reasons**
  - First-class TypeScript support (no build step), secure by default.
  - Simple single-binary distribution and good cross-platform story (including Windows, important per README examples).
  - Good fit for quick sandbox-style execution with permission controls.
- **Integration**
  - Python server spawns Deno as a subprocess.
  - Deno uses `servers/client-deno.ts` to talk back via MCP protocol.

### 5.3 Why Dual Authentication (GitHub App + PAT)

- **GitHub App**
  - Higher rate limits (15,000 req/hour) and fine-grained repository-scoped permissions.
  - Preferred for most day-to-day GitHub operations.
- **PAT**
  - Required for operations not supported by GitHub Apps, notably release/tag creation.
  - Provides compatibility with environments where App installation is not available.
- **Dual Strategy**
  - Achieves both high rate limits and full feature coverage.
  - Automatic fallback keeps user experience smooth without manual toggling.

### 5.4 Architectural Trade-offs

- **Pros**
  - Highly expressive workflows in a single call.
  - Strong separation of concerns: Python for GitHub + MCP, Deno for code execution + discovery.
  - AI-first design: discovery APIs optimized for agent usability.
  - Strong test suite and CI pipeline for safety.
- **Cons / Costs**
  - Requires maintaining both Python and TypeScript code paths.
  - Need to keep TS `GITHUB_TOOLS` definitions in sync with Python tool implementations (addressed by contract tests).
  - Additional moving part (Deno process) introduces a class of integration failures (exec, path, permission issues).

---

## 6. Data Flow

### 6.1 Request Lifecycle (Detailed)

1. **Client Invokes `execute_code`**
   - Request payload: `{ code: string }`.

2. **MCP Server (Python)**
   - Validates Deno availability (already done at startup).
   - Spawns Deno subprocess: `deno run deno_executor/mod.ts` (exact arguments in `deno_runtime.py`/`github_mcp.py`).
   - Sends the `code` string to Deno via stdin.

3. **Deno Executor**
   - Reads from stdin or falls back to `Deno.args[0]` if stdin empty (esp. for test environments).
   - Calls `executeUserCode(code)`:
     - `initializeMCPClient()` – sets up MCP connection.
     - Constructs `userFunction` with injected helpers.
     - Awaits `userFunction(...)`.
     - On success, returns `{ success: true, result }`.
     - On error, returns `{ success: false, error, stack }`.
   - Always prints JSON to stdout and exits with code `0` or `1` depending on `success`.

4. **Python MCP Server**
   - Reads stdout, parses JSON.
   - Wraps or directly returns this JSON as the MCP tool result of `execute_code`.

5. **Client / LLM**
   - Receives JSON, inspects `success` and `result`/`error`.
   - Renders human-readable markdown or triggers additional calls.

### 6.2 Error Propagation

- **HTTP Errors (GitHub API)**
  - `_make_github_request()` catches `httpx.HTTPStatusError` and other specific exceptions.
  - `_handle_api_error()` maps them to friendly error messages with hints:
    - 401 – auth required.
    - 403 – insufficient permissions.
    - 404 – resource not found.
    - 409 – conflict.
    - 422 – validation failed.
    - 429 – rate limited (with `Retry-After` hint when available).
    - 5xx – transient GitHub errors.
- **Deno Execution Errors**
  - `executeUserCode` logs to stderr (for debugging) and then:
    - Constructs JSON `{ success: false, error, stack }`.
    - Prints it to stdout.
  - This guarantees the Python side always sees **valid JSON**, even for TypeScript exceptions.
- **Tool Contract / Schema Errors**
  - Pydantic model validation errors surfaced as structured messages.
  - Contract tests ensure TS schema matches Python's expectations.

### 6.3 Response Formatting (JSON vs Markdown)

- **Tool-Level Options**
  - Many tools support a `response_format` parameter (`"json"` or `"markdown"`).
  - Others (mainly write operations) intentionally *do not* support `response_format` to keep semantics clear.
- **Server Behavior**
  - For `markdown` responses:
    - Tools return pre-formatted Markdown strings summarizing results (lists, tables, bullet points).
  - For `json` responses:
    - Tools return structured JSON objects suitable for programmatic handling or further code processing.
- **Truncation**
  - `_truncate_response` enforces `CHARACTER_LIMIT` (25,000 chars) for responses.
  - Adds a truncation notice recommending pagination/filters.

---

## 7. Testing & Quality

### 7.1 Test Structure & Coverage

- Test suite highlights (per `TEST_SUITE_GUIDE.md`):
  - **Total Tests:** 214
  - **Coverage:** ~63%
  - **Pass Rate:** 100%

- Coverage areas:
  - Schema validation for all tools.
  - Error handling across common HTTP codes (401, 403, 404, 409, 422, 429, 500).
  - Authentication flows, including debug logging and fallback behavior.
  - `execute_code` path, including Deno executor and MCP bridge.
  - Individual tools: repo operations, issues, PRs, files, search, releases, actions, workspace operations, licensing.
  - Contract alignment between TypeScript `GITHUB_TOOLS` and Python tools.

### 7.2 CI/CD Pipeline

- Configured in `.github/workflows/ci.yml`:
  - Environment:
    - `ubuntu-latest`, Python 3.12, Deno v2.x.
  - Steps:
    - Install dependencies via `requirements.txt` plus dev tooling.
    - **Lint:** Ruff (`ruff check .`).
    - **Type-check:** mypy on `src` with `mypy.ini`.
    - **Security:** `pip-audit -r requirements.txt` (non-fatal on failure).
    - **Tests:** `pytest -q --capture=tee-sys` with `GITHUB_TOKEN` available.
    - **Coverage:** `pytest --cov=github_mcp --cov=auth --cov-report=term --cov-report=xml`.

### 7.3 Quality Practices

- Strong reliance on Pydantic models for parameter validation.
- Centralized HTTP error mapping prevents inconsistent error surfaces across tools.
- Contract tests enforce parity between TS tool definitions and Python server implementations.
- Discovery scripts (e.g., `tests/discover_tool_issues.py`) detect subtle mismatches like `response_format` availability.

---

## 8. Extension Points

### 8.1 Adding New Tools

1. **Python Side (Server Implementation)**
   - Define a Pydantic input model (or parameters) in `github_mcp.py`.
   - Implement a tool function using `@conditional_tool(...)` or `@mcp.tool(...)` depending on exposure strategy.
   - Use `_make_github_request()` for GitHub API calls where applicable.
   - Ensure consistent error mapping via `_handle_api_error()`.

2. **TypeScript Side (Discovery Schema)**
   - Add a new `ToolDefinition` entry to `deno_executor/tool-definitions.ts` with:
     - Appropriate `category`, `description`, parameter descriptors, and an `example` snippet.
   - This makes the new tool visible to `listAvailableTools`, `searchTools`, `getToolInfo`.

3. **Tests**
   - Add tests in `tests/test_individual_tools.py` (or specialized test files) covering typical and edge cases.
   - Update contract and schema tests if needed.

### 8.2 Modifying Existing Tools

- Change logic in Python tool implementations in `github_mcp.py`.
- Update corresponding `ToolDefinition` in `tool-definitions.ts` **in lockstep**.
- Run the discovery script (`tests/discover_tool_issues.py`) to identify mismatches.
- Run the full test suite to validate behavior.

### 8.3 Configuration vs Hardcoding

- **Configurable via Environment**:
  - Auth:
    - `GITHUB_TOKEN`, `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID`, `GITHUB_APP_PRIVATE_KEY`, `GITHUB_APP_PRIVATE_KEY_PATH`, `GITHUB_AUTH_MODE`.
  - Workspace root: `MCP_WORKSPACE_ROOT`.
  - Auth diagnostics: `GITHUB_MCP_DEBUG_AUTH`.
  - Code-first toggle: `MCP_CODE_FIRST_MODE` (though README emphasizes code-first as the reference architecture and default).
- **Hardcoded / Conventional**:
  - GitHub API base URL (`https://api.github.com`).
  - `CHARACTER_LIMIT` for output.
  - Default pagination limits.
  - Tool categorizations and names.

---

## 9. Current State

### 9.1 Version & Tool Count

- **Version:** 2.4.0 (per `pyproject.toml` and README badges).
- **Total Tools:** 62 as per `listAvailableTools().totalTools` and `tool-definitions.ts`.
  - External MCP surface: `execute_code`.
  - Internal tools: 61 GitHub/workspace/meta tools.

### 9.2 Recent Major Changes (from README)

- **v2.4.0** – Phase 1 tool expansion (48 → 62 tools).
- **v2.3.1** – Code-first mode enforced by default.
  - `MCP_CODE_FIRST_MODE` is defaulted to `true`, fully aligning runtime with documented architecture.
- **v2.3.0** – Architecture formalization and testing uplift.
  - Single-tool (`execute_code`) architecture clarified and documented.
  - CLI utilities moved to `github-mcp-cli`.
  - Test count increased to 214; coverage to 63%.
- **v2.2.0** – Enterprise-ready auth.
  - GitHub App authentication added.
  - Dual-auth (App + PAT) with automatic fallback.
  - `.env` / `python-dotenv` support for simpler configuration.

### 9.3 Known Limitations / TODOs

- Some tools do not support `response_format=json` though they appear in JSON-capable lists – flagged by `discover_tool_issues.py` (e.g., `github_read_file_chunk`, `repo_read_file_chunk` in certain arrays).
- Deno runtime is a hard requirement; without it, the server exits early.
- Maintaining strict sync between TS `GITHUB_TOOLS` schema and Python tool implementations is non-trivial (mitigated by tests but still a human process).

---

## 10. The Meta Aspect (Dogfooding & Self-Use)

### 10.1 Self-Hosting & Self-Development

- The README and testing docs emphasize that this MCP server is **used to develop itself**:
  - The tools are used on this very repo to file issues, open PRs, and create releases.
  - The `github_create_release` tool has been used to publish its own releases.
  - Workspace tools operate on this project to refactor code, update docs, and manage tests.

### 10.2 Recursive Testing

- Test suite runs within environments (e.g., Cursor) that themselves use the GitHub MCP server.
- Tests call `execute_code`, which spawns a new MCP server subprocess, which calls tools that are being tested.
- This **recursion** validates:
  - MCP client/server contract.
  - Deno executor behavior.
  - Tool robustness under real-world usage patterns.

### 10.3 Dogfooding Outcomes

- Many features in the tool set (e.g., workspace tools, advanced PR operations, release helpers) originated from hitting limitations when using the server on its own repo.
- Tool discovery improvements (`searchTools`, `getToolInfo`) were driven by AI's perspective as primary user.
- Auth system evolved in response to real-world rate-limit and permission needs.

---

## 11. Architecture Diagram

### 11.1 ASCII Diagram

```text
+--------------------------+          +-----------------------------+
|      MCP Client          |          |      GitHub (API)          |
| (Cursor, Claude, etc.)   |          |  REST & GraphQL Endpoints  |
+------------+-------------+          +--------------+-------------+
             |                                       ^
             | execute_code(code)                   |
             v                                       |
+------------+--------------------------------------+|
|         Python MCP Server (github_mcp.py)         |
|    - FastMCP("github_mcp")                       |
|    - CODE_FIRST_MODE (default true)               |
|    - Tools (GitHub, workspace, license)           |
|    - Auth (GitHub App + PAT) via auth/github_app  |
+------------+--------------------------+-----------+
             |                          |
             | spawn Deno (mod.ts)      | _make_github_request()
             v                          v
+------------+--------------------------+-----------+
|          Deno Executor (mod.ts)                   |
|   - Reads code from stdin                         |
|   - initializeMCPClient / closeMCPClient          |
|   - callMCPTool() -> MCP bridge to Python tools   |
|   - listAvailableTools(), searchTools(),          |
|     getToolInfo(), getToolsInCategory()           |
|   - Executes user TS code with injected helpers   |
+---------------------------------------------------+
```

### 11.2 Mermaid Diagram

```mermaid
flowchart TD
  client[MCP Client
  (Cursor, Claude, etc.)]
  subgraph python[Python MCP Server (github_mcp.py)]
    mcp[FastMCP "github_mcp"\nCODE_FIRST_MODE=true]
    tools[GitHub & Workspace Tools\n(46 internal tools)]
    auth[GitHub App + PAT Auth\n(auth/github_app.py)]
  end

  subgraph deno[Deno Executor (deno_executor/mod.ts)]
    exec[executeUserCode(code)]
    discovery[listAvailableTools()/searchTools()/\ngetToolInfo()/getToolsInCategory()\n(tool-definitions.ts)]
  end

  client -->|execute_code(code)| mcp
  mcp -->|spawn Deno, pass code| exec
  exec --> discovery
  exec -->|callMCPTool(name, params)| tools
  tools -->|_make_github_request| auth
  auth -->|token| tools
  tools -->|HTTP/GraphQL| githubAPI[(GitHub API)]
  exec -->|JSON { success, result/error }| mcp
  mcp -->|MCP result| client
```

---

## 12. Key Insights & Observations

- **Code-first MCP is implemented thoroughly and coherently**:
  - Single exposed tool (`execute_code`) with Deno-based TypeScript execution matches the documented "code-first" pattern.
  - Tool discovery utilities are clearly designed for AI agents, not humans.
- **Auth and rate-limiting strategy is pragmatic and robust**:
  - Dual-auth with clear priority and safe fallbacks ensures reliability and enterprise scalability.
- **Strong emphasis on testing and meta-validation**:
  - High test coverage, self-referential usage, and contract tests significantly reduce the risk of breaking changes.
- **Architecture is highly extensible**:
  - Adding tools is straightforward when following the Python+TS+tests pattern.
  - Workspace tools open the door for more advanced local-code workflows beyond GitHub.

---

## 13. Recommendations for Improvement

- **Automated Sync Between Python Tools and `tool-definitions.ts`**
  - Consider generating `tool-definitions.ts` from Python tool metadata (or vice versa) to remove manual sync and reduce drift.
  - Alternatively, introduce a shared schema (e.g., JSON) that both sides generate from.

- **Richer Error Typing Across the Boundary**
  - Currently, Deno executor wraps errors as `{ success: false, error, stack }`.
  - Consider encoding a structured error type (e.g., `type`, `statusCode`, `hint`) to make error handling in TypeScript workflows more programmatic.

- **Configurable Execution Limits**
  - Introduce configuration for code execution limits (max runtime, max MCP calls per execution) to harden against pathological scripts.

- **Surface Tool Categories & Metadata in MCP-Level Docs**
  - Provide a dedicated `ARCHITECTURE.md` (this document) and a short "for AI agents" appendix summarizing discovery APIs and categories, so agents have guidance even before first `execute_code` call.

- **Optional Non-Code-First Mode for Debugging**
  - While `CODE_FIRST_MODE` already exists, a small CLI or environment-driven switch (with docs) that exposes all tools directly to MCP clients can help during debugging and during migration.
