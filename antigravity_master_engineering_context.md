# MASTER META-PROMPT: GENERATE A PROJECT-SPECIFIC ...

# ANTIGRAVITY MASTER ENGINEERING CONTEXT & INSTRUCTION SYSTEM

**Target Project:** Cross-Project Code Review Finding Tracker **Author & Final Authority:** Project Lead / Author **Role:** Principal Software Architect, Staff Engineer, TDD Specialist & QA Architect **Version:** 1.0 (MVP Implementation Baseline)

## 1. PROJECT SPECIFIC BASELINE & GOVERNANCE (LAYER A)

### 1.1 Project Purpose & Executive Summary

The Cross-Project Code Review Finding Tracker is an enterprise internal web application designed to track and manage code-review findings across multiple projects and repositories. The primary objective is establishing accountability, traceability, and structured resolution of code review feedback without external Git automation.

### 1.2 Core Architectural Principles & Scope Boundaries

- **In-Scope (MVP):**

* Admin-provisioned user accounts (admin and developer / user).
* Session and identity management via Argon2id password hashing and JWT authentication.
* Project creation, updates, and membership assignment by users; global view and soft-delete by admins.
* Repository registration (manual metadata: name, manual URL, technology, default branch; **no Git webhooks, API cloning, or CI integrations**).
* Finding creation and lifecycle management with deterministic, concurrency-safe yearly sequence codes (e.g., CRF-2026-0001).
* Finding workflow: project users submit work (In Review), admins approve (Resolved), reject insufficient work (Reopened), or transition to terminal states (Rejected, Closed).
* Three strictly isolated data streams: **Feedback** (threaded reviews/replies), **Work History** (append-only progress logs), and **Status History** (audit transitions with mandatory reasons for Reopened and Rejected).
* File attachments limited to **JPG, PDF, and TXT** (maximum 10 MB per file) stored in a backend-managed local filesystem (uploads/) outside the public web root.
* Soft deletion (deleted_at timestamp) across projects and findings to preserve historical auditability.

- **Strict Exclusions (Out-of-Scope):**

* Direct Git provider API integration (no GitHub, GitLab, or Bitbucket APIs).
* Cloning, parsing, or automated scanning (no SonarQube, SAST, or CI runners).
* Public registration or open password reset endpoints.
* Hard deletion of audit trails or findings.

### 1.3 Confirmed Data Architecture (9 Relational Tables + 1 Concurrency Allocator)

The backend persistence layer MUST strictly implement PostgreSQL managed via SQLAlchemy ORM and Alembic migrations:

