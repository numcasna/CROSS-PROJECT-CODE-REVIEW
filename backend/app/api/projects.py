import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.project import Project, ProjectMember
from backend.app.models.user import User
from backend.app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

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
