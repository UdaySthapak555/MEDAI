const RESULT_PARAMETER_KEYS = [
  "hemoglobin",
  "wbc",
  "platelets",
  "glucose",
  "cholesterol",
  "rbc",
];

export function minimizeAnalysisForStorage(result) {
  if (result?.success !== true) {
    return {
      success: false,
      message: "No readable text was found in the report.",
    };
  }

  const medicalData = {};
  RESULT_PARAMETER_KEYS.forEach((key) => {
    const value = result.medical_data?.[key];
    if (Number.isFinite(value)) medicalData[key] = value;
  });

  const sourceClassification = result.classification;
  const classification = sourceClassification && typeof sourceClassification === "object"
    ? {
      status: typeof sourceClassification.status === "string"
        ? sourceClassification.status
        : undefined,
      confidence: Number.isFinite(sourceClassification.confidence)
        ? sourceClassification.confidence
        : undefined,
      flags: Array.isArray(sourceClassification.flags)
        ? sourceClassification.flags.filter((flag) => typeof flag === "string")
        : [],
    }
    : null;

  const sourceDocumentType = result.document_type;
  const documentType = sourceDocumentType && typeof sourceDocumentType === "object"
    ? {
      status: typeof sourceDocumentType.status === "string"
        ? sourceDocumentType.status
        : undefined,
      category: typeof sourceDocumentType.category === "string"
        ? sourceDocumentType.category
        : null,
      uncertainty: typeof sourceDocumentType.uncertainty === "string"
        ? sourceDocumentType.uncertainty
        : undefined,
    }
    : null;

  return {
    success: true,
    medical_data: medicalData,
    classification,
    document_type: documentType,
  };
}

export function sanitizeStoredAnalysis(storage = null) {
  let activeStorage = storage;
  let stored;
  try {
    activeStorage ??= globalThis.sessionStorage;
    if (!activeStorage) return;
    stored = activeStorage.getItem("medai_result");
  } catch {
    return;
  }
  if (stored === null) return;

  try {
    const result = JSON.parse(stored);
    if (!result || typeof result !== "object" || Array.isArray(result)
      || (result.success !== true && result.success !== false)) {
      activeStorage.removeItem("medai_result");
      return;
    }

    const minimized = JSON.stringify(minimizeAnalysisForStorage(result));
    if (minimized !== stored) activeStorage.setItem("medai_result", minimized);
  } catch {
    try {
      activeStorage.removeItem("medai_result");
    } catch {
      // Storage can be unavailable or read-only in restricted browser contexts.
    }
  }
}
