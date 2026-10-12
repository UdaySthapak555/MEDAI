# MEDAI — AI-Based Medical Report Classification and Health Assistant

MEDAI is an educational prototype that extracts supported information from medical reports, screens a small set of laboratory markers with transparent rules, and predicts a document category with a text-classification model. It also provides locally curated explanations of supported markers and general health topics.

MEDAI is not a diagnostic system and is not a substitute for advice from a qualified healthcare professional.

## Project objectives

- Accept supported PDF and image reports and extract readable text.
- Identify a limited set of lab markers when their values and units can be interpreted safely.
- Keep rule-based lab screening distinct from machine-learning document categorization.
- Show cautious results, including partial and unavailable states, with educational context.
- Provide a small local health education assistant without sending questions to an AI service.

## Implemented features

- Upload PDF, PNG, and JPEG reports up to 10 MB, with file selection and drag-and-drop validation.
- Extract selectable text from PDFs and use Tesseract OCR for scanned PDF pages and images when configured.
- Extract hemoglobin, RBC, WBC, platelet, glucose, and total cholesterol values for recognized units and formats. Missing, conflicting, or unsupported values remain unavailable.
- Apply rule-based screening thresholds to the supported lab values. Incomplete results require review; this logic is not a trained model.
- Predict one of 14 source-provided document categories using a local TF-IDF and LogisticRegression pipeline when the text passes the model's English and minimum-text checks.
- Show curated marker explanations and source links on the Results page, plus a local assistant for report-reading basics and the six supported marker topics.
- Keep the latest minimized analysis in tab-scoped `sessionStorage` for the current Results experience. Extracted report text and the uploaded filename are excluded from that stored result. There is no persistent report-history feature.
- Expose `GET /`, `POST /api/upload`, and `POST /api/analyze` through FastAPI.

## Technology stack

- **Frontend:** React, Vite, React Router, Axios, and lucide-react.
- **Backend:** Python, FastAPI, Uvicorn, and multipart upload support.
- **Document processing:** pypdf for PDF text, pypdfium2 and Pillow for OCR preparation, and the separately installed Tesseract OCR engine with English (`eng`) language data.
- **Document-type ML:** scikit-learn TF-IDF feature pipelines and LogisticRegression; joblib loads the saved pipeline.
- **Tests:** Python `unittest` tests and Node's built-in test runner for frontend utility tests. The frontend package has lint and production-build scripts, not an `npm test` script.

## Architecture and processing workflow

1. The React application provides Dashboard, Upload Report, Results, and Health Assistant routes.
2. The upload page validates a selected or dropped file and posts it as multipart field `file` to `http://127.0.0.1:8000/api/analyze`.
3. FastAPI validates the filename, extension, declared type, file signature, and 10 MB limit. Analysis reads the upload in memory; it does not create a persistent report copy.
4. PDF text is extracted with pypdf. Pages without extractable text, and uploaded images, use the local Tesseract OCR pipeline. OCR requires the native Tesseract executable and English language data.
5. The extracted text is passed separately to the medical parameter extractor and the document-type model. The lab classifier applies existing rules to the extracted values; the ML model predicts a document category from report text.
6. The backend response contains extracted text, medical data, the lab classification, and document-type result. Before browser storage, the frontend keeps only supported numeric marker values and the minimal classification/document-type fields needed by Results.
7. Results shows available values, incomplete/unavailable states, document category, and relevant curated explanations. The assistant selects from local educational content and does not call the backend or an external AI service.

## Document-type ML and lab-marker screening

These are separate functions:

| Component | Method | Output and limits |
| --- | --- | --- |
| Document-type classifier | Trained scikit-learn TF-IDF + LogisticRegression pipeline. It uses report text to predict the source `doc_type_id` among 14 categories. | English-only research prototype. Confidence is not calibrated; the API does not report a probability. Short, unsupported-script, or insufficiently English text can yield an unavailable result. |
| Lab-marker assessment | Deterministic Python rules applied to recognized, unit-normalized values for six markers. | `NORMAL`, `REVIEW`, or `ATTENTION` according to the existing prototype thresholds and completeness rules. This is not ML and these statuses are not diagnoses. |

