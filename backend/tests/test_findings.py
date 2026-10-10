import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.finding import Finding, FindingStatusHistory, YearlyFindingCounter
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.user import User


@pytest.fixture
def admin_user(db_session):
    admin = User(
        id=uuid.uuid4(),
        name="Security Admin",
        email="sec_admin@example.com",
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
def dev_lead(db_session):
    dev = User(
        id=uuid.uuid4(),
        name="Lead Dev Leo",
        email="leo_lead@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(dev)
    db_session.commit()
    return dev


@pytest.fixture
def dev_lead_token(dev_lead):
    return create_access_token(subject=str(dev_lead.id))


@pytest.fixture
def dev_member(db_session):
    member = User(
        id=uuid.uuid4(),
        name="Teammate Maya",
        email="maya_dev@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(member)
    db_session.commit()
    return member


@pytest.fixture
def dev_outsider(db_session):
    outsider = User(
        id=uuid.uuid4(),
        name="Outsider dev",
        email="outsider_finding@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(outsider)
    db_session.commit()
    return outsider


@pytest.fixture
def project(db_session, dev_lead, dev_member):
    proj_id = uuid.uuid4()
    p = Project(
        id=proj_id,
        name="Fintech Core Banking",
        description="Core banking backend",
        project_lead_id=dev_lead.id,
        created_by=dev_lead.id,
    )
    db_session.add(p)

    pm_lead = ProjectMember(project_id=proj_id, user_id=dev_lead.id, added_by=dev_lead.id)
    pm_member = ProjectMember(project_id=proj_id, user_id=dev_member.id, added_by=dev_lead.id)
    db_session.add(pm_lead)
    db_session.add(pm_member)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def repository(db_session, project):
    repo = Repository(
        id=uuid.uuid4(),
        project_id=project.id,
        name="auth-service",
        repository_url="https://github.com/bank/auth-service",
        branch_name="staging",
        technology="Python",
        is_active=True,
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)
    return repo


# =========================================================================
# REQ-08: POST /api/findings
# =========================================================================

def test_admin_can_create_finding_with_sequential_code(
    client, admin_token, admin_user, project, repository, dev_member, db_session
):
    """
    REQ-08: Admin creates finding; server generates CRF-YYYY-XXXX sequentially;
    initial status is Open; audit entry created in finding_status_history.
    """
    current_year = datetime.now(timezone.utc).year
    due = (date.today() + timedelta(days=14)).isoformat()

    # 1. First finding
    resp1 = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "SQL Injection in User Lookup",
            "description": "User lookup query concatenates untrusted input directly into SQL statement.",
            "project_id": str(project.id),
            "repository_id": str(repository.id),
            "severity": "High",
            "category": "Security",
            "assignee_id": str(dev_member.id),
            "due_date": due,
        },
    )
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["finding_code"] == f"CRF-{current_year}-0001"
    assert data1["title"] == "SQL Injection in User Lookup"
    assert data1["status"] == "Open"
    assert data1["severity"] == "High"
    assert data1["category"] == "Security"
    assert data1["created_by"] == str(admin_user.id)
    assert data1["assignee_id"] == str(dev_member.id)
    # Inherited branch from repository
    assert data1["branch_name"] == "staging"

    # Verify status history entry in DB
    history = (
        db_session.query(FindingStatusHistory)
        .filter(FindingStatusHistory.finding_id == uuid.UUID(data1["id"]))
        .first()
    )
    assert history is not None
    assert history.new_status == "Open"
    assert history.changed_by == admin_user.id

    # 2. Second finding in same year increments sequence to 0002
    resp2 = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Broken Object Level Authorization",
            "description": "Missing tenant check on account balance endpoint.",
            "project_id": str(project.id),
            "repository_id": str(repository.id),
            "severity": "Critical",
            "category": "Security",
            "assignee_id": str(dev_member.id),
            "due_date": due,
        },
    )
    assert resp2.status_code == 201
    assert resp2.json()["finding_code"] == f"CRF-{current_year}-0002"


def test_branch_name_explicit_override_takes_precedence(
    client, admin_token, project, repository, dev_member
):
    """
    REQ-08: Explicitly provided branch_name in payload overrides repository default.
    """
    due = (date.today() + timedelta(days=7)).isoformat()
    resp = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Memory leak in crypto routine",
            "description": "Buffers are not freed on error paths.",
            "project_id": str(project.id),
            "repository_id": str(repository.id),
            "branch_name": "feature/crypto-v2",
            "severity": "Medium",
            "category": "Performance",
            "assignee_id": str(dev_member.id),
            "due_date": due,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["branch_name"] == "feature/crypto-v2"


def test_branch_name_null_when_repository_has_no_default(
    client, admin_token, project, dev_member, db_session
):
    """
    REQ-08: If branch_name is omitted and repository has no default branch set, stores null.
    """
    repo_no_branch = Repository(
        id=uuid.uuid4(),
        project_id=project.id,
        name="no-branch-service",
        branch_name=None,
        is_active=True,
    )
    db_session.add(repo_no_branch)
    db_session.commit()

    due = (date.today() + timedelta(days=5)).isoformat()
    resp = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Hardcoded API Token",
            "description": "Found test token hardcoded in repo.",
            "project_id": str(project.id),
            "repository_id": str(repo_no_branch.id),
            "severity": "Critical",
            "category": "Security",
            "assignee_id": str(dev_member.id),
            "due_date": due,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["branch_name"] is None


