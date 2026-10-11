import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.config import settings
from backend.app.models.finding import (
    Finding,
    FindingAttachment,
    FindingFeedback,
    FindingStatusHistory,
    FindingWorkHistory,
    YearlyFindingCounter,
)
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.user import User
from backend.app.schemas.finding import (
    FindingAttachmentResponse,
    FindingCreate,
    FindingFeedbackCreate,
    FindingFeedbackResponse,
    FindingListResponse,
    FindingResponse,
    FindingStatusUpdate,
    FindingSubmitForReview,
    FindingWorkHistoryCreate,
    FindingWorkHistoryResponse,
)

router = APIRouter(prefix="/api/findings", tags=["findings"])

ALLOWED_SEVERITIES = {"critical", "high", "medium", "low", "informational"}
ALLOWED_SUBMISSION_STATUSES = {"Open", "In Progress", "Reopened"}
ALLOWED_ATTACHMENT_EXTENSIONS = {".jpg", ".jpeg", ".pdf", ".txt"}
ALLOWED_ATTACHMENT_KINDS = {"resolution_proof", "supporting_evidence"}
VALID_STATUS_MAP = {
    "open": "Open",
    "in progress": "In Progress",
    "in review": "In Review",
    "resolved": "Resolved",
    "reopened": "Reopened",
    "rejected": "Rejected",
    "closed": "Closed",
}


@router.post("", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
def create_finding(
    finding_in: FindingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Admin-only: Create a code review finding.
    - Generates sequential finding_code CRF-YYYY-XXXX via yearly_finding_counters table.
    - Requires title, description, category, project_id, repository_id, severity, due_date, assignee_id.
    - assignee_id must be an active enrolled member of project_members for the project.
    - branch_name inherits repository branch_name if omitted.
    - Sets initial status to 'Open' and logs initial FindingStatusHistory entry.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create findings",
        )

    # 1. Validate title & description
    if not finding_in.title or not finding_in.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title is required",
        )
    if not finding_in.description or not finding_in.description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description is required",
        )

    # 2. Validate severity
    clean_severity = finding_in.severity.strip().lower()
    if clean_severity not in ALLOWED_SEVERITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid severity level. Must be one of: {', '.join(sorted(ALLOWED_SEVERITIES))}",
        )
    normalized_severity = clean_severity.capitalize()

    # 3. Validate category
    if not finding_in.category or not finding_in.category.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category is required",
        )

    # 4. Validate project exists and is not soft-deleted
    project = (
        db.query(Project)
        .filter(Project.id == finding_in.project_id, Project.deleted_at.is_(None))
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # 5. Validate repository exists and belongs to the project
    repo = (
        db.query(Repository)
        .filter(Repository.id == finding_in.repository_id)
        .first()
    )
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
    if repo.project_id != finding_in.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository does not belong to the selected project",
        )

    # 6. Validate assignee user exists and is enrolled in project_members
    assignee = (
        db.query(User)
        .filter(User.id == finding_in.assignee_id, User.is_active == True)
        .first()
    )
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee user not found",
        )

    is_member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == finding_in.project_id,
            ProjectMember.user_id == finding_in.assignee_id,
        )
        .first()
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be an active member of the project",
        )

    # 7. Branch fallback logic
    if finding_in.branch_name and finding_in.branch_name.strip():
        branch = finding_in.branch_name.strip()
    else:
        branch = repo.branch_name.strip() if repo.branch_name and repo.branch_name.strip() else None

    # 8. Sequential code generation (CRF-YYYY-XXXX) using yearly_finding_counters row lock
    current_year = datetime.now(timezone.utc).year
    counter = (
        db.query(YearlyFindingCounter)
        .filter(YearlyFindingCounter.year == current_year)
        .with_for_update()
        .first()
    )
    if not counter:
        counter = YearlyFindingCounter(year=current_year, last_seq=1)
        db.add(counter)
        seq = 1
    else:
        counter.last_seq += 1
        seq = counter.last_seq

    finding_code = f"CRF-{current_year}-{seq:04d}"

    # 9. Create Finding record
    finding_id = uuid.uuid4()
    new_finding = Finding(
        id=finding_id,
        finding_code=finding_code,
        title=finding_in.title.strip(),
        description=finding_in.description.strip(),
        project_id=finding_in.project_id,
        repository_id=finding_in.repository_id,
        branch_name=branch,
        severity=normalized_severity,
        category=finding_in.category.strip(),
        status="Open",
        assignee_id=finding_in.assignee_id,
        created_by=current_user.id,
        due_date=finding_in.due_date,
    )
    db.add(new_finding)

    # 10. Audit history entry
    status_history = FindingStatusHistory(
        id=uuid.uuid4(),
        finding_id=finding_id,
        old_status=None,
        new_status="Open",
        changed_by=current_user.id,
        reason="Initial finding creation",
    )
    db.add(status_history)

    db.commit()
    db.refresh(new_finding)
    return FindingResponse.model_validate(new_finding)


