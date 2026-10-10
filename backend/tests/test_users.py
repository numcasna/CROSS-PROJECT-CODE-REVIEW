import uuid
import pytest
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User

@pytest.fixture
def admin_token(db_session):
    admin = User(
        id=uuid.uuid4(),
        name="Global Admin",
        email="global_admin@example.com",
        password_hash=get_password_hash("AdminSecret123!"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    return create_access_token(subject=str(admin.id))

@pytest.fixture
def dev_token(db_session):
    dev = User(
        id=uuid.uuid4(),
        name="Regular Dev",
        email="regular_dev@example.com",
        password_hash=get_password_hash("DevSecret123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(dev)
    db_session.commit()
    return create_access_token(subject=str(dev.id))


def test_admin_creates_developer_user_success(client, admin_token, db_session):
    """
    REQ-04: Admin can create a new developer account (201 Created).
    """
    response = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Alice Developer",
            "email": "alice@example.com",
            "password": "AlicePassword123!",
            "role": "developer",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice Developer"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "developer"
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data

    # Verify password hashed with Argon2id in DB
    created_user = db_session.query(User).filter(User.email == "alice@example.com").first()
    assert created_user is not None
    assert created_user.password_hash.startswith("$argon2id$")


def test_admin_creates_admin_user_success(client, admin_token):
    """
    REQ-04: Admin can create another admin account (201 Created).
    """
    response = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Bob Admin",
            "email": "bob_admin@example.com",
            "password": "BobPassword123!",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "admin"


def test_developer_cannot_create_user_returns_403(client, dev_token):
    """
    REQ-04: Non-admin users are rejected with 403 Forbidden when creating accounts.
    """
    response = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {dev_token}"},
        json={
            "name": "Eve Hacker",
            "email": "eve@example.com",
            "password": "EvePassword123!",
            "role": "developer",
        },
    )
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


def test_unauthenticated_cannot_create_user_returns_401(client):
    """
    REQ-04: Unauthenticated calls to POST /api/users return 401 Unauthorized.
    """
    response = client.post(
        "/api/users",
        json={
            "name": "No Auth",
            "email": "noauth@example.com",
            "password": "Password123!",
            "role": "developer",
        },
    )
    assert response.status_code == 401


def test_create_user_duplicate_email_returns_409(client, admin_token):
    """
    REQ-04: Creating a user with an existing email returns 409 Conflict.
    """
    payload = {
        "name": "First User",
        "email": "duplicate@example.com",
        "password": "Password123!",
        "role": "developer",
    }
    resp1 = client.post("/api/users", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/users", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


def test_create_user_invalid_role_returns_422(client, admin_token):
    """
    REQ-04: Creating a user with invalid role returns 422 Unprocessable Entity.
    """
    response = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Invalid Role",
            "email": "invalid_role@example.com",
            "password": "Password123!",
            "role": "superadmin",
        },
    )
    assert response.status_code == 422


def test_get_users_list_authenticated_success(client, dev_token, admin_token):
    """
    REQ-04: Authenticated user can query user list for dropdowns (200 OK).
    """
    response = client.get("/api/users", headers={"Authorization": f"Bearer {dev_token}"})
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 2
    # Verify no password leaks
    for u in users:
        assert "password" not in u
        assert "password_hash" not in u


def test_get_users_list_with_role_filter(client, dev_token, admin_token):
    """
    REQ-04: GET /api/users?role=admin filters users by role.
    """
    response = client.get("/api/users?role=admin", headers={"Authorization": f"Bearer {dev_token}"})
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 1
    for u in users:
        assert u["role"] == "admin"


def test_get_users_unauthenticated_returns_401(client):
    """
    REQ-04: Unauthenticated GET /api/users returns 401 Unauthorized.
    """
    response = client.get("/api/users")
    assert response.status_code == 401
