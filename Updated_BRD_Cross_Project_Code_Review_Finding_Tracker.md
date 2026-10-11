# BUSINESS REQUIREMENTS DOCUMENT

## Cross-Project Code Review Finding Tracker

Updated project-specific scope | Version 1.0 | 10 October 2026

**Document purpose** Faculty overview and agreed MVP requirements

**Backend direction** Python / FastAPI

**Authentication** Admin-created accounts; no public registration

**Database** PostgreSQL recommended; confirmation pending

Cross-Project Code Review Finding Tracker • BRD v1.0 Page 1

## 1. Document Purpose

This Business Requirements Document (BRD) describes the agreed project scope for the Cross-Project Code Review Finding Tracker. It is intended to give faculty, mentors, and the implementation team a concise overview of the product, its users, its key workflows, and the capabilities included in the current release. This document reflects the project-specific scope clarified during discussion. It is not a replacement for the supporting technical documents: the Backend Workflow & Architecture Document, Database Schema & Data Model, and API Contract define implementation details.

## 2. Project Overview

The Cross-Project Code Review Finding Tracker is a web application for organizing projects and tracking code-review findings across those projects. In the current release, findings are entered and managed manually. The application records their status, feedback, work history, and supporting evidence, and provides role-appropriate access to projects and findings. The central requirement is a functional finding-management workflow: an administrator can create, view, edit, delete, and manage the lifecycle of findings; project users can access their projects and submit work for review; only an administrator can mark a finding as Resolved.

## 3. Objectives

- Provide one place to maintain projects and their associated code-review findings.
- Allow administrators to manage findings and validate submitted fixes.
- Allow project users to manage project information and membership within the agreed permissions.
- Keep feedback, work-history updates, status changes, and evidence organized and traceable.
- Enforce account authentication, roles, and project-level access in the backend.
- Deliver an MVP without Git provider integration or automated code analysis.
## 4. Scope

**4.1 In Scope**
- A web frontend, with the existing frontend updated to match the agreed product behavior.
- A new backend implemented using Python and FastAPI.
- Admin-provisioned user accounts; public self-registration is not included.
- Login, logout, current-user identity, and role-based authorization.
- Project creation and editing by users; project membership management and project-lead assignment by users, subject to authorization rules.
- Admin visibility across all projects and findings.
- Project users can view projects and findings for projects they are members of.
- Project records include at minimum a project name, repository information, project members, and project lead.
- Admin creation, viewing, editing, deletion, and lifecycle management of findings.
- Finding details including title, description, project/repository association, severity/category, status, creation date, and other agreed fields.
- Users can submit a finding's work/fix for admin review. Submission changes the finding status to In Review.
- Only admins can mark findings Resolved. If a submitted fix is insufficient, the admin can move the finding to Reopened.
- Separate records for feedback, chronological work-history updates, and status-change history.
- Evidence attachments in JPG, PDF, and TXT formats, subject to server-side validation and a configured size limit.
- Project/finding lists, details, filtering, and summary views to the extent supported by the finalized frontend and API contract.
## 5. Out of Scope / Exclusions

- Connecting to GitHub, GitLab, Bitbucket, or any other Git provider/API.

- Cloning, fetching, or synchronizing repository contents.
- Automatically running code reviews, static analysis, CI jobs, or automated vulnerability scans.
- Agentic/AI-driven review, autonomous remediation, or autonomous status decisions.
- Automatically detecting findings from source code; findings are created manually by an admin.
- Public user registration; accounts are created by an admin.
- Allowing project users to mark findings Resolved directly.
- Allowing project users to delete projects or findings.
- Treating a user submission as final approval; an admin must review it.
- Any unconfirmed integrations, notifications, exports, SSO, or advanced analytics not explicitly included in the agreed MVP.
## 6. User Roles and Permissions

**6.1 Administrator**
- Create user accounts and assign an allowed role.
- View all projects and findings.
- Create, view, edit, delete, and manage finding status.
- Review user submissions and decide whether to mark a finding Resolved or Reopened.
- Provide feedback and participate in the work-history thread.
- Delete projects.
**6.2 Project User**
- Log in using an admin-provisioned account.
- Create and edit projects.
- Manage project membership and assign project leads, within the final authorization rules.
- View projects and findings for projects they are permitted to access.
- Add work updates and submit a finding for admin review.
- Provide or view feedback according to the finalized permissions.
- Cannot delete projects or findings and cannot mark a finding Resolved.
**6.3 Permission Principle** The backend must enforce permissions on every protected request. Hiding a button in the frontend is not sufficient. Project users must not gain access to another project's data merely by changing an ID in a request.
## 7. Core Business Workflows

**7.1 Account Provisioning and Login** – The first administrator is created through a controlled setup procedure. – An administrator creates user accounts; there is no public registration flow. – The user logs in with provisioned credentials. – The backend verifies credentials securely and applies role and project-access checks to subsequent requests. The proposed implementation uses password hashing and JWT-based authentication. Exact browser token/cookie handling, session expiry, and password-reset behavior are technical decisions to finalize.
**7.2 Project Management** – An authenticated user creates a project and supplies its required information, including project name, repository details, members, and project lead. – The backend validates referenced users and saves project information and related membership/repository records. – Users with appropriate access can edit project details, manage membership, and assign a lead.

– Administrators can view all projects and are the only role allowed to delete a project.

