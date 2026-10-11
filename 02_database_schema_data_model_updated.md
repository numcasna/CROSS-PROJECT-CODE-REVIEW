# Cross-Project Code Review Finding Tracker

## Database Schema & Data Model Document

**Version:** Draft 0.2  
**Status:** Updated proposed logical model; PostgreSQL confirmed. Database tables will be created and changed using Alembic migrations.

## 1. Design principles

- Use PostgreSQL as the relational database.
- Use SQLAlchemy models and Alembic migrations to create and evolve the schema. Do not rely on manually creating production tables outside migrations.
- Keep feedback, work-history entries, status history, and attachments as separate records because they serve different purposes.
- Store attachment metadata in PostgreSQL and file bytes in private file storage.
- Enforce project access, role permissions, and status-transition rules in the backend; use database constraints where suitable as additional safeguards.
- Never store plaintext passwords.
- Use soft deletion for projects and findings where deletion is permitted, retaining records for traceability.
- Use UTC-aware timestamps (`TIMESTAMPTZ`) for stored event times.

## 2. Confirmed scope and decisions

1. **Database:** PostgreSQL.
2. **Schema management:** SQLAlchemy models with Alembic migrations.
3. **Roles:** `admin` and `developer`.
4. **Account provisioning:** Admins create user accounts; public self-registration is not in scope.
5. **Project permissions:** Users can create and edit projects, manage project membership, and assign project leads. Only admins can delete projects.
6. **Project lead:** Must also be a member of that project.
7. **Repositories:** A project can have multiple repositories. A single optional/manual `branch_name` field is retained on `repositories`; no separate branches table is planned.
8. **Findings:** Assignee and due date are mandatory.
9. **Finding category:** Controlled vocabulary, not arbitrary free text. The allowed values must be agreed and encoded as a constraint or reference table before implementation.
10. **Deletion:** Soft deletion. Use `deleted_at` where applicable and exclude deleted records from normal queries. Related-record retention and deletion behavior must be implemented consistently.
11. **Statuses:** `Open`, `In Progress`, `Resolved`, `Reopened`, `Rejected`, and `Closed`. A reason is required when a finding is moved to `Reopened` or `Rejected`. Exact allowed transitions and which role may perform each transition must be encoded in backend service logic.
12. **Feedback:** Feedback supports replies. Use a nullable self-referencing `parent_feedback_id` on `finding_feedback` to represent a reply thread. Feedback editing is supported; the policy for who may edit and whether edits need auditing should be enforced by the backend.
13. **Work history:** Append-only; existing entries must not be edited in place. Add a new entry for a correction.
14. **Attachments:** Maximum 10 MB per file. Allow JPG, PDF, and TXT. Validate file content and size server-side, not just the filename extension.
15. **Finding codes:** Sequential by year, e.g. `CRF-2026-0001`. Allocate codes safely under concurrent requests; do not generate them by simply counting existing findings.
16. **Attachment storage:** During development, store file bytes in a backend-managed local `uploads/` directory outside publicly served frontend assets. Store only metadata and a generated storage key in PostgreSQL. For deployment, prefer private object storage if the app uses multiple backend instances or needs durable shared storage. Serve files only after authorization checks.

## 3. Proposed entities

The current logical model has **9 tables**:

1. `users`
2. `projects`
3. `project_members`
4. `repositories`
5. `findings`
6. `finding_feedback`
7. `finding_work_history`
8. `finding_status_history`
9. `finding_attachments`

Additional tables such as `refresh_tokens`, `audit_events`, a category lookup table, or a dedicated yearly finding-code counter may be added if required by implementation decisions. They are not included in the nine-table count above.

## 4. Proposed table definitions

Types below are PostgreSQL-oriented recommendations. Use UUID primary keys unless stated otherwise. Review the constraints and relationships before writing the first migration.

### 4.1 `users`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | VARCHAR(150) | Required |
| `email` | VARCHAR(254) | Required; unique after normalization |
| `password_hash` | TEXT | Required; Argon2id hash; never plaintext |
| `role` | VARCHAR(30) | Required; restricted to `admin` or `developer` |
| `is_active` | BOOLEAN | Required; default true |
| `created_at` | TIMESTAMPTZ | Required; default current timestamp |
| `updated_at` | TIMESTAMPTZ | Required; updated whenever the user record changes |

Account creation is admin-only. Public self-registration is not in scope. Use a unique index on normalized email addresses.

### 4.2 `projects`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | VARCHAR(200) | Required |
| `description` | TEXT | Optional |
| `project_lead_id` | UUID | Required FK to `users.id` |
| `created_by` | UUID | Required FK to `users.id` |
| `created_at` | TIMESTAMPTZ | Required |
| `updated_at` | TIMESTAMPTZ | Required |
| `deleted_at` | TIMESTAMPTZ | Nullable; set for soft deletion if the project is deleted |