The local training experiment reads the supplied IndicPHI JSONL train and evaluation splits, filters to English, uses only `text` as model input, and retains the original 14 document-type labels. It compares a majority-class baseline, TF-IDF with LogisticRegression, and TF-IDF with LinearSVC. The saved evaluation artifact currently reports 22,554 training records and 3,982 evaluation records overall, with 1,033 English training records and 182 English evaluation records. Both text models report accuracy, macro-F1, and weighted-F1 of 1.00 on that English evaluation subset; the majority baseline reports accuracy 0.0714 and macro-F1 0.0095.

These are results on a small English subset of a synthetic dataset, not evidence of performance on real clinical reports. Synthetic templates or identifiers may make the task easier, and evaluation support is limited for some labels. The model has not been validated on real reports or OCR output. The dataset card lists MIT and says the personas come from NVIDIA Nemotron-Personas-India, which is listed under CC BY 4.0; attribution and source links are in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). This repository includes only the LogisticRegression inference pipeline needed by the API. Raw JSONL datasets, the saved evaluation report, and the alternative LinearSVC pipeline remain local and excluded.

## Requirements

- Windows with PowerShell.
- Node.js and npm for the frontend.
- Python and the project virtual environment at `backend/venv` for the documented commands. The backend requirements are in `backend/requirements.txt`.
- Tesseract OCR installed separately with English language data for OCR of scanned documents and images. Set `TESSERACT_CMD` if the executable is not on `PATH`; the backend invokes Tesseract with the `eng` language.
- The frontend development server uses port 5173 by default. The backend API uses port 8000 and allows the configured local Vite origins.

## Setup and run on Windows

Open two PowerShell terminals from the repository root.

### Terminal 1: backend

If the project virtual environment already exists:

```powershell
Set-Location .\backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

For a fresh local environment, create it and install the listed backend requirements before starting the API:

```powershell
Set-Location .\backend
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

The API health endpoint is `http://127.0.0.1:8000/`. The document-type model artifact is expected at `backend/artifacts/indicphi_document_type/logistic_regression.joblib`; if it cannot be loaded, the API reports document categorization as unavailable while analysis can continue.

### Terminal 2: frontend

```powershell
Set-Location .\frontend
npm ci
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). Keep the backend running while using report upload and analysis.

## Tests and quality checks

Run the backend's available tests with Python's built-in test runner:

```powershell
Set-Location .\backend
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run the frontend utility tests and checks:

```powershell
Set-Location .\frontend
node --test src/utils/analysisStorage.test.js src/utils/uploadValidation.test.js
npm run lint
npm run build
```

The frontend package does not define an `npm test` script. These tests use synthetic data; do not place real patient reports in test fixtures.

## API endpoints

| Method and path | Purpose |
| --- | --- |
| `GET /` | Basic API health response. |
| `POST /api/upload` | Validates an upload and returns metadata; does not retain a report copy. |
| `POST /api/analyze` | Extracts text, recognized lab values, rule-based lab assessment, and document category for a PDF, PNG, or JPEG upload. |

Both POST routes accept multipart form data with the field name `file`. The upload limit is 10 MB. The frontend currently calls `/api/analyze` at `http://127.0.0.1:8000`.

## Privacy and safety

Medical reports and extracted values can be sensitive. The backend processes report contents in memory for analysis and does not intentionally save a second copy. The frontend temporarily stores a minimized result in the current tab's session storage; client-side storage and memory are not a secure-deletion guarantee. Do not use real patient data for project testing or commit reports, extracted text, credentials, or environment secrets.

MEDAI is an educational assistance prototype. Extracted values may be missing or incorrect, OCR can misread a report, and the document-type model is not validated on real-world data. Rule-based flags and document categories do not diagnose disease, recommend treatment, or replace professional medical advice. Consult a qualified healthcare professional for interpretation of personal results.
