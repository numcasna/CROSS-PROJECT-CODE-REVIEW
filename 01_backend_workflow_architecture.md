# Cross-Project Code Review Finding Tracker

## Backend Workflow & Architecture Document

**Version:** Draft 0.1\
**Status:** Working draft based on the BRD and confirmed project-scope
decisions

## 1. Purpose

Describe the backend workflow and components for a manual
finding-tracking application. The system records findings identified
during code reviews; it does not automatically review code and does not
integrate with GitHub/GitLab APIs in the current scope.

## 2. Confirmed scope

-   Backend: Python + FastAPI, built from scratch.
-   Database: PostgreSQL recommended; final confirmation pending.
-   Frontend: Existing frontend; it will be updated to match the agreed
    scope.
-   Authentication: Admin-created accounts; no self-registration.
-   Users create and edit projects, manage project membership, and
    assign project leads.
-   Only admins can delete projects.
-   Admins can view all projects and findings.
-   Project users can view projects and findings for projects they
    belong to.
-   Admins create, edit, status-manage, and delete findings.
-   Users work on assigned/accessibly visible findings and submit them
    for admin review.
-   User submission changes status to `In Review`; users cannot mark
    findings `Resolved`.
-   Only admins can mark findings `Resolved`.
-   If an admin determines a submitted fix is insufficient, the finding
    moves to `Reopened`.
-   Finding creation date is the finding's start/created date.
-   Feedback and the chronological work-history thread are separate
    concepts.
-   Evidence file types: JPG, PDF, TXT.
-   No repository API integration, automated code review, or agentic
    workflow.

## 3. High-level architecture

1.  **Frontend:** Login, project pages, finding list/detail pages,
    forms, comments/feedback, work-history thread, attachments, and
    dashboards.
2.  **FastAPI REST API:** Authentication, authorization, request
    validation, project and membership operations, finding operations,
    status workflow, comments, attachments, and dashboard queries.
3.  **Service/business-logic layer:** Applies project permissions and
    allowed status transitions; coordinates multi-table updates.
4.  **Data-access layer:** Reads/writes relational records using the
    chosen Python database/ORM stack.
5.  **Relational database:** PostgreSQL is recommended for users,
    projects, membership, repositories, findings, comments, work-history
    entries, status history, and attachment metadata.
6.  **File storage:** Stores attachment bytes outside the relational
    database; the database stores metadata and a storage key/path.
    Storage choice is TBD.

## 4. Authentication and authorization

### Account provisioning

-   No public registration endpoint.
-   An existing authorized admin creates user accounts.
-   The first admin must be provisioned through a controlled setup/CLI
    script or equivalent one-time deployment process.
-   Store a password hash, never a plaintext password.
-   Recommended password hashing: Argon2id.
-   Recommended session approach: short-lived JWT access token, with
    secure browser storage strategy finalized during implementation. For
    a browser frontend, an `HttpOnly`, `Secure`, appropriately
    configured `SameSite` cookie is a strong option; if cookies are
    used, address CSRF protection.
-   `GET /api/auth/me` returns the authenticated user's identity and
    role.
-   Logout/session invalidation design depends on whether refresh tokens
    or server-side sessions are used.

### Authorization principles

-   Every protected request identifies the authenticated user.
-   Backend checks role and resource access; hiding frontend controls is
    not sufficient.
-   Admin can view all projects and findings and perform admin-only
    finding operations.
-   A project user can access only projects where their membership is
    valid.
-   Only admin can delete projects and findings, subject to the final
    deletion policy.
-   Only admin can mark a finding `Resolved`.
-   Only admin can reject a submitted fix by moving it to `Reopened`.
-   The precise permissions for project leads and any additional BRD
    roles must be confirmed before implementation.

## 5. Core workflows

### 5.1 Admin account provisioning

1.  Initial admin is created through a controlled setup procedure.
2.  Admin submits a user-creation form.
3.  API validates required fields and email uniqueness.
4.  Backend hashes the password and stores the user with an assigned
    role and active status.
5.  The user can log in with provisioned credentials. Password
    reset/change policy is a decision to finalize.

### 5.2 Project creation and management

1.  Authenticated user submits project title, description,
    repository/branch details, project members, and project lead.
