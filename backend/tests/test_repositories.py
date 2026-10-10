import uuid
from datetime import datetime, timezone
import pytest
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.user import User


@pytest.fixture
def admin_user(db_session):
    admin = User(
        id=uuid.uuid4(),
        name="Global Admin",
        email="admin_repo@example.com",
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
def lead_user(db_session):
    lead = User(
        id=uuid.uuid4(),
        name="Project Lead Frank",
        email="frank_lead@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(lead)
    db_session.commit()
    return lead


@pytest.fixture
def lead_token(lead_user):
    return create_access_token(subject=str(lead_user.id))


@pytest.fixture
def member_user(db_session):
    member = User(
        id=uuid.uuid4(),
        name="Team Dev Grace",
        email="grace_member@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(member)
    db_session.commit()
    return member


@pytest.fixture
def member_token(member_user):
    return create_access_token(subject=str(member_user.id))


@pytest.fixture
def outsider_user(db_session):
    outsider = User(
        id=uuid.uuid4(),
        name="Outsider dev",
        email="outsider_repo@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(outsider)
    db_session.commit()
    return outsider


@pytest.fixture
def outsider_token(outsider_user):
    return create_access_token(subject=str(outsider_user.id))


@pytest.fixture
def project(db_session, lead_user, member_user):
    proj_id = uuid.uuid4()
    p = Project(
        id=proj_id,
        name="E-Commerce Core",
        description="Checkout and payment microservices",
        project_lead_id=lead_user.id,
        created_by=lead_user.id,
    )
    db_session.add(p)

    pm_lead = ProjectMember(
        project_id=proj_id,
        user_id=lead_user.id,
        added_by=lead_user.id,
    )
    pm_member = ProjectMember(
        project_id=proj_id,
        user_id=member_user.id,
        added_by=lead_user.id,
    )
    db_session.add(pm_lead)
    db_session.add(pm_member)
    db_session.commit()
    db_session.refresh(p)
    return p


# =========================================================================
# POST /api/projects/{project_id}/repositories
# =========================================================================

def test_project_lead_can_register_repository(client, project, lead_token, db_session):
    """
    REQ-07: Project Lead can register a new repository record (201 Created).
    """
    resp = client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={
            "name": "payment-gateway-service",
            "repository_url": "https://github.com/org/payment-gateway-service",
            "branch_name": "main",
            "technology": "Python / FastAPI",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "payment-gateway-service"
    assert data["repository_url"] == "https://github.com/org/payment-gateway-service"
    assert data["branch_name"] == "main"
    assert data["technology"] == "Python / FastAPI"
    assert data["project_id"] == str(project.id)
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data

    # Verify DB persistence
    repo = db_session.query(Repository).filter(Repository.id == uuid.UUID(data["id"])).first()
    assert repo is not None
    assert repo.project_id == project.id
    assert repo.name == "payment-gateway-service"


def test_register_repository_missing_or_blank_name_returns_400(client, project, lead_token):
    """
    REQ-07: Registering a repository with a blank or empty name returns 400 Bad Request.
    """
    resp = client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"name": "   ", "branch_name": "main"},
    )
    assert resp.status_code == 400
    assert "name is required" in resp.json()["detail"].lower()


def test_register_repository_duplicate_name_within_project_returns_409(client, project, lead_token):
    """
    REQ-07: Registering a duplicate repository name within the same project returns 409 Conflict.
    """
    # First registration
    resp1 = client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"name": "order-processor", "branch_name": "master"},
    )
    assert resp1.status_code == 201

    # Second registration with duplicate name
    resp2 = client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"name": "order-processor", "branch_name": "develop"},
    )
    assert resp2.status_code == 409
    assert "already exists in this project" in resp2.json()["detail"].lower()


def test_same_repo_name_in_different_projects_is_allowed(client, project, lead_token, lead_user, db_session):
    """
    REQ-07: The same repository name in distinct projects is permitted.
    """
    # Repo in Project 1
    resp1 = client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"name": "shared-frontend"},
    )
    assert resp1.status_code == 201

    # Create Project 2 with same lead
    proj2 = Project(
        id=uuid.uuid4(),
        name="Second App",
        project_lead_id=lead_user.id,
        created_by=lead_user.id,
    )
    db_session.add(proj2)
    db_session.add(ProjectMember(project_id=proj2.id, user_id=lead_user.id, added_by=lead_user.id))
    db_session.commit()

    # Repo in Project 2 with same name
    resp2 = client.post(
        f"/api/projects/{proj2.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"name": "shared-frontend"},
    )
    assert resp2.status_code == 201


def test_non_lead_project_member_cannot_add_repository_returns_403(client, project, member_token):
    """
    REQ-07: Regular project members receive 403 Forbidden when attempting to register a repository.
    """
    resp = client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"name": "unauthorized-repo"},
    )
    assert resp.status_code == 403
    assert "only the project lead" in resp.json()["detail"].lower()


def test_admin_cannot_add_repository_returns_403(client, project, admin_token):
    """
    REQ-07: Admins receive 403 Forbidden when attempting to register repositories (Lead only).
    """
    resp = client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "admin-forbidden-repo"},
    )
    assert resp.status_code == 403


def test_outsider_cannot_add_repository_returns_403(client, project, outsider_token):
    """
    REQ-07: Non-member developers receive 403 Forbidden.
    """
    resp = client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {outsider_token}"},
        json={"name": "outsider-repo"},
    )
    assert resp.status_code == 403


# =========================================================================
# GET /api/projects/{project_id}/repositories
# =========================================================================

def test_list_repositories_by_lead_member_and_admin(client, project, lead_token, member_token, admin_token):
    """
    REQ-07: Project Lead, enrolled members, and admins can view project repositories (200 OK).
    """
    # Lead registers two repos
    client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"name": "frontend-app", "branch_name": "main"},
    )
    client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"name": "backend-api", "branch_name": "main"},
    )

    # 1. Lead can list
    resp_lead = client.get(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
    )
    assert resp_lead.status_code == 200
    repos_lead = resp_lead.json()
    assert len(repos_lead) == 2
    repo_names = {r["name"] for r in repos_lead}
    assert "frontend-app" in repo_names
    assert "backend-api" in repo_names

    # 2. Member can list
    resp_member = client.get(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp_member.status_code == 200
    assert len(resp_member.json()) == 2

    # 3. Admin can list
    resp_admin = client.get(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_admin.status_code == 200
    assert len(resp_admin.json()) == 2


def test_outsider_cannot_list_repositories_returns_403(client, project, outsider_token):
    """
    REQ-07: Non-members receive 403 Forbidden when attempting to list repositories.
    """
    resp = client.get(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert resp.status_code == 403


def test_repository_operations_on_nonexistent_or_deleted_project_returns_404(
    client, project, lead_token, db_session
):
    """
    REQ-07: Operations on non-existent or soft-deleted projects return 404 Not Found.
    """
    random_project_id = uuid.uuid4()

    # Nonexistent project
    assert client.get(
        f"/api/projects/{random_project_id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
    ).status_code == 404

    assert client.post(
        f"/api/projects/{random_project_id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"name": "ghost-repo"},
    ).status_code == 404

    # Soft-deleted project
    project.deleted_at = datetime.now(timezone.utc)
    db_session.commit()

    assert client.get(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
    ).status_code == 404

    assert client.post(
        f"/api/projects/{project.id}/repositories",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"name": "deleted-proj-repo"},
    ).status_code == 404
