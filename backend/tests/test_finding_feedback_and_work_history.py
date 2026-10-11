import uuid
from datetime import date, timedelta
import pytest
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.finding import Finding, FindingFeedback, FindingWorkHistory


@pytest.fixture
def feedback_setup(db_session):
    admin = User(
        id=uuid.uuid4(),
        name="Admin Reviewer",
        email="admin_fb@test.com",
        password_hash=get_password_hash("pass123"),
        role="admin",
        is_active=True,
    )
    dev1 = User(
        id=uuid.uuid4(),
        name="Assignee Dev",
        email="dev1_fb@test.com",
        password_hash=get_password_hash("pass123"),
        role="developer",
        is_active=True,
    )
    dev2 = User(
        id=uuid.uuid4(),
        name="Peer Dev",
        email="dev2_fb@test.com",
        password_hash=get_password_hash("pass123"),
        role="developer",
        is_active=True,
    )
    dev3 = User(
        id=uuid.uuid4(),
        name="Outsider Dev",
        email="dev3_fb@test.com",
        password_hash=get_password_hash("pass123"),
        role="developer",
        is_active=True,
    )
    db_session.add_all([admin, dev1, dev2, dev3])
    db_session.commit()

    proj = Project(
        id=uuid.uuid4(),
        name="Project Feedback Test",
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
        name="repo-fb",
        branch_name="main",
        is_active=True,
    )
    db_session.add(repo)
    db_session.commit()

    finding = Finding(
        id=uuid.uuid4(),
        finding_code="CRF-2026-0301",
        title="Unvalidated Redirect",
        description="Redirect URL not checked against domain whitelist",
        project_id=proj.id,
        repository_id=repo.id,
        branch_name="main",
        severity="Medium",
        category="Security",
        status="Open",
        assignee_id=dev1.id,
        created_by=admin.id,
        due_date=date.today() + timedelta(days=3),
    )
    db_session.add(finding)
    db_session.commit()

    return {
        "admin": admin,
        "dev1": dev1,
        "dev2": dev2,
        "dev3": dev3,
        "finding": finding,
        "tokens": {
            "admin": create_access_token(subject=str(admin.id)),
            "dev1": create_access_token(subject=str(dev1.id)),
            "dev2": create_access_token(subject=str(dev2.id)),
            "dev3": create_access_token(subject=str(dev3.id)),
        },
    }


def test_post_feedback_by_project_member_success(client, feedback_setup, db_session):
    fid = feedback_setup["finding"].id
    token = feedback_setup["tokens"]["dev2"]  # peer member in project

    resp = client.post(
        f"/api/findings/{fid}/feedback",
        json={"body": "Consider using urllib.parse.urlparse to validate netloc."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["body"] == "Consider using urllib.parse.urlparse to validate netloc."
    assert data["author_id"] == str(feedback_setup["dev2"].id)
    assert data["finding_id"] == str(fid)
    assert data["parent_feedback_id"] is None


def test_post_feedback_reply_with_parent_id(client, feedback_setup, db_session):
    fid = feedback_setup["finding"].id
    token_admin = feedback_setup["tokens"]["admin"]
    token_dev = feedback_setup["tokens"]["dev1"]

    # 1. Root comment
    root_resp = client.post(
        f"/api/findings/{fid}/feedback",
        json={"body": "Please address this before Tuesday."},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert root_resp.status_code == 201
    root_id = root_resp.json()["id"]

    # 2. Reply to root comment
    reply_resp = client.post(
        f"/api/findings/{fid}/feedback",
        json={"body": "Working on it today.", "parent_feedback_id": root_id},
        headers={"Authorization": f"Bearer {token_dev}"},
    )
    assert reply_resp.status_code == 201
    assert reply_resp.json()["parent_feedback_id"] == root_id


def test_post_feedback_by_outsider_forbidden(client, feedback_setup):
    fid = feedback_setup["finding"].id
    token = feedback_setup["tokens"]["dev3"]

    resp = client.post(
        f"/api/findings/{fid}/feedback",
        json={"body": "Outsider comment"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_post_feedback_empty_body_bad_request(client, feedback_setup):
    fid = feedback_setup["finding"].id
    token = feedback_setup["tokens"]["dev1"]

    resp = client.post(
        f"/api/findings/{fid}/feedback",
        json={"body": "   "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_get_feedback_list_chronological(client, feedback_setup):
    fid = feedback_setup["finding"].id
    token_admin = feedback_setup["tokens"]["admin"]
    token_dev = feedback_setup["tokens"]["dev1"]

    client.post(
        f"/api/findings/{fid}/feedback",
        json={"body": "First comment"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    client.post(
        f"/api/findings/{fid}/feedback",
        json={"body": "Second comment"},
        headers={"Authorization": f"Bearer {token_dev}"},
    )

    get_resp = client.get(
        f"/api/findings/{fid}/feedback",
        headers={"Authorization": f"Bearer {token_dev}"},
    )
    assert get_resp.status_code == 200
    feedbacks = get_resp.json()
    assert len(feedbacks) >= 2
    assert feedbacks[0]["body"] == "First comment"
    assert feedbacks[1]["body"] == "Second comment"


def test_post_work_history_by_assignee_success(client, feedback_setup, db_session):
    fid = feedback_setup["finding"].id
    token = feedback_setup["tokens"]["dev1"]

    resp = client.post(
        f"/api/findings/{fid}/work-history",
        json={"body": "Implemented URL parsing whitelist in middleware."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["body"] == "Implemented URL parsing whitelist in middleware."
    assert data["author_id"] == str(feedback_setup["dev1"].id)
    assert data["entry_type"] == "progress_update"


def test_post_work_history_by_admin_success(client, feedback_setup):
    fid = feedback_setup["finding"].id
    token = feedback_setup["tokens"]["admin"]

    resp = client.post(
        f"/api/findings/{fid}/work-history",
        json={"body": "Admin verified patch builds on staging.", "entry_type": "admin_update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["entry_type"] == "admin_update"


def test_post_work_history_by_peer_member_forbidden(client, feedback_setup):
    fid = feedback_setup["finding"].id
    token = feedback_setup["tokens"]["dev2"]  # peer, not assignee

    resp = client.post(
        f"/api/findings/{fid}/work-history",
        json={"body": "Peer posting work update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_get_work_history_list_chronological(client, feedback_setup):
    fid = feedback_setup["finding"].id
    token = feedback_setup["tokens"]["dev1"]

    client.post(
        f"/api/findings/{fid}/work-history",
        json={"body": "Work step 1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        f"/api/findings/{fid}/work-history",
        json={"body": "Work step 2"},
        headers={"Authorization": f"Bearer {token}"},
    )

    get_resp = client.get(
        f"/api/findings/{fid}/work-history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    entries = get_resp.json()
    assert len(entries) >= 2
    assert entries[0]["body"] == "Work step 1"
    assert entries[1]["body"] == "Work step 2"
