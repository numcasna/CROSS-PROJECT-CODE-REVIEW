# Cross-Project Code Review Finding Tracker

## API Contract

**Version:** Draft 0.1\
**Base path:** `/api`\
**Backend:** Python + FastAPI\
**Status:** Proposed contract based on current notes; schemas and
unresolved rules require review

## 1. Purpose and conventions

This contract defines the frontend/backend interface for a manual
finding tracker. There is no Git provider API integration and no
automated/agentic code-review processing in the current scope.

-   JSON for ordinary request/response bodies.
-   `multipart/form-data` for file uploads.
-   Use ISO 8601 timestamps with timezone offsets; date-only fields use
    `YYYY-MM-DD`.
-   Use UUIDs for internal resource IDs and a separate human-readable
    finding code such as `CRF-2026-0001`.
-   Backend must enforce authorization and project membership.
-   Authentication uses admin-provisioned accounts; public registration
    is not supported.
-   Exact response envelope and error schema should be standardized
    before implementation.

## 2. Authentication and account administration

### `POST /api/auth/login`

Authenticates an existing provisioned account. No self-registration. -
Request: `email`, `password` - Success: authenticated user/session
credentials - Errors: `401` invalid credentials; `403` inactive
account - Token/cookie transport and refresh strategy TBD.

### `POST /api/auth/logout`

Ends the authenticated session or revokes the refresh token, depending
on selected session design. - Success: `204` - Errors: `401`
unauthenticated if required by the chosen design.

### `GET /api/auth/me`

Returns the current user's ID, name, email, role and active status. -
Success: `200` - Errors: `401`

### `POST /api/users`

Admin-only: create a user account. - Request: `name`, `email`, initial
password or secure invite/setup flow, `role` - Success: `201` - Errors:
`400` validation error; `401` unauthenticated; `403` not admin; `409`
email already exists. - Password provisioning/reset flow must be
finalized; never return password hashes.

### `GET /api/users`

Admin-only or permission-scoped user listing for dropdowns. The exact
visibility rules must be finalized. - Optional filters: `project_id`,
`role`, `is_active` - Success: `200`

## 3. Projects

### `POST /api/projects`

Authenticated project user creates a project. - Request: `name`,
`description`, repository/branch entries, member IDs, project lead ID -
Success: `201` with project ID and created details - Errors: `400`
invalid fields; `401` unauthenticated; `403` invalid operation; `404`
referenced user not found.

### `GET /api/projects`

Returns projects visible to the caller. - Admin: all projects. - Project
user: only projects where the user is a member, unless final policy
explicitly grants another scope. - Optional filters: search, lead,
active status. - Success: `200`

### `GET /api/projects/{project_id}`

Returns project title, description, lead, repositories, and members. -
Success: `200` - Errors: `401`, `403` or `404` according to the selected
resource-disclosure policy.

### `PATCH /api/projects/{project_id}`

Project user with appropriate access edits project information. -
Request: permitted fields such as `name`, `description`,
`project_lead_id` - Success: `200` - Errors: `400`, `401`, `403`, `404`

### `DELETE /api/projects/{project_id}`

Admin-only. - Success: `204` - Deletion strategy (soft delete/archive vs
permanent delete) and dependent-record behavior TBD. - Errors: `401`,
`403`, `404`, `409` if deletion is blocked by dependent records.

### `GET /api/projects/{project_id}/members`

Returns project members. - Success: `200`

### `PUT /api/projects/{project_id}/members`

Replaces or synchronizes project membership. The exact semantics must be
confirmed. - Request: list of user IDs - Authorized project user
according to current scope. - Success: `200` - Errors: `400`, `401`,
`403`, `404`

### `GET /api/projects/{project_id}/repositories`

Returns manually registered repositories and branch metadata. - Success:
`200`

### `POST /api/projects/{project_id}/repositories`

Adds a repository record; no external Git API call. - Request: `name`,
`repository_url`, optional `branch_name`, optional `technology` -
Success: `201` - Errors: `400`, `401`, `403`, `404`

## 4. Findings

### `POST /api/findings`

Admin-only finding creation. - Request fields: `title`, `description`,
`project_id`, `repository_id`, `severity`, `category`, optional
`assignee_id`, `due_date`, branch reference, initial feedback, and
attachment metadata/files via an agreed upload flow. - Backend generates
`finding_code`; client must not choose it. - Initial status: `Open`. -
Creation date is recorded by the backend. - Success: `201` - Errors:
`400` validation error; `401`; `403`; `404` invalid
project/repository/user; `409` uniqueness conflict if applicable.

### `GET /api/findings`

Returns findings visible to the caller. - Admin: all findings. - Project
user: findings only in projects where they have access. - Suggested
query filters: `project_id`, `repository_id`, `status`, `severity`,
`category`, `assignee_id`, `created_from`, `created_to`, `due_before`,
`search`, `sort`, `page`, `page_size`. - Success: `200` with pagination
metadata and results.

### `GET /api/projects/{project_id}/findings`

Returns findings for a project after authorization checks. - Success:
`200` - Errors: `401`, `403`/`404`

