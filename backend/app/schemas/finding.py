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

