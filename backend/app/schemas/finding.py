import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class FindingCreate(BaseModel):
    title: str
    description: str
    project_id: uuid.UUID
    repository_id: uuid.UUID
    branch_name: Optional[str] = None
    severity: str
    category: str
    assignee_id: uuid.UUID
    due_date: date

class FindingSubmitForReview(BaseModel):
    resolution_description: str

class FindingStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None

class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finding_code: str
    title: str
    description: str
    project_id: uuid.UUID
    repository_id: uuid.UUID
    branch_name: Optional[str] = None
    severity: str
    category: str
    status: str
    assignee_id: uuid.UUID
    reviewer_id: Optional[uuid.UUID] = None
    created_by: uuid.UUID
    due_date: date
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

class FindingListResponse(BaseModel):
    items: list[FindingResponse]
    total: int
    page: int
    page_size: int
    pages: int


class FindingFeedbackCreate(BaseModel):
    body: str
    parent_feedback_id: Optional[uuid.UUID] = None


class FindingFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finding_id: uuid.UUID
    author_id: uuid.UUID
    parent_feedback_id: Optional[uuid.UUID] = None
    body: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class FindingWorkHistoryCreate(BaseModel):
    body: str
    entry_type: Optional[str] = "progress_update"


class FindingWorkHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finding_id: uuid.UUID
    author_id: uuid.UUID
    entry_type: str
    body: str
    created_at: datetime


class FindingAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finding_id: uuid.UUID
    uploaded_by: uuid.UUID
    original_filename: str
    media_type: str
    size_bytes: int
    attachment_kind: str
    created_at: datetime


