from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FahuiUserBase(BaseModel):
    施主编号: str
    施主姓名: str
    电话: Optional[str] = None
    地址: Optional[str] = None
    功德主: int = 1
    佛光接引一: Optional[str] = None
    佛光接引二: Optional[str] = None
    佛光接引三: Optional[str] = None
    佛光接引四: Optional[str] = None
    阳上一: Optional[str] = None
    阳上二: Optional[str] = None
    阳上三: Optional[str] = None
    阳上四: Optional[str] = None
    阳上五: Optional[str] = None
    阳上六: Optional[str] = None
    佛光注照一: Optional[str] = None
    佛光注照二: Optional[str] = None
    佛光注照三: Optional[str] = None
    佛光注照四: Optional[str] = None
    登记人: Optional[str] = None
    登记时间: Optional[str] = None
    备注: Optional[str] = None

class FahuiUserCreate(FahuiUserBase):
    pass

class FahuiUserUpdate(BaseModel):
    施主编号: Optional[str] = None
    施主姓名: Optional[str] = None
    电话: Optional[str] = None
    地址: Optional[str] = None
    功德主: Optional[int] = None
    佛光接引一: Optional[str] = None
    佛光接引二: Optional[str] = None
    佛光接引三: Optional[str] = None
    佛光接引四: Optional[str] = None
    阳上一: Optional[str] = None
    阳上二: Optional[str] = None
    阳上三: Optional[str] = None
    阳上四: Optional[str] = None
    阳上五: Optional[str] = None
    阳上六: Optional[str] = None
    佛光注照一: Optional[str] = None
    佛光注照二: Optional[str] = None
    佛光注照三: Optional[str] = None
    佛光注照四: Optional[str] = None
    登记人: Optional[str] = None
    登记时间: Optional[str] = None
    备注: Optional[str] = None

class FahuiUserResponse(FahuiUserBase):
    id: int
    temple_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
