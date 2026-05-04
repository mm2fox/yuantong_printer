from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class PrinterTemplate(Base):
    __tablename__ = "printer_templates"

    id = Column(Integer, primary_key=True, index=True)
    模板名称 = Column(String(100), nullable=False)
    模板类型 = Column(String(50), nullable=False)
    牌位类型 = Column(String(50))
    布局配置 = Column(Text)
    默认参数 = Column(Text)
    是否启用 = Column(Integer, default=1)
    是否默认 = Column(Integer, default=0)
    备注 = Column(Text)
    temple_id = Column(Integer, ForeignKey("temples.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    temple = relationship("Temple", backref="printer_templates")
