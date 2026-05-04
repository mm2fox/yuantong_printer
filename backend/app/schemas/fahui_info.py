from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FahuiInfoBase(BaseModel):
    法会名称: str
    开始日期: Optional[str] = None
    截止日期: Optional[str] = None
    功德金中: Optional[str] = None
    功德金小: Optional[str] = None
    功德金大: Optional[str] = None
    完成状态: Optional[str] = None
    备注: Optional[str] = None

class FahuiInfoCreate(FahuiInfoBase):
    pass

class FahuiInfoUpdate(BaseModel):
    法会名称: Optional[str] = None
    开始日期: Optional[str] = None
    截止日期: Optional[str] = None
    功德金中: Optional[str] = None
    功德金小: Optional[str] = None
    功德金大: Optional[str] = None
    完成状态: Optional[str] = None
    备注: Optional[str] = None

class FahuiInfoResponse(FahuiInfoBase):
    id: int
    temple_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
