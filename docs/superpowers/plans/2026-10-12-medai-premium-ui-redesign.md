# MEDAI Premium UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (if selected) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle MEDAI’s four existing frontend routes to match the approved warm, orange-accented design while preserving truthful data, current flows, and privacy protections.

**Architecture:** Add a shared responsive `AppShell` around the existing React Router routes, define design tokens and common styles in the existing CSS system, and keep route-specific content in the existing page components. Upload validation will be shared by browse and drop paths; results and assistant behavior remain locally driven by existing API/session data and curated content.

**Tech Stack:** React 19, Vite, JavaScript, React Router, lucide-react, CSS, Node built-in `node:test`.

**Spec:** `docs/superpowers/specs/2026-10-12-medai-premium-ui-redesign-design.md`

## Global Constraints

- Primary orange is `#FF5A1F`; supporting yellow is `#FFCA4E`; warm off-white is `#FFF4E9`; white is `#FFFFFF`.
- Preserve React, Vite, JavaScript, React Router, lucide-react, and the existing CSS styling approach.
- Preserve backend endpoints, API response shape, upload validation, OCR, extraction and classification behavior, privacy protections, educational content, and all existing uncommitted work.
- Do not add dependencies, backend changes, model changes, or fabricated data.
- Do not add persistent history, user accounts, profile/settings, comparison, notifications, statistics, a separate landing page, sample-report or paste-text functionality, generative AI, analytics, or a database.
- Do not stage or commit files.
- Run frontend lint and production build after each logical task; report checks only when actually run.

## Review Focus

1. Picker and drop uploads must apply the same MIME and 10 MB validation and must not submit when invalid. Task 2 adds pure-function tests for the accepted types and size boundary and manual checks for the real browser drop event.
2. A second upload must clear old results before the request and show only the latest response. Task 2 verifies the existing clear-before-submit path is preserved; Task 5 includes a two-upload manual flow.
3. Missing, malformed, unreadable, partial, or empty results must not crash or appear as completed/normal. Task 3 includes manual checks for each existing Results branch and storage utility tests.
4. Curated Assistant behavior must not become a generative or clinical-advice experience. Task 4 manually checks a supported question and an unsupported/personal question.
5. Narrow screens, keyboard navigation, visible focus, and reduced-motion behavior must remain usable. Task 5 includes viewport and keyboard checks; no browser automation dependency is added.

---

### Task 1: Shared shell, navigation, and design tokens

**Files:**
- Create: `frontend/src/components/AppShell.jsx`
- Create: `frontend/src/components/AppShell.css`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/App.css`
- Modify: `frontend/src/pages/Dashboard.jsx`

**Interfaces:**
- `AppShell` renders shared brand/navigation and an `<Outlet />` for the active route.
- Navigation uses `NavLink` targets `/`, `/upload`, `/results`, and `/assistant`; route labels are Dashboard, Analyze Report, Results, and Health Assistant.
- Existing page components keep their current routes and page-specific responsibilities.

- [x] **Step 1: Create the shared shell.** Add an `AppShell` component using existing lucide icons and `NavLink`, with a compact desktop sidebar, active route styling, and a responsive navigation container. Do not add inert Settings, History, notifications, or Profile controls.
- [x] **Step 2: Nest existing routes under the shell.** Update `App.jsx` to render the existing four page routes through `AppShell`, retaining the existing `sanitizeStoredAnalysis()` call.
- [x] **Step 3: Define shared CSS tokens and base styles.** Update `index.css`, `App.css`, and `AppShell.css` for the approved palette, typography hierarchy, spacing, common cards/buttons, accessible focus, subtle gradients, and reduced-motion preference.
- [x] **Step 4: Move Dashboard content into the shared layout.** Remove Dashboard’s duplicated sidebar/top-level shell markup while preserving its honest no-history state and its upload, assistant, and available latest-result links.
- [x] **Step 5: Verify the shell and Dashboard.** From `frontend/`, run `npm run lint` and `npm run build`; both must exit successfully. Run `node --test src/utils/analysisStorage.test.js`; all existing storage tests must pass.

### Task 2: Upload selection, validation, and drag-and-drop

**Files:**
- Create: `frontend/src/utils/uploadValidation.js`
- Create: `frontend/src/utils/uploadValidation.test.js`
- Modify: `frontend/src/pages/UploadReport.jsx`
- Modify: `frontend/src/pages/UploadReport.css`

**Interfaces:**
- `validateUploadFile(file)` returns `{ valid: true }` for PDF (`application/pdf`), PNG (`image/png`), or JPEG (`image/jpeg`) at or below `10 * 1024 * 1024` bytes; otherwise it returns `{ valid: false, message }` using the current user-facing validation messages.
- Both file-input selection and drop handling call `validateUploadFile(file)` before setting `selectedFile`.
- The existing upload request remains `POST http://127.0.0.1:8000/api/analyze` with multipart field `file`.

