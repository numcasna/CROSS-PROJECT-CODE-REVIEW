import uuid
from datetime import date, timedelta
import pytest
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.finding import Finding, FindingStatusHistory


@pytest.fixture
def status_setup(db_session):
    admin = User(
        id=uuid.uuid4(),
        name="Admin User",
        email="admin_status@test.com",
        password_hash=get_password_hash("pass123"),
        role="admin",
        is_active=True,
    )
    dev1 = User(
        id=uuid.uuid4(),
        name="Assignee Dev",
        email="assignee_status@test.com",
        password_hash=get_password_hash("pass123"),
        role="developer",
        is_active=True,
    )
    dev2 = User(
        id=uuid.uuid4(),
        name="Peer Dev",
        email="peer_status@test.com",
        password_hash=get_password_hash("pass123"),
        role="developer",
        is_active=True,
    )
    db_session.add_all([admin, dev1, dev2])
    db_session.commit()

    proj = Project(
        id=uuid.uuid4(),
        name="Project Epsilon",
        project_lead_id=dev1.id,
        created_by=dev1.id,
    )
    db_session.add(proj)
    db_session.commit()

    db_session.add(ProjectMember(project_id=proj.id, user_id=dev1.id, added_by=dev1.id))
    db_session.add(ProjectMember(project_id=proj.id, user_id=dev2.id, added_by=dev1.id))
    db_session.commit()

    repo = Repository(
        id=uuid.uuid4(),
        project_id=proj.id,
        name="repo-eps",
        branch_name="main",
        is_active=True,
    )
    db_session.add(repo)
    db_session.commit()

    finding = Finding(
        id=uuid.uuid4(),
        finding_code="CRF-2026-0201",
        title="Cross-Site Scripting in Comment Box",
        description="User input rendered raw in innerHTML",
        project_id=proj.id,
        repository_id=repo.id,
        branch_name="main",
        severity="High",
        category="Security",
        status="Open",
        assignee_id=dev1.id,
        created_by=admin.id,
        due_date=date.today() + timedelta(days=5),
    )
    db_session.add(finding)
    db_session.commit()

    admin_token = create_access_token(subject=str(admin.id))
    dev1_token = create_access_token(subject=str(dev1.id))
    dev2_token = create_access_token(subject=str(dev2.id))

    return {
        "admin": admin,
        "dev1": dev1,
        "dev2": dev2,
        "finding": finding,
        "tokens": {
            "admin": admin_token,
            "dev1": dev1_token,
            "dev2": dev2_token,
        },
    }


def test_transition_open_to_in_progress_by_assignee_success(client, status_setup, db_session):
    fid = status_setup["finding"].id
    token = status_setup["tokens"]["dev1"]

    resp = client.patch(
        f"/api/findings/{fid}/status",
        json={"status": "In Progress"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "In Progress"

    history = db_session.query(FindingStatusHistory).filter(FindingStatusHistory.finding_id == fid).all()
    assert len(history) == 1
    assert history[0].old_status == "Open"
    assert history[0].new_status == "In Progress"
    assert history[0].changed_by == status_setup["dev1"].id


def test_transition_open_to_in_progress_by_peer_forbidden(client, status_setup):
    fid = status_setup["finding"].id
    token = status_setup["tokens"]["dev2"]

    resp = client.patch(
        f"/api/findings/{fid}/status",
        json={"status": "In Progress"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_transition_in_review_to_resolved_by_admin_success(client, status_setup, db_session):
    finding = status_setup["finding"]
    finding.status = "In Review"
    db_session.commit()

    token = status_setup["tokens"]["admin"]
    resp = client.patch(
        f"/api/findings/{finding.id}/status",
        json={"status": "Resolved", "reason": "Code review approved, test suite green"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "Resolved"


def test_transition_in_review_to_resolved_by_dev_forbidden(client, status_setup, db_session):
    finding = status_setup["finding"]
    finding.status = "In Review"
    db_session.commit()

    token = status_setup["tokens"]["dev1"]
    resp = client.patch(
        f"/api/findings/{finding.id}/status",
        json={"status": "Resolved"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_transition_in_review_to_reopened_requires_reason(client, status_setup, db_session):
    finding = status_setup["finding"]
    finding.status = "In Review"
    db_session.commit()

    token = status_setup["tokens"]["admin"]
    # Missing reason
    resp = client.patch(
        f"/api/findings/{finding.id}/status",
        json={"status": "Reopened"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "Reason is mandatory when reopening" in resp.json()["detail"]

    # With non-empty reason
    resp_ok = client.patch(
        f"/api/findings/{finding.id}/status",
        json={"status": "Reopened", "reason": "Edge case vulnerability still present in sanitize()"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["status"] == "Reopened"


def test_transition_to_rejected_requires_reason(client, status_setup, db_session):
    finding = status_setup["finding"]
    token = status_setup["tokens"]["admin"]

    # Missing reason
    resp = client.patch(
        f"/api/findings/{finding.id}/status",
        json={"status": "Rejected"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "Reason is mandatory when rejecting" in resp.json()["detail"]

    # With non-empty reason
    resp_ok = client.patch(
        f"/api/findings/{finding.id}/status",
        json={"status": "Rejected", "reason": "Duplicate of CRF-2026-0001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["status"] == "Rejected"


def test_transition_resolved_to_closed_by_admin_success(client, status_setup, db_session):
    finding = status_setup["finding"]
    finding.status = "Resolved"
    db_session.commit()

    token = status_setup["tokens"]["admin"]
    resp = client.patch(
        f"/api/findings/{finding.id}/status",
        json={"status": "Closed"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "Closed"


def test_transition_invalid_from_terminal_states_conflict(client, status_setup, db_session):
    finding = status_setup["finding"]
    finding.status = "Closed"
    db_session.commit()

    token = status_setup["tokens"]["admin"]
    resp = client.patch(
        f"/api/findings/{finding.id}/status",
        json={"status": "Open"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
    assert "Cannot transition from terminal status 'Closed'" in resp.json()["detail"]


def test_transition_to_in_review_via_patch_status_instructs_submit_for_review(client, status_setup):
    finding = status_setup["finding"]
    token = status_setup["tokens"]["admin"]

    resp = client.patch(
        f"/api/findings/{finding.id}/status",
        json={"status": "In Review"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
    assert "submit-for-review" in resp.json()["detail"]


def test_transition_unknown_status_bad_request(client, status_setup):
    fid = status_setup["finding"].id
    token = status_setup["tokens"]["admin"]

    resp = client.patch(
        f"/api/findings/{fid}/status",
        json={"status": "NonExistentStatus"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
