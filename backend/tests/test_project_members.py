import uuid
from datetime import datetime, timezone
import pytest
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.project import Project, ProjectMember
from backend.app.models.user import User


@pytest.fixture
def admin_user(db_session):
    admin = User(
        id=uuid.uuid4(),
        name="Global Admin",
        email="admin_mem@example.com",
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
        name="Project Lead Dave",
        email="lead_dave@example.com",
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
        name="Member Emily",
        email="member_emily@example.com",
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
        name="Outsider Oscar",
        email="outsider_oscar@example.com",
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
def new_dev_user(db_session):
    dev = User(
        id=uuid.uuid4(),
        name="Newbie Nick",
        email="newbie_nick@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(dev)
    db_session.commit()
    return dev


@pytest.fixture
def project(db_session, lead_user, member_user):
    proj_id = uuid.uuid4()
    p = Project(
        id=proj_id,
        name="Titan Security Engine",
        description="Core security infrastructure",
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
# GET /api/projects/{project_id}/members
# =========================================================================

def test_list_project_members_by_lead_member_and_admin(client, project, lead_token, member_token, admin_token, lead_user, member_user):
    """
    REQ-06: Project Lead, enrolled members, and global admins can list project members.
    """
    # 1. Lead can list members
    resp_lead = client.get(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {lead_token}"},
    )
    assert resp_lead.status_code == 200
    members = resp_lead.json()
    assert len(members) == 2
    user_ids = {m["user_id"] for m in members}
    assert str(lead_user.id) in user_ids
    assert str(member_user.id) in user_ids

    # 2. Member can list members
    resp_member = client.get(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp_member.status_code == 200
    assert len(resp_member.json()) == 2

    # 3. Admin can list members (global view)
    resp_admin = client.get(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_admin.status_code == 200
    assert len(resp_admin.json()) == 2


def test_list_project_members_non_member_forbidden(client, project, outsider_token):
    """
    REQ-06: Non-member developer cannot list project members (403 Forbidden).
    """
    resp = client.get(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert resp.status_code == 403


# =========================================================================
# POST /api/projects/{project_id}/members
# =========================================================================

def test_project_lead_can_add_member(client, project, lead_token, new_dev_user, lead_user, db_session):
    """
    REQ-06: Only the Project Lead can add new members (201 Created).
    """
    resp = client.post(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"user_id": str(new_dev_user.id)},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["project_id"] == str(project.id)
    assert data["user_id"] == str(new_dev_user.id)
    assert data["name"] == new_dev_user.name
    assert data["email"] == new_dev_user.email

    # Verify database persistence
    pm = (
        db_session.query(ProjectMember)
        .filter(ProjectMember.project_id == project.id, ProjectMember.user_id == new_dev_user.id)
        .first()
    )
    assert pm is not None
    assert pm.added_by == lead_user.id


def test_add_member_duplicate_returns_409(client, project, lead_token, member_user):
    """
    REQ-06: Adding a user who is already a member returns 409 Conflict.
    """
    resp = client.post(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"user_id": str(member_user.id)},
    )
    assert resp.status_code == 409
    assert "already a member" in resp.json()["detail"].lower()


def test_non_lead_cannot_add_member_returns_403(client, project, member_token, new_dev_user):
    """
    REQ-06: Regular project members receive 403 Forbidden when attempting to add members.
    """
    resp = client.post(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"user_id": str(new_dev_user.id)},
    )
    assert resp.status_code == 403
    assert "only the project lead" in resp.json()["detail"].lower()


def test_admin_cannot_add_member_returns_403(client, project, admin_token, new_dev_user):
    """
    REQ-06: Admins cannot add members (only the Project Lead is authorized; 403 Forbidden).
    """
    resp = client.post(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"user_id": str(new_dev_user.id)},
    )
    assert resp.status_code == 403


def test_add_nonexistent_user_returns_404(client, project, lead_token):
    """
    REQ-06: Adding a non-existent user returns 404 Not Found.
    """
    random_user_id = uuid.uuid4()
    resp = client.post(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"user_id": str(random_user_id)},
    )
    assert resp.status_code == 404
    assert "user not found" in resp.json()["detail"].lower()


# =========================================================================
# DELETE /api/projects/{project_id}/members/{user_id}
# =========================================================================

def test_project_lead_can_remove_member(client, project, lead_token, member_user, db_session):
    """
    REQ-06: Project Lead can remove a team member (204 No Content).
    """
    resp = client.delete(
        f"/api/projects/{project.id}/members/{member_user.id}",
        headers={"Authorization": f"Bearer {lead_token}"},
    )
    assert resp.status_code == 204

    # Verify deleted from DB
    pm = (
        db_session.query(ProjectMember)
        .filter(ProjectMember.project_id == project.id, ProjectMember.user_id == member_user.id)
        .first()
    )
    assert pm is None


def test_project_lead_cannot_remove_self_returns_400(client, project, lead_token, lead_user):
    """
    REQ-06: The Project Lead cannot be removed from project_members (must return 400 Bad Request).
    """
    resp = client.delete(
        f"/api/projects/{project.id}/members/{lead_user.id}",
        headers={"Authorization": f"Bearer {lead_token}"},
    )
    assert resp.status_code == 400
    assert "project lead cannot be removed" in resp.json()["detail"].lower()


def test_non_lead_cannot_remove_member_returns_403(client, project, member_token, lead_user):
    """
    REQ-06: Non-lead project members receive 403 Forbidden when attempting to remove members.
    """
    resp = client.delete(
        f"/api/projects/{project.id}/members/{lead_user.id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp.status_code == 403
    assert "only the project lead" in resp.json()["detail"].lower()


def test_admin_cannot_remove_member_returns_403(client, project, admin_token, member_user):
    """
    REQ-06: Admins receive 403 Forbidden when attempting to remove members (Lead only).
    """
    resp = client.delete(
        f"/api/projects/{project.id}/members/{member_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 403


def test_remove_nonexistent_member_returns_404(client, project, lead_token, outsider_user):
    """
    REQ-06: Removing a user who is not a member of the project returns 404 Not Found.
    """
    resp = client.delete(
        f"/api/projects/{project.id}/members/{outsider_user.id}",
        headers={"Authorization": f"Bearer {lead_token}"},
    )
    assert resp.status_code == 404
    assert "not a member" in resp.json()["detail"].lower()


def test_member_operations_on_nonexistent_or_soft_deleted_project_returns_404(
    client, project, lead_token, member_user, new_dev_user, db_session
):
    """
    REQ-06: Operations on non-existent or soft-deleted projects return 404 Not Found.
    """
    random_project_id = uuid.uuid4()

    # Nonexistent project
    assert client.get(
        f"/api/projects/{random_project_id}/members",
        headers={"Authorization": f"Bearer {lead_token}"},
    ).status_code == 404

    assert client.post(
        f"/api/projects/{random_project_id}/members",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"user_id": str(new_dev_user.id)},
    ).status_code == 404

    assert client.delete(
        f"/api/projects/{random_project_id}/members/{member_user.id}",
        headers={"Authorization": f"Bearer {lead_token}"},
    ).status_code == 404

    # Soft-deleted project
    project.deleted_at = datetime.now(timezone.utc)
    db_session.commit()

    assert client.get(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {lead_token}"},
    ).status_code == 404

    assert client.post(
        f"/api/projects/{project.id}/members",
        headers={"Authorization": f"Bearer {lead_token}"},
        json={"user_id": str(new_dev_user.id)},
    ).status_code == 404

    assert client.delete(
        f"/api/projects/{project.id}/members/{member_user.id}",
        headers={"Authorization": f"Bearer {lead_token}"},
    ).status_code == 404
