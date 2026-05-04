from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TempleBase(BaseModel):
    寺庙名称: str
    寺庙地址: Optional[str] = None
    联系电话: Optional[str] = None
    备注: Optional[str] = None

class TempleCreate(TempleBase):
    pass

class TempleUpdate(BaseModel):
    寺庙名称: Optional[str] = None
    寺庙地址: Optional[str] = None
    联系电话: Optional[str] = None
    备注: Optional[str] = None

class TempleResponse(TempleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