### `GET /api/findings/{finding_id}`

Returns full finding details, including project/repository summary,
assignee, severity, category, dates, current status, feedback,
work-history thread, attachments, and status history where permitted. -
Success: `200` - Errors: `401`, `403`/`404`

### `PATCH /api/findings/{finding_id}`

Admin-only for editing finding details unless specific user-editable
fields are approved. - Request: permitted mutable finding fields. -
Success: `200` - Errors: `400`, `401`, `403`, `404`

### `DELETE /api/findings/{finding_id}`

Admin-only. - Success: `204` - Deletion strategy and history retention
TBD. - Errors: `401`, `403`, `404`, `409` where deletion is blocked.

## 5. Finding status and submission

### `POST /api/findings/{finding_id}/submit-for-review`

Authorized project user submits work for admin review. - Request:
`resolution_description` and optional attachment IDs/files (JPG, PDF,
TXT). - Backend changes status to `In Review`, records status history,
and creates the appropriate work-history entry. - User cannot set status
to `Resolved` directly. - Success: `200` or `202` (choose consistently
based on whether processing is asynchronous; this workflow is expected
to be synchronous). - Errors: `400` invalid status/fields; `401`; `403`;
`404`; `409` invalid transition.

### `PATCH /api/findings/{finding_id}/status`

Admin-only status transition endpoint. - Request: `status`, optional
`reason`/`comment`. - Admin may mark an `In Review` finding `Resolved`
if accepted. - If the submitted fix is insufficient, admin can change it
to `Reopened`. - Other transitions involving `Open`, `In Progress`,
`Rejected`, and `Closed` need a finalized transition matrix. - Success:
`200` - Errors: `400` invalid status; `401`; `403`; `404`; `409`
disallowed transition.

## 6. Feedback and work-history thread

These are separate concepts and must not be collapsed into one table by
default.

### `GET /api/findings/{finding_id}/feedback`

Returns feedback entries. - Success: `200`

### `POST /api/findings/{finding_id}/feedback`

Adds reviewer feedback or a feedback entry, subject to role rules. -
Request: `body` - Success: `201` - Exact author permissions and whether
feedback supports replies/editing are TBD.

### `GET /api/findings/{finding_id}/work-history`

Returns chronological work updates by admin and user. - Success: `200`,
ordered oldest-first or newest-first as agreed by the frontend contract.

### `POST /api/findings/{finding_id}/work-history`

Adds a work update. - Request: `body`, optional `entry_type` - Success:
`201` - Entries should preserve author and creation timestamp. Whether
entries are append-only must be finalized.

### `GET /api/findings/{finding_id}/history`

Returns status-change history: old status, new status, actor, timestamp
and reason. - Success: `200` - This is distinct from the work-history
thread.

## 7. Attachments

### `POST /api/findings/{finding_id}/attachments`

Uploads a file using `multipart/form-data`. - Allowed formats: JPG, PDF,
TXT. - Backend must validate extension, actual content/type, and
configured maximum size. - Success: `201` with attachment metadata. -
Errors: `400` unsupported/invalid file; `401`; `403`; `404`; `413` file
too large.

### `GET /api/findings/{finding_id}/attachments`

Returns attachment metadata visible to the caller. - Success: `200`

### `GET /api/attachments/{attachment_id}/download`

Returns or redirects to a securely authorized download. - Success:
`200` - Errors: `401`, `403`, `404`

Storage provider, upload limits, and whether attachments can be deleted
are TBD.

## 8. Project dashboard and reporting

### `GET /api/projects/{project_id}/summary`

Returns project-level counts and status summaries for an authorized
caller. - Suggested fields: total findings, counts by status, overdue
count. - Success: `200`

### `GET /api/dashboard/summary`

Returns dashboard metrics scoped to the caller's permissions. - Admin
sees global counts; project users see only permitted project data. -
Exact metric definitions and filters TBD.

### `GET /api/reports/findings`

Returns filtered findings for reports/export if exports remain in
scope. - Supported export format and authorization rules TBD.

## 9. Standard error behavior

Recommended error shape:

``` json
{
  "detail": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "The requested status transition is not allowed."
  }
}
```

Use appropriate HTTP codes: - `400` invalid input or transition - `401`
missing/invalid authentication - `403` authenticated but unauthorized -
`404` resource not found or deliberately concealed - `409` uniqueness or
state conflict - `413` attachment too large - `422` FastAPI/Pydantic
request validation (unless normalized to the standard error shape) -
`500` unexpected server error, without exposing internal stack traces

## 10. Contract decisions required

1.  Confirm database and internal ID format.
2.  Finalize all endpoint paths and request/response schemas.
3.  Confirm roles and project membership permission rules.
4.  Confirm user-editable finding fields.
5.  Finalize the full status-transition matrix.
6.  Confirm feedback and work-history authoring rules.
7.  Confirm attachment size, storage provider, and deletion behavior.
8.  Confirm pagination defaults, sort values, and dashboard metrics.
9.  Confirm authentication token/cookie and session-expiration strategy.
10. Confirm project/finding deletion strategy and its impact on history.
