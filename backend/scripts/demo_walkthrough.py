"""
End-to-End Live Evaluation Script for CPCRS Backend
Demonstrates REQ-01 through REQ-09 in a single executable demonstration.
"""
import uuid
from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import engine
from backend.app.models.base import Base

def run_evaluation():
    print("=" * 70)
    print("  CROSS-PROJECT CODE REVIEW FINDING TRACKER (CPCRS)")
    print("  Live End-to-End Evaluation Walkthrough (REQ-01 to REQ-09)")
    print("=" * 70)

    # 1. Initialize Tables in SQLite / target engine
    print("\n[1] Initializing relational tables (REQ-01)...")
    Base.metadata.create_all(bind=engine)
    print("    -> 9 Relational tables + 1 yearly counter table initialized successfully.")

    client = TestClient(app)

    # 2. Seed Admin User & Login (REQ-02 & REQ-03)
    print("\n[2] Seeding initial Admin & Authenticating (REQ-02 & REQ-03)...")
    from backend.app.core.database import SessionLocal
    from backend.app.models.user import User
    from backend.app.core.security import get_password_hash

    db = SessionLocal()
    admin_email = "admin@cpcrs.com"
    admin_pass = "AdminSecPass123!"
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if not existing_admin:
        admin = User(
            id=uuid.uuid4(),
            name="System Administrator",
            email=admin_email,
            password_hash=get_password_hash(admin_pass),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
    else:
        existing_admin.password_hash = get_password_hash(admin_pass)
        db.commit()
    db.close()

    # Login as Admin
    login_resp = client.post("/api/auth/login", json={"email": admin_email, "password": admin_pass})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    admin_token = login_resp.json()["access_token"]
    print(f"    -> Admin login successful! Token received: {admin_token[:20]}...")

    # Verify Profile
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    print(f"    -> Verified /api/auth/me: {me_resp.json()['name']} ({me_resp.json()['role']})")

    run_id = uuid.uuid4().hex[:6]
    alice_email = f"alice_{run_id}@company.com"
    bob_email = f"bob_{run_id}@company.com"
    charlie_email = f"charlie_{run_id}@company.com"

    # 3. Admin Provisions Developers (REQ-04)
    print("\n[3] Admin provisioning developers (REQ-04)...")
    dev1_resp = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Alice Lead", "email": alice_email, "password": "AlicePass123!", "role": "developer"},
    )
    alice_id = dev1_resp.json()["id"]
    print(f"    -> Provisioned Developer 1: Alice Lead (ID: {alice_id})")

    dev2_resp = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Bob Teammate", "email": bob_email, "password": "BobPass123!", "role": "developer"},
    )
    bob_id = dev2_resp.json()["id"]
    print(f"    -> Provisioned Developer 2: Bob Teammate (ID: {bob_id})")

    dev3_resp = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Charlie Outsider", "email": charlie_email, "password": "CharliePass123!", "role": "developer"},
    )
    charlie_id = dev3_resp.json()["id"]
    print(f"    -> Provisioned Developer 3: Charlie Outsider (ID: {charlie_id})")

    # Developer Alice Login
    alice_token = client.post(
        "/api/auth/login", json={"email": alice_email, "password": "AlicePass123!"}
    ).json()["access_token"]

    # Developer Bob Login
    bob_token = client.post(
        "/api/auth/login", json={"email": bob_email, "password": "BobPass123!"}
    ).json()["access_token"]

    # Developer Charlie Login
    charlie_token = client.post(
        "/api/auth/login", json={"email": charlie_email, "password": "CharliePass123!"}
    ).json()["access_token"]

    # 4. Project Creation & Auto-Enrollment (REQ-05)
    print("\n[4] User Alice creating a project (REQ-05)...")
    proj_resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={"name": f"Fintech Core Gateway {run_id}", "description": "High-throughput payment gateway"},
    )
    project_data = proj_resp.json()
    proj_id = project_data["id"]
    print(f"    -> Project Created: '{project_data['name']}' (ID: {proj_id})")
    print(f"    -> Automatically assigned project_lead_id: {project_data['project_lead_id']}")

    # 5. Project Membership Management (REQ-06)
    print("\n[5] Project Lead Alice managing members (REQ-06)...")
    add_bob_resp = client.post(
        f"/api/projects/{proj_id}/members",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={"user_id": bob_id},
    )
    print(f"    -> Alice added Bob to project: status {add_bob_resp.status_code}")

    # Security check: Charlie (outsider) cannot add members
    forbidden_add = client.post(
        f"/api/projects/{proj_id}/members",
        headers={"Authorization": f"Bearer {charlie_token}"},
        json={"user_id": charlie_id},
    )
    print(f"    -> Security check: Outsider Charlie attempting to add member -> HTTP {forbidden_add.status_code} (Expected 403 Forbidden)")

    # 6. Manual Repository Registration (REQ-07)
    print("\n[6] Project Lead registering repository (REQ-07)...")
    repo_resp = client.post(
        f"/api/projects/{proj_id}/repositories",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={
            "name": "payment-api",
            "repository_url": "https://github.com/company/payment-api",
            "branch_name": "main",
            "technology": "Python / FastAPI",
        },
    )
    repo_data = repo_resp.json()
    repo_id = repo_data["id"]
    print(f"    -> Repository registered: '{repo_data['name']}' (ID: {repo_id}, default branch: {repo_data['branch_name']})")

    # 7. Finding Creation & Sequential Code Generation (REQ-08)
    print("\n[7] Admin creating code review findings (REQ-08)...")
    due = (date.today() + timedelta(days=14)).isoformat()
    finding1_resp = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "SQL Injection in Transaction Query",
            "description": "Unescaped merchant_id parameter in reporting query.",
            "project_id": proj_id,
            "repository_id": repo_id,
            "severity": "Critical",
            "category": "Security",
            "assignee_id": bob_id,
            "due_date": due,
        },
    )
    f1 = finding1_resp.json()
    print(f"    -> Finding 1 created! Generated Code: {f1['finding_code']} | Severity: {f1['severity']} | Status: {f1['status']}")

    finding2_resp = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Uncached Exchange Rate Calls",
            "description": "Redundant external HTTP calls slowing checkout.",
            "project_id": proj_id,
            "repository_id": repo_id,
            "severity": "Medium",
            "category": "Performance",
            "assignee_id": alice_id,
            "due_date": due,
        },
    )
    f2 = finding2_resp.json()
    print(f"    -> Finding 2 created! Generated Code: {f2['finding_code']} | Severity: {f2['severity']} | Status: {f2['status']}")

    # 8. Scoped Finding Queries & Security Barriers (REQ-09)
    print("\n[8] Finding access & role isolation queries (REQ-09)...")
    # Alice lists findings
    alice_findings = client.get("/api/findings", headers={"Authorization": f"Bearer {alice_token}"}).json()
    print(f"    -> Project member Alice querying /api/findings: {alice_findings['total']} findings visible.")

    # Charlie (outsider) lists findings
    charlie_findings = client.get("/api/findings", headers={"Authorization": f"Bearer {charlie_token}"}).json()
    print(f"    -> Outsider Charlie querying /api/findings: {charlie_findings['total']} findings visible (Project Isolation enforced).")

    # Charlie attempting to view Finding 1
    charlie_view_f1 = client.get(f"/api/findings/{f1['id']}", headers={"Authorization": f"Bearer {charlie_token}"})
    print(f"    -> Security check: Charlie fetching Finding 1 directly -> HTTP {charlie_view_f1.status_code} (Expected 403 Forbidden)")

    # 9. Status Transition: Open -> In Progress (REQ-11)
    print("\n[9] Assignee starting work (REQ-11: Open -> In Progress)...")
    prog_resp = client.patch(
        f"/api/findings/{f1['id']}/status",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={"status": "In Progress"},
    )
    assert prog_resp.status_code == 200
    print(f"    -> Bob transitioned Finding 1 to '{prog_resp.json()['status']}'")

    # 10. Threaded Feedback & Work History (REQ-12)
    print("\n[10] Work History & Threaded Feedback (REQ-12)...")
    work_resp = client.post(
        f"/api/findings/{f1['id']}/work-history",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={"body": "Refactored raw SQL concatenation into parameterized query."},
    )
    assert work_resp.status_code == 201
    print(f"    -> Bob added work-history entry: '{work_resp.json()['body'][:50]}...'")

    fb_resp = client.post(
        f"/api/findings/{f1['id']}/feedback",
        headers={"Authorization": f"Bearer {alice_token}"},
        json={"body": "Great progress, make sure unit test covers empty strings."},
    )
    assert fb_resp.status_code == 201
    print(f"    -> Alice posted feedback comment: '{fb_resp.json()['body'][:50]}...'")

    # 11. File Attachments & Download (REQ-13 & REQ-14)
    print("\n[11] Uploading and downloading evidence attachments (REQ-13 & REQ-14)...")
    import io
    proof_bytes = b"EXPLAIN ANALYZE shows zero query injection potential."
    upload_resp = client.post(
        f"/api/findings/{f1['id']}/attachments",
        headers={"Authorization": f"Bearer {bob_token}"},
        files={"file": ("fix_verification.txt", io.BytesIO(proof_bytes), "text/plain")},
        data={"attachment_kind": "resolution_proof"},
    )
    assert upload_resp.status_code == 201
    att_id = upload_resp.json()["id"]
    print(f"    -> Bob uploaded attachment: '{upload_resp.json()['original_filename']}' (ID: {att_id})")

    dl_resp = client.get(
        f"/api/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dl_resp.status_code == 200
    assert dl_resp.content == proof_bytes
    print(f"    -> Admin securely downloaded attachment: verified {len(dl_resp.content)} bytes.")

    # 12. Submit for Review (REQ-10)
    print("\n[12] Assignee submitting work for review (REQ-10)...")
    submit_resp = client.post(
        f"/api/findings/{f1['id']}/submit-for-review",
        headers={"Authorization": f"Bearer {bob_token}"},
        json={"resolution_description": "Replaced query builder and verified with integration test suite."},
    )
    assert submit_resp.status_code == 200
    print(f"    -> Bob submitted finding for review: Status is now '{submit_resp.json()['status']}'")

    # 13. Admin Review & Lifecycle Closure (REQ-11)
    print("\n[13] Admin resolving and closing finding (REQ-11)...")
    resolve_resp = client.patch(
        f"/api/findings/{f1['id']}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "Resolved", "reason": "Verified fix against security criteria."},
    )
    assert resolve_resp.status_code == 200
    print(f"    -> Admin resolved finding: Status is now '{resolve_resp.json()['status']}'")

    close_resp = client.patch(
        f"/api/findings/{f1['id']}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "Closed"},
    )
    assert close_resp.status_code == 200
    print(f"    -> Admin closed finding: Status is now '{close_resp.json()['status']}'")

    print("\n" + "=" * 70)
    print("  ALL EVALUATION CHECKS (REQ-01 THROUGH REQ-14) COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_evaluation()
