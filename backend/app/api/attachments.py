import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.finding import Finding, FindingAttachment
from backend.app.models.project import ProjectMember
from backend.app.models.user import User

router = APIRouter(prefix="/api/attachments", tags=["attachments"])


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Secure authorized download of finding attachment (REQ-14):
    - Enforces project membership or admin role.
    - Prevents path traversal and unauthorized data leaks.
    """
    attachment = db.query(FindingAttachment).filter(FindingAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    finding = db.query(Finding).filter(Finding.id == attachment.finding_id, Finding.deleted_at.is_(None)).first()
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
                detail="Access denied to this attachment",
            )

    if not os.path.exists(attachment.storage_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file not found on server")

    return FileResponse(
        path=attachment.storage_key,
        media_type=attachment.media_type,
        filename=attachment.original_filename,
    )
