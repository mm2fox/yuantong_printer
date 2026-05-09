from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class VersionInfoBase(BaseModel):
    version: Optional[str] = None
    git_commit: Optional[str] = None
    git_branch: Optional[str] = None
    git_author: Optional[str] = None
    git_message: Optional[str] = None
    git_date: Optional[str] = None
    change_summary: Optional[str] = None

class VersionInfoCreate(VersionInfoBase):
    pass

class VersionInfoResponse(VersionInfoBase):
    id: int
    build_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
