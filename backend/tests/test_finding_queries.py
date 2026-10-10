import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.finding import Finding
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.user import User


@pytest.fixture
def admin_user(db_session):
    admin = User(
        id=uuid.uuid4(),
        name="Global Admin",
        email="admin_query@example.com",
        password_hash=get_password_hash("AdminPass123!"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(subject=str(admin_user.id))


@pytest.fixture
def dev_alice(db_session):
    alice = User(
        id=uuid.uuid4(),
        name="Alice Dev",
        email="alice_q@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(alice)
    db_session.commit()
    return alice


@pytest.fixture
def dev_alice_token(dev_alice):
    return create_access_token(subject=str(dev_alice.id))


@pytest.fixture
def dev_bob(db_session):
    bob = User(
        id=uuid.uuid4(),
        name="Bob Teammate",
        email="bob_q@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(bob)
    db_session.commit()
    return bob


@pytest.fixture
def dev_bob_token(dev_bob):
    return create_access_token(subject=str(dev_bob.id))


@pytest.fixture
def dev_charlie(db_session):
    charlie = User(
        id=uuid.uuid4(),
        name="Charlie Outsider",
        email="charlie_q@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(charlie)
    db_session.commit()
    return charlie


@pytest.fixture
def dev_charlie_token(dev_charlie):
    return create_access_token(subject=str(dev_charlie.id))


@pytest.fixture
def setup_projects_and_findings(db_session, admin_user, dev_alice, dev_bob, dev_charlie):
    # Project A (Alice & Bob are members)
    proj_a_id = uuid.uuid4()
    proj_a = Project(
        id=proj_a_id,
        name="Alpha Service",
        project_lead_id=dev_alice.id,
        created_by=dev_alice.id,
    )
    db_session.add(proj_a)
    db_session.add(ProjectMember(project_id=proj_a_id, user_id=dev_alice.id, added_by=dev_alice.id))
    db_session.add(ProjectMember(project_id=proj_a_id, user_id=dev_bob.id, added_by=dev_alice.id))

    repo_a = Repository(
        id=uuid.uuid4(),
        project_id=proj_a_id,
        name="alpha-repo",
        branch_name="main",
        is_active=True,
    )
    db_session.add(repo_a)

    # Project B (Only Charlie is member)
    proj_b_id = uuid.uuid4()
    proj_b = Project(
        id=proj_b_id,
        name="Beta Service",
        project_lead_id=dev_charlie.id,
        created_by=dev_charlie.id,
    )
    db_session.add(proj_b)
    db_session.add(ProjectMember(project_id=proj_b_id, user_id=dev_charlie.id, added_by=dev_charlie.id))

    repo_b = Repository(
        id=uuid.uuid4(),
        project_id=proj_b_id,
        name="beta-repo",
        branch_name="main",
        is_active=True,
    )
    db_session.add(repo_b)

    # Finding A1 (Project A, assigned to Alice)
    due = date.today() + timedelta(days=10)
    finding_a1 = Finding(
        id=uuid.uuid4(),
        finding_code="CRF-2026-0001",
        title="SQL Injection vulnerability",
        description="Found in auth controller query",
        project_id=proj_a_id,
        repository_id=repo_a.id,
        branch_name="main",
        severity="High",
        category="Security",
        status="Open",
        assignee_id=dev_alice.id,
        created_by=admin_user.id,
        due_date=due,
    )
    db_session.add(finding_a1)

    # Finding A2 (Project A, assigned to Bob)
    finding_a2 = Finding(
        id=uuid.uuid4(),
        finding_code="CRF-2026-0002",
        title="Remote Code Execution",
        description="Insecure deserialization in worker",
        project_id=proj_a_id,
        repository_id=repo_a.id,
        branch_name="main",
        severity="Critical",
        category="Security",
        status="In Progress",
        assignee_id=dev_bob.id,
        created_by=admin_user.id,
        due_date=due,
    )
    db_session.add(finding_a2)

    # Finding B1 (Project B, assigned to Charlie)
    finding_b1 = Finding(
        id=uuid.uuid4(),
        finding_code="CRF-2026-0003",
        title="Cross-Site Scripting XSS",
        description="Reflected XSS in search endpoint",
        project_id=proj_b_id,
        repository_id=repo_b.id,
        branch_name="main",
        severity="Medium",
        category="Security",
        status="Open",
        assignee_id=dev_charlie.id,
        created_by=admin_user.id,
        due_date=due,
    )
    db_session.add(finding_b1)

    # Soft-deleted Finding A3 (Project A)
    finding_a3_deleted = Finding(
        id=uuid.uuid4(),
        finding_code="CRF-2026-0004",
        title="Obsolete Finding",
        description="Soft deleted finding",
        project_id=proj_a_id,
        repository_id=repo_a.id,
        branch_name="main",
        severity="Low",
        category="Documentation",
        status="Closed",
        assignee_id=dev_alice.id,
        created_by=admin_user.id,
        due_date=due,
        deleted_at=datetime.now(timezone.utc),
    )
    db_session.add(finding_a3_deleted)

    db_session.commit()
    return {
        "proj_a": proj_a,
        "proj_b": proj_b,
        "repo_a": repo_a,
        "repo_b": repo_b,
        "finding_a1": finding_a1,
        "finding_a2": finding_a2,
        "finding_b1": finding_b1,
        "finding_a3_deleted": finding_a3_deleted,
    }


# =========================================================================
# REQ-09: GET /api/findings
# =========================================================================

def test_admin_can_view_all_findings_globally(client, admin_token, setup_projects_and_findings):
    """
    REQ-09: Admins see all active findings across all projects in paginated envelope.
    """
    resp = client.get("/api/findings", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "pages" in data

    # 3 active findings, soft-deleted is excluded
    assert data["total"] == 3
    assert len(data["items"]) == 3
    codes = {f["finding_code"] for f in data["items"]}
    assert "CRF-2026-0001" in codes
    assert "CRF-2026-0002" in codes
    assert "CRF-2026-0003" in codes
    assert "CRF-2026-0004" not in codes


def test_developer_can_only_view_findings_in_assigned_projects(
    client, dev_alice_token, dev_charlie_token, setup_projects_and_findings
):
    """
    REQ-09: Developers can only view findings belonging to projects they are enrolled in.
    """
    # Alice (Project A member) sees finding A1 and A2, but not B1
    resp_alice = client.get("/api/findings", headers={"Authorization": f"Bearer {dev_alice_token}"})
    assert resp_alice.status_code == 200
    data_alice = resp_alice.json()
    assert data_alice["total"] == 2
    alice_codes = {f["finding_code"] for f in data_alice["items"]}
    assert "CRF-2026-0001" in alice_codes
    assert "CRF-2026-0002" in alice_codes
    assert "CRF-2026-0003" not in alice_codes

    # Charlie (Project B member) sees finding B1 only
    resp_charlie = client.get("/api/findings", headers={"Authorization": f"Bearer {dev_charlie_token}"})
    assert resp_charlie.status_code == 200
    data_charlie = resp_charlie.json()
    assert data_charlie["total"] == 1
    assert data_charlie["items"][0]["finding_code"] == "CRF-2026-0003"


def test_filter_findings_by_severity_status_and_search(client, admin_token, setup_projects_and_findings):
    """
    REQ-09: Filtering findings by severity, status, or search keywords.
    """
    # 1. Filter by severity=Critical
    resp_crit = client.get(
        "/api/findings?severity=Critical",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_crit.status_code == 200
    assert resp_crit.json()["total"] == 1
    assert resp_crit.json()["items"][0]["finding_code"] == "CRF-2026-0002"

    # 2. Filter by status=Open
    resp_open = client.get(
        "/api/findings?status=Open",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_open.status_code == 200
    assert resp_open.json()["total"] == 2

    # 3. Search keyword
    resp_search = client.get(
        "/api/findings?search=Injection",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_search.status_code == 200
    assert resp_search.json()["total"] == 1
    assert resp_search.json()["items"][0]["finding_code"] == "CRF-2026-0001"


def test_pagination_envelope_page_and_page_size(client, admin_token, setup_projects_and_findings):
    """
    REQ-09: Paginated response envelope with page and page_size.
    """
    resp = client.get(
        "/api/findings?page=1&page_size=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] == 3
    assert data["pages"] == 2
    assert len(data["items"]) == 2

    # Page 2
    resp_page2 = client.get(
        "/api/findings?page=2&page_size=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_page2.status_code == 200
    data_page2 = resp_page2.json()
    assert data_page2["page"] == 2
    assert len(data_page2["items"]) == 1


# =========================================================================
# REQ-09: GET /api/findings/{id}
# =========================================================================

def test_get_single_finding_detail_by_admin_and_project_member(
    client, admin_token, dev_alice_token, dev_bob_token, setup_projects_and_findings
):
    """
    REQ-09: Admin and enrolled project members can view single finding detail.
    """
    f_a1 = setup_projects_and_findings["finding_a1"]

    # 1. Admin can view
    resp_admin = client.get(f"/api/findings/{f_a1.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200
    assert resp_admin.json()["id"] == str(f_a1.id)
    assert resp_admin.json()["finding_code"] == "CRF-2026-0001"

    # 2. Assignee (Alice) can view
    resp_alice = client.get(f"/api/findings/{f_a1.id}", headers={"Authorization": f"Bearer {dev_alice_token}"})
    assert resp_alice.status_code == 200
    assert resp_alice.json()["id"] == str(f_a1.id)

    # 3. Teammate in same project (Bob) can view
    resp_bob = client.get(f"/api/findings/{f_a1.id}", headers={"Authorization": f"Bearer {dev_bob_token}"})
    assert resp_bob.status_code == 200
    assert resp_bob.json()["id"] == str(f_a1.id)


def test_get_single_finding_by_outsider_developer_returns_403(
    client, dev_charlie_token, setup_projects_and_findings
):
    """
    REQ-09: Outsider developer receives 403 Forbidden when requesting finding in another project.
    """
    f_a1 = setup_projects_and_findings["finding_a1"]
    resp = client.get(f"/api/findings/{f_a1.id}", headers={"Authorization": f"Bearer {dev_charlie_token}"})
    assert resp.status_code == 403
    assert "access denied" in resp.json()["detail"].lower()


def test_get_nonexistent_or_deleted_finding_returns_404(
    client, admin_token, setup_projects_and_findings
):
    """
    REQ-09: Nonexistent or soft-deleted findings return 404 Not Found.
    """
    # Nonexistent
    random_id = uuid.uuid4()
    resp_random = client.get(f"/api/findings/{random_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_random.status_code == 404

    # Soft-deleted
    f_deleted = setup_projects_and_findings["finding_a3_deleted"]
    resp_del = client.get(f"/api/findings/{f_deleted.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_del.status_code == 404


# =========================================================================
# REQ-09: GET /api/projects/{project_id}/findings
# =========================================================================

def test_get_project_findings_scoped_endpoint(
    client, admin_token, dev_alice_token, dev_charlie_token, setup_projects_and_findings
):
    """
    REQ-09: GET /api/projects/{project_id}/findings returns project-scoped findings.
    """
    proj_a = setup_projects_and_findings["proj_a"]

    # 1. Admin can list
    resp_admin = client.get(
        f"/api/projects/{proj_a.id}/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_admin.status_code == 200
    assert resp_admin.json()["total"] == 2

    # 2. Project member (Alice) can list
    resp_alice = client.get(
        f"/api/projects/{proj_a.id}/findings",
        headers={"Authorization": f"Bearer {dev_alice_token}"},
    )
    assert resp_alice.status_code == 200
    assert resp_alice.json()["total"] == 2

    # 3. Outsider (Charlie) receives 403 Forbidden
    resp_charlie = client.get(
        f"/api/projects/{proj_a.id}/findings",
        headers={"Authorization": f"Bearer {dev_charlie_token}"},
    )
    assert resp_charlie.status_code == 403
