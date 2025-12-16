/// <reference lib="deno.ns" />
import { assertEquals, assertFalse, assert } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { validateCode } from "./code-validator.ts";

Deno.test("validateCode - allows safe code", () => {
  const result = validateCode(`
    const repos = await callMCPTool("github_list_repos", { owner: "test" });
    return repos;
  `);
  assert(result.valid, `Expected valid but got errors: ${result.errors.join(", ")}`);
  assertEquals(result.errors.length, 0);
});

Deno.test("validateCode - blocks eval()", () => {
  const result = validateCode(`eval("console.log('hack')")`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("eval()")));
});

Deno.test("validateCode - blocks new Function()", () => {
  const result = validateCode(`const fn = new Function("return 1")`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("new Function()")));
});

Deno.test("validateCode - blocks Deno.run()", () => {
  const result = validateCode(`Deno.run({ cmd: ["ls"] })`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("Deno.run()")));
});

Deno.test("validateCode - blocks Deno.writeFile()", () => {
  const result = validateCode(`await Deno.writeFile("test.txt", new Uint8Array())`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("Deno.writeFile()")));
});

Deno.test("validateCode - blocks __proto__ access", () => {
  const result = validateCode(`obj.__proto__.polluted = true`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("__proto__")));
});

Deno.test("validateCode - blocks prototype pollution via Object.defineProperty", () => {
  const result = validateCode(`Object.defineProperty(Object.prototype, "x", { value: 1 })`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("Object.defineProperty")));
});

Deno.test("validateCode - blocks WebSocket", () => {
  const result = validateCode(`const ws = new WebSocket("ws://evil.com")`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("WebSocket")));
});

Deno.test("validateCode - blocks dynamic import with variables", () => {
  const result = validateCode(`const mod = await import(userInput)`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("Dynamic import")));
});

Deno.test("validateCode - allows static imports", () => {
  const result = validateCode(`import { something } from "https://example.com/mod.ts"`);
  assert(result.valid);
});

Deno.test("validateCode - rejects empty code", () => {
  const result = validateCode("");
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("empty")));
});

Deno.test("validateCode - rejects oversized code", () => {
  const hugeCode = "x".repeat(100001);
  const result = validateCode(hugeCode);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("maximum length")));
});

Deno.test("validateCode - detects unbalanced brackets", () => {
  const result = validateCode(`{ { { }`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("Unbalanced")));
});

Deno.test("validateCode - warns about JSON.parse", () => {
  const result = validateCode(`const data = JSON.parse(input)`);
  assert(result.valid); // Should be valid but with warning
  assert(result.warnings.some(w => w.includes("JSON.parse")));
});

Deno.test("validateCode - allows callMCPTool", () => {
  const result = validateCode(`
    const result = await callMCPTool("github_get_repo_info", {
      owner: "facebook",
      repo: "react"
    });
    return result;
  `);
  assert(result.valid);
});

Deno.test("validateCode - allows listAvailableTools", () => {
  const result = validateCode(`
    const tools = listAvailableTools();
    return tools;
  `);
  assert(result.valid);
});

Deno.test("validateCode - case insensitive blocking", () => {
  const result = validateCode(`EVAL("test")`);
  assertFalse(result.valid);
});

Deno.test("validateCode - blocks require()", () => {
  const result = validateCode(`const fs = require('fs')`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("require()")));
});

Deno.test("validateCode - blocks process access", () => {
  const result = validateCode(`process.env.SECRET`);
  assertFalse(result.valid);
  assert(result.errors.some(e => e.includes("process")));
});

Deno.test("validateCode - blocks Deno.exit", () => {
  const result = validateCode(`Deno.exit(1)`);
  assertFalse(result.valid);
});

Deno.test("validateCode - blocks Deno.env.set", () => {
  const result = validateCode(`Deno.env.set("PATH", "/evil")`);
  assertFalse(result.valid);
});

Deno.test("validateCode - blocks setTimeout with string", () => {
  const result = validateCode(`setTimeout("alert('xss')", 1000)`);
  assertFalse(result.valid);
});

Deno.test("validateCode - allows setTimeout with function", () => {
  const result = validateCode(`setTimeout(() => console.log("ok"), 1000)`);
  assert(result.valid);
});

