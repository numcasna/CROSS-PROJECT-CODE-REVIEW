# PROJECT STATE & TRACEABILITY RECORD

**Target Project:** Cross-Project Code Review Finding Tracker  
**Governance Document:** [antigravity_master_engineering_context.md](file:///home/nitin/Documents/CPCRS_ag/antigravity_master_engineering_context.md)  
**Author & Final Authority:** Project Lead / Author  
**Current Phase:** Phase 1 - Foundation & DB Schemas  
**Active Requirement:** REQ-01 (Database Engine & Migrations)  

---

## 1. Traceability Matrix & Lifecycle States

*Legend: [Specified] -> [Tests Written] -> [Red Phase Verified] -> [Implemented] -> [Passing] -> [Approved]*

| Req ID | Requirement Description | Target Module / Endpoints | Phase | Status | Red-Phase Test | Verification Date |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | Database Engine & Migrations | `backend/app/models/*`, Alembic env | Phase 1 | [Approved] | `test_database_schema.py` | 2026-10-11 |
| **REQ-02** | Initial Admin Provisioning | `backend/scripts/seed_admin.py` | Phase 1 | [Approved] | `test_seed_admin.py` | 2026-10-11 |
| **REQ-03** | Auth: Login & JWT Tokens | `POST /api/auth/login`, `GET /api/auth/me` | Phase 2 | [Approved] | `test_auth.py` | 2026-10-11 |
| **REQ-04** | User Management (Admin Only) | `POST /api/users`, `GET /api/users` | Phase 2 | [Approved] | `test_users.py` | 2026-10-11 |
| **REQ-05** | Project CRUD & Soft Delete | `/api/projects`, `/api/projects/{id}` | Phase 3 | [Approved] | `test_projects.py` | 2026-10-11 |
| **REQ-06** | Project Membership & Lead Rules | `/api/projects/{id}/members` | Phase 3 | [Passing] | `test_project_members.py` | 2026-10-11 |
| **REQ-07** | Manual Repository Management | `/api/projects/{id}/repositories` | Phase 3 | [Specified] | - | - |
| **REQ-08** | Finding Creation & Yearly Code | `POST /api/findings` (CRF-YYYY-XXXX) | Phase 4 | [Specified] | - | - |
| **REQ-09** | Finding Access & Scoped Queries | `GET /api/findings`, `GET /findings/{id}` | Phase 4 | [Specified] | - | - |
| **REQ-10** | Work Submission (In Review) | `POST /findings/{id}/submit-for-review` | Phase 5 | [Specified] | - | - |
| **REQ-11** | Status State Machine Transitions | `PATCH /findings/{id}/status` | Phase 5 | [Specified] | - | - |
| **REQ-12** | Threaded Feedback & Work History | `/findings/{id}/feedback`, `/work-history` | Phase 6 | [Specified] | - | - |
| **REQ-13** | File Attachments (JPG/PDF/TXT, 10MB) | `POST /findings/{id}/attachments` | Phase 7 | [Specified] | - | - |
| **REQ-14** | Authorized Secure File Download | `GET /attachments/{id}/download` | Phase 7 | [Specified] | - | - |

---

## 2. Active Session Log

- **Active Task:** REQ-06: Project Membership & Lead Rules (`/api/projects/{id}/members`).
- **Author Rules Confirmed & Implemented:**
  1. Only the Project Lead can add (`POST /api/projects/{id}/members`) or remove (`DELETE /api/projects/{id}/members/{user_id}`) members.
  2. Non-lead members receive `403 Forbidden` if attempting to add or remove members.
  3. The Project Lead cannot be removed from `project_members` (must return `400 Bad Request`).
  4. Project members and admins can list members (`GET /api/projects/{id}/members`).
- **TDD Verification:**
  - Red Phase: 12 tests failed as expected before implementation.
  - Green Phase: 13 tests passed in `backend/tests/test_project_members.py`.
  - Regression Suite: All 48 tests across the entire project pass.
- **Status:** Pending User Approval for REQ-06.











