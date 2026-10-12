const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const ALLOWED_TYPES = new Set([
  "application/pdf",
  "image/png",
  "image/jpeg",
]);

export function validateUploadFile(file) {
  if (!file) {
    return { valid: false, message: "Please select a medical report first." };
  }

  if (!ALLOWED_TYPES.has(file.type)) {
    return { valid: false, message: "Please upload a PDF, PNG, or JPG file." };
  }

  if (!Number.isFinite(file.size) || file.size > MAX_UPLOAD_BYTES) {
    return { valid: false, message: "File size must be at most 10 MB." };
  }

  return { valid: true };
}