Users can create and edit projects, manage membership, and assign project leads. Only admins can delete projects. The project lead must also be a member of the project. Enforce that rule in the service layer and, if practical, with a composite foreign key from `(id, project_lead_id)` to `project_members(project_id, user_id)`; this requires a matching unique key on the referenced membership columns.

### 4.3 `project_members`

| Column | Type | Constraints / purpose |
|---|---|---|
| `project_id` | UUID | FK to `projects.id`; part of composite primary key |
| `user_id` | UUID | FK to `users.id`; part of composite primary key |
| `added_by` | UUID | FK to `users.id` |
| `joined_at` | TIMESTAMPTZ | Required |

**Primary key:** (`project_id`, `user_id`). This prevents duplicate membership. Backend authorization must control who can add or remove members. Membership changes must preserve the rule that the project lead is a member.

### 4.4 `repositories`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `project_id` | UUID | Required FK to `projects.id` |
| `name` | VARCHAR(200) | Required |
| `repository_url` | TEXT | Manual metadata only; no Git API integration |
| `branch_name` | VARCHAR(255) | Optional single branch reference; no separate branches table |
| `technology` | VARCHAR(100) | Optional |
| `is_active` | BOOLEAN | Required; default true |
| `created_at` | TIMESTAMPTZ | Required |

A project can have multiple repositories. If independent management of many branches becomes a requirement later, revisit the decision to add a `repository_branches` table.

### 4.5 `findings`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `finding_code` | VARCHAR(30) | Required; unique, yearly sequential code such as `CRF-2026-0001` |
| `title` | VARCHAR(250) | Required |
| `description` | TEXT | Required |
| `project_id` | UUID | Required FK to `projects.id` |
| `repository_id` | UUID | Required FK to `repositories.id` |
| `branch_name` | VARCHAR(255) | Optional manual branch reference for the finding |
| `severity` | VARCHAR(30) | Required; `Critical`, `High`, `Medium`, `Low`, `Informational` |
| `category` | VARCHAR(100) | Required; controlled vocabulary, values to be finalized |
| `status` | VARCHAR(30) | Required; default `Open`; restricted to the six agreed statuses |
| `assignee_id` | UUID | Required FK to `users.id` |
| `reviewer_id` | UUID | Optional or required according to finalized reviewer workflow; FK to `users.id` |
| `created_by` | UUID | Required FK to `users.id` |
| `created_at` | TIMESTAMPTZ | Required; finding creation/start date |
| `due_date` | DATE | Required |
| `updated_at` | TIMESTAMPTZ | Required |
| `deleted_at` | TIMESTAMPTZ | Nullable; set for soft deletion |

The selected repository must belong to the same project as the finding. Enforce this in service validation or with a composite foreign key. Validate that the assignee is eligible to work on the project according to the finalized access rules.

**Allowed statuses:** `Open`, `In Progress`, `Resolved`, `Reopened`, `Rejected`, `Closed`.

A reason is required for transitions into `Reopened` and `Rejected`. Maintain an explicit transition map in backend service logic. A successful status change and its history record must be committed in the same database transaction.

**Yearly finding-code generation:** The code must be unique and sequential within each year. Use a transaction-safe allocator, such as a dedicated counter table keyed by year or another concurrency-safe mechanism. A dedicated counter table would be an additional implementation table beyond the nine logical tables listed above.

### 4.6 `finding_feedback`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `finding_id` | UUID | Required FK to `findings.id` |
| `author_id` | UUID | Required FK to `users.id` |
| `parent_feedback_id` | UUID | Nullable self-FK to `finding_feedback.id`; null for top-level feedback, populated for replies |
| `body` | TEXT | Required |
| `created_at` | TIMESTAMPTZ | Required |
| `updated_at` | TIMESTAMPTZ | Nullable; populated when feedback is edited |

Feedback and replies are stored as separate rows. Backend rules must define who may post, reply to, or edit feedback and must enforce project access. Consider audit requirements for edited feedback.

### 4.7 `finding_work_history`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `finding_id` | UUID | Required FK to `findings.id` |
| `author_id` | UUID | Required FK to `users.id` |
| `entry_type` | VARCHAR(30) | Required; e.g. `progress_update`, `submission`, `admin_update`; allowed values to be finalized |
| `body` | TEXT | Required |
| `created_at` | TIMESTAMPTZ | Required |

This is the chronological record of work performed and updates. Entries are append-only: do not edit or overwrite existing entries. Add a new entry to clarify or correct an earlier one.

### 4.8 `finding_status_history`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `finding_id` | UUID | Required FK to `findings.id` |
| `old_status` | VARCHAR(30) | Nullable for initial creation |
| `new_status` | VARCHAR(30) | Required |
| `changed_by` | UUID | Required FK to `users.id` |
| `reason` | TEXT | Required when the transition is into `Reopened` or `Rejected`; otherwise optional unless another rule requires it |
| `changed_at` | TIMESTAMPTZ | Required |

Create the status-history record in the same database transaction as each successful status change. Store the initial `Open` state as an initial history record if the application needs a complete lifecycle timeline. Validate status transitions and required reasons in the backend.

