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
        email="admin_proj@example.com",
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
def dev1_user(db_session):
    dev1 = User(
        id=uuid.uuid4(),
        name="Lead Dev Alice",
        email="alice@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(dev1)
    db_session.commit()
    return dev1

@pytest.fixture
def dev1_token(dev1_user):
    return create_access_token(subject=str(dev1_user.id))

@pytest.fixture
def dev2_user(db_session):
    dev2 = User(
        id=uuid.uuid4(),
        name="Teammate Bob",
        email="bob@example.com",
        password_hash=get_password_hash("DevPass123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(dev2)
    db_session.commit()
    return dev2

@pytest.fixture
def dev2_token(dev2_user):
    return create_access_token(subject=str(dev2_user.id))


def test_user_creates_project_success_and_auto_enrolled_as_lead(client, dev1_token, dev1_user, dev2_user, db_session):
    """
    REQ-05: User creates project, is automatically assigned as lead and enrolled into project_members.
    """
    response = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {dev1_token}"},
        json={
            "name": "Alpha Platform",
            "description": "Cross-project review system",
            "member_ids": [str(dev2_user.id)],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alpha Platform"
    assert data["description"] == "Cross-project review system"
    assert data["project_lead_id"] == str(dev1_user.id)
    assert data["created_by"] == str(dev1_user.id)

    # Verify both creator/lead and teammate are enrolled in project_members
    project_id = uuid.UUID(data["id"])
    memberships = db_session.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
    member_user_ids = {m.user_id for m in memberships}
    assert dev1_user.id in member_user_ids
    assert dev2_user.id in member_user_ids


def test_admin_cannot_create_project_returns_403(client, admin_token):
    """
    REQ-05: Admins have view-only access; creating a project is restricted to regular users.
    """
    response = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Admin Forbidden Project", "description": "Should fail"},
    )
    assert response.status_code == 403
    assert "view-only" in response.json()["detail"].lower()


def test_admin_can_view_all_projects(client, admin_token, dev1_token, dev2_user):
    """
    REQ-05: Admins can view all projects globally.
    """
    # Create project as dev1
    resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {dev1_token}"},
        json={"name": "Global Audit Project", "member_ids": []},
    )
    assert resp.status_code == 201
    proj_id = resp.json()["id"]

    # Admin lists projects
    response = client.get("/api/projects", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert proj_id in ids


def test_developer_can_only_view_assigned_projects(client, dev1_token, dev2_token, dev1_user, dev2_user):
    """
    REQ-05: Developers can only view projects they are members of.
    """
    # Dev1 creates Project A (only Dev1 is member)
    resp_a = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {dev1_token}"},
        json={"name": "Alice Private Project"},
    )
    proj_a_id = resp_a.json()["id"]

    # Dev2 creates Project B (only Dev2 is member)
    resp_b = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {dev2_token}"},
        json={"name": "Bob Private Project"},
    )
    proj_b_id = resp_b.json()["id"]

    # Dev1 lists projects
    resp_dev1 = client.get("/api/projects", headers={"Authorization": f"Bearer {dev1_token}"})
    assert resp_dev1.status_code == 200
    dev1_ids = [p["id"] for p in resp_dev1.json()]
    assert proj_a_id in dev1_ids
    assert proj_b_id not in dev1_ids

    # Dev1 attempts to fetch Project B details directly (should return 403 or 404)
    resp_detail = client.get(f"/api/projects/{proj_b_id}", headers={"Authorization": f"Bearer {dev1_token}"})
    assert resp_detail.status_code in (403, 404)


def test_developer_can_view_assigned_project_detail(client, dev1_token):
    """
    REQ-05: Developer can view details of projects they belong to.
    """
    create_resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {dev1_token}"},
        json={"name": "Detail Test Project", "description": "Has description"},
    )
    proj_id = create_resp.json()["id"]

    response = client.get(f"/api/projects/{proj_id}", headers={"Authorization": f"Bearer {dev1_token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Detail Test Project"
    assert response.json()["description"] == "Has description"


def test_project_member_can_update_project(client, dev1_token):
    """
    REQ-05: Authorized project user can update project information.
    """
    create_resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {dev1_token}"},
        json={"name": "Initial Name", "description": "Initial Desc"},
    )
    proj_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/projects/{proj_id}",
        headers={"Authorization": f"Bearer {dev1_token}"},
        json={"name": "Updated Name", "description": "Updated Desc"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Updated Name"
    assert patch_resp.json()["description"] == "Updated Desc"


def test_non_member_cannot_update_project_returns_403(client, dev1_token, dev2_token):
    """
    REQ-05: Non-member cannot update another project (403 Forbidden).
    """
    create_resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {dev1_token}"},
        json={"name": "Alice Fortress"},
    )
    proj_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/projects/{proj_id}",
        headers={"Authorization": f"Bearer {dev2_token}"},
        json={"name": "Bob Intrusion Attempt"},
    )
    assert patch_resp.status_code in (403, 404)


def test_admin_can_soft_delete_project_and_exclude_from_listings(client, admin_token, dev1_token, db_session):
    """
    REQ-05: Only admin can soft-delete projects; deleted projects are excluded from normal listings.
    """
    create_resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {dev1_token}"},
        json={"name": "Delete Me Project"},
    )
    proj_id = create_resp.json()["id"]

    # Admin soft-deletes project
    del_resp = client.delete(f"/api/projects/{proj_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_resp.status_code == 204

    # Verify deleted_at timestamp in DB
    db_proj = db_session.get(Project, uuid.UUID(proj_id))
    assert db_proj.deleted_at is not None

    # Excluded from admin listing
    list_resp = client.get("/api/projects", headers={"Authorization": f"Bearer {admin_token}"})
    assert proj_id not in [p["id"] for p in list_resp.json()]


def test_developer_cannot_delete_project_returns_403(client, dev1_token):
    """
    REQ-05: Developers are barred from deleting projects (403 Forbidden).
    """
    create_resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {dev1_token}"},
        json={"name": "Protected Project"},
    )
    proj_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/projects/{proj_id}", headers={"Authorization": f"Bearer {dev1_token}"})
    assert del_resp.status_code == 403
