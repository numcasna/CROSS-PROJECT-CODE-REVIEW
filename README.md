# Cross-Project Code Review Finding Tracker (CPCRS)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![React 18](https://img.shields.io/badge/Frontend-React%2018-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Bundler-Vite%205-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-D71F00.svg)](https://www.sqlalchemy.org)
[![Tests](https://img.shields.io/badge/Tests-112%20Passing-success.svg)](backend/tests/)

A centralized, role-governed platform designed for engineering teams to capture, assign, triage, and remediate code review findings across disparate software repositories.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Repository Structure](#-repository-structure)
- [Local Setup & Quickstart](#-local-setup--quickstart)
- [Pre-Seeded Test Accounts](#-pre-seeded-test-accounts)
- [Automated Testing](#-automated-testing)
- [API Contract Summary](#-api-contract-summary)
- [Cloud Deployment (Render)](#-cloud-deployment-render)

---

## 🚀 Overview

Engineering organizations managing multiple repositories often struggle with tracking systemic code review findings, ensuring remediation accountability, and enforcing review closure. 

**CPCRS** solves this by offering:
- **Project Isolation & Ownership**: Projects and repositories are owned by their respective teams.
- **Independent Finding Governance**: Findings are logged with annual sequential identifiers (`CRF-YYYY-XXXX`) and tracked through a formal status lifecycle.
- **Evidence-Based Resolution**: Remediation requires resolution explanations and verifiable evidence attachments before admin sign-off.

---

## ✨ Key Features

### 1. Role-Based Access Control (RBAC)
- **Global Administrator**: Responsible for finding registration, severity triage, work evaluation, and lifecycle decisions (Resolve, Reopen, Reject, Close).
- **Project Lead**: Automatically designated upon project creation. Sole authority over adding/removing team members and registering repositories.
- **Developer / Assignee**: Reviews assigned findings, transitions status (`Open` ➔ `In Progress`), records progress logs, and submits completed fixes (`In Review`).

### 2. Strict Finding State Machine
```
   [Open]
      │
      ▼
[In Progress] ──▶ [In Review] ──▶ [Resolved] ──▶ [Closed]
      ▲                 │              │
      │                 ▼              ▼
      └─────────── [Reopened]    [Rejected]
```
- Direct transition from `In Progress` to `Resolved` is strictly disallowed; developers must submit work for review.
- Any transition to `Reopened`, `Rejected`, or `Resolved` requires mandatory decision rationale recorded in the audit trail.

### 3. Threaded Discussion & Work History
- **Work History Log**: Chronological progress notes recorded by assignees during remediation.
- **Feedback Threads**: Threaded conversation between reviewers, admins, and developers with author badges and timestamps.

### 4. Secure Evidence Attachments
- Supports JPG, PNG, PDF, and TXT evidence files (up to 10MB per upload).
- Uploads are validated by MIME type and securely served via authorized endpoints.

### 5. Multi-Dimensional Dashboard & Filters
- Real-time search by title, ID, or description.
- Multi-filter capability: **Project**, **Severity**, **Finding Label**, **Status**, and **Overdue Only**.

---

## 🛠 Architecture & Tech Stack

```
┌────────────────────────────────────────────────────────┐
│             Vite + React 18 Frontend                   │
│   (Tailwind CSS, React Router v6, DataContext / Auth)  │
└───────────────────────────┬────────────────────────────┘
                            │ Reverse Proxy (/api)
┌───────────────────────────▼────────────────────────────┐
│                FastAPI REST API Gateway                │
│    (JWT Bearer Auth, Pydantic v2 Models, CORS)         │
└───────────────────────────┬────────────────────────────┘
                            │ SQLAlchemy 2.0 ORM
┌───────────────────────────▼────────────────────────────┐
│      Relational Database (SQLite / PostgreSQL)         │
│  - Users & Membership      - Yearly Counters           │
│  - Projects & Repositories - Findings & Audit History  │
└────────────────────────────────────────────────────────┘
```

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.12) |
| **Data Layer / ORM** | SQLAlchemy 2.0 + Alembic migrations |
| **Authentication** | OAuth2 / JWT (python-jose) with Argon2-cffi password hashing |
| **Frontend Framework** | React 18 + Vite 5 (Single Page Application) |
| **Styling** | Vanilla CSS + Tailwind CSS |
| **Testing** | Pytest, TestClient (FastAPI), In-memory SQLite isolation |

---

## 📂 Repository Structure

```
.
├── backend/
│   ├── alembic/                 # Database migration scripts
│   ├── app/
│   │   ├── api/                 # REST endpoints (auth, users, projects, findings, attachments)
│   │   ├── core/                # Database engine, config, security & JWT utilities
│   │   ├── models/              # SQLAlchemy relational models
│   │   ├── schemas/             # Pydantic v2 validation models
│   │   └── main.py              # Application entrypoint & CORS middleware
│   ├── scripts/
│   │   ├── demo_walkthrough.py  # End-to-end evaluation scenario runner
│   │   ├── seed_admin.py        # Standalone admin bootstrapper
│   │   └── seed_dev_data.py     # Comprehensive seed data populator
│   ├── tests/                   # Pytest test suite (112 automated tests)
│   └── requirements.txt         # Backend Python dependencies
├── Cross_Project_Code_Review_Admin_Managed_Frontend/
│   └── Cross_Project_Code_Review-main/
│       ├── src/
│       │   ├── api/             # API client (Fetch wrapper with Bearer token handling)
│       │   ├── components/      # Reusable UI widgets (Badges, Topbar, Sidebar, FeedbackThread)
│       │   ├── context/         # AuthContext and DataContext (live state synchronization)
│       │   ├── layouts/         # AdminLayout and UserLayout navigation shells
│       │   └── pages/           # Admin & Developer view screens
│       ├── package.json         # Frontend Node dependencies & scripts
│       └── vite.config.js       # Vite dev server with /api reverse proxy
├── requirements.txt             # Root requirements pointer
└── user_credentials_and_test_guide.md # Credential ledger & test walkthrough
```

---

## 💻 Local Setup & Quickstart

### Prerequisites
- **Python 3.10+** (Python 3.12 recommended)
- **Node.js 18+** & **npm**
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/numcasna/CROSS-PROJECT-CODE-REVIEW.git
cd CROSS-PROJECT-CODE-REVIEW
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Run the backend API server (runs on port 8000)
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000
```
> *On server startup, the database tables and seed test accounts are automatically initialized.*

### 3. Frontend Setup
In a new terminal window:
```bash
cd Cross_Project_Code_Review_Admin_Managed_Frontend/Cross_Project_Code_Review-main

# Install dependencies
npm install

# Start the Vite development server (runs on port 5173)
npm run dev
```

### 4. Access the Application
- **Web App**: Open [http://localhost:5173](http://localhost:5173) in your browser.
- **Interactive Swagger API Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🔑 Pre-Seeded Test Accounts

All accounts use the standard test password pattern: `<firstname>123`

| Name | Role | Email | Password | Primary Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Sachin Jain** | Global Admin | `sachin@cpcrs.com` | `sachin123` | Full admin governance across all projects |
| **Saloni Rana** | Developer | `saloni@cpcrs.com` | `saloni123` | Project Lead: *Core Payment Gateway* |
| **Khushi** | Developer | `khushi@cpcrs.com` | `khushi123` | Project Lead: *Cloud Infrastructure & DevOps* |
| **Yash Tanwar** | Developer | `yash@cpcrs.com` | `yash123` | Project Lead: *Identity & Auth Platform* |
| **Tanmay Garg** | Developer | `tanmay@cpcrs.com` | `tanmay123` | Project Lead: *Analytics & Reporting Engine* |
| **Nitin Aman** | Developer | `nitin@cpcrs.com` | `nitin123` | Project Lead: *Customer Engagement Hub* |

*Additional developers available for testing: `aarav@cpcrs.com`, `priya@cpcrs.com`, `rohan@cpcrs.com`, `ananya@cpcrs.com`, `vikram@cpcrs.com`, `neha@cpcrs.com`, `arjun@cpcrs.com`, `sneha@cpcrs.com`.*

---

## 🧪 Automated Testing

The backend includes a comprehensive automated test suite providing **100% test passing coverage**:

```bash
# Run the complete test suite
PYTHONPATH=. pytest backend/tests

# Run an individual requirement test module
PYTHONPATH=. pytest backend/tests/test_findings.py
PYTHONPATH=. pytest backend/tests/test_finding_status_transitions.py
PYTHONPATH=. pytest backend/tests/test_finding_attachments.py

# Run the live End-to-End Walkthrough evaluation
PYTHONPATH=. python backend/scripts/demo_walkthrough.py
```

---

## 📡 API Contract Summary

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT bearer token | Public |
| `GET` | `/api/auth/me` | Fetch authenticated user profile | Bearer Token |
| `POST` | `/api/users` | Provision new developer account | Admin Only |
| `GET` | `/api/projects` | List visible projects | Authenticated |
| `POST` | `/api/projects` | Create a new project (creator becomes Lead) | Authenticated |
| `POST` | `/api/projects/{id}/members` | Enroll team member | Project Lead Only |
| `POST` | `/api/projects/{id}/repositories` | Register repository metadata | Project Lead Only |
| `GET` | `/api/findings` | Scoped queries with filtering & pagination | Authenticated |
| `POST` | `/api/findings` | Log new code review finding (`CRF-YYYY-XXXX`) | Admin Only |
| `PATCH` | `/api/findings/{id}/status` | Perform state transition | Role-Enforced |
| `POST` | `/api/findings/{id}/submit-for-review` | Submit remediation for evaluation | Assignee Only |
| `POST` | `/api/findings/{id}/feedback` | Post threaded discussion comment | Authenticated |
| `POST` | `/api/findings/{id}/work-history` | Record progress log | Assignee Only |
| `POST` | `/api/findings/{id}/attachments` | Upload evidence attachment | Authenticated |
| `GET` | `/api/attachments/{id}/download` | Secure authorized file download | Authenticated |

---

## ☁️ Cloud Deployment (Render)

This repository is deployed and hosted live on [Render](https://render.com):

| Component | Service Type | Live Production URL | Description |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | Static Site | [https://cpcrs-frontend.onrender.com](https://cpcrs-frontend.onrender.com) | React 18 / Vite 5 / Tailwind CSS Single Page Application |
| **Backend API** | Web Service | [https://cpcrs-backend.onrender.com](https://cpcrs-backend.onrender.com) | FastAPI REST API Service |
| **Interactive Docs** | OpenAPI | [https://cpcrs-backend.onrender.com/docs](https://cpcrs-backend.onrender.com/docs) | Swagger UI for exploring and testing endpoints |

### Render Service Specifications

1. **Backend Web Service (`cpcrs-backend`)**:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `DATABASE_URL`: `sqlite:///./prod.db`
     - `SECRET_KEY`: `production-super-secret-key-cpcrs-2026-secure-random`
     - `PROJECT_NAME`: `Cross-Project Code Review Finding Tracker`
     - `ACCESS_TOKEN_EXPIRE_MINUTES`: `1440`

2. **Frontend Static Site (`cpcrs-frontend`)**:
   - **Build Command**: `cd Cross_Project_Code_Review_Admin_Managed_Frontend/Cross_Project_Code_Review-main && npm install && npm run build`
   - **Publish Directory**: `Cross_Project_Code_Review_Admin_Managed_Frontend/Cross_Project_Code_Review-main/dist`
   - **Environment Variables**:
     - `VITE_API_BASE_URL`: `https://cpcrs-backend.onrender.com`
   - **Routes / Rewrites**:
     - `/*` ➔ `/index.html` (Rewrite rule for client-side React Router navigation)

---

## 📄 License

Internal Engineering Project — Distributed under proprietary license for cross-project code review management.