1. users: id (UUID PK), name (VARCHAR 150), email (VARCHAR 254 UNIQUE), password_hash (TEXT, Argon2id), role (VARCHAR 30: admin | developer), is_active (BOOLEAN, default True), created_at (TIMESTAMPTZ), updated_at (TIMESTAMPTZ).
2. projects: id (UUID PK), name (VARCHAR 200), description (TEXT nullable), project_lead_id (UUID FK -> users.id), created_by (UUID FK -> users.id), created_at (TIMESTAMPTZ), updated_at (TIMESTAMPTZ), deleted_at (TIMESTAMPTZ nullable).
3. project_members: project_id (UUID FK), user_id (UUID FK), added_by (UUID FK), joined_at (TIMESTAMPTZ). Composite PK: (project_id, user_id).
4. repositories: id (UUID PK), project_id (UUID FK), name (VARCHAR 200), repository_url (TEXT nullable), branch_name (VARCHAR 255 nullable), technology (VARCHAR 100 nullable), is_active (BOOLEAN default True), created_at (TIMESTAMPTZ).
5. findings: id (UUID PK), finding_code (VARCHAR 30 UNIQUE, e.g., CRF-2026-0001), title (VARCHAR 250), description (TEXT), project_id (UUID FK), repository_id (UUID FK), branch_name (VARCHAR 255 nullable), severity (VARCHAR 30: Critical, High, Medium, Low, Informational), category (VARCHAR 100), status (VARCHAR 30: Open, In Progress, In Review, Resolved, Reopened, Rejected, Closed), assignee_id (UUID FK -> users.id), reviewer_id (UUID FK nullable), created_by (UUID FK -> users.id), due_date (DATE), created_at (TIMESTAMPTZ), updated_at (TIMESTAMPTZ), deleted_at (TIMESTAMPTZ nullable).
6. finding_feedback: id (UUID PK), finding_id (UUID FK), author_id (UUID FK), parent_feedback_id (UUID self-referencing FK nullable for replies), body (TEXT), created_at (TIMESTAMPTZ), updated_at (TIMESTAMPTZ nullable).
7. finding_work_history: id (UUID PK), finding_id (UUID FK), author_id (UUID FK), entry_type (VARCHAR 30: progress_update, submission, admin_update), body (TEXT), created_at (TIMESTAMPTZ). **Append-only; no updates or deletes allowed.**
8. finding_status_history: id (UUID PK), finding_id (UUID FK), old_status (VARCHAR 30 nullable), new_status (VARCHAR 30), changed_by (UUID FK), reason (TEXT nullable; mandatory for transitions to Reopened or Rejected), changed_at (TIMESTAMPTZ).
9. finding_attachments: id (UUID PK), finding_id (UUID FK), uploaded_by (UUID FK), original_filename (VARCHAR 255), storage_key (TEXT), media_type (VARCHAR 100), size_bytes (BIGINT <= 10485760), attachment_kind (VARCHAR 30: resolution_proof, supporting_evidence), created_at (TIMESTAMPTZ).
10. yearly_finding_counters (Implementation Table): year (INTEGER PK), last_seq (INTEGER NOT NULL). Utilizes SELECT FOR UPDATE to avoid race conditions during code generation.

### 1.4 State Machine Matrix & Authorization Rules

| Current Status     | Target Status | Permitted Actor         | Mandatory Validation / Payload                                              |
| ------------------ | ------------- | ----------------------- | --------------------------------------------------------------------------- |
| Open               | In Progress   | Assignee / Project User | Must be member of project.                                                  |
| Open / In Progress | In Review     | Assignee / Project User | Call POST /api/findings/{id}/submit-for-review with resolution_description. |
| In Review          | Resolved      | Admin Only              | Administrative approval of work.                                            |
| In Review          | Reopened      | Admin Only              | Requires non-empty reason in payload and status history.                    |
| Any non-terminal   | Rejected      | Admin Only              | Requires non-empty reason (duplicate, invalid, etc.).                       |
| Resolved           | Closed        | Admin Only              | Final verified closure.                                                     |
| Any                | Soft Deleted  | Admin Only              | Sets deleted_at = NOW() via DELETE /api/findings/{id}.                      |

## 2. PERSISTENT OPERATING RULES (LAYER B)

### 2.1 The Test-Driven Engineering Loop

Antigravity MUST follow this exact red-green-refactor cycle on every unit of implementation without deviation:

[Phase A: Understand Context & Inspect Existing Files]
                    │
                    ▼
[Phase B: Define Testable Acceptance Criteria & Matrix]
                    │
                    ▼
[Phase C: Write Targeted Failing Test (Red Phase)]
                    │
                    ▼
[Phase D: Implement Minimal Code to Pass (Green Phase)]
                    │
                    ▼
[Phase E: Verification, Static Analysis & Regressions]
                    │
                    ▼
[Phase F: Record Results & Update Requirements Traceability]


1. **Phase A (Understand):**

- Review the exact API contract schema (03_api_contract (1).md) and data model specification (02_database_schema_data_model_updated.md).
- Inspect existing codebase files and test suites. Do NOT infer or hallucinate missing endpoints.

2. **Phase B (Specify):**

