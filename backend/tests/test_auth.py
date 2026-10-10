import uuid
import pytest
from backend.app.core.security import get_password_hash
from backend.app.models.user import User

@pytest.fixture
def test_user(db_session):
    user = User(
        id=uuid.uuid4(),
        name="Developer One",
        email="dev1@example.com",
        password_hash=get_password_hash("DevPassword123!"),
        role="developer",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def inactive_user(db_session):
    user = User(
        id=uuid.uuid4(),
        name="Inactive Developer",
        email="inactive@example.com",
        password_hash=get_password_hash("DevPassword123!"),
        role="developer",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_successful_returns_jwt_and_user_profile(client, test_user):
    """
    REQ-03: POST /api/auth/login returns 200, JWT token, and user profile.
    """
    response = client.post(
        "/api/auth/login",
        json={"email": "dev1@example.com", "password": "DevPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["id"] == str(test_user.id)
    assert data["user"]["email"] == "dev1@example.com"
    assert data["user"]["role"] == "developer"
    assert data["user"]["is_active"] is True
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_login_wrong_password_returns_401(client, test_user):
    """
    REQ-03: POST /api/auth/login returns 401 when password is invalid.
    """
    response = client.post(
        "/api/auth/login",
        json={"email": "dev1@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_nonexistent_email_returns_401(client):
    """
    REQ-03: POST /api/auth/login returns 401 when email does not exist.
    """
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "AnyPassword!"},
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_inactive_user_returns_403(client, inactive_user):
    """
    REQ-03: POST /api/auth/login returns 403 when user is inactive.
    """
    response = client.post(
        "/api/auth/login",
        json={"email": "inactive@example.com", "password": "DevPassword123!"},
    )
    assert response.status_code == 403
    assert "Inactive account" in response.json()["detail"]


def test_get_current_user_me_with_valid_token(client, test_user):
    """
    REQ-03: GET /api/auth/me returns 200 and authenticated user identity.
    """
    # 1. Login to obtain token
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "dev1@example.com", "password": "DevPassword123!"},
    )
    token = login_resp.json()["access_token"]

    # 2. Call /api/auth/me
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    me_data = response.json()
    assert me_data["id"] == str(test_user.id)
    assert me_data["email"] == "dev1@example.com"
    assert me_data["role"] == "developer"
    assert me_data["is_active"] is True


def test_get_current_user_me_missing_token_returns_401(client):
    """
    REQ-03: GET /api/auth/me returns 401 when Authorization header is absent.
    """
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_get_current_user_me_invalid_token_returns_401(client):
    """
    REQ-03: GET /api/auth/me returns 401 when token is invalid.
    """
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer bad.token.value"},
    )
    assert response.status_code == 401


def test_logout_returns_204(client):
    """
    REQ-03: POST /api/auth/logout returns 204.
    """
    response = client.post("/api/auth/logout")
    assert response.status_code == 204
