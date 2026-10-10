import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.project import Project, ProjectMember
from backend.app.models.repository import Repository
from backend.app.models.user import User
from backend.app.models.finding import Finding
from backend.app.schemas.finding import FindingListResponse, FindingResponse
from backend.app.schemas.project import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)
from backend.app.schemas.repository import RepositoryCreate, RepositoryResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    User-only: Create project.
    Admins have view-only access (rejected with 403).
    The user creating the project is always the project lead (project_lead_id = created_by = current_user.id).
    The creator/lead is automatically enrolled into project_members.
    """
    if current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins have view-only access to projects; projects can only be created by users",
        )

    if not project_in.name or not project_in.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project name is required",
        )

    project_id = uuid.uuid4()
    new_project = Project(
        id=project_id,
        name=project_in.name.strip(),
        description=project_in.description.strip() if project_in.description else None,
        project_lead_id=current_user.id,
        created_by=current_user.id,
    )
    db.add(new_project)

    # 1. Automatically enroll creator/lead into project_members
    creator_membership = ProjectMember(
        project_id=project_id,
        user_id=current_user.id,
        added_by=current_user.id,
    )
    db.add(creator_membership)

    # 2. Enroll teammates from member_ids
    if project_in.member_ids:
        for mid in project_in.member_ids:
            if mid != current_user.id:
                # Check user exists
                teammate = db.query(User).filter(User.id == mid, User.is_active == True).first()
                if teammate:
                    teammate_membership = ProjectMember(
                        project_id=project_id,
                        user_id=mid,
                        added_by=current_user.id,
                    )
                    db.add(teammate_membership)

    db.commit()
    db.refresh(new_project)
    return ProjectResponse.model_validate(new_project)


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    search: Optional[str] = Query(None, description="Search by project name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List projects.
    Admins: View all active projects globally.
    Developers: View only active projects where they are enrolled as members.
    Soft-deleted projects are excluded.
    """
    query = db.query(Project).filter(Project.deleted_at.is_(None))

    if current_user.role != "admin":
        # Join project_members to filter projects accessible to developer
        query = query.join(ProjectMember, Project.id == ProjectMember.project_id).filter(
            ProjectMember.user_id == current_user.id
        )

    if search:
        query = query.filter(Project.name.ilike(f"%{search.strip()}%"))

    projects = query.order_by(Project.created_at.desc()).all()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get project detail.
    Admins can view any project.
    Developers must be members of the project.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role != "admin":
        is_member = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
            .first()
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update project info.
    Must be project member or admin.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role != "admin":
        is_member = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
            .first()
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to modify this project",
            )

    if project_in.name is not None:
        if not project_in.name.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project name cannot be empty")
        project.name = project_in.name.strip()

    if project_in.description is not None:
        project.description = project_in.description.strip()

    db.commit()
    db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Admin-only: Soft-delete project (sets deleted_at timestamp).
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete projects",
        )

    project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    project.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return None


@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
def list_project_members(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List members of a project.
    Accessible to admins and project members.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role != "admin":
        is_member = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
            .first()
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

    members = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.joined_at.asc())
        .all()
    )
    return [ProjectMemberResponse.model_validate(m) for m in members]


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: uuid.UUID,
    member_in: ProjectMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a team member to the project.
    Only the Project Lead is authorized to add members (403 Forbidden for non-leads and admins).
    """
    project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.project_lead_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Project Lead can add members",
        )

    # Validate target user exists and is active
    target_user = db.query(User).filter(User.id == member_in.user_id, User.is_active == True).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already a member
    existing_membership = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == member_in.user_id)
        .first()
    )
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project",
        )

    new_membership = ProjectMember(
        project_id=project_id,
        user_id=member_in.user_id,
        added_by=current_user.id,
    )
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    return ProjectMemberResponse.model_validate(new_membership)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a team member from the project.
    Only the Project Lead is authorized to remove members (403 Forbidden for non-leads and admins).
    The Project Lead cannot be removed (400 Bad Request).
    """
    project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.project_lead_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Project Lead can remove members",
        )

    if user_id == project.project_lead_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The Project Lead cannot be removed from project membership",
        )

    membership = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this project",
        )

    db.delete(membership)
    db.commit()
    return None


@router.get("/{project_id}/repositories", response_model=List[RepositoryResponse])
def list_project_repositories(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List repositories of a project.
    Accessible to admins and project members.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role != "admin":
        is_member = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
            .first()
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

    repos = (
        db.query(Repository)
        .filter(Repository.project_id == project_id)
        .order_by(Repository.created_at.asc())
        .all()
    )
    return [RepositoryResponse.model_validate(r) for r in repos]


@router.post("/{project_id}/repositories", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def register_project_repository(
    project_id: uuid.UUID,
    repo_in: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register a new repository record.
    Only the Project Lead is authorized to register repositories (403 Forbidden for non-leads and admins).
    Repository names must be unique within the same project (409 Conflict on duplicate).
    """
    if not repo_in.name or not repo_in.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository name is required",
        )

    project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project.project_lead_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Project Lead can register repositories",
        )

    clean_name = repo_in.name.strip()
    existing_repo = (
        db.query(Repository)
        .filter(Repository.project_id == project_id, Repository.name == clean_name)
        .first()
    )
    if existing_repo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository name already exists in this project",
        )

    new_repo = Repository(
        id=uuid.uuid4(),
        project_id=project_id,
        name=clean_name,
        repository_url=repo_in.repository_url.strip() if repo_in.repository_url else None,
        branch_name=repo_in.branch_name.strip() if repo_in.branch_name else None,
        technology=repo_in.technology.strip() if repo_in.technology else None,
        is_active=True,
    )
    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)
    return RepositoryResponse.model_validate(new_repo)


@router.get("/{project_id}/findings", response_model=FindingListResponse)
def list_project_findings(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List findings scoped to a project.
    - Accessible to admins and enrolled project members.
    - Non-members receive 403 Forbidden.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role != "admin":
        is_member = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
            .first()
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

    query = db.query(Finding).filter(Finding.project_id == project_id, Finding.deleted_at.is_(None))
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



