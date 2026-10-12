import assert from "node:assert/strict";
import test from "node:test";
import { validateUploadFile } from "./uploadValidation.js";

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

function syntheticFile(type, size = 128) {
  return { type, size };
}

test("accepts PDF, PNG, and JPEG file types", () => {
  for (const type of ["application/pdf", "image/png", "image/jpeg"]) {
    assert.deepEqual(validateUploadFile(syntheticFile(type)), { valid: true });
  }
});

test("accepts a file exactly at the 10 MB limit", () => {
  assert.deepEqual(
    validateUploadFile(syntheticFile("application/pdf", MAX_UPLOAD_BYTES)),
    { valid: true },
  );
});

test("rejects a file one byte above the 10 MB limit", () => {
  assert.deepEqual(
    validateUploadFile(syntheticFile("application/pdf", MAX_UPLOAD_BYTES + 1)),
    { valid: false, message: "File size must be at most 10 MB." },
  );
});

test("rejects unsupported file types", () => {
  assert.deepEqual(
    validateUploadFile(syntheticFile("text/plain")),
    { valid: false, message: "Please upload a PDF, PNG, or JPG file." },
  );
});

test("requires a selected file", () => {
  assert.deepEqual(
    validateUploadFile(null),
    { valid: false, message: "Please select a medical report first." },
  );
});
