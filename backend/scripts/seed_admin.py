import argparse
import getpass
import os
import sys
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.user import User

def seed_admin(
    name: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    db: Optional[Session] = None,
) -> bool:
    """
    Seed initial system administrator account using Argon2id password hashing.
    Supports CLI flags, environment variable fallbacks, and interactive hidden prompts.
    """
    # 1. Fallback to environment variables if parameters not supplied
    resolved_name = name or os.getenv("SEED_ADMIN_NAME")
    resolved_email = email or os.getenv("SEED_ADMIN_EMAIL")
    resolved_password = password if password is not None else os.getenv("SEED_ADMIN_PASSWORD")

    # 2. Interactive prompt fallback if running in interactive terminal
    if sys.stdin.isatty():
        if not resolved_name:
            resolved_name = input("Enter admin name: ").strip()
        if not resolved_email:
            resolved_email = input("Enter admin email: ").strip()
        if resolved_password is None:
            resolved_password = getpass.getpass("Enter admin password: ")

    # 3. Validation
    if not resolved_name:
        resolved_name = "System Administrator"

    if not resolved_email or "@" not in resolved_email:
        raise ValueError("A valid email address is required")

    if not resolved_password:
        raise ValueError("Password cannot be empty")

    normalized_email = resolved_email.strip().lower()

    # 4. Persistence
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            print(f"[WARN] Admin user with email '{normalized_email}' already exists. Skipping.")
            return False

        hashed_pw = get_password_hash(resolved_password)
        admin_user = User(
            id=uuid.uuid4(),
            name=resolved_name.strip(),
            email=normalized_email,
            password_hash=hashed_pw,
            role="admin",
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"[SUCCESS] Admin user '{normalized_email}' successfully provisioned (ID: {admin_user.id}).")
        return True
    finally:
        if owns_session:
            db.close()


def main():
    parser = argparse.ArgumentParser(description="Provision the initial system administrator account.")
    parser.add_argument("--name", help="Admin user full name (or via SEED_ADMIN_NAME env var)")
    parser.add_argument("--email", help="Admin user email address (or via SEED_ADMIN_EMAIL env var)")
    parser.add_argument("--password", help="Admin user password (or via SEED_ADMIN_PASSWORD env var, or interactive prompt)")

    args = parser.parse_args()
    success = seed_admin(name=args.name, email=args.email, password=args.password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
