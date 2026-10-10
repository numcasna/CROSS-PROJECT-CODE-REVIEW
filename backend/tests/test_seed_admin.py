import os
import pytest
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from backend.app.models.user import User

def test_seed_admin_creates_admin_user_via_args(db_session):
    """
    REQ-02: seed_admin provisions initial admin with Argon2id hash and admin role.
    """
    from backend.scripts.seed_admin import seed_admin

    result = seed_admin(
        name="System Admin",
        email="admin@internal.system",
        password="ValidPassword123!",
        db=db_session,
    )
    assert result is True

    user = db_session.query(User).filter(User.email == "admin@internal.system").first()
    assert user is not None
    assert user.name == "System Admin"
    assert user.role == "admin"
    assert user.is_active is True
    assert user.password_hash.startswith("$argon2id$")
    assert user.password_hash != "ValidPassword123!"

    # Verify password verification using Argon2id
    ph = PasswordHasher()
    assert ph.verify(user.password_hash, "ValidPassword123!") is True

def test_seed_admin_reads_from_environment_variables(db_session, monkeypatch):
    """
    REQ-02: seed_admin falls back to SEED_ADMIN_* environment variables when flags are omitted.
    """
    from backend.scripts.seed_admin import seed_admin

    monkeypatch.setenv("SEED_ADMIN_NAME", "Env Admin")
    monkeypatch.setenv("SEED_ADMIN_EMAIL", "env_admin@internal.system")
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "EnvSecret123!")

    result = seed_admin(db=db_session)
    assert result is True

    user = db_session.query(User).filter(User.email == "env_admin@internal.system").first()
    assert user is not None
    assert user.name == "Env Admin"
    assert user.role == "admin"

    ph = PasswordHasher()
    assert ph.verify(user.password_hash, "EnvSecret123!") is True

def test_seed_admin_idempotent_when_email_already_exists(db_session):
    """
    REQ-02: seed_admin safely handles existing admin email without duplication or crash.
    """
    from backend.scripts.seed_admin import seed_admin

    seed_admin(
        name="Original Admin",
        email="existing_admin@internal.system",
        password="Pass1!",
        db=db_session,
    )

    # Re-run with same email
    result = seed_admin(
        name="Duplicate Attempt",
        email="existing_admin@internal.system",
        password="Pass2!",
        db=db_session,
    )
    assert result is False

    # Ensure only 1 record exists with original name
    count = db_session.query(User).filter(User.email == "existing_admin@internal.system").count()
    assert count == 1
    user = db_session.query(User).filter(User.email == "existing_admin@internal.system").first()
    assert user.name == "Original Admin"

def test_seed_admin_rejects_empty_password(db_session):
    """
    REQ-02: seed_admin rejects invalid inputs (e.g., blank password).
    """
    from backend.scripts.seed_admin import seed_admin

    with pytest.raises(ValueError, match="Password cannot be empty"):
        seed_admin(
            name="Blank Admin",
            email="blank@internal.system",
            password="",
            db=db_session,
        )
