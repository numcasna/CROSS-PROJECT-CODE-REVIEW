import io
import uuid
from datetime import date, timedelta
import pytest
from backend.app.core.security import create_access_token, get_password_hash
from backend.app.models.user import User
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.finding import Finding, FindingAttachment


@pytest.fixture
def attachment_setup(db_session, tmp_path, monkeypatch):
    # Admin
    admin = User(
        id=uuid.uuid4(),
        name="Admin Attach",
        email="admin_att@test.com",
        password_hash=get_password_hash("pass123"),
        role="admin",
        is_active=True,
    )
    # Dev in project
    dev1 = User(
        id=uuid.uuid4(),
        name="Dev Attach",
        email="dev1_att@test.com",
        password_hash=get_password_hash("pass123"),
        role="developer",
        is_active=True,
    )
    # Outsider
    dev2 = User(
        id=uuid.uuid4(),
        name="Outsider Attach",
        email="dev2_att@test.com",
        password_hash=get_password_hash("pass123"),
        role="developer",
        is_active=True,
    )
    db_session.add_all([admin, dev1, dev2])
    db_session.commit()

    proj = Project(
        id=uuid.uuid4(),
        name="Project Attachments",
        project_lead_id=dev1.id,
        created_by=dev1.id,
    )
    db_session.add(proj)
    db_session.commit()

    db_session.add(ProjectMember(project_id=proj.id, user_id=dev1.id, added_by=dev1.id))
    db_session.commit()

    repo = Repository(
        id=uuid.uuid4(),
        project_id=proj.id,
        name="repo-att",
        branch_name="main",
        is_active=True,
    )
    db_session.add(repo)
    db_session.commit()

    finding = Finding(
        id=uuid.uuid4(),
        finding_code="CRF-2026-0401",
        title="Path Traversal in File Upload",
        description="Filename not sanitized before joining upload dir",
        project_id=proj.id,
        repository_id=repo.id,
        branch_name="main",
        severity="Critical",
        category="Security",
        status="Open",
        assignee_id=dev1.id,
        created_by=admin.id,
        due_date=date.today() + timedelta(days=2),
    )
    db_session.add(finding)
    db_session.commit()

    return {
        "admin": admin,
        "dev1": dev1,
        "dev2": dev2,
        "finding": finding,
        "tokens": {
            "admin": create_access_token(subject=str(admin.id)),
            "dev1": create_access_token(subject=str(dev1.id)),
            "dev2": create_access_token(subject=str(dev2.id)),
        },
    }


def test_upload_txt_attachment_by_project_member_success(client, attachment_setup, db_session):
    fid = attachment_setup["finding"].id
    token = attachment_setup["tokens"]["dev1"]

    file_content = b"PoC reproduction steps: run curl with --path-as-is"
    files = {"file": ("repro.txt", io.BytesIO(file_content), "text/plain")}
    data = {"attachment_kind": "supporting_evidence"}

    resp = client.post(
        f"/api/findings/{fid}/attachments",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    res = resp.json()
    assert res["original_filename"] == "repro.txt"
    assert res["media_type"] == "text/plain"
    assert res["size_bytes"] == len(file_content)
    assert res["attachment_kind"] == "supporting_evidence"
    assert res["uploaded_by"] == str(attachment_setup["dev1"].id)

    # Verify saved in DB
    att = db_session.query(FindingAttachment).filter(FindingAttachment.id == uuid.UUID(res["id"])).first()
    assert att is not None


def test_upload_pdf_attachment_by_admin_success(client, attachment_setup):
    fid = attachment_setup["finding"].id
    token = attachment_setup["tokens"]["admin"]

    file_content = b"%PDF-1.4 test pdf content"
    files = {"file": ("report.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {"attachment_kind": "resolution_proof"}

    resp = client.post(
        f"/api/findings/{fid}/attachments",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["original_filename"] == "report.pdf"


def test_upload_jpg_attachment_success(client, attachment_setup):
    fid = attachment_setup["finding"].id
    token = attachment_setup["tokens"]["dev1"]

    file_content = b"\xff\xd8\xff\xe0 fake jpeg bytes"
    files = {"file": ("screenshot.jpg", io.BytesIO(file_content), "image/jpeg")}

    resp = client.post(
        f"/api/findings/{fid}/attachments",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["original_filename"] == "screenshot.jpg"


def test_upload_disallowed_file_type_fails(client, attachment_setup):
    fid = attachment_setup["finding"].id
    token = attachment_setup["tokens"]["dev1"]

    files = {"file": ("exploit.exe", io.BytesIO(b"binary"), "application/octet-stream")}
    resp = client.post(
        f"/api/findings/{fid}/attachments",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "Only JPG, PDF, and TXT" in resp.json()["detail"]


def test_upload_by_outsider_forbidden(client, attachment_setup):
    fid = attachment_setup["finding"].id
    token = attachment_setup["tokens"]["dev2"]

    files = {"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")}
    resp = client.post(
        f"/api/findings/{fid}/attachments",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_list_attachments_for_finding(client, attachment_setup):
    fid = attachment_setup["finding"].id
    token = attachment_setup["tokens"]["dev1"]

    # Upload one
    client.post(
        f"/api/findings/{fid}/attachments",
        files={"file": ("notes.txt", io.BytesIO(b"some notes"), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = client.get(
        f"/api/findings/{fid}/attachments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    atts = resp.json()
    assert len(atts) >= 1
    assert atts[0]["original_filename"] == "notes.txt"


def test_download_attachment_authorized_success(client, attachment_setup):
    fid = attachment_setup["finding"].id
    token_dev = attachment_setup["tokens"]["dev1"]

    payload = b"Authorized secret proof content"
    upload_resp = client.post(
        f"/api/findings/{fid}/attachments",
        files={"file": ("proof.txt", io.BytesIO(payload), "text/plain")},
        headers={"Authorization": f"Bearer {token_dev}"},
    )
    assert upload_resp.status_code == 201
    att_id = upload_resp.json()["id"]

    # Download as dev1
    dl_resp = client.get(
        f"/api/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {token_dev}"},
    )
    assert dl_resp.status_code == 200
    assert dl_resp.content == payload


def test_download_attachment_by_outsider_forbidden(client, attachment_setup):
    fid = attachment_setup["finding"].id
    token_dev = attachment_setup["tokens"]["dev1"]
    token_outsider = attachment_setup["tokens"]["dev2"]

    upload_resp = client.post(
        f"/api/findings/{fid}/attachments",
        files={"file": ("proof.txt", io.BytesIO(b"secret"), "text/plain")},
        headers={"Authorization": f"Bearer {token_dev}"},
    )
    att_id = upload_resp.json()["id"]

    # Attempt download by outsider
    dl_resp = client.get(
        f"/api/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {token_outsider}"},
    )
    assert dl_resp.status_code == 403


def test_download_nonexistent_attachment_returns_404(client, attachment_setup):
    fake_id = uuid.uuid4()
    token = attachment_setup["tokens"]["dev1"]

    resp = client.get(
        f"/api/attachments/{fake_id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