@router.get("", response_model=FindingListResponse)
def list_findings(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    project_id: Optional[uuid.UUID] = Query(None, description="Filter by project ID"),
    repository_id: Optional[uuid.UUID] = Query(None, description="Filter by repository ID"),
    status: Optional[str] = Query(None, description="Filter by finding status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(None, description="Filter by category"),
    assignee_id: Optional[uuid.UUID] = Query(None, description="Filter by assignee user ID"),
    search: Optional[str] = Query(None, description="Keyword search in title, description, finding_code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List findings.
    - Admins see all findings globally.
    - Developers see findings only in projects they are enrolled in.
    - Excludes soft-deleted findings.
    - Returns paginated envelope.
    """
    query = db.query(Finding).filter(Finding.deleted_at.is_(None))

    if current_user.role != "admin":
        query = query.join(
            ProjectMember,
            Finding.project_id == ProjectMember.project_id,
        ).filter(ProjectMember.user_id == current_user.id)

    if project_id:
        query = query.filter(Finding.project_id == project_id)
    if repository_id:
        query = query.filter(Finding.repository_id == repository_id)
    if status:
        query = query.filter(Finding.status.ilike(status.strip()))
    if severity:
        query = query.filter(Finding.severity.ilike(severity.strip()))
    if category:
        query = query.filter(Finding.category.ilike(category.strip()))
    if assignee_id:
        query = query.filter(Finding.assignee_id == assignee_id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (Finding.title.ilike(term))
            | (Finding.description.ilike(term))
            | (Finding.finding_code.ilike(term))
        )

    total = query.count()
    pages = (total + page_size - 1) // page_size if total > 0 else 0
    items = (
        query.order_by(Finding.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return FindingListResponse(
        items=[FindingResponse.model_validate(f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{finding_id}", response_model=FindingResponse)
def get_finding(
    finding_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed finding by ID.
    - Accessible to admins and enrolled members of the project.
    - Non-members receive 403 Forbidden.
    - Excludes soft-deleted findings (404 Not Found).
    """
    finding = db.query(Finding).filter(Finding.id == finding_id, Finding.deleted_at.is_(None)).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    if current_user.role != "admin":
        is_member = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == finding.project_id,
                ProjectMember.user_id == current_user.id,
            )
            .first()
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this finding",
            )

    return FindingResponse.model_validate(finding)
 
 
@router.post("/{finding_id}/submit-for-review", response_model=FindingResponse)
def submit_finding_for_review(
    finding_id: uuid.UUID,
    submission_in: FindingSubmitForReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit work for review (REQ-10):
    - Caller must be the assigned developer or an admin.
    - resolution_description is mandatory and non-empty.
    - Allowed prior statuses: Open, In Progress, Reopened.
    - Transitions finding to 'In Review'.
    - Appends FindingWorkHistory (type: submission) and FindingStatusHistory records.
    """
    if not submission_in.resolution_description or not submission_in.resolution_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resolution description is required",
        )

    finding = (
        db.query(Finding)
        .filter(Finding.id == finding_id, Finding.deleted_at.is_(None))
        .first()
    )
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )

    if current_user.role != "admin" and finding.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned developer or an administrator can submit this finding for review",
        )

    if finding.status not in ALLOWED_SUBMISSION_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot submit for review from status '{finding.status}'",
        )

    old_status = finding.status
    resolution_text = submission_in.resolution_description.strip()
    finding.status = "In Review"

    # 1. Work history entry
    work_entry = FindingWorkHistory(
        id=uuid.uuid4(),
        finding_id=finding.id,
        author_id=current_user.id,
        entry_type="submission",
        body=resolution_text,
    )
    db.add(work_entry)

    # 2. Status history entry
    status_entry = FindingStatusHistory(
        id=uuid.uuid4(),
        finding_id=finding.id,
        old_status=old_status,
        new_status="In Review",
        changed_by=current_user.id,
        reason=resolution_text,
    )
    db.add(status_entry)

    db.commit()
    db.refresh(finding)
    return FindingResponse.model_validate(finding)


@router.patch("/{finding_id}/status", response_model=FindingResponse)
def update_finding_status(
    finding_id: uuid.UUID,
    status_in: FindingStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update finding status according to state machine transitions (REQ-11):
    - 'Open' -> 'In Progress': Assignee or Admin.
    - 'In Review' -> 'Resolved': Admin only.
    - 'In Review' -> 'Reopened': Admin only (mandatory reason).
    - Non-terminal -> 'Rejected': Admin only (mandatory reason).
    - 'Resolved' -> 'Closed': Admin only.
    - Transition to 'In Review' must use POST /api/findings/{id}/submit-for-review.
    - Terminal states ('Closed', 'Rejected') cannot transition.
    """
    raw_status = (status_in.status or "").strip().lower()
    if raw_status not in VALID_STATUS_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUS_MAP.values())}",
        )
    target_status = VALID_STATUS_MAP[raw_status]

    if target_status == "In Review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Status 'In Review' must be transitioned via POST /api/findings/{id}/submit-for-review",
        )

    finding = (
        db.query(Finding)
        .filter(Finding.id == finding_id, Finding.deleted_at.is_(None))
        .first()
    )
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )

    current_status = finding.status

    # Terminal state check
    if current_status in {"Closed", "Rejected"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition from terminal status '{current_status}'",
        )

    clean_reason = status_in.reason.strip() if status_in.reason and status_in.reason.strip() else None

    # Transition validation logic
    if target_status == "In Progress":
        if current_status != "Open":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot transition to 'In Progress' from '{current_status}'",
            )
        if current_user.role != "admin" and finding.assignee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned developer or an administrator can move a finding to 'In Progress'",
            )

    elif target_status == "Resolved":
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can resolve findings",
            )
        if current_status != "In Review":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot resolve finding from status '{current_status}'. Work must be 'In Review'",
            )

    elif target_status == "Reopened":
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can reopen findings",
            )
        if current_status != "In Review":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot reopen finding from status '{current_status}'. Only 'In Review' findings can be reopened",
            )
        if not clean_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reason is mandatory when reopening a finding",
            )

    elif target_status == "Rejected":
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can reject findings",
            )
        if not clean_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reason is mandatory when rejecting a finding",
            )

    elif target_status == "Closed":
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can close findings",
            )
        if current_status != "Resolved":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot close finding from status '{current_status}'. Only 'Resolved' findings can be closed",
            )

    # Perform atomic update
    old_status = finding.status
    finding.status = target_status

    status_entry = FindingStatusHistory(
        id=uuid.uuid4(),
        finding_id=finding.id,
        old_status=old_status,
        new_status=target_status,
        changed_by=current_user.id,
        reason=clean_reason,
    )
    db.add(status_entry)

    db.commit()
    db.refresh(finding)
    return FindingResponse.model_validate(finding)


