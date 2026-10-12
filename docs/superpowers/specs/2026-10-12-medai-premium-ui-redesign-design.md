# MEDAI Premium UI Redesign — Design Specification

**Date:** 2026-10-12
**Status:** Approved
**Scope:** Frontend visual redesign of the four existing MEDAI routes

## 1. Goal and constraints

Apply the visual language of the supplied MEDAI UI/UX design board to the existing React application while keeping its current behavior truthful and functional. The redesign covers Dashboard (`/`), Upload Report (`/upload`), Results (`/results`), and Health Assistant (`/assistant`).

Preserve React, Vite, JavaScript, React Router, lucide-react, the existing CSS styling approach, backend endpoints, API response shape, upload validation, OCR, extraction and classification behavior, privacy protections, educational content, and all existing uncommitted work. No dependency changes, backend changes, model changes, or fabricated data are in scope.

The board is a visual reference, not a complete feature specification. The reference shows persistent history, comparison charts, profile/settings, sample reports, paste-text input, model confidence claims, and a marketing landing page. Those features are not represented as available unless the existing project already implements them truthfully. MEDAI currently has no persistent report-history API, so the Dashboard must retain its honest empty state and must not show fabricated counts, reports, or activity.

## 2. Approved design decisions

### Palette

- Primary orange: `#FF5A1F`
- Supporting yellow: `#FFCA4E`
- Warm off-white: `#FFF4E9`
- White: `#FFFFFF`
- Use accessible dark neutral text, light neutral borders, and subtle warm gradients as supporting colors. Do not rely on color alone to convey result status.

### Shared visual system

All four routes will use consistent navigation, typography, spacing, rounded cards, button and input styling, visible focus states, and subtle hover/transition treatments. Desktop uses a compact persistent sidebar with a clear active route. Smaller screens use a responsive navigation pattern and stacked content. Existing `lucide-react` icons are reused. The existing CSS approach is retained; Tailwind or another styling dependency is not introduced.

### Dashboard

Keep Dashboard as the root route; do not add a separate marketing landing page. Provide functional links to upload, latest session result when available, and the Health Assistant. Preserve the truthful no-history state. Do not introduce fake report history, statistics, account/profile details, notification state, or settings controls.

### Upload Report

Provide a clear file-selection experience with supported formats, 10 MB size limit, selected-file state, loading state, success/error feedback, and a privacy notice consistent with actual processing. Preserve the real `POST /api/analyze` multipart request, `file` field, current validation, error handling, and minimized session result storage.

The upload surface may advertise drag-and-drop only if actual drag events are implemented correctly and share the existing validation path. Browse-file selection must remain available. Do not add paste-text or sample-report modes because they are not currently supported.

### Results

Display only the current API response and existing locally stored minimum result data. Preserve document type and lab classification objects, current status semantics, partial/unavailable behavior, marker values, curated explanations, authoritative links, and disclaimers. Do not introduce fabricated confidence, charts, unsupported interpretations, diagnoses, or treatment recommendations. If result data is missing or malformed, retain the existing safe empty/re-upload behavior.

### Health Assistant

Restyle the current local curated experience. Preserve supported topics, locally stored educational answers, source links, suggested questions, and unsupported-question behavior. Clearly label it as educational and curated, not generative AI or diagnostic. Questions remain local and are not sent to an external service.

## 3. Application structure and data flow

Create or adapt one shared app shell for route navigation and common layout, using the existing React Router configuration. Page-specific components remain responsible for their current content and behavior. Shared styling should live in global tokens/base rules and reusable shell/component classes, while route-specific CSS handles each page layout.

The upload flow remains:

1. User selects or drops a file.
2. The existing client validation runs.
3. The frontend sends the file to the existing FastAPI analysis endpoint.
4. The response is minimized by existing privacy logic before temporary session storage.
5. Results reads and validates the stored response, displaying the existing actual values and states.

No report text or new sensitive data is added to browser storage, and no new persistence or external service is introduced.

## 4. Responsive and accessibility requirements

- Desktop navigation is compact and consistent across all four routes.
- Tablet layouts adapt spacing and card grids without clipping.
- Mobile layouts stack cards, keep controls easy to use, and provide usable route navigation.
- Prevent horizontal overflow at supported viewport widths.
- Maintain semantic headings, labels, keyboard operation, visible focus indicators, and appropriate status/error announcements.
- Use motion sparingly and honor `prefers-reduced-motion` for transitions or animation.
- Maintain readable text contrast and do not use color as the only status indicator.

## 5. Error and unavailable states

Retain existing upload error messages for invalid formats, oversize files, backend connection failures, OCR configuration/timeouts, and unreadable input. Keep uploading/loading controls disabled while the request is in flight. Preserve distinct Results states for unavailable, incomplete, partial, and completed analyses. The Dashboard history placeholder remains explicit that history is unavailable.

## 6. Implementation sequence

1. Inspect current selectors and define shared palette, typography, focus, button, card, and page-shell styles.
2. Add shared responsive navigation/layout and restyle Dashboard without changing its truthful data state.
3. Restyle Upload Report and implement real drag-and-drop through the existing validation path if feasible without changing API behavior.
4. Restyle Results while preserving result logic and marker education.
5. Restyle Health Assistant while preserving local answers and safety messaging.
6. Refine responsive behavior, keyboard/focus behavior, contrast, and reduced-motion support.

Keep changes focused and preserve pre-existing dirty work. Run frontend lint and production build after each logical stage. At completion run relevant existing frontend tests, backend tests only if backend files are changed, and `git diff --check`. Do not claim browser testing unless an actual browser interaction test is performed. No files are staged or committed.

## 7. Verification criteria

- Existing routes and navigation links work, including Dashboard → Upload, Dashboard → Assistant, Assistant → Dashboard, and Upload → Results.
- Upload accepts only the existing supported types and configured size limit; selected and dropped files use the same validation.
- Each upload clears stale prior results and displays only the latest completed API response.
- Results render complete, partial, unavailable, and malformed/missing-result states without converting missing values to normal.
- Marker explanations and their authoritative source links remain visible only for relevant available markers.
- Assistant suggested questions return the existing curated answers; unsupported and personal clinical advice queries do not produce fabricated guidance.
- Dashboard never presents fabricated history or statistics.
- Layout remains usable at desktop, tablet, and mobile widths with keyboard-visible focus.
- Existing storage privacy protections, API contract, extraction, OCR, classification, and thresholds are unchanged.

## 8. Out of scope

- Persistent report history, user accounts, profile/settings, report comparison, notifications, or aggregate statistics.
- A separate marketing landing page, demo video, sample report, or paste-text feature.
- Generative AI, LLMs, external AI services, API keys, database, analytics, or new dependencies.
- Backend/API, OCR, extraction, classifier/model, threshold, or medical-content changes.
- Clinical validation, diagnostic claims, personalized treatment, or prescriptions.
