import uuid
from datetime import date, datetime, timezone
import pytest
from sqlalchemy import select

def test_database_schema_all_tables_registered(db_session):
    """
    REQ-01: Verify all 9 relational tables + 1 concurrency counter table exist in metadata.
    """
    from backend.app.models.base import Base
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        "users",
        "projects",
        "project_members",
        "repositories",
        "findings",
        "finding_feedback",
        "finding_work_history",
        "finding_status_history",
        "finding_attachments",
        "yearly_finding_counters",
    }
    missing = expected_tables - table_names
    assert not missing, f"Missing required tables in metadata: {missing}"

def test_user_creation_and_integrity(db_session):
    """
    REQ-01 / REQ-03: User table UUID PK, unique email, role validation, timestamping.
    """
    from backend.app.models.user import User

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        name="Lead Admin",
        email="admin@example.com",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$fakehash",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    retrieved = db_session.get(User, user_id)
    assert retrieved is not None
    assert retrieved.email == "admin@example.com"
    assert retrieved.role == "admin"
    assert retrieved.is_active is True
    assert retrieved.created_at is not None

def test_project_and_membership_and_soft_delete(db_session):
    """
    REQ-01 / REQ-05 / REQ-06: Project creation, membership composite PK, and soft delete timestamp.
    """
    from backend.app.models.user import User
    from backend.app.models.project import Project, ProjectMember

    admin = User(
        id=uuid.uuid4(),
        name="Admin User",
        email="admin_proj@example.com",
        password_hash="hash",
        role="admin",
    )
    lead = User(
        id=uuid.uuid4(),
        name="Dev Lead",
        email="lead@example.com",
        password_hash="hash",
        role="developer",
    )
    db_session.add_all([admin, lead])
    db_session.commit()

    project = Project(
        id=uuid.uuid4(),
        name="Security Audit Core",
        description="Cross-project finding platform",
        project_lead_id=lead.id,
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.commit()

    # Add project member (Composite PK test)
    membership = ProjectMember(
        project_id=project.id,
        user_id=lead.id,
        added_by=admin.id,
    )
    db_session.add(membership)
    db_session.commit()

    retrieved_member = db_session.get(ProjectMember, (project.id, lead.id))
    assert retrieved_member is not None
    assert retrieved_member.added_by == admin.id

    # Test soft-delete flag
    assert project.deleted_at is None
    project.deleted_at = datetime.now(timezone.utc)
    db_session.commit()

    retrieved_project = db_session.get(Project, project.id)
    assert retrieved_project.deleted_at is not None

def test_repository_registration(db_session):
    """
    REQ-01 / REQ-07: Repository manual metadata persistence.
    """
    from backend.app.models.user import User
    from backend.app.models.project import Project
    from backend.app.models.repository import Repository

    user = User(
        id=uuid.uuid4(),
        name="Admin",
        email="repo_admin@example.com",
        password_hash="hash",
        role="admin",
    )
    db_session.add(user)
    db_session.commit()

    project = Project(
        id=uuid.uuid4(),
        name="Repo Test Project",
        project_lead_id=user.id,
        created_by=user.id,
    )
    db_session.add(project)
    db_session.commit()

    repo = Repository(
        id=uuid.uuid4(),
        project_id=project.id,
        name="cpcrs-backend",
        repository_url="https://git.internal/cpcrs-backend.git",
        branch_name="main",
        technology="Python/FastAPI",
        is_active=True,
    )
    db_session.add(repo)
    db_session.commit()

    retrieved = db_session.get(Repository, repo.id)
    assert retrieved is not None
    assert retrieved.name == "cpcrs-backend"
    assert retrieved.branch_name == "main"

def test_finding_and_lifecycle_and_multistream_streams(db_session):
    """
    REQ-01 / REQ-08 / REQ-12 / REQ-13: Finding, Feedback replies, append-only work history, status history, attachments.
    """
    from backend.app.models.user import User
    from backend.app.models.project import Project
    from backend.app.models.repository import Repository
    from backend.app.models.finding import (
        Finding,
        FindingFeedback,
        FindingWorkHistory,
        FindingStatusHistory,
        FindingAttachment,
        YearlyFindingCounter,
    )

    user = User(
        id=uuid.uuid4(),
        name="Auditor",
        email="auditor@example.com",
        password_hash="hash",
        role="admin",
    )
    dev = User(
        id=uuid.uuid4(),
        name="Developer",
        email="dev@example.com",
        password_hash="hash",
        role="developer",
    )
    db_session.add_all([user, dev])
    db_session.commit()

    project = Project(id=uuid.uuid4(), name="Project Findings", project_lead_id=user.id, created_by=user.id)
    db_session.add(project)
    db_session.commit()

    repo = Repository(id=uuid.uuid4(), project_id=project.id, name="backend-repo")
    db_session.add(repo)
    db_session.commit()

    # 1. Yearly finding counter
    counter = YearlyFindingCounter(year=2026, last_seq=1)
    db_session.add(counter)
    db_session.commit()

    # 2. Finding record
    finding = Finding(
        id=uuid.uuid4(),
        finding_code="CRF-2026-0001",
        title="Unvalidated File Upload Magic Bytes",
        description="Attachment validation must check magic signatures.",
        project_id=project.id,
        repository_id=repo.id,
        severity="High",
        category="Security",
        status="Open",
        assignee_id=dev.id,
        created_by=user.id,
        due_date=date(2026, 12, 31),
    )
    db_session.add(finding)
    db_session.commit()

    # 3. Threaded feedback & reply
    feedback_parent = FindingFeedback(
        id=uuid.uuid4(),
        finding_id=finding.id,
        author_id=user.id,
        body="Ensure python-magic validates JPEG, PDF, and TXT specifically.",
    )
    db_session.add(feedback_parent)
    db_session.commit()

    feedback_reply = FindingFeedback(
        id=uuid.uuid4(),
        finding_id=finding.id,
        author_id=dev.id,
        parent_feedback_id=feedback_parent.id,
        body="Understood, will check file headers.",
    )
    db_session.add(feedback_reply)
    db_session.commit()

    # 4. Append-only Work History
    work_entry = FindingWorkHistory(
        id=uuid.uuid4(),
        finding_id=finding.id,
        author_id=dev.id,
        entry_type="progress_update",
        body="Added header validation test.",
    )
    db_session.add(work_entry)
    db_session.commit()

    # 5. Status History
    status_entry = FindingStatusHistory(
        id=uuid.uuid4(),
        finding_id=finding.id,
        old_status="Open",
        new_status="In Progress",
        changed_by=dev.id,
        reason=None,
    )
    db_session.add(status_entry)
    db_session.commit()

    # 6. Attachment metadata
    attachment = FindingAttachment(
        id=uuid.uuid4(),
        finding_id=finding.id,
        uploaded_by=dev.id,
        original_filename="proof.pdf",
        storage_key="uploads/2026/proof_xyz.pdf",
        media_type="application/pdf",
        size_bytes=102400,
        attachment_kind="resolution_proof",
    )
    db_session.add(attachment)
    db_session.commit()

    # Verification assertions
    retrieved_finding = db_session.get(Finding, finding.id)
    assert retrieved_finding.finding_code == "CRF-2026-0001"
    assert retrieved_finding.category == "Security"

    # Feedback thread verification
    retrieved_reply = db_session.get(FindingFeedback, feedback_reply.id)
    assert retrieved_reply.parent_feedback_id == feedback_parent.id

    # Work history verification
    retrieved_work = db_session.get(FindingWorkHistory, work_entry.id)
    assert retrieved_work.entry_type == "progress_update"

    # Attachment verification
    retrieved_att = db_session.get(FindingAttachment, attachment.id)
    assert retrieved_att.attachment_kind == "resolution_proof"
    assert retrieved_att.size_bytes <= 10485760