def _check_finding_access_or_admin(finding: Finding, current_user: User, db: Session):
    if current_user.role == "admin":
        return
    is_member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == finding.project_id,
            ProjectMember.user_id == current_user.id,
        )
        .first()
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this finding",
        )


@router.post("/{finding_id}/feedback", response_model=FindingFeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    finding_id: uuid.UUID,
    feedback_in: FindingFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create threaded feedback (REQ-12):
    - Accessible to enrolled project members and administrators.
    - Optional parent_feedback_id for replies.
    """
    if not feedback_in.body or not feedback_in.body.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback body is required",
        )

    finding = db.query(Finding).filter(Finding.id == finding_id, Finding.deleted_at.is_(None)).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    _check_finding_access_or_admin(finding, current_user, db)

    if feedback_in.parent_feedback_id:
        parent = (
            db.query(FindingFeedback)
            .filter(
                FindingFeedback.id == feedback_in.parent_feedback_id,
                FindingFeedback.finding_id == finding.id,
            )
            .first()
        )
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent feedback not found on this finding",
            )

    new_feedback = FindingFeedback(
        id=uuid.uuid4(),
        finding_id=finding.id,
        author_id=current_user.id,
        parent_feedback_id=feedback_in.parent_feedback_id,
        body=feedback_in.body.strip(),
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return FindingFeedbackResponse.model_validate(new_feedback)


@router.get("/{finding_id}/feedback", response_model=List[FindingFeedbackResponse])
def list_feedback(
    finding_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get chronological feedback list (REQ-12).
    """
    finding = db.query(Finding).filter(Finding.id == finding_id, Finding.deleted_at.is_(None)).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    _check_finding_access_or_admin(finding, current_user, db)

    items = (
        db.query(FindingFeedback)
        .filter(FindingFeedback.finding_id == finding.id)
        .order_by(FindingFeedback.created_at.asc())
        .all()
    )
    return [FindingFeedbackResponse.model_validate(f) for f in items]


@router.post("/{finding_id}/work-history", response_model=FindingWorkHistoryResponse, status_code=status.HTTP_201_CREATED)
def create_work_history(
    finding_id: uuid.UUID,
    work_in: FindingWorkHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Append work history entry (REQ-12):
    - Strictly authorized to the assigned developer or an administrator.
    - Append-only progress log.
    """
    if not work_in.body or not work_in.body.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Work history body is required",
        )

    finding = db.query(Finding).filter(Finding.id == finding_id, Finding.deleted_at.is_(None)).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    if current_user.role != "admin" and finding.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned developer or an administrator can add work history updates",
        )

    entry_type = (
        work_in.entry_type.strip()
        if work_in.entry_type and work_in.entry_type.strip()
        else ("admin_update" if current_user.role == "admin" else "progress_update")
    )

    new_work = FindingWorkHistory(
        id=uuid.uuid4(),
        finding_id=finding.id,
        author_id=current_user.id,
        entry_type=entry_type,
        body=work_in.body.strip(),
    )
    db.add(new_work)
    db.commit()
    db.refresh(new_work)
    return FindingWorkHistoryResponse.model_validate(new_work)


@router.get("/{finding_id}/work-history", response_model=List[FindingWorkHistoryResponse])
def list_work_history(
    finding_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get chronological work history entries (REQ-12).
    """
    finding = db.query(Finding).filter(Finding.id == finding_id, Finding.deleted_at.is_(None)).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    _check_finding_access_or_admin(finding, current_user, db)

    items = (
        db.query(FindingWorkHistory)
        .filter(FindingWorkHistory.finding_id == finding.id)
        .order_by(FindingWorkHistory.created_at.asc())
        .all()
    )
    return [FindingWorkHistoryResponse.model_validate(w) for w in items]


@router.post("/{finding_id}/attachments", response_model=FindingAttachmentResponse, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    finding_id: uuid.UUID,
    file: UploadFile = File(...),
    attachment_kind: str = Form("supporting_evidence"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload file attachment for a finding (REQ-13):
    - JPG, PDF, TXT up to 10 MB.
    - Stored in backend-managed uploads/ folder.
    - Requires project membership or admin role.
    """
    finding = db.query(Finding).filter(Finding.id == finding_id, Finding.deleted_at.is_(None)).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    _check_finding_access_or_admin(finding, current_user, db)

    orig_filename = file.filename or "attachment"
    _, ext = os.path.splitext(orig_filename.lower())
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PDF, and TXT files are allowed",
        )

    kind = attachment_kind.strip().lower() if attachment_kind else "supporting_evidence"
    if kind not in ALLOWED_ATTACHMENT_KINDS:
        kind = "supporting_evidence"

    content = file.file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds maximum allowed size of 10 MB",
        )

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    att_id = uuid.uuid4()
    storage_filename = f"{att_id}{ext}"
    storage_path = os.path.join(upload_dir, storage_filename)
    with open(storage_path, "wb") as f:
        f.write(content)

    media_type = file.content_type
    if not media_type or media_type == "application/octet-stream":
        if ext in {".jpg", ".jpeg"}:
            media_type = "image/jpeg"
        elif ext == ".pdf":
            media_type = "application/pdf"
        elif ext == ".txt":
            media_type = "text/plain"

    attachment = FindingAttachment(
        id=att_id,
        finding_id=finding.id,
        uploaded_by=current_user.id,
        original_filename=orig_filename,
        storage_key=storage_path,
        media_type=media_type,
        size_bytes=len(content),
        attachment_kind=kind,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return FindingAttachmentResponse.model_validate(attachment)


@router.get("/{finding_id}/attachments", response_model=List[FindingAttachmentResponse])
def list_attachments(
    finding_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List attachments for a finding (REQ-13).
    """
    finding = db.query(Finding).filter(Finding.id == finding_id, Finding.deleted_at.is_(None)).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    _check_finding_access_or_admin(finding, current_user, db)

    items = (
        db.query(FindingAttachment)
        .filter(FindingAttachment.finding_id == finding.id)
        .order_by(FindingAttachment.created_at.asc())
        .all()
    )
    return [FindingAttachmentResponse.model_validate(a) for a in items]