2.  API validates project fields and verifies that selected members/lead
    are valid accounts.
3.  Backend creates the project and related repository and membership
    records in a transaction.
4.  Users can edit projects, manage membership, and assign project
    leads.
5.  Admin can view all projects and delete projects. Deletion behavior
    (hard delete vs archive/soft delete) is TBD.
6.  Project list/detail responses are scoped to the current user's
    memberships unless the caller is an admin.

### 5.3 Finding creation

1.  Admin selects a project and provides finding title, description,
    repository details, assignee, severity, category/label, due date,
    feedback, and optional attachments.
2.  Backend validates that the project and repository are valid and that
    the assignee is eligible for the project.
3.  Backend generates a unique finding identifier.
4.  Backend creates the finding with status `Open`, created timestamp,
    reviewer/admin identity, and related metadata.
5.  Optional initial feedback and attachments are saved using their own
    records.
6.  The API returns the created finding.

### 5.4 Finding work and submission

1.  Authorized project user views a finding.
2.  User records work updates in the work-history thread and may add
    feedback/comments according to the final permissions.
3.  User submits the finding for admin review, including the resolution
    explanation and optional JPG/PDF/TXT evidence.
4.  Backend verifies that the user can access the project and is allowed
    to submit the finding.
5.  Backend changes status to `In Review` and records the transition in
    status history.
6.  Submission content is stored separately from general reviewer
    feedback and work-history entries as defined by the final data
    model.

### 5.5 Admin review

1.  Admin reviews the submitted explanation and evidence.
2.  If acceptable, admin changes the status to `Resolved`.
3.  If insufficient, admin changes the status to `Reopened` and provides
    feedback/reason according to the final validation rules.
4.  Backend records the previous status, new status, actor, timestamp,
    and reason/comment.
5.  Finding details and dashboard counts reflect the current status.

### 5.6 Finding deletion

-   Only admin can delete findings.
-   The BRD favors disabling normal-user deletion and suggests soft
    deletion/archive by admin. Whether this project uses soft deletion
    or permanent deletion remains to be decided.
-   If audit/history retention is required, deletion must not silently
    erase required audit records.

## 6. Proposed finding statuses

Confirmed statuses from the BRD plus the project-specific addition: -
`Open` - `In Progress` - `In Review` --- added for user submission -
`Resolved` --- admin-only transition - `Reopened` --- used when admin
determines the submitted fix is insufficient - `Rejected` - `Closed`

The exact transition matrix and whether `Resolved`, `Rejected`, and
`Closed` remain separate terminal states must be approved before
implementation. The BRD defines `Rejected` and `Closed`; this project
has explicitly confirmed the `In Review`, `Resolved`, and `Reopened`
behaviors above.

## 7. API request flow

For every protected operation: 1. Frontend sends request. 2.
Authentication layer validates session/token. 3. Authorization layer
checks role and project membership. 4. Pydantic request schema validates
input. 5. Service layer applies business rules and transaction
boundaries. 6. Data-access layer reads/writes database records. 7. API
returns a documented success or error response.

## 8. Non-functional requirements

-   Use database transactions for related changes such as creating a
    project plus memberships.
-   Validate uploaded file type, size, and content; do not trust the
    filename or browser-provided MIME type alone.
-   Restrict attachment types to JPG, PDF, and TXT.
-   Store uploaded files safely outside the web root or in private
    object storage; authorize every download.
-   Use environment variables/secrets management for database
    credentials and signing keys.
-   Configure CORS narrowly for the frontend origin.
-   Provide API documentation through FastAPI's OpenAPI/Swagger support.
-   Add tests for authorization, status transitions, validation, and
    project isolation.

## 9. Decisions still required

1.  Confirm PostgreSQL.
2.  Decide storage for attachment bytes and maximum upload size.
3.  Decide whether project/finding deletion is soft delete or permanent
    deletion.
4.  Finalize role model: Admin and Project User only, or retain
    additional BRD roles.
5.  Define exact permissions for project leads and membership changes.
6.  Finalize status transition matrix, including `Rejected` and
    `Closed`.
7.  Define password change/reset and session expiration policy.
8.  Confirm whether users can edit finding fields or only submit
    work/proof.
9.  Define dashboard metrics, filters, and export scope.
