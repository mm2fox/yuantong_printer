from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PrinterTemplateBase(BaseModel):
    模板名称: str
    模板类型: str
    牌位类型: Optional[str] = None
    布局配置: Optional[str] = None
    默认参数: Optional[str] = None
    是否启用: int = 1
    是否默认: int = 0
    备注: Optional[str] = None

class PrinterTemplateCreate(PrinterTemplateBase):
    pass

class PrinterTemplateUpdate(BaseModel):
    模板名称: Optional[str] = None
    模板类型: Optional[str] = None
    牌位类型: Optional[str] = None
    布局配置: Optional[str] = None
    默认参数: Optional[str] = None
    是否启用: Optional[int] = None
    备注: Optional[str] = None

class PrinterTemplateResponse(PrinterTemplateBase):
    id: int
    temple_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
