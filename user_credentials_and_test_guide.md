# Dialoka · CPCRS User Credentials & Test Environment Guide

**Live Production URL:** [https://cross-project-code-review-system.onrender.com](https://cross-project-code-review-system.onrender.com)  
**Live API Docs (Swagger):** [https://cpcrs-backend.onrender.com/docs](https://cpcrs-backend.onrender.com/docs)  
**Local Web App URL:** [http://localhost:5173](http://localhost:5173)  
**Common Password Pattern:** `<username>123` (lowercase first name + `123`)

---

## 1. User Accounts & Login Credentials

### Administrator Account
| Name | Role | Email | Password | Access & Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Sachin Jain** | Global Admin | `sachin@cpcrs.com` *(or `admin@cpcrs.com`)* | `sachin123` *(or `admin123`)* | Full administrative oversight: Create findings, review submitted work, resolve/reopen/close/reject findings, view all projects and users. |

### Core Team of 5 (Requested Members)
| # | Name | Role | Email | Password | Assigned Project Lead Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Saloni Rana** | Developer | `saloni@cpcrs.com` | `saloni123` | Project Lead: *Core Payment Gateway* |
| 2 | **Khushi** | Developer | `khushi@cpcrs.com` | `khushi123` | Project Lead: *Cloud Infrastructure & DevOps* |
| 3 | **Yash Tanwar** | Developer | `yash@cpcrs.com` | `yash123` | Project Lead: *Identity & Auth Platform* |
| 4 | **Tanmay Garg** | Developer | `tanmay@cpcrs.com` | `tanmay123` | Project Lead: *Analytics & Reporting Engine* |
| 5 | **Nitin Aman** | Developer | `nitin@cpcrs.com` | `nitin123` | Project Lead: *Customer Engagement Hub* |

### Additional Team Members (8 Developers)
| # | Name | Role | Email | Password | Default Enrolled Projects |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 6 | **Aarav Sharma** | Developer | `aarav@cpcrs.com` | `aarav123` | Analytics & Reporting Engine |
| 7 | **Priya Nair** | Developer | `priya@cpcrs.com` | `priya123` | General Engineering Member |
| 8 | **Rohan Gupta** | Developer | `rohan@cpcrs.com` | `rohan123` | Core Payment Gateway |
| 9 | **Ananya Verma** | Developer | `ananya@cpcrs.com` | `ananya123` | Analytics & Reporting Engine |
| 10 | **Vikram Patel** | Developer | `vikram@cpcrs.com` | `vikram123` | Customer Engagement Hub |
| 11 | **Neha Singh** | Developer | `neha@cpcrs.com` | `neha123` | Identity & Auth Platform |
| 12 | **Arjun Mehta** | Developer | `arjun@cpcrs.com` | `arjun123` | Cloud Infrastructure & DevOps |
| 13 | **Sneha Reddy** | Developer | `sneha@cpcrs.com` | `sneha123` | Cloud Infrastructure & DevOps |

---

## 2. Seeded Projects & Repositories

| Project Name | Project Lead | Repositories | Team Members |
| :--- | :--- | :--- | :--- |
| **Core Payment Gateway** | Saloni Rana | `payment-service`, `checkout-api`, `transaction-worker` | Saloni Rana, Khushi, Nitin Aman, Rohan Gupta |
| **Identity & Auth Platform** | Yash Tanwar | `auth-server`, `token-vault`, `sso-portal` | Yash Tanwar, Tanmay Garg, Saloni Rana, Neha Singh |
| **Analytics & Reporting Engine** | Tanmay Garg | `data-pipeline`, `reporting-api`, `analytics-dashboard` | Tanmay Garg, Nitin Aman, Aarav Sharma, Ananya Verma |
| **Customer Engagement Hub** | Nitin Aman | `notification-service`, `chat-gateway`, `crm-connector` | Nitin Aman, Khushi, Yash Tanwar, Vikram Patel |
| **Cloud Infrastructure & DevOps** | Khushi | `infra-terraform`, `k8s-manifests`, `monitoring-agent` | Khushi, Tanmay Garg, Arjun Mehta, Sneha Reddy |

---

## 3. Test Coverage Matrix

The database is populated with **19 interactive findings** designed to test every feature of the platform:

### A. All 5 Severities
- **Critical**: `CRF-2026-0001`, `CRF-2026-0002`, `CRF-2026-0007`, `CRF-2026-0013`
- **High**: `CRF-2026-0004`, `CRF-2026-0006`, `CRF-2026-0008`, `CRF-2026-0014`, `CRF-2026-0019`
- **Medium**: `CRF-2026-0003`, `CRF-2026-0005`, `CRF-2026-0010`, `CRF-2026-0015`
- **Low**: `CRF-2026-0009`, `CRF-2026-0012`, `CRF-2026-0016`, `CRF-2026-0018`
- **Informational**: `CRF-2026-0011`, `CRF-2026-0017`

### B. All 7 Lifecycle Statuses
- **Open**: `CRF-2026-0001`, `CRF-2026-0003`, `CRF-2026-0006`, `CRF-2026-0007`, `CRF-2026-0011`, `CRF-2026-0017`
- **In Progress**: `CRF-2026-0002`, `CRF-2026-0004`, `CRF-2026-0008`, `CRF-2026-0014`
- **In Review**: `CRF-2026-0010`, `CRF-2026-0013` *(ready for Admin evaluation)*
- **Resolved**: `CRF-2026-0005`, `CRF-2026-0009`, `CRF-2026-0015` *(available for Reopen, Reject, or Close)*
- **Reopened**: `CRF-2026-0012`, `CRF-2026-0018` *(contains reviewer feedback explanation)*
- **Rejected**: `CRF-2026-0016`
- **Closed**: `CRF-2026-0019`

### C. All 11 Finding Labels
`SQL Injection`, `AWS / Cloud Problem`, `Performance`, `Authentication`, `DB Problem`, `Security`, `Data Exposure`, `Authorization`, `Configuration`, `Code Quality`, `Other`.

### D. Overdue Filter Testing
- `CRF-2026-0001` (Due 3 days ago, Status: `Open`)
- `CRF-2026-0003` (Due 5 days ago, Status: `Open`)
- Enabling the **"Overdue only"** checkbox immediately highlights and isolates these items.