- Translate the user story into concrete test scenarios covering: Happy path, Unauthorized access (401/403), Payload validation failures (400/422), Entity missing (404), and Disallowed state transitions (409).

3. **Phase C (Write Tests First):**

- Write tests using pytest and fastapi.testclient.TestClient.
- Execute the tests against current code. **Antigravity MUST verify that the test fails specifically due to missing functionality**, not due to import errors or test-harness broken syntax.

4. **Phase D (Implement Minimally):**

- Write the minimum Python/FastAPI code necessary to satisfy the assertions.
- Reuse database models and dependency injections (get_db, get_current_user, require_admin).
- Do NOT add speculative abstractions or unrequested third-party packages.

5. **Phase E (Verify):**

- Execute pytest -v over the target test suite and run full regression sweeps.
- Verify linting and typing (ruff / mypy or flake8).

6. **Phase F (Review & Record):**

- Log the red-green progression evidence and update the requirements matrix before marking any task complete.

### 2.2 Author Approval Protocol

The project author retains final authority over product behavior and contracts. Antigravity MUST immediately pause and request approval using the mandatory decision format before making any of the following changes:

- Adding, modifying, or removing any endpoint path, HTTP method, or payload schema defined in 03_api_contract (1).md.
- Changing PostgreSQL schemas, adding migrations, or modifying table relationships defined in 02_database_schema_data_model_updated.md.
- Altering the role matrix (admin vs developer/user) or permission scopes.
- Modifying the file upload format limits (JPG, PDF, TXT; 10 MB).
- Introducing external services, cloud storage dependencies, or Git webhooks.

**Mandatory Decision-Request Template:**

### DECISION REQUIRED BY PROJECT AUTHOR
1\. **Decision Required:** [Clear, single question]
2\. **Context:** [Why has this surfaced during development?]
3\. **Available Options:**
  - Option A: [Description]
  - Option B: [Description]
4\. **Recommendation & Justification:** [Architectural perspective]
5\. **Trade-offs:** [Impact on security, maintenance, frontend contracts]
6\. **Impacted Components:** [List of files, schemas, endpoints affected]
7\. **Default Action if Deferred:** [Safe isolated fallback path]


### 2.3 Strict Engineering Safeguards

- **No Test Weakening:** Antigravity MUST NOT modify, skip (@pytest.mark.skip), weaken, or delete any existing test to make code pass.
- **File Upload Verification:** Attachments must have their magic numbers/signatures inspected (python-magic or file header validation for JPEG \xFF\xD8\xFF, PDF %PDF-, and ASCII/UTF-8 for TXT). Never rely on user-supplied MIME headers or file extensions alone.
- **Soft Deletion Enforced:** All queries for projects and findings MUST append WHERE deleted_at IS NULL unless explicitly requesting an administrative audit archive.
- **No Plaintext Passwords:** Argon2id hashing must be used for user authentication. Passwords must never be logged or returned in Pydantic serialization schemas.

## 3. IMPLEMENTATION ROADMAP & TRACEABILITY MATRIX

Antigravity must follow this dependency sequence, completing and verifying each phase before progressing:

[Phase 1: Foundation & DB Schemas] ──► [Phase 2: Authentication & Security Engine]
                                                       │
                                                       ▼
[Phase 4: Findings Core & Seq Codes] ◄── [Phase 3: Project & Membership Scoping]
                │
                ▼
[Phase 5: Status State Machine Engine]
                │
                ▼
[Phase 6: Multi-stream Audit & Feedback]
                │
                ▼
[Phase 7: Attachments & Private Storage] ──► [Phase 8: Frontend Verification]


### Traceability Matrix

