# MEDAI Project Instructions

## Project layout
- `frontend/` contains the React application, Vite configuration, and ESLint configuration.
- `frontend/src/pages/` contains the Dashboard, UploadReport, and Results pages.
- `backend/main.py` defines the FastAPI application and HTTP endpoints.
- `backend/services/` contains PDF text extraction, medical parameter extraction, and report classification.
- `backend/uploads/` is used to store uploaded reports. Treat its contents as sensitive user data.
- `backend/requirements.txt` lists Python dependencies.
- The repository root and `frontend/` are separate npm projects, not an npm workspace. The root package has its own manifest and lockfile; the frontend package has its own manifest and lockfile and defines the frontend scripts.

## Install and start the frontend
Run these commands from the repository root in a PowerShell terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Run the frontend checks from the `frontend/` directory:

```powershell
npm run lint
npm run build
```

Do not use `npm ci` at the repository root as the frontend installation command.

## Start the backend
Run the backend from its directory so the relative `uploads/` path resolves there:

```powershell
Set-Location backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

## Checks and tests
- The frontend defines `lint` and `build` scripts as documented above.
- No frontend test script, backend test suite, or backend lint script was found during inspection.
- Do not claim lint, build, or tests passed unless they were actually run and their results observed. Report unavailable checks and any failures accurately.

## API and integration conventions
- `GET /` returns a basic API health response.
- `POST /api/upload` accepts multipart form data with a `file` field and returns upload metadata.
- `POST /api/analyze` accepts multipart form data with a `file` field and returns extraction and classification results.
- The current upload flow accepts PDF, PNG, and JPEG files up to 10 MB.
- The frontend currently calls `http://127.0.0.1:8000/api/analyze`; backend CORS allows `http://localhost:5173` and `http://localhost:5174`.
- Keep frontend request URLs, multipart field names, response handling, and backend route behavior in sync when changing the integration.
- The frontend stores the analysis response temporarily in `sessionStorage` under `medai_result`.

## Medical data, secrets, and privacy
- Treat reports and extracted medical information as sensitive personal data. Do not print, copy, commit, or send their contents to external services unless the task requires it and the user approves.
- Never use real reports or personal data as test fixtures; use synthetic or explicitly approved data.
- Keep uploaded reports and user-specific data out of Git. Preserve the root ignore rule for `backend/uploads/`.
- Do not expose or commit `.env` files, API keys, credentials, tokens, or private keys. Keep placeholder-only examples in `.env.example` files.
- If a task requires elevated permissions, external services, credentials, or actions outside the current workspace, explain why and ask for approval before proceeding.

## Git and change safety
- Before editing project files, inspect `git status` and preserve existing uncommitted user changes.
- Make focused changes that follow existing project conventions. Avoid unrelated rewrites.
- Ask before destructive actions, dependency changes, or major architectural decisions.
- Do not initialize Git, stage, or commit files unless the user asks.
- Before claiming a change is complete, run relevant available checks and report exactly what ran, its result, and any checks that were unavailable.
- Use applicable Superpowers workflows. Use Context7 when current library documentation is needed.
