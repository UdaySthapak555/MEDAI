from io import BytesIO
from pathlib import Path
import time

from pypdf import PdfReader

from services.ocr_extractor import (
    MAX_OCR_PAGES,
    OCR_DOCUMENT_TIMEOUT_SECONDS,
    OCR_TIMEOUT_SECONDS,
    OcrResourceLimitError,
    OcrTimeoutError,
    extract_text_from_pdf_page,
)


def extract_text_from_pdf(source: bytes | Path) -> str:
    """
    Extract text from PDF bytes or a file path.
    """

    reader = PdfReader(BytesIO(source)) if isinstance(source, bytes) else PdfReader(str(source))

    source_bytes = source if isinstance(source, bytes) else None
    extracted_text = []
    ocr_page_count = 0
    ocr_deadline = time.monotonic() + OCR_DOCUMENT_TIMEOUT_SECONDS

    for page_number, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()

        if text:
            extracted_text.append(text)
            continue

        ocr_page_count += 1
        if ocr_page_count > MAX_OCR_PAGES:
            raise OcrResourceLimitError("PDF contains too many pages that require OCR.")

        remaining_time = ocr_deadline - time.monotonic()
        if remaining_time <= 0:
            raise OcrTimeoutError("OCR processing exceeded the document time limit.")

        if source_bytes is None:
            source_bytes = Path(source).read_bytes()
        ocr_text = extract_text_from_pdf_page(
            source_bytes,
            page_number,
            timeout_seconds=min(OCR_TIMEOUT_SECONDS, remaining_time),
        )
        if ocr_text:
            extracted_text.append(ocr_text)

    return "\n".join(extracted_text).strip()
