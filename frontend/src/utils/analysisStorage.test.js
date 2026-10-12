import assert from "node:assert/strict";
import test from "node:test";
import { minimizeAnalysisForStorage, sanitizeStoredAnalysis } from "./analysisStorage.js";

function createMemoryStorage(initialValue) {
  let value = initialValue;
  return {
    getItem: () => value,
    setItem: (_key, nextValue) => { value = nextValue; },
    removeItem: () => { value = null; },
    read: () => value,
  };
}

test("stored successful analysis excludes report text, filename, and unrelated fields", () => {
  const stored = minimizeAnalysisForStorage({
    success: true,
    filename: "private-name.pdf",
    text: "Synthetic report body that must not be retained.",
    medical_data: {
      hemoglobin: 14,
      wbc: 7000,
      private_identifier: "must not be retained",
    },
    classification: {
      status: "REVIEW",
      confidence: 0.82,
      flags: ["Review note."],
      debug_detail: "must not be retained",
    },
    document_type: {
      status: "predicted",
      category: "lab_report",
      uncertainty: "Prototype output.",
      debug_detail: "must not be retained",
    },
    extra: "must not be retained",
  });

  assert.deepEqual(stored, {
    success: true,
    medical_data: { hemoglobin: 14, wbc: 7000 },
    classification: { status: "REVIEW", confidence: 0.82, flags: ["Review note."] },
    document_type: {
      status: "predicted",
      category: "lab_report",
      uncertainty: "Prototype output.",
    },
  });
  assert.equal(JSON.stringify(stored).includes("Synthetic report body"), false);
  assert.equal(JSON.stringify(stored).includes("private-name.pdf"), false);
});

test("legacy full response in session storage is minimized on startup", () => {
  const storage = createMemoryStorage(JSON.stringify({
    success: true,
    filename: "legacy.pdf",
    text: "Legacy extracted report text.",
    medical_data: { hemoglobin: 13.5, private_note: "discard" },
  }));

  sanitizeStoredAnalysis(storage);

  const stored = storage.read();
  assert.equal(stored.includes("Legacy extracted report text"), false);
  assert.equal(stored.includes("legacy.pdf"), false);
  assert.deepEqual(JSON.parse(stored), {
    success: true,
    medical_data: { hemoglobin: 13.5 },
    classification: null,
    document_type: null,
  });
});

test("unreadable response stores only a fixed generic message", () => {
  const stored = minimizeAnalysisForStorage({
    success: false,
    filename: "private-name.pdf",
    text: "Sensitive content",
    message: "Sensitive backend detail",
  });

  assert.deepEqual(stored, {
    success: false,
    message: "No readable text was found in the report.",
  });
});

test("malformed stored data is removed", () => {
  const storage = createMemoryStorage("not valid JSON");
  sanitizeStoredAnalysis(storage);
  assert.equal(storage.read(), null);
});
