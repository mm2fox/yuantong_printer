from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    用户名 = Column(String(50))
    操作类型 = Column(String(50))
    操作内容 = Column(Text)
    temple_id = Column(Integer, ForeignKey("temples.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    temple = relationship("Temple", backref="system_logs")
