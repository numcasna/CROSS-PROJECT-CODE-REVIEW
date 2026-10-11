import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.finding import Finding, FindingStatusHistory, FindingWorkHistory


@pytest.fixture
def test_setup(db_session):
    # Admin
    admin = User(
        id=uuid.uuid4(),
        name="Admin User",
        email="admin_submit@test.com",
        password_hash=get_password_hash("pass123"),
        role="admin",
        is_active=True,
    )
    # Assignee dev
    dev1 = User(
        id=uuid.uuid4(),
        name="Assignee Dev",
        email="assignee@test.com",
        password_hash=get_password_hash("pass123"),
        role="developer",
        is_active=True,
    )
    # Peer dev in same project
    dev2 = User(
        id=uuid.uuid4(),
        name="Peer Dev",
        email="peer@test.com",
        password_hash=get_password_hash("pass123"),
        role="developer",
        is_active=True,
    )
    # Outsider dev
    dev3 = User(
        id=uuid.uuid4(),
        name="Outsider Dev",
        email="outsider@test.com",
        password_hash=get_password_hash("pass123"),
        role="developer",
        is_active=True,
    )
    db_session.add_all([admin, dev1, dev2, dev3])
    db_session.commit()

    # Project
    proj = Project(
        id=uuid.uuid4(),
        name="Project Delta",
        project_lead_id=dev1.id,
        created_by=dev1.id,
    )
    db_session.add(proj)
    db_session.commit()

    # Enrolled members: dev1 and dev2
    db_session.add(ProjectMember(project_id=proj.id, user_id=dev1.id, added_by=dev1.id))
    db_session.add(ProjectMember(project_id=proj.id, user_id=dev2.id, added_by=dev1.id))
    db_session.commit()

    # Repository
    repo = Repository(
        id=uuid.uuid4(),
        project_id=proj.id,
        name="repo-delta",
        branch_name="main",
        is_active=True,
    )
    db_session.add(repo)
    db_session.commit()

    # Finding assigned to dev1
    finding = Finding(
        id=uuid.uuid4(),
        finding_code="CRF-2026-0101",
        title="SQL Injection Vulnerability",
        description="Improper escaping in auth query",
        project_id=proj.id,
        repository_id=repo.id,
        branch_name="main",
        severity="High",
        category="Security",
        status="Open",
        assignee_id=dev1.id,
        created_by=admin.id,
        due_date=date.today() + timedelta(days=7),
    )
    db_session.add(finding)
    db_session.commit()

    admin_token = create_access_token(subject=str(admin.id))
    dev1_token = create_access_token(subject=str(dev1.id))
    dev2_token = create_access_token(subject=str(dev2.id))
    dev3_token = create_access_token(subject=str(dev3.id))

    return {
        "admin": admin,
        "dev1": dev1,
        "dev2": dev2,
        "dev3": dev3,
        "project": proj,
        "repo": repo,
        "finding": finding,
        "tokens": {
            "admin": admin_token,
            "dev1": dev1_token,
            "dev2": dev2_token,
            "dev3": dev3_token,
        },
    }


def test_submit_for_review_by_assignee_success(client, test_setup, db_session):
    fid = test_setup["finding"].id
    token = test_setup["tokens"]["dev1"]

    resp = client.post(
        f"/api/findings/{fid}/submit-for-review",
        json={"resolution_description": "Parameterized the query using SQLAlchemy ORM."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(fid)
    assert data["status"] == "In Review"

    # Verify status history record created
    history = db_session.query(FindingStatusHistory).filter(FindingStatusHistory.finding_id == fid).all()
    assert len(history) == 1
    assert history[0].old_status == "Open"
    assert history[0].new_status == "In Review"
    assert history[0].changed_by == test_setup["dev1"].id
    assert history[0].reason == "Parameterized the query using SQLAlchemy ORM."

    # Verify work history record created
    work = db_session.query(FindingWorkHistory).filter(FindingWorkHistory.finding_id == fid).all()
    assert len(work) == 1
    assert work[0].entry_type == "submission"
    assert work[0].body == "Parameterized the query using SQLAlchemy ORM."
    assert work[0].author_id == test_setup["dev1"].id


def test_submit_for_review_by_admin_success(client, test_setup, db_session):
    fid = test_setup["finding"].id
    token = test_setup["tokens"]["admin"]

    resp = client.post(
        f"/api/findings/{fid}/submit-for-review",
        json={"resolution_description": "Admin submitted patch on behalf of assignee."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "In Review"


def test_submit_for_review_by_peer_member_forbidden(client, test_setup):
    fid = test_setup["finding"].id
    token = test_setup["tokens"]["dev2"]  # peer member in same project, but not assignee

    resp = client.post(
        f"/api/findings/{fid}/submit-for-review",
        json={"resolution_description": "Peer trying to submit"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert "Only the assigned developer" in resp.json()["detail"]


def test_submit_for_review_by_outsider_forbidden(client, test_setup):
    fid = test_setup["finding"].id
    token = test_setup["tokens"]["dev3"]  # not a project member

    resp = client.post(
        f"/api/findings/{fid}/submit-for-review",
        json={"resolution_description": "Outsider submitting"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_submit_for_review_empty_description_bad_request(client, test_setup):
    fid = test_setup["finding"].id
    token = test_setup["tokens"]["dev1"]

    resp = client.post(
        f"/api/findings/{fid}/submit-for-review",
        json={"resolution_description": "   "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "Resolution description is required" in resp.json()["detail"]


def test_submit_for_review_from_reopened_status_success(client, test_setup, db_session):
    finding = test_setup["finding"]
    finding.status = "Reopened"
    db_session.commit()

    token = test_setup["tokens"]["dev1"]
    resp = client.post(
        f"/api/findings/{finding.id}/submit-for-review",
        json={"resolution_description": "Fixed edge case reported after review."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "In Review"


def test_submit_for_review_invalid_transition_conflict(client, test_setup, db_session):
    finding = test_setup["finding"]
    token = test_setup["tokens"]["dev1"]

    # If already 'In Review'
    finding.status = "In Review"
    db_session.commit()

    resp = client.post(
        f"/api/findings/{finding.id}/submit-for-review",
        json={"resolution_description": "Submitting again"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
    assert "Cannot submit for review from status 'In Review'" in resp.json()["detail"]

    # If terminal status 'Resolved'
    finding.status = "Resolved"
    db_session.commit()

    resp = client.post(
        f"/api/findings/{finding.id}/submit-for-review",
        json={"resolution_description": "Submitting resolved"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


def test_submit_for_review_nonexistent_finding_returns_404(client, test_setup):
    fake_id = uuid.uuid4()
    token = test_setup["tokens"]["dev1"]

    resp = client.post(
        f"/api/findings/{fake_id}/submit-for-review",
        json={"resolution_description": "Some description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404

