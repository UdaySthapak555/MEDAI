import os
import shutil
import subprocess
from io import BytesIO
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageOps, UnidentifiedImageError


OCR_TIMEOUT_SECONDS = 30
OCR_DOCUMENT_TIMEOUT_SECONDS = 120
OCR_RENDER_SCALE = 2.5
MAX_OCR_PAGES = 25
MAX_IMAGE_PIXELS = 12_000_000


class OcrEngineUnavailableError(Exception):
    """Raised when the Tesseract executable cannot be found."""


class OcrExecutionError(Exception):
    """Raised when Tesseract fails to process an image."""


class OcrTimeoutError(Exception):
    """Raised when OCR exceeds its per-image time limit."""


class InvalidImageError(Exception):
    """Raised when image bytes cannot be decoded safely."""


class InvalidPdfRenderError(Exception):
    """Raised when a PDF page cannot be rendered for OCR."""


class OcrResourceLimitError(Exception):
    """Raised when the document exceeds OCR resource limits."""


def _tesseract_executable() -> str:
    configured_path = os.environ.get("TESSERACT_CMD")
    if configured_path:
        resolved_path = shutil.which(configured_path)
        if resolved_path:
            return resolved_path
        if Path(configured_path).is_file():
            return configured_path
        raise OcrEngineUnavailableError("The configured OCR executable is unavailable.")

    executable = shutil.which("tesseract")
    if not executable:
        raise OcrEngineUnavailableError("Tesseract OCR is not installed or is not on PATH.")
    return executable


def _run_tesseract(png_bytes: bytes, timeout_seconds: float = OCR_TIMEOUT_SECONDS) -> str:
    command = [_tesseract_executable(), "stdin", "stdout", "-l", "eng", "--psm", "6"]
    try:
        result = subprocess.run(
            command,
            input=png_bytes,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        raise OcrTimeoutError("OCR processing exceeded its time limit.") from None
    except OSError as exc:
        raise OcrEngineUnavailableError("Tesseract OCR could not be started.") from exc

    if result.returncode != 0:
        raise OcrExecutionError("Tesseract OCR could not process the image.")
    return result.stdout.decode("utf-8", errors="replace").strip()


def _image_as_png_bytes(image: Image.Image) -> bytes:
    oriented = ImageOps.exif_transpose(image)
    if "A" in oriented.getbands():
        rgba = oriented.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        rgba.close()
        normalized = background
    else:
        normalized = oriented.convert("RGB")

    output = BytesIO()
    normalized.save(output, format="PNG")
    if normalized is not oriented:
        normalized.close()
    if oriented is not image:
        oriented.close()
    return output.getvalue()


def extract_text_from_image(contents: bytes) -> str:
    try:
        with Image.open(BytesIO(contents)) as image:
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise OcrResourceLimitError("Image dimensions exceed the OCR processing limit.")
            image.load()
            png_bytes = _image_as_png_bytes(image)
    except OcrResourceLimitError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise InvalidImageError("The uploaded image is invalid or unreadable.") from exc

    return _run_tesseract(png_bytes)


def extract_text_from_pdf_page(
    contents: bytes,
    page_number: int,
    timeout_seconds: float = OCR_TIMEOUT_SECONDS,
) -> str:
    document = None
    page = None
    bitmap = None
    image = None
    try:
        document = pdfium.PdfDocument(contents)
        if page_number < 0 or page_number >= len(document):
            raise InvalidPdfRenderError("The requested PDF page is unavailable.")
        page = document[page_number]
        width, height = page.get_size()
        if width * height * OCR_RENDER_SCALE**2 > MAX_IMAGE_PIXELS:
            raise OcrResourceLimitError("PDF page dimensions exceed the OCR processing limit.")

        bitmap = page.render(scale=OCR_RENDER_SCALE)
        image = bitmap.to_pil()
        png_bytes = _image_as_png_bytes(image)
    except (InvalidPdfRenderError, OcrResourceLimitError):
        raise
    except Exception as exc:
        raise InvalidPdfRenderError("The PDF page could not be rendered for OCR.") from exc
    finally:
        if image is not None:
            image.close()
        if bitmap is not None:
            bitmap.close()
        if page is not None:
            page.close()
        if document is not None:
            document.close()

    return _run_tesseract(png_bytes, timeout_seconds=timeout_seconds)