### 4.9 `finding_attachments`

| Column | Type | Constraints / purpose |
|---|---|---|
| `id` | UUID | Primary key |
| `finding_id` | UUID | Required FK to `findings.id` |
| `uploaded_by` | UUID | Required FK to `users.id` |
| `original_filename` | VARCHAR(255) | Required; display name only |
| `storage_key` | TEXT | Required; generated private storage identifier, not a user-controlled path |
| `media_type` | VARCHAR(100) | Required after server-side content validation |
| `size_bytes` | BIGINT | Required; must be greater than zero and no more than 10 MB |
| `attachment_kind` | VARCHAR(30) | Required; e.g. `resolution_proof`, `supporting_evidence`; allowed values to be finalized |
| `created_at` | TIMESTAMPTZ | Required |

**Attachment policy**

- Maximum file size: **10 MB per file**.
- Allowed formats: JPG, PDF, TXT.
- Validate actual content/signature and size on the server; do not trust the extension or client-supplied MIME type.
- During development, store file bytes in a backend-managed `uploads/` directory that is not publicly served. Store metadata and a generated `storage_key` in PostgreSQL.
- For deployment, consider private object storage for durability and shared access across multiple backend instances.
- Never expose raw storage paths to clients. Download endpoints must verify that the requester can access the related project/finding.
- Define backup, retention, and orphan-file cleanup procedures before production deployment.

## 5. Relationships

- `users` many-to-many `projects` through `project_members`.
- `users` one-to-many `projects` through `created_by`.
- `users` one-to-many `projects` through `project_lead_id`.
- `projects` one-to-many `repositories`.
- `projects` one-to-many `findings`.
- `repositories` one-to-many `findings`.
- `users` one-to-many findings as creator, reviewer, or assignee.
- `findings` one-to-many feedback entries, work-history entries, status-history entries, and attachments.
- `finding_feedback` can have replies through the self-referencing `parent_feedback_id`.

## 6. Recommended indexes and constraints

- Unique index on normalized `users.email`.
- Unique index on `findings.finding_code`.
- Index `findings(project_id, status)`.
- Index `findings(assignee_id, status)`.
- Index `findings(due_date)`.
- Index `finding_status_history(finding_id, changed_at)`.
- Index `finding_work_history(finding_id, created_at)`.
- Index `finding_feedback(finding_id, created_at)`.
- Index `finding_feedback(parent_feedback_id)`.
- Index `repositories(project_id)`.
- Foreign keys for all relationships.
- Check constraints for roles, severity, statuses, positive attachment size, and attachment size no greater than 10 MB.
- Controlled category values enforced by a check constraint or reference table.
- Transactional creation of projects with their required membership/lead relationship.
- Transactional status changes with history entries.
- Transaction-safe yearly finding-code allocation.
- Consistent soft-delete filtering and retention behavior.

## 7. Remaining implementation details to settle

The main scope decisions are confirmed. The following details still need to be specified in code or agreed before the schema is considered fully frozen:

1. **Exact category values:** list the approved categories and add a constraint or lookup table.
2. **Status transition map:** specify allowed transitions between `Open`, `In Progress`, `Resolved`, `Reopened`, `Rejected`, and `Closed`, and which role can perform each transition. Reasons are mandatory for transitions into `Reopened` and `Rejected`.
3. **Reviewer workflow:** confirm whether `reviewer_id` is required at finding creation or may be null until review is assigned.
4. **Soft deletion policy:** decide how project deletion handles associated findings, repositories, memberships, feedback, work history, status history, and attachments. Only admins may delete projects.
5. **Feedback edit policy:** define who can edit feedback and whether edit history must be retained.
6. **Attachment storage in production:** local `uploads/` is suitable for development; choose the production private storage provider before deployment.
7. **Finding-code allocator:** implement a concurrency-safe yearly sequence. A dedicated counter table would increase the physical table count beyond the nine logical entities.

## 8. Alembic implementation plan

1. Configure the PostgreSQL connection using environment variables; keep secrets out of source control.
2. Define SQLAlchemy models for the nine entities and their relationships.
3. Configure Alembic to load the SQLAlchemy metadata.
4. Generate an initial migration, inspect it carefully, and revise it if necessary.
5. Apply migrations to the development database using `alembic upgrade head`.
6. Verify tables, foreign keys, unique constraints, check constraints, and indexes in PostgreSQL.
7. Add future schema changes through new Alembic revisions; do not manually modify deployed schemas.
8. Test permissions and transactional behavior, particularly project-lead membership, soft deletion, status history, and yearly finding-code allocation.

## 9. Scope summary

The logical schema contains **9 proposed tables**. The yearly finding-code counter may require an additional implementation table, depending on the chosen allocation design. Optional tables such as refresh tokens, audit events, or category lookup data are not included in the nine-table logical count unless adopted later.

This document is the updated proposed data model. It should be treated as implementation-ready in overall direction, while the remaining details in Section 7 are completed before the initial schema is frozen.
