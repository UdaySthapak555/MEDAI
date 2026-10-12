from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
import re
import unicodedata

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import joblib
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from starlette.concurrency import run_in_threadpool

from services.pdf_extractor import extract_text_from_pdf
from services.ocr_extractor import (
    InvalidImageError,
    InvalidPdfRenderError,
    OcrEngineUnavailableError,
    OcrExecutionError,
    OcrResourceLimitError,
    OcrTimeoutError,
    extract_text_from_image,
)
from services.medical_extractor import extract_medical_parameters
from services.classifier import classify_medical_report
from ml_experiments.indicphi_document_type import DOCUMENT_TYPES


DOCUMENT_TYPE_MODEL_PATH = (
    Path(__file__).resolve().parent
    / "artifacts"
    / "indicphi_document_type"
    / "logistic_regression.joblib"
)
MIN_DOCUMENT_TYPE_CHARACTERS = 132
UNCALIBRATED_MODEL_NOTE = (
    "No calibrated confidence is available. This model was trained on synthetic "
    "English data; language is checked with a basic text signal, not definitively detected. "
    "It has not been validated on real-world reports."
)
ENGLISH_FUNCTION_WORDS = frozenset(
    "the and of to in for with on at by from is are was were be as this that it "
    "has have had not no or into per after before during without due than within between under over about".split()
)

document_type_pipeline = None
document_type_model_load_error = False


def _load_document_type_pipeline() -> None:
    """Load the local prototype model once at application startup."""

    global document_type_pipeline, document_type_model_load_error
    try:
        pipeline = joblib.load(DOCUMENT_TYPE_MODEL_PATH)
        classes = getattr(pipeline, "classes_", ())
        if set(classes) != set(DOCUMENT_TYPES) or len(classes) != len(DOCUMENT_TYPES):
            raise ValueError("The model classes do not match the supported categories.")
    except Exception:
        document_type_pipeline = None
        document_type_model_load_error = True
        return

    document_type_pipeline = pipeline
    document_type_model_load_error = False


@asynccontextmanager
async def lifespan(_app):
    _load_document_type_pipeline()
    yield


def _unavailable_document_type(message: str) -> dict:
    return {
        "status": "unavailable",
        "category": None,
        "confidence": None,
        "uncertainty": message,
    }


def _has_supported_script(text: str) -> bool:
    letters = [character for character in text if character.isalpha()]
    if not letters:
        return False
    latin_letters = sum("LATIN" in unicodedata.name(character, "") for character in letters)
    return latin_letters / len(letters) >= 0.8


def _has_english_language_signal(text: str) -> bool:
    words = re.findall(r"[a-z]+", text.casefold())
    return sum(word in ENGLISH_FUNCTION_WORDS for word in words) >= 3


def classify_document_type(text: str) -> dict:
    """Return a cautious category result without exposing model errors or scores."""

    if not isinstance(text, str) or not text.strip():
        return _unavailable_document_type("No readable text is available for document categorization.")
    if len(text.strip()) < MIN_DOCUMENT_TYPE_CHARACTERS:
        return _unavailable_document_type(
            "There is not enough text for this document-type prototype."
        )
    if not _has_supported_script(text):
        return _unavailable_document_type(
            "This English-only document-type prototype cannot categorize text in this script."
        )
    if not _has_english_language_signal(text):
        return _unavailable_document_type(
            "The text does not contain enough English-language signal for this prototype."
        )
    if document_type_pipeline is None:
        message = (
            "The document-type model could not be loaded at application startup."
            if document_type_model_load_error
            else "The document-type model is unavailable."
        )
        return _unavailable_document_type(message)

    try:
        predictions = document_type_pipeline.predict([text])
        if len(predictions) != 1:
            return _unavailable_document_type("The document-type model returned an invalid result.")
        category = str(predictions[0])
    except Exception:
        return _unavailable_document_type("The document-type model could not process this report.")

    if category not in DOCUMENT_TYPES:
        return _unavailable_document_type("The document-type model returned an unsupported category.")
    return {
        "status": "predicted",
        "category": category,
        "confidence": None,
        "uncertainty": UNCALIBRATED_MODEL_NOTE,
    }


app = FastAPI(
    title="MEDAI API",
    description="AI-Based Medical Report Classification System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    "application/pdf": {".pdf"},
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
}


def _validate_filename(filename: str | None) -> str:
    if (
        not filename
        or filename in {".", ".."}
        or any(separator in filename for separator in ("/", "\\", ":"))
        or any(ord(character) < 32 for character in filename)
    ):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    return filename