**7.3 Finding Creation** – An administrator selects a project and its repository, enters the finding details, and optionally assigns a user and due date. – The backend validates the project/repository relationship and required fields, generates a finding identifier, and records the creation timestamp. – The finding starts in Open status unless the approved status rules specify otherwise. – The administrator can add feedback and supporting evidence.
**7.4 User Work and Submission** – A project user opens a finding they are authorized to access. – The user records progress in the work-history thread and may attach supported evidence. – When ready, the user submits the work/fix for review. – The backend changes the finding status to In Review and records the status change and submission event. Submission does not resolve the finding; it signals that the administrator should review the submitted work.
**7.5 Administrator Review** – The administrator reviews the submitted work, evidence, and related history. – If the fix is acceptable, the administrator marks the finding Resolved. – If the fix is insufficient, the administrator moves the finding to Reopened and may provide a reason or feedback. – The backend records the actor, timestamp, previous status, new status, and any required reason.
**7.6 Feedback and Work History** Feedback is a reviewer comment/feedback concept. The work-history thread is a chronological record of work and updates by both users and administrators. Status history is a separate audit-style record of lifecycle transitions. These three concepts should remain distinct in the data model.
## 8. Finding Statuses

The current working status set is Open, In Progress, In Review, Resolved, Reopened, Rejected, and Closed. In Review is used when a project user submits work for administrator review. Only an administrator can set Resolved. Reopened is used when the administrator determines that a submitted fix is insufficient. The complete allowed transition matrix—including how Rejected and Closed are used and whether all statuses are needed in the MVP—must be approved before implementation. The backend must reject invalid status transitions.

## 9. Key Information Managed

- User: name, email, password hash, role, active state, timestamps.
- Project: name, description, creator, project lead, members, timestamps, and archive/deletion state if applicable.
- Repository: project association, repository name/URL, branch metadata, technology, active state. These are manually entered records, not live Git integrations.
- Finding: identifier, title, description, project/repository, severity, category, status, creator, reviewer, assignee, creation date, due date, and timestamps.
- Feedback: finding, author, message, and timestamps.
- Work history: finding, author, entry type, update text, and timestamp.
- Status history: finding, old/new status, actor, reason, and timestamp.
- Attachment metadata: finding, uploader, original filename, validated type, size, storage reference, purpose, and timestamp.
## 10. Non-Functional Requirements

- Security: password hashes only; protected endpoints; least-privilege authorization; no secrets committed to source control.
- Data isolation: project users only access data permitted by their membership and role.

- Validation: backend validates required fields, status transitions, foreign-key relationships, and file uploads.
- Attachment safety: only JPG, PDF, and TXT are allowed; validate file content/type and enforce a maximum size. Store files in private storage and authorize downloads.
- Integrity: related writes such as project creation and status-history recording should use database transactions.
- Maintainability: separate API routes, business/service logic, and data-access responsibilities.
- API documentation: expose and maintain the FastAPI OpenAPI/Swagger contract.
- Testing: test authentication, role permissions, project isolation, CRUD behavior, and status transitions.
## 11. Proposed Technology Direction

- Backend framework: Python FastAPI.
- Database: PostgreSQL recommended; not yet formally confirmed.
- Authentication: admin-created accounts, secure password hashing, and JWT-based authentication proposed.
- Repository handling: manual entry only; no Git provider integration.
- File storage: a private local or object-storage solution is required; provider remains undecided.
These are implementation recommendations and must not be treated as finalized choices where this document explicitly says they are pending.

## 12. Success Criteria / Acceptance Summary

- An administrator can log in and create user accounts.
- Users can create and edit projects, manage membership, and assign project leads within the agreed permissions.
- An administrator can view all projects; a project user sees only authorized projects.
- An administrator can create, view, edit, and delete findings.
- A project user can view an authorized finding, add a work update, and submit it for review.
- Submission moves the finding to In Review, not Resolved.
- Only an administrator can mark a finding Resolved or Reopened.
- The application stores feedback, work-history entries, and status history separately.
- Allowed evidence formats are restricted to JPG, PDF, and TXT, with server-side validation.
- Protected endpoints reject unauthenticated or unauthorized access.
## 13. Assumptions, Dependencies, and Open Decisions

- PostgreSQL is recommended but awaits confirmation.
- The exact role model and any additional BRD-defined roles need confirmation.
- The precise permissions for project leads and membership management need confirmation.
- The final status transition matrix needs confirmation, especially for Rejected and Closed.
- Project and finding deletion policy—soft delete/archive versus permanent deletion—needs confirmation.
- Attachment storage provider and maximum file size need confirmation.
- Password reset, initial credential delivery, session expiry, and logout invalidation need confirmation.
- The exact set of finding fields, category values, filters, dashboard metrics, and any export functionality must match the approved frontend/API scope.
- The existing frontend must be reviewed against the API contract before implementation is considered complete.
## 14. Supporting Technical Documents

This BRD should be read alongside these three implementation documents:

- Backend Workflow & Architecture Document — explains component responsibilities and the order of backend operations.
- Database Schema & Data Model — defines entities, fields, relationships, constraints, and indexes.

- API Contract — defines endpoint paths, methods, request/response behavior, permissions, and error handling.
Together, these documents provide the faculty-facing requirements overview and the implementation baseline. Any unresolved items should be agreed and recorded before the corresponding feature is built.