def test_developer_cannot_create_finding_returns_403(
    client, dev_lead_token, project, repository, dev_member
):
    """
    REQ-08: Non-admin developers (even Project Leads) receive 403 Forbidden.
    """
    due = (date.today() + timedelta(days=7)).isoformat()
    resp = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {dev_lead_token}"},
        json={
            "title": "Dev Creation Attempt",
            "description": "Should fail with 403",
            "project_id": str(project.id),
            "repository_id": str(repository.id),
            "severity": "Low",
            "category": "Code Quality",
            "assignee_id": str(dev_member.id),
            "due_date": due,
        },
    )
    assert resp.status_code == 403
    assert "only administrators" in resp.json()["detail"].lower()


def test_assignee_not_in_project_members_returns_400(
    client, admin_token, project, repository, dev_outsider
):
    """
    REQ-08: Assignee must be an active enrolled member of project_members (400 Bad Request if not).
    """
    due = (date.today() + timedelta(days=7)).isoformat()
    resp = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Cross-Project Assignment Attempt",
            "description": "Dev outsider is not in project members",
            "project_id": str(project.id),
            "repository_id": str(repository.id),
            "severity": "Low",
            "category": "Documentation",
            "assignee_id": str(dev_outsider.id),
            "due_date": due,
        },
    )
    assert resp.status_code == 400
    assert "assignee must be an active member" in resp.json()["detail"].lower()


def test_assignee_nonexistent_user_returns_404(
    client, admin_token, project, repository
):
    """
    REQ-08: Non-existent assignee user returns 404 Not Found.
    """
    due = (date.today() + timedelta(days=7)).isoformat()
    random_user_id = uuid.uuid4()
    resp = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Ghost Assignee",
            "description": "User does not exist",
            "project_id": str(project.id),
            "repository_id": str(repository.id),
            "severity": "Low",
            "category": "Code Quality",
            "assignee_id": str(random_user_id),
            "due_date": due,
        },
    )
    assert resp.status_code == 404
    assert "user not found" in resp.json()["detail"].lower()


def test_repository_not_belonging_to_project_returns_400(
    client, admin_token, project, dev_member, dev_lead, db_session
):
    """
    REQ-08: Repository must belong to the specified project (400 Bad Request if mismatched).
    """
    # Create distinct project 2 and repository in project 2
    proj2 = Project(
        id=uuid.uuid4(),
        name="Second Project",
        project_lead_id=dev_lead.id,
        created_by=dev_lead.id,
    )
    db_session.add(proj2)
    db_session.commit()

    foreign_repo = Repository(
        id=uuid.uuid4(),
        project_id=proj2.id,
        name="foreign-repo",
        is_active=True,
    )
    db_session.add(foreign_repo)
    db_session.commit()

    due = (date.today() + timedelta(days=7)).isoformat()
    resp = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Mismatched Repo Finding",
            "description": "Repo belongs to proj2, but project_id is proj1",
            "project_id": str(project.id),
            "repository_id": str(foreign_repo.id),
            "severity": "Medium",
            "category": "Security",
            "assignee_id": str(dev_member.id),
            "due_date": due,
        },
    )
    assert resp.status_code in (400, 404)
    assert "does not belong" in resp.json()["detail"].lower() or "not found" in resp.json()["detail"].lower()


def test_invalid_severity_returns_400(
    client, admin_token, project, repository, dev_member
):
    """
    REQ-08: Invalid severity level returns 400 Bad Request.
    """
    due = (date.today() + timedelta(days=7)).isoformat()
    resp = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Invalid Severity Finding",
            "description": "Severity is invalid",
            "project_id": str(project.id),
            "repository_id": str(repository.id),
            "severity": "Extreme_Danger",
            "category": "Security",
            "assignee_id": str(dev_member.id),
            "due_date": due,
        },
    )
    assert resp.status_code == 400
    assert "invalid severity" in resp.json()["detail"].lower()


def test_blank_title_or_description_returns_400(
    client, admin_token, project, repository, dev_member
):
    """
    REQ-08: Blank title or description returns 400 Bad Request.
    """
    due = (date.today() + timedelta(days=7)).isoformat()
    resp = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "   ",
            "description": "Non-empty description",
            "project_id": str(project.id),
            "repository_id": str(repository.id),
            "severity": "Low",
            "category": "Security",
            "assignee_id": str(dev_member.id),
            "due_date": due,
        },
    )
    assert resp.status_code == 400
    assert "title is required" in resp.json()["detail"].lower()


def test_nonexistent_or_deleted_project_returns_404(
    client, admin_token, project, repository, dev_member, db_session
):
    """
    REQ-08: Attempting to create finding in non-existent or soft-deleted project returns 404 Not Found.
    """
    due = (date.today() + timedelta(days=7)).isoformat()
    random_project_id = uuid.uuid4()

    # Nonexistent project
    resp_nonexistent = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Ghost Project Finding",
            "description": "Project does not exist",
            "project_id": str(random_project_id),
            "repository_id": str(repository.id),
            "severity": "Low",
            "category": "Security",
            "assignee_id": str(dev_member.id),
            "due_date": due,
        },
    )
    assert resp_nonexistent.status_code == 404

    # Soft-deleted project
    project.deleted_at = datetime.now(timezone.utc)
    db_session.commit()

    resp_deleted = client.post(
        "/api/findings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Deleted Project Finding",
            "description": "Project is soft deleted",
            "project_id": str(project.id),
            "repository_id": str(repository.id),
            "severity": "Low",
            "category": "Security",
            "assignee_id": str(dev_member.id),
            "due_date": due,
        },
    )
    assert resp_deleted.status_code == 404