def _validate_file_signature(content_type: str, contents: bytes) -> None:
    matches_type = (
        content_type == "application/pdf" and contents.startswith(b"%PDF-")
        or content_type == "image/png" and contents.startswith(b"\x89PNG\r\n\x1a\n")
        or content_type == "image/jpeg" and contents.startswith(b"\xff\xd8\xff")
    )
    if not matches_type:
        raise HTTPException(status_code=415, detail="File content does not match its declared type.")


async def _read_upload(file: UploadFile) -> tuple[str, bytes]:
    filename = _validate_filename(file.filename)
    content_type = file.content_type
    extensions = ALLOWED_EXTENSIONS.get(content_type)
    if extensions is None:
        raise HTTPException(status_code=415, detail="Unsupported file type. Upload a PDF, PNG, or JPG.")

    if Path(filename).suffix.lower() not in extensions:
        raise HTTPException(status_code=415, detail="File extension does not match its content type.")

    try:
        contents = await file.read(MAX_UPLOAD_SIZE + 1)
    except OSError as exc:
        raise HTTPException(status_code=400, detail="Unable to read uploaded file.") from exc

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds the 10 MB limit.")

    _validate_file_signature(content_type, contents)
    return filename, contents


def _validate_pdf(contents: bytes) -> None:
    try:
        PdfReader(BytesIO(contents))
    except (PdfReadError, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="The uploaded PDF is invalid or unreadable.") from exc


def _raise_ocr_http_error(exc: Exception) -> None:
    if isinstance(exc, OcrResourceLimitError):
        raise HTTPException(status_code=413, detail="The report exceeds the OCR processing limits.") from exc
    if isinstance(exc, OcrTimeoutError):
        raise HTTPException(status_code=504, detail="OCR processing timed out.") from exc
    if isinstance(exc, (InvalidImageError, InvalidPdfRenderError)):
        raise HTTPException(status_code=400, detail="The uploaded report could not be read for OCR.") from exc
    if isinstance(exc, (OcrEngineUnavailableError, OcrExecutionError)):
        raise HTTPException(status_code=503, detail="OCR processing is unavailable.") from exc
    raise HTTPException(status_code=500, detail="Report OCR failed.") from exc


@app.get("/")
def root():
    return {"success": True, "message": "MEDAI API is running"}


@app.post("/api/upload")
async def upload_report(file: UploadFile = File(...)):
    filename, contents = await _read_upload(file)
    if file.content_type == "application/pdf":
        _validate_pdf(contents)

    return {
        "success": True,
        "filename": filename,
        "content_type": file.content_type,
        "size": len(contents),
        "message": "Medical report uploaded successfully.",
    }


@app.post("/api/analyze")
async def analyze_report(file: UploadFile = File(...)):
    filename, contents = await _read_upload(file)

    if file.content_type == "application/pdf":
        try:
            extracted_text = await run_in_threadpool(extract_text_from_pdf, contents)
        except (PdfReadError, OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="The uploaded PDF is invalid or unreadable.") from exc
        except (
            InvalidPdfRenderError,
            OcrEngineUnavailableError,
            OcrExecutionError,
            OcrResourceLimitError,
            OcrTimeoutError,
        ) as exc:
            _raise_ocr_http_error(exc)

        if not extracted_text:
            return {
                "success": False,
                "message": "No readable text was found in the PDF.",
                "filename": filename,
            }

        medical_data = extract_medical_parameters(extracted_text)
        classification = classify_medical_report(medical_data)
        document_type = await run_in_threadpool(classify_document_type, extracted_text)
        return {
            "success": True,
            "filename": filename,
            "message": "Report analyzed successfully.",
            "text": extracted_text,
            "medical_data": medical_data,
            "classification": classification,
            "document_type": document_type,
        }

    try:
        extracted_text = await run_in_threadpool(extract_text_from_image, contents)
    except (InvalidImageError, OcrEngineUnavailableError, OcrExecutionError, OcrResourceLimitError, OcrTimeoutError) as exc:
        _raise_ocr_http_error(exc)

    if not extracted_text:
        return {
            "success": False,
            "message": "No readable text was found in the report.",
            "filename": filename,
        }

    medical_data = extract_medical_parameters(extracted_text)
    classification = classify_medical_report(medical_data)
    document_type = await run_in_threadpool(classify_document_type, extracted_text)
    return {
        "success": True,
        "filename": filename,
        "message": "Report analyzed successfully.",
        "text": extracted_text,
        "medical_data": medical_data,
        "classification": classification,
        "document_type": document_type,
    }
