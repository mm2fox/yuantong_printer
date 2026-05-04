from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FahuiRecordBase(BaseModel):
    fahui_user_id: Optional[int] = None
    fahui_id: Optional[int] = None
    fahui_name: Optional[str] = None
    座次: Optional[str] = None
    amount: float = 0
    paiwei_type: Optional[str] = None
    yanwang: int = 0
    xm1: Optional[str] = None
    xm2: Optional[str] = None
    xm3: Optional[str] = None
    xm4: Optional[str] = None
    xm5: Optional[str] = None
    xm6: Optional[str] = None
    xm7: Optional[str] = None
    xm8: Optional[str] = None
    xm9: Optional[str] = None
    xm10: Optional[str] = None
    xm: Optional[str] = None
    djdate: Optional[str] = None
    经办人: Optional[str] = None
    prt: int = 0
    remarks: Optional[str] = None

class FahuiRecordCreate(FahuiRecordBase):
    pass

class FahuiRecordUpdate(BaseModel):
    fahui_user_id: Optional[int] = None
    fahui_id: Optional[int] = None
    fahui_name: Optional[str] = None
    座次: Optional[str] = None
    amount: Optional[float] = None
    paiwei_type: Optional[str] = None
    yanwang: Optional[int] = None
    xm1: Optional[str] = None
    xm2: Optional[str] = None
    xm3: Optional[str] = None
    xm4: Optional[str] = None
    xm5: Optional[str] = None
    xm6: Optional[str] = None
    xm7: Optional[str] = None
    xm8: Optional[str] = None
    xm9: Optional[str] = None
    xm10: Optional[str] = None
    xm: Optional[str] = None
    djdate: Optional[str] = None
    经办人: Optional[str] = None
    prt: Optional[int] = None
    remarks: Optional[str] = None

class FahuiRecordResponse(FahuiRecordBase):
    id: int
    temple_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
