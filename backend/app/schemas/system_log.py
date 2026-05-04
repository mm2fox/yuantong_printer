from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SystemLogBase(BaseModel):
    用户名: Optional[str] = None
    操作类型: Optional[str] = None
    操作内容: Optional[str] = None

class SystemLogCreate(SystemLogBase):
    pass

class SystemLogResponse(SystemLogBase):
    id: int
    temple_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SystemLogDelete(BaseModel):
    start_date: str
    end_date: str
    用户名: Optional[str] = None
    操作类型: Optional[str] = None
