import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.finding import Finding, FindingStatusHistory, YearlyFindingCounter
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.user import User
from backend.app.schemas.finding import FindingCreate, FindingListResponse, FindingResponse

router = APIRouter(prefix="/api/findings", tags=["findings"])

ALLOWED_SEVERITIES = {"critical", "high", "medium", "low", "informational"}


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