| Req ID     | Requirement Description              | Target Module / Endpoints              | Test Verification Level                  | Status Gate |
| ---------- | ------------------------------------ | -------------------------------------- | ---------------------------------------- | ----------- |
| **REQ-01** | Database Engine & Migrations         | app/models/\*, Alembic env             | Integration (DB Schema inspection)       | Phase 1     |
| **REQ-02** | Initial Admin Provisioning           | seed_admin.py                          | CLI execution & DB verification          | Phase 1     |
| **REQ-03** | Auth: Login & JWT Tokens             | POST /api/auth/login, GET /api/auth/me | Contract & Security Unit Tests           | Phase 2     |
| **REQ-04** | User Management (Admin Only)         | POST /api/users, GET /api/users        | Integration & Role Barrier Tests         | Phase 2     |
| **REQ-05** | Project CRUD & Soft Delete           | /api/projects, /api/projects/{id}      | Contract, Unit & Soft-Delete Tests       | Phase 3     |
| **REQ-06** | Project Membership & Lead Rules      | /api/projects/{id}/members             | Service Layer Boundary Tests             | Phase 3     |
| **REQ-07** | Manual Repository Management         | /api/projects/{id}/repositories        | CRUD Integration Tests                   | Phase 3     |
| **REQ-08** | Finding Creation & Yearly Code       | POST /api/findings (CRF-YYYY-XXXX)     | Concurrency & Integrity Tests            | Phase 4     |
| **REQ-09** | Finding Access & Scoped Queries      | GET /api/findings, GET /findings/{id}  | Role/Membership Isolation Tests          | Phase 4     |
| **REQ-10** | Work Submission (In Review)          | POST /findings/{id}/submit-for-review  | Workflow & Status Transition Tests       | Phase 5     |
| **REQ-11** | Status State Machine Transitions     | PATCH /findings/{id}/status            | Exhaustive Transition Matrix Tests       | Phase 5     |
| **REQ-12** | Threaded Feedback & Work History     | /findings/{id}/feedback, /work-history | Append-only & Tree Structure Tests       | Phase 6     |
| **REQ-13** | File Attachments (JPG/PDF/TXT, 10MB) | POST /findings/{id}/attachments        | Magic Byte, MIME & Size Limit Tests      | Phase 7     |
| **REQ-14** | Authorized Secure File Download      | GET /attachments/{id}/download         | Authentication & Storage Isolation Tests | Phase 7     |

## 4. AGENT SESSION EXECUTION PROTOCOL

At the start of **every** development session, Antigravity MUST execute the following checklist:

### SESSION INITIALIZATION CHECKLIST
1\. [ ] Check current Git working tree for uncommitted changes (`git status`).
2\. [ ] Read `PROJECT_STATE.md` (or progress record) to determine active requirement and task status.
3\. [ ] Verify environment dependencies and database availability.
4\. [ ] Declare active Task ID and state intended Acceptance Criteria.
5\. [ ] Confirm no unresolved author decision blocks the current task.


At the conclusion of **every** task, Antigravity MUST report using this format:

### TASK COMPLETION SUMMARY
- **Task ID & Requirement:** [e.g., REQ-08 Finding Creation]
- **Red Phase Evidence:** [Test name that failed and confirmed failure error output]
- **Green Phase Evidence:** [Passing test run output with execution duration]
- **Files Created/Modified:** [List of paths]
- **Contracts Preserved:** [Confirmation of API schema compliance]
- **Regressions & Static Checks:** [Output of full test suite and linter]
- **Pending Approvals / Next Step:** [Immediate subsequent task from roadmap]


## 5. RECONCILIATION OF GAPS & ASSUMPTIONS

1. **Category Master List:** Until an explicit vocabulary table is provided by the author, default categories are locked to: ['Security', 'Performance', 'Code Quality', 'Bug', 'Architecture', 'Documentation']. Any modifications require author sign-off.
2. **Reviewer ID Field:** In accordance with Section 4.5 of the schema document, reviewer_id is optional upon creation and assigned when an admin reviews or claims the finding.
3. **Frontend API URL:** The React/Vite frontend communicates with the FastAPI backend over proxy or base URL configured at http\://localhost:8000/api matching the defined contract prefix.

