import os
import uuid
from datetime import date, datetime, timedelta, timezone
from backend.app.core.database import SessionLocal, engine
from backend.app.core.security import get_password_hash
from backend.app.models.base import Base
from backend.app.models.user import User
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.finding import (
    Finding,
    FindingStatusHistory,
    YearlyFindingCounter,
    FindingFeedback,
    FindingWorkHistory,
)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("[1/5] Seeding Users...")
    # Admin User: Sachin Jain
    # Password format: 'username123'
    users_data = [
        # Admin
        {
            "name": "Sachin Jain",
            "email": "sachin@cpcrs.com",
            "password": "sachin123",
            "role": "admin",
        },
        # Also ensure admin@cpcrs.com exists with admin123 for convenience
        {
            "name": "Sachin Jain",
            "email": "admin@cpcrs.com",
            "password": "admin123",
            "role": "admin",
        },
        # 5 Requested Team Members
        {
            "name": "Saloni Rana",
            "email": "saloni@cpcrs.com",
            "password": "saloni123",
            "role": "developer",
        },
        {
            "name": "Khushi",
            "email": "khushi@cpcrs.com",
            "password": "khushi123",
            "role": "developer",
        },
        {
            "name": "Yash Tanwar",
            "email": "yash@cpcrs.com",
            "password": "yash123",
            "role": "developer",
        },
        {
            "name": "Tanmay Garg",
            "email": "tanmay@cpcrs.com",
            "password": "tanmay123",
            "role": "developer",
        },
        {
            "name": "Nitin Aman",
            "email": "nitin@cpcrs.com",
            "password": "nitin123",
            "role": "developer",
        },
        # 8 Additional Developers
        {
            "name": "Aarav Sharma",
            "email": "aarav@cpcrs.com",
            "password": "aarav123",
            "role": "developer",
        },
        {
            "name": "Priya Nair",
            "email": "priya@cpcrs.com",
            "password": "priya123",
            "role": "developer",
        },
        {
            "name": "Rohan Gupta",
            "email": "rohan@cpcrs.com",
            "password": "rohan123",
            "role": "developer",
        },
        {
            "name": "Ananya Verma",
            "email": "ananya@cpcrs.com",
            "password": "ananya123",
            "role": "developer",
        },
        {
            "name": "Vikram Patel",
            "email": "vikram@cpcrs.com",
            "password": "vikram123",
            "role": "developer",
        },
        {
            "name": "Neha Singh",
            "email": "neha@cpcrs.com",
            "password": "neha123",
            "role": "developer",
        },
        {
            "name": "Arjun Mehta",
            "email": "arjun@cpcrs.com",
            "password": "arjun123",
            "role": "developer",
        },
        {
            "name": "Sneha Reddy",
            "email": "sneha@cpcrs.com",
            "password": "sneha123",
            "role": "developer",
        },
    ]

    user_map = {}
    for u_spec in users_data:
        existing = db.query(User).filter(User.email == u_spec["email"]).first()
        if not existing:
            new_u = User(
                id=uuid.uuid4(),
                name=u_spec["name"],
                email=u_spec["email"],
                password_hash=get_password_hash(u_spec["password"]),
                role=u_spec["role"],
                is_active=True,
            )
            db.add(new_u)
            db.commit()
            db.refresh(new_u)
            user_map[u_spec["email"]] = new_u
        else:
            existing.name = u_spec["name"]
            existing.role = u_spec["role"]
            existing.password_hash = get_password_hash(u_spec["password"])
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            user_map[u_spec["email"]] = existing

    admin = user_map["sachin@cpcrs.com"]
    saloni = user_map["saloni@cpcrs.com"]
    khushi = user_map["khushi@cpcrs.com"]
    yash = user_map["yash@cpcrs.com"]
    tanmay = user_map["tanmay@cpcrs.com"]
    nitin = user_map["nitin@cpcrs.com"]
    aarav = user_map["aarav@cpcrs.com"]
    priya = user_map["priya@cpcrs.com"]
    rohan = user_map["rohan@cpcrs.com"]
    ananya = user_map["ananya@cpcrs.com"]
    vikram = user_map["vikram@cpcrs.com"]
    neha = user_map["neha@cpcrs.com"]
    arjun = user_map["arjun@cpcrs.com"]
    sneha = user_map["sneha@cpcrs.com"]

    print("[2/5] Seeding Projects & Repositories...")
    projects_spec = [
        {
            "name": "Core Payment Gateway",
            "description": "High-throughput transaction settlement and checkout payment processing engine.",
            "lead": saloni,
            "members": [saloni, khushi, nitin, rohan],
            "repos": [
                {"name": "payment-service", "tech": "Python / FastAPI", "branch": "main"},
                {"name": "checkout-api", "tech": "Go / Gin", "branch": "main"},
                {"name": "transaction-worker", "tech": "Node.js / Express", "branch": "master"},
            ],
        },
        {
            "name": "Identity & Auth Platform",
            "description": "Centralized OAuth2, JWT token authorization, and federated SSO identity provider.",
            "lead": yash,
            "members": [yash, tanmay, saloni, neha],
            "repos": [
                {"name": "auth-server", "tech": "Go / Gin", "branch": "main"},
                {"name": "token-vault", "tech": "Rust", "branch": "main"},
                {"name": "sso-portal", "tech": "React / Vite", "branch": "main"},
            ],
        },
        {
            "name": "Analytics & Reporting Engine",
            "description": "Distributed event streaming and real-time business metrics data pipeline.",
            "lead": tanmay,
            "members": [tanmay, nitin, aarav, ananya],
            "repos": [
                {"name": "data-pipeline", "tech": "Python / PySpark", "branch": "main"},
                {"name": "reporting-api", "tech": "FastAPI", "branch": "main"},
                {"name": "analytics-dashboard", "tech": "TypeScript / React", "branch": "main"},
            ],
        },
        {
            "name": "Customer Engagement Hub",
            "description": "Omnichannel notification dispatch, transactional emails, and messaging gateway.",
            "lead": nitin,
            "members": [nitin, khushi, yash, vikram],
            "repos": [
                {"name": "notification-service", "tech": "Node.js / Express", "branch": "main"},
                {"name": "chat-gateway", "tech": "WebSocket / Go", "branch": "main"},
                {"name": "crm-connector", "tech": "Python", "branch": "main"},
            ],
        },
        {
            "name": "Cloud Infrastructure & DevOps",
            "description": "Kubernetes cluster orchestration, Terraform IaC, and deployment automation pipelines.",
            "lead": khushi,
            "members": [khushi, tanmay, arjun, sneha],
            "repos": [
                {"name": "infra-terraform", "tech": "Terraform / HCL", "branch": "main"},
                {"name": "k8s-manifests", "tech": "YAML / Helm", "branch": "main"},
                {"name": "monitoring-agent", "tech": "Go", "branch": "main"},
            ],
        },
    ]

    project_map = {}
    repo_map = {}
    for p_spec in projects_spec:
        proj = db.query(Project).filter(Project.name == p_spec["name"]).first()
        if not proj:
            proj = Project(
                id=uuid.uuid4(),
                name=p_spec["name"],
                description=p_spec["description"],
                project_lead_id=p_spec["lead"].id,
                created_by=p_spec["lead"].id,
            )
            db.add(proj)
            db.commit()
            db.refresh(proj)
        else:
            proj.description = p_spec["description"]
            proj.project_lead_id = p_spec["lead"].id
            db.commit()
            db.refresh(proj)
        project_map[p_spec["name"]] = proj

        # Members
        for member in p_spec["members"]:
            mem_link = db.query(ProjectMember).filter(
                ProjectMember.project_id == proj.id,
                ProjectMember.user_id == member.id,
            ).first()
            if not mem_link:
                db.add(ProjectMember(project_id=proj.id, user_id=member.id, added_by=p_spec["lead"].id))
        db.commit()

        # Repositories
        for r_spec in p_spec["repos"]:
            repo = db.query(Repository).filter(
                Repository.project_id == proj.id,
                Repository.name == r_spec["name"],
            ).first()
            if not repo:
                repo = Repository(
                    id=uuid.uuid4(),
                    project_id=proj.id,
                    name=r_spec["name"],
                    repository_url=f"https://github.com/company/{r_spec['name']}",
                    branch_name=r_spec["branch"],
                    technology=r_spec["tech"],
                    is_active=True,
                )
                db.add(repo)
                db.commit()
                db.refresh(repo)
            repo_map[f"{p_spec['name']}/{r_spec['name']}"] = repo

    print("[3/5] Seeding Yearly Counter...")
    year = datetime.now(timezone.utc).year
    counter = db.query(YearlyFindingCounter).filter(YearlyFindingCounter.year == year).first()
    if not counter:
        counter = YearlyFindingCounter(year=year, last_seq=20)
        db.add(counter)
        db.commit()
    else:
        counter.last_seq = max(counter.last_seq, 20)
        db.commit()

    print("[4/5] Seeding Findings across all Severities, Statuses, and Categories...")
    today = date.today()

    # 18 Diverse findings covering:
    # Severities: Critical, High, Medium, Low, Informational
    # Statuses: Open, In Progress, In Review, Resolved, Reopened, Rejected, Closed
    # Categories: SQL Injection, AWS / Cloud Problem, Performance, Authentication, DB Problem, Security, Data Exposure, Authorization, Configuration, Code Quality, Other
    # Overdue states: Several findings with due_date in past for Open/In Progress
    findings_spec = [
        # 1. Critical | Open | Overdue (due -3 days) | SQL Injection
        {
            "code": f"CRF-{year}-0001",
            "title": "SQL Injection in User Search & Transaction History",
            "description": "Raw string concatenation detected in /api/transactions search query, allowing unescaped database extraction.",
            "project": "Core Payment Gateway",
            "repo": "payment-service",
            "severity": "Critical",
            "category": "SQL Injection",
            "status": "Open",
            "assignee": saloni,
            "due_date": today - timedelta(days=3),
            "recommendation": "Use SQLAlchemy parameterized filters and validate search term length.",
            "work_history": [],
            "feedback": [],
        },
        # 2. Critical | In Progress | AWS / Cloud Problem
        {
            "code": f"CRF-{year}-0002",
            "title": "Hardcoded AWS Production Credentials in Config",
            "description": "AWS_ACCESS_KEY_ID and secret committed to repository configuration rather than environment secrets.",
            "project": "Cloud Infrastructure & DevOps",
            "repo": "infra-terraform",
            "severity": "Critical",
            "category": "AWS / Cloud Problem",
            "status": "In Progress",
            "assignee": khushi,
            "due_date": today + timedelta(days=2),
            "recommendation": "Rotate compromised AWS IAM credentials and migrate secrets to AWS Secrets Manager or HashiCorp Vault.",
            "work_history": ["Rotated IAM key pair and updated KMS policies."],
            "feedback": ["Ensured secret rotation is verified in staging cluster."],
        },
        # 3. Medium | Open | Overdue (due -5 days) | Performance
        {
            "code": f"CRF-{year}-0003",
            "title": "N+1 Query Amplification in Permission Matrix Load",
            "description": "Loading account overview makes redundant database roundtrips for each assigned organization role.",
            "project": "Identity & Auth Platform",
            "repo": "auth-server",
            "severity": "Medium",
            "category": "Performance",
            "status": "Open",
            "assignee": yash,
            "due_date": today - timedelta(days=5),
            "recommendation": "Eagerly load role memberships using joinedload or subqueryload.",
            "work_history": [],
            "feedback": [],
        },
        # 4. High | In Progress | Authentication
        {
            "code": f"CRF-{year}-0004",
            "title": "Missing Rate Limiter on Authentication Endpoint",
            "description": "Login endpoint /api/auth/login does not enforce IP or account throttle limits against automated brute-force attempts.",
            "project": "Identity & Auth Platform",
            "repo": "auth-server",
            "severity": "High",
            "category": "Authentication",
            "status": "In Progress",
            "assignee": tanmay,
            "due_date": today + timedelta(days=5),
            "recommendation": "Add Redis-backed token bucket sliding window rate limiting (5 attempts/min).",
            "work_history": ["Added slowapi rate limiting middleware prototype."],
            "feedback": ["Please test IP header spoofing with X-Forwarded-For."],
        },
        # 5. Medium | Resolved | DB Problem
        {
            "code": f"CRF-{year}-0005",
            "title": "Unindexed Foreign Key on Audit Ledger Causing Table Locks",
            "description": "Missing index on audit_records.event_id causing full table scans during transactional batch write operations.",
            "project": "Core Payment Gateway",
            "repo": "checkout-api",
            "severity": "Medium",
            "category": "DB Problem",
            "status": "Resolved",
            "assignee": nitin,
            "due_date": today + timedelta(days=8),
            "recommendation": "Add B-tree index on audit_records(event_id).",
            "work_history": ["Added Alembic migration creating idx_audit_event_id.", "Ran EXPLAIN ANALYZE showing index scan instead of sequential scan."],
            "feedback": ["Verified on staging database. Query latency dropped from 420ms to 4ms."],
        },
        # 6. High | Open | Security
        {
            "code": f"CRF-{year}-0006",
            "title": "Cross-Site Scripting (XSS) in Notification Activity Feed",
            "description": "HTML rendering unsanitized username input in email and in-app notification activity templates.",
            "project": "Customer Engagement Hub",
            "repo": "notification-service",
            "severity": "High",
            "category": "Security",
            "status": "Open",
            "assignee": nitin,
            "due_date": today + timedelta(days=4),
            "recommendation": "Sanitize HTML using DOMPurify before injecting into email templates.",
            "work_history": [],
            "feedback": [],
        },
        # 7. Critical | Open | Data Exposure
        {
            "code": f"CRF-{year}-0007",
            "title": "Public S3 Bucket Policy Exposing Customer Export Files",
            "description": "Export S3 bucket ACL misconfigured with public read permissions, allowing unauthenticated file download.",
            "project": "Analytics & Reporting Engine",
            "repo": "data-pipeline",
            "severity": "Critical",
            "category": "Data Exposure",
            "status": "Open",
            "assignee": tanmay,
            "due_date": today + timedelta(days=1),
            "recommendation": "Enforce S3 Block Public Access and use presigned URLs with 15-minute expirations.",
            "work_history": [],
            "feedback": [],
        },
        # 8. High | In Progress | Authorization
        {
            "code": f"CRF-{year}-0008",
            "title": "Insecure Direct Object Reference (IDOR) on Invoice PDF Endpoint",
            "description": "Invoice download endpoint accepts arbitrary invoice UUID without verifying account ownership.",
            "project": "Core Payment Gateway",
            "repo": "payment-service",
            "severity": "High",
            "category": "Authorization",
            "status": "In Progress",
            "assignee": saloni,
            "due_date": today + timedelta(days=6),
            "recommendation": "Validate current_user.org_id matches invoice.org_id before returning file stream.",
            "work_history": ["Added tenancy check in /invoices/{id}/download handler."],
            "feedback": ["Ensure integration test covers cross-tenant invoice download attempt."],
        },
        # 9. Low | Resolved | Configuration
        {
            "code": f"CRF-{year}-0009",
            "title": "Verbose Stack Traces & Debug Mode Enabled in Production",
            "description": "Uncaught 500 exceptions print internal stack traces disclosing database schema and module paths.",
            "project": "Analytics & Reporting Engine",
            "repo": "reporting-api",
            "severity": "Low",
            "category": "Configuration",
            "status": "Resolved",
            "assignee": aarav,
            "due_date": today + timedelta(days=12),
            "recommendation": "Set DEBUG=False and return standard JSON error envelopes.",
            "work_history": ["Disabled fastapi debug mode in production environment config."],
            "feedback": ["Confirmed error payload is now sanitized."],
        },
        # 10. Medium | In Review | DB Problem
        {
            "code": f"CRF-{year}-0010",
            "title": "Connection Pool Exhaustion During Peak Webhook Delivery",
            "description": "External webhook delivery blocks worker database connection during HTTP request timeout.",
            "project": "Customer Engagement Hub",
            "repo": "notification-service",
            "severity": "Medium",
            "category": "DB Problem",
            "status": "In Review",
            "assignee": khushi,
            "due_date": today + timedelta(days=7),
            "recommendation": "Release database connection before initiating outgoing HTTP dispatch.",
            "work_history": ["Decoupled DB transaction from HTTP client call using asynchronous event queue."],
            "feedback": ["Fix submitted for review. Load test simulated 5,000 concurrent webhooks without connection pool starvation."],
        },
        # 11. Informational | Open | Code Quality
        {
            "code": f"CRF-{year}-0011",
            "title": "Deprecated Cryptographic Hash Function (SHA1) in Checksum Utility",
            "description": "File integrity checks use hashlib.sha1 instead of SHA256/BLAKE3.",
            "project": "Cloud Infrastructure & DevOps",
            "repo": "monitoring-agent",
            "severity": "Informational",
            "category": "Code Quality",
            "status": "Open",
            "assignee": arjun,
            "due_date": today + timedelta(days=20),
            "recommendation": "Migrate checksum utilities to SHA-256.",
            "work_history": [],
            "feedback": [],
        },
        # 12. Low | Reopened | Other
        {
            "code": f"CRF-{year}-0012",
            "title": "CORS Allowed Origins Wildcard with Credentials Enabled",
            "description": "FastAPI middleware configured with allow_origins=['*'] alongside allow_credentials=True.",
            "project": "Customer Engagement Hub",
            "repo": "chat-gateway",
            "severity": "Low",
            "category": "Other",
            "status": "Reopened",
            "assignee": vikram,
            "due_date": today + timedelta(days=3),
            "recommendation": "Explicitly whitelist frontend client origin domains.",
            "work_history": ["Initial PR restricted to localhost:5173."],
            "feedback": ["Reopened: Staging domain cpcrs.company.internal was missing from whitelist and broke staging QA."],
        },
        # 13. Critical | In Review | Security
        {
            "code": f"CRF-{year}-0013",
            "title": "Server-Side Request Forgery (SSRF) in Webhook URL Validator",
            "description": "Webhook test trigger accepts loopback IP (127.0.0.1) and AWS metadata IP (169.254.169.254).",
            "project": "Customer Engagement Hub",
            "repo": "crm-connector",
            "severity": "Critical",
            "category": "Security",
            "status": "In Review",
            "assignee": nitin,
            "due_date": today + timedelta(days=3),
            "recommendation": "Block private IP CIDRs (RFC 1918, RFC 3927) and loopback addresses.",
            "work_history": ["Added ipaddress validator rejecting private, loopback, and multicast IP ranges."],
            "feedback": ["Ready for security sign-off. Verified SSRF payload against 169.254.169.254 is rejected with 400 Bad Request."],
        },
        # 14. High | In Progress | Performance
        {
            "code": f"CRF-{year}-0014",
            "title": "Memory Leak in Persistent WebSocket Connection Pool",
            "description": "Disconnected WebSocket clients retain event listener references causing RSS memory growth.",
            "project": "Customer Engagement Hub",
            "repo": "chat-gateway",
            "severity": "High",
            "category": "Performance",
            "status": "In Progress",
            "assignee": khushi,
            "due_date": today + timedelta(days=5),
            "recommendation": "Explicitly remove listener on client close event and set connection ttl.",
            "work_history": ["Added onClose cleanup handler and weakref listener tracking."],
            "feedback": ["Heap dump shows listener garbage collected successfully."],
        },
        # 15. Medium | Resolved | Authorization
        {
            "code": f"CRF-{year}-0015",
            "title": "Session Invalidation Failure on Password Reset",
            "description": "Existing JWT tokens remain valid after password change due to missing token generation timestamp check.",
            "project": "Identity & Auth Platform",
            "repo": "auth-server",
            "severity": "Medium",
            "category": "Authorization",
            "status": "Resolved",
            "assignee": yash,
            "due_date": today + timedelta(days=14),
            "recommendation": "Store password_changed_at and verify iat >= password_changed_at in JWT validator.",
            "work_history": ["Added password_changed_at claim verification in JWT dependency."],
            "feedback": ["Verified old session tokens are immediately rejected with 401 Unauthorized upon password change."],
        },
        # 16. Low | Rejected | Configuration
        {
            "code": f"CRF-{year}-0016",
            "title": "Proposed Migration from HCL to JSON Terraform Definitions",
            "description": "Request to convert terraform configurations to JSON syntax.",
            "project": "Cloud Infrastructure & DevOps",
            "repo": "infra-terraform",
            "severity": "Low",
            "category": "Configuration",
            "status": "Rejected",
            "assignee": sneha,
            "due_date": today + timedelta(days=18),
            "recommendation": "Maintain standard HCL formatting per company engineering standards.",
            "work_history": [],
            "feedback": ["Rejected by Lead: Standard company policy requires native HCL for Terraform readability."],
        },
        # 17. Informational | Open | Code Quality
        {
            "code": f"CRF-{year}-0017",
            "title": "Upgrade React Router and Vite Dependencies to Latest Patch",
            "description": "Minor security and performance improvements available in upstream packages.",
            "project": "Identity & Auth Platform",
            "repo": "sso-portal",
            "severity": "Informational",
            "category": "Code Quality",
            "status": "Open",
            "assignee": neha,
            "due_date": today + timedelta(days=30),
            "recommendation": "Run npm update and verify build pipeline.",
            "work_history": [],
            "feedback": [],
        },
        # 18. Low | Reopened | Other
        {
            "code": f"CRF-{year}-0018",
            "title": "Missing Health Check Liveness Probe on Worker Container",
            "description": "Kubernetes pod restarts are not triggered if the background queue consumer hangs.",
            "project": "Core Payment Gateway",
            "repo": "transaction-worker",
            "severity": "Low",
            "category": "Other",
            "status": "Reopened",
            "assignee": rohan,
            "due_date": today + timedelta(days=2),
            "recommendation": "Add HTTP /health/live endpoint to worker process.",
            "work_history": ["Added /health endpoint."],
            "feedback": ["Reopened: Endpoint returned 200 even when rabbitmq connection was dropped. Needs active connection check."],
        },
        # 19. High | Closed | Security
        {
            "code": f"CRF-{year}-0019",
            "title": "Permissive File Upload Allowing Executable Script Execution",
            "description": "Profile picture upload endpoint failed to validate MIME magic bytes, allowing .php upload.",
            "project": "Customer Engagement Hub",
            "repo": "crm-connector",
            "severity": "High",
            "category": "Security",
            "status": "Closed",
            "assignee": nitin,
            "due_date": today - timedelta(days=10),
            "recommendation": "Check magic bytes via python-magic and store uploads in isolated object storage.",
            "work_history": ["Strict file extension and MIME header checking added.", "Moved upload directory to non-executable S3 bucket."],
            "feedback": ["Verified and signed off by Admin. Closed."],
        },
    ]

    for item in findings_spec:
        f = db.query(Finding).filter(Finding.finding_code == item["code"]).first()
        proj = project_map[item["project"]]
        repo = repo_map[f"{item['project']}/{item['repo']}"]
        assignee_u = item["assignee"]

        if not f:
            f = Finding(
                id=uuid.uuid4(),
                finding_code=item["code"],
                title=item["title"],
                description=item["description"],
                project_id=proj.id,
                repository_id=repo.id,
                branch_name="main",
                severity=item["severity"],
                category=item["category"],
                status=item["status"],
                assignee_id=assignee_u.id,
                reviewer_id=admin.id,
                created_by=admin.id,
                due_date=item["due_date"],
            )
            db.add(f)
            db.commit()
            db.refresh(f)

            # Initial status
            db.add(FindingStatusHistory(
                id=uuid.uuid4(),
                finding_id=f.id,
                old_status=None,
                new_status=item["status"],
                changed_by=admin.id,
                reason="Initial finding registration",
            ))
        else:
            f.title = item["title"]
            f.description = item["description"]
            f.project_id = proj.id
            f.repository_id = repo.id
            f.severity = item["severity"]
            f.category = item["category"]
            f.status = item["status"]
            f.assignee_id = assignee_u.id
            f.reviewer_id = admin.id
            f.due_date = item["due_date"]
            db.commit()
            db.refresh(f)

        # Work history
        for wh in item["work_history"]:
            existing_wh = db.query(FindingWorkHistory).filter(
                FindingWorkHistory.finding_id == f.id,
                FindingWorkHistory.body == wh,
            ).first()
            if not existing_wh:
                db.add(FindingWorkHistory(
                    id=uuid.uuid4(),
                    finding_id=f.id,
                    author_id=assignee_u.id,
                    entry_type="progress_update",
                    body=wh,
                ))

        # Feedback
        for fb in item["feedback"]:
            existing_fb = db.query(FindingFeedback).filter(
                FindingFeedback.finding_id == f.id,
                FindingFeedback.body == fb,
            ).first()
            if not existing_fb:
                db.add(FindingFeedback(
                    id=uuid.uuid4(),
                    finding_id=f.id,
                    author_id=admin.id,
                    body=fb,
                ))

    db.commit()
    db.close()
    print("[5/5] All Users, Projects, Repositories, and Findings Seeded Successfully!")


if __name__ == "__main__":
    seed()
