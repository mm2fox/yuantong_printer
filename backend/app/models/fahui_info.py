from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class FahuiInfo(Base):
    __tablename__ = "fahui_info"

    id = Column(Integer, primary_key=True, index=True)
    法会名称 = Column(String(100), nullable=False)
    开始日期 = Column(String(50))
    截止日期 = Column(String(50))
    功德金中 = Column(String(50))
    功德金小 = Column(String(50))
    功德金大 = Column(String(50))
    完成状态 = Column(String(20))
    备注 = Column(Text)
    temple_id = Column(Integer, ForeignKey("temples.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    temple = relationship("Temple", backref="fahui_infos")
