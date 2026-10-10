import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.finding import Finding, FindingStatusHistory, YearlyFindingCounter
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.user import User
from backend.app.schemas.finding import FindingCreate, FindingResponse

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
