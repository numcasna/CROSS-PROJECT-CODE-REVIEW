# Cross-Project Code Review Finding Tracker — Frontend

This ZIP contains the React/Vite frontend only. It includes the workflow and UI updates aligned with the supplied API contract and workflow documents. Backend and database files are intentionally excluded.

## Run locally

1. Install Node.js (LTS).
2. In this folder, run `npm install`.
3. Run `npm run dev`.
4. Open the local URL printed by Vite.

## Workflow reflected in the UI

- Admins create findings with a project, repository, severity, finding label, assignee, due date, description, optional recommendation, and evidence attachments.
- Project users can accept an Open finding to move it to In Progress.
- Users submit completed work for admin review; this moves the finding to In Review, not Resolved.
- Admin review supports accepting the fix (Resolved) or reopening it (Reopened) with mandatory feedback.
- Evidence file selection is limited to JPG, PDF, and TXT.
- The UI keeps feedback/work discussion separate from status history presentation where supported by the existing frontend model.

## Important

This is a frontend-only demo and currently uses mock data in React context. It does not make live HTTP requests or persist changes to a backend/database. The API contract is used as the design reference for UI behavior; live integration requires a separately supplied API service.


## Updated frontend navigation

- Admin: Findings and Projects only. Admins can view all project details but cannot create or edit projects.
- User: My Findings and Projects only. Users can create projects using the dedicated Create Project screen.
- Finding status history is shown in the finding details; admin review actions support resolving, reopening, rejecting, and closing eligible findings.
- This remains a frontend demo using mock state; no backend or database is included.