- [x] **Step 1: Add tests for the shared file validator.** Use Node’s built-in test runner and synthetic file-like objects. Cover PDF, PNG, JPEG, one byte over the 10 MB limit, exact 10 MB boundary, unsupported MIME, and no selected file; assert only supported/in-limit files pass.
- [x] **Step 2: Run the focused tests and confirm the new helper is not yet implemented.** Run `node --test src/utils/uploadValidation.test.js`; confirm it fails because the helper is absent.
- [x] **Step 3: Implement and wire `validateUploadFile(file)`.** Use the exact accepted MIME types and `10 * 1024 * 1024` byte limit. Replace duplicated validation inside `handleFileChange` with the helper.
- [x] **Step 4: Implement functional drag-and-drop.** Add drag-enter/over/leave/drop handlers to the upload surface. Prevent browser navigation for dropped files; process only the first file using the same validator; keep the hidden file chooser and browse interaction available. Do not start analysis automatically on drop.
- [x] **Step 5: Restyle upload states.** Update `UploadReport.css` for the approved surfaces, drop target, selected file, errors, success, loading, privacy notice, and responsive layout. Preserve request, response handling, storage minimization, and error mapping.
- [x] **Step 6: Verify Upload.** Run the focused test, `node --test src/utils/analysisStorage.test.js src/utils/uploadValidation.test.js`, `npm run lint`, and `npm run build` from `frontend/`. All must pass. If browser testing is available, manually verify file picker and drag-drop; otherwise record the behavior as unverified in browser.

### Task 3: Results presentation

**Files:**
- Modify: `frontend/src/pages/Results.jsx`
- Modify: `frontend/src/pages/Results.css`

**Interfaces:**
- Continue reading only the minimized `medai_result` session entry.
- Keep the six current parameter names, displayed values, existing classification fields/statuses, document type, marker education text and links, and all unavailable/partial branches.
- Use the shared shell supplied by Task 1; the Results page must not introduce a second navigation shell.

- [x] **Step 1: Update Results structure only where needed for the new card layout.** Preserve current result derivation and conditional branches; use semantic sections/headings and accessible status labels without changing API or storage fields.
- [x] **Step 2: Restyle result states and data cards.** Replace dark palette styling in `Results.css` with warm surfaces, orange accents, clear hierarchy, legible data cards, and responsive grids. Retain explicit `N/A`, REVIEW, incomplete, and unavailable wording; do not add mock confidence or charts.
- [x] **Step 3: Verify Results.** Run the session-storage tests, `npm run lint`, and `npm run build` from `frontend/`. With a browser, manually inspect stored values for: no result, malformed result, unreadable response, zero values, partial values, and full result; verify no missing value is styled or labeled as NORMAL. If browser testing is unavailable, explicitly report this gap.

### Task 4: Health Assistant presentation

**Files:**
- Modify: `frontend/src/pages/HealthAssistant.jsx`
- Modify: `frontend/src/pages/HealthAssistant.css`

**Interfaces:**
- Preserve existing topic list, question selection, local topic lookup, answer text, MedlinePlus links, unsupported response, and no-network behavior.
- The shared shell owns route navigation; the page retains its assistant-specific content and controls.

- [x] **Step 1: Adapt assistant markup to the shared layout.** Remove only redundant standalone page/back-navigation wrappers as needed. Keep curated/educational/not-generative disclosures, suggested-question controls, local answer display, source links, and unsupported-question response.
- [x] **Step 2: Restyle the assistant.** Update `HealthAssistant.css` to use shared typography, warm cards, orange actions, visible keyboard focus, readable notices, and responsive question/answer layouts.
- [x] **Step 3: Verify Assistant.** Run `npm run lint` and `npm run build` from `frontend/`. Manually select one supported topic and submit an unsupported/personal interpretation question if browser testing is available; verify local curated behavior and fallback copy. Otherwise report that browser interaction was not tested.

### Task 5: Cross-route responsive and accessibility refinement

**Files:**
- Modify as needed: `frontend/src/components/AppShell.css`
- Modify as needed: `frontend/src/App.css`
- Modify as needed: `frontend/src/index.css`
- Modify as needed: `frontend/src/pages/UploadReport.css`
- Modify as needed: `frontend/src/pages/Results.css`
- Modify as needed: `frontend/src/pages/HealthAssistant.css`

**Interfaces:**
- All routes use the shared shell and palette; page-specific components retain the interfaces defined above.

- [x] **Step 1: Refine responsive breakpoints.** Apply focused responsive rules for sidebar/navigation, page padding, cards, forms, result grids, and assistant questions at desktop, tablet, and mobile widths to prevent clipping and horizontal overflow.
- [x] **Step 2: Refine keyboard and motion behavior.** Add visible global focus indicators, a visible focus state for the file chooser, active-route semantics, and `prefers-reduced-motion` support. If browser testing is available, verify keyboard operation; otherwise report interaction as unverified.
- [x] **Step 3: Run end-to-end manual checks if a browser is available.** Visit Dashboard → Upload → Results; perform a second upload and confirm stale data is cleared; visit Dashboard → Assistant → supported answer → Dashboard; verify empty and malformed result behavior. Use synthetic reports only. Do not claim browser testing if only lint/build ran.
- [x] **Step 4: Run final quality gates.** From `frontend/`, run `node --test src/utils/analysisStorage.test.js src/utils/uploadValidation.test.js`, `npm run lint`, and `npm run build`. From repository root, run `git diff --check`. All commands must be executed and observed; report exact outcomes. Backend tests are unnecessary unless backend files change.

## Execution Notes

- Do not overwrite the existing uncommitted work listed by `git status`; inspect each target file immediately before editing it.
- Keep changes grouped by the tasks above and stop to report any unexpected API, state, or styling issue before broadening scope.
- Do not stage or commit. This plan is a task checklist, not authorization to change files until the user approves the plan and execution method.
