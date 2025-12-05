/// <reference lib="deno.ns" />
import { assertEquals, assert } from "https://deno.land/std@0.208.0/assert/mod.ts";
import type { ErrorResponse, SuccessResponse } from "./mod.ts";
import { ErrorCodes } from "./error-codes.ts";

Deno.test("error response - has correct structure", () => {
  const errorResponse: ErrorResponse = {
    error: true,
    message: "Test error",
    code: ErrorCodes.EXECUTION_ERROR,
  };
  
  assert(errorResponse.error === true);
  assertEquals(typeof errorResponse.message, "string");
  assertEquals(errorResponse.code, ErrorCodes.EXECUTION_ERROR);
});

Deno.test("error response - code is optional", () => {
  const errorResponse: ErrorResponse = {
    error: true,
    message: "Test error",
  };
  
  assert(errorResponse.error === true);
  assertEquals(errorResponse.code, undefined);
});

Deno.test("success response - has correct structure", () => {
  const successResponse: SuccessResponse = {
    error: false,
    data: { result: "test" },
  };
  
  assert(successResponse.error === false);
  assert("data" in successResponse);
});

Deno.test("isErrorResponse - detects error responses", () => {
  const isErrorResponse = (obj: unknown): boolean => {
    return (
      typeof obj === 'object' &&
      obj !== null &&
      'error' in obj &&
      (obj as Record<string, unknown>).error === true
    );
  };
  
  assert(isErrorResponse({ error: true, message: "test" }));
  assert(!isErrorResponse({ error: false, data: {} }));
  assert(!isErrorResponse({ message: "test" }));
  assert(!isErrorResponse(null));
  assert(!isErrorResponse("error string"));
});

