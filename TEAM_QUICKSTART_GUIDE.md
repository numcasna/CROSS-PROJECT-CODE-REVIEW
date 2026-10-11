# Dailoqa · Cross-Project Code Review System (CPCRS)
## 📋 Team Quickstart Guide

---

### 🌐 Live Application Link

| Service | Live URL | Description |
| :--- | :--- | :--- |
| **Web Application** | **[https://cross-project-code-review-system.onrender.com](https://cross-project-code-review-system.onrender.com)** | Main team interface (React/Vite/Tailwind) |
| **Interactive API Docs** | **[https://cpcrs-backend.onrender.com/docs](https://cpcrs-backend.onrender.com/docs)** | Swagger UI for backend API testing |

---

### 🔑 User Login Credentials

> **Password Rule:** All accounts follow `<firstname>123` (lowercase first name + `123`).

#### 1. Administrator Account
| Name | Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Sachin Jain** | Global Admin | `sachin@cpcrs.com` | `sachin123` | Full access: log findings, triage severity, review & resolve/close findings, manage all projects & users. |

#### 2. Core Intern Team (5 Members)
| Name | Role | Email | Password | Assigned Project Lead |
| :--- | :--- | :--- | :--- | :--- |
| **Saloni Rana** | Developer | `saloni@cpcrs.com` | `saloni123` | Project Lead: *Core Payment Gateway* |
| **Khushi** | Developer | `khushi@cpcrs.com` | `khushi123` | Project Lead: *Cloud Infrastructure & DevOps* |
| **Yash Tanwar** | Developer | `yash@cpcrs.com` | `yash123` | Project Lead: *Identity & Auth Platform* |
| **Tanmay Garg** | Developer | `tanmay@cpcrs.com` | `tanmay123` | Project Lead: *Analytics & Reporting Engine* |
| **Nitin Aman** | Developer | `nitin@cpcrs.com` | `nitin123` | Project Lead: *Customer Engagement Hub* |

#### 3. Additional Team Members (8 Developers)
| Name | Role | Email | Password | Assigned Project |
| :--- | :--- | :--- | :--- | :--- |
| **Aarav Sharma** | Developer | `aarav@cpcrs.com` | `aarav123` | Analytics & Reporting Engine |
| **Priya Nair** | Developer | `priya@cpcrs.com` | `priya123` | Core Platform Contributor |
| **Rohan Gupta** | Developer | `rohan@cpcrs.com` | `rohan123` | Core Payment Gateway |
| **Ananya Verma** | Developer | `ananya@cpcrs.com` | `ananya123` | Analytics & Reporting Engine |
| **Vikram Patel** | Developer | `vikram@cpcrs.com` | `vikram123` | Customer Engagement Hub |
| **Neha Singh** | Developer | `neha@cpcrs.com` | `neha123` | Identity & Auth Platform |
| **Arjun Mehta** | Developer | `arjun@cpcrs.com` | `arjun123` | Cloud Infrastructure & DevOps |
| **Sneha Reddy** | Developer | `sneha@cpcrs.com` | `sneha123` | Cloud Infrastructure & DevOps |

---

### 🚀 Quick Testing Steps for Teammates

1. **Log In**: Open [https://cross-project-code-review-system.onrender.com](https://cross-project-code-review-system.onrender.com) and sign in using your email and password above.
2. **Review Assigned Findings**: Go to **My Findings** to view findings assigned to you, filter by severity (Critical, High, Medium, Low), and inspect code lines and repository context.
3. **Take Action**:
   - Change status to **In Progress** when starting work.
   - Post comments in the **Discussion & Feedback** thread.
   - When finished, click **Submit for Review** with your explanation and evidence.
4. **Admin Sign-Off**: Log in as **Sachin Jain** to review submissions and mark them **Resolved** or **Closed**.
