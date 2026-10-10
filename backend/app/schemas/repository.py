import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class RepositoryCreate(BaseModel):
    name: str
    repository_url: Optional[str] = None
    branch_name: Optional[str] = None
    technology: Optional[str] = None

class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    repository_url: Optional[str] = None
    branch_name: Optional[str] = None
    technology: Optional[str] = None
    is_active: bool
    created_at: datetime
