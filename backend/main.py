from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.pdf_extractor import extract_text_from_pdf
from services.medical_extractor import extract_medical_parameters
from services.classifier import classify_medical_report


app = FastAPI(
    title="MEDAI API",
    description="AI-Based Medical Report Classification System",
    version="1.0.0",
)


# -----------------------------
# CORS
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Upload directory
# -----------------------------

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# -----------------------------
# Root / Health Check
# -----------------------------

@app.get("/")
def root():
    return {
        "success": True,
        "message": "MEDAI API is running",
    }


# -----------------------------
# Upload Medical Report
# -----------------------------

@app.post("/api/upload")
async def upload_report(file: UploadFile = File(...)):

    allowed_types = {
        "application/pdf",
        "image/png",
        "image/jpeg",
    }

    # Check file type
    if file.content_type not in allowed_types:
        return {
            "success": False,
            "message": "Unsupported file type. Please upload PDF, PNG, or JPG.",
        }

    # Read file
    contents = await file.read()

    # Check file size — 10 MB
    max_size = 10 * 1024 * 1024

    if len(contents) > max_size:
        return {
            "success": False,
            "message": "File size exceeds the 10 MB limit.",
        }

    # Save file
    file_path = UPLOAD_DIR / file.filename
    file_path.write_bytes(contents)

    return {
        "success": True,
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
        "message": "Medical report uploaded successfully.",
    }


# -----------------------------
# Analyze Medical Report
# -----------------------------

@app.post("/api/analyze")
async def analyze_report(file: UploadFile = File(...)):

    allowed_types = {
        "application/pdf",
        "image/png",
        "image/jpeg",
    }

    # Check file type
    if file.content_type not in allowed_types:
        return {
            "success": False,
            "message": "Unsupported file type.",
        }

    # Read file
    contents = await file.read()

    # Check file size — 10 MB
    max_size = 10 * 1024 * 1024

    if len(contents) > max_size:
        return {
            "success": False,
            "message": "File size exceeds the 10 MB limit.",
        }

    # Save file
    file_path = UPLOAD_DIR / file.filename
    file_path.write_bytes(contents)

    # --------------------------------
    # PDF PROCESSING
    # --------------------------------

    if file.content_type == "application/pdf":

        # Step 1: Extract text
        extracted_text = extract_text_from_pdf(file_path)

        if not extracted_text:
            return {
                "success": False,
                "message": "No readable text was found in the PDF.",
                "filename": file.filename,
            }

        # Step 2: Extract medical parameters
        medical_data = extract_medical_parameters(
            extracted_text
        )

        # Step 3: Classify report
        classification = classify_medical_report(
            medical_data
        )

        # Step 4: Return complete result
        return {
            "success": True,
            "filename": file.filename,
            "message": "Report analyzed successfully.",
            "text": extracted_text,
            "medical_data": medical_data,
            "classification": classification,
        }

    # --------------------------------
    # IMAGE PROCESSING
    # --------------------------------

    return {
        "success": True,
        "filename": file.filename,
        "message": "Image uploaded. OCR processing will be added next.",
        "text": "",
        "medical_data": {},
        "classification": {
            "status": "PENDING",
            "confidence": 0,
            "flags": [],
        },
    }