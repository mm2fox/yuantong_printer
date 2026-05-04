from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class FahuiUser(Base):
    __tablename__ = "fahui_users"

    id = Column(Integer, primary_key=True, index=True)
    施主编号 = Column(String(50), nullable=False)
    施主姓名 = Column(String(50), nullable=False)
    电话 = Column(String(20))
    地址 = Column(String(200))
    功德主 = Column(Integer, default=1)
    佛光接引一 = Column(String(50))
    佛光接引二 = Column(String(50))
    佛光接引三 = Column(String(50))
    佛光接引四 = Column(String(50))
    阳上一 = Column(String(50))
    阳上二 = Column(String(50))
    阳上三 = Column(String(50))
    阳上四 = Column(String(50))
    阳上五 = Column(String(50))
    阳上六 = Column(String(50))
    佛光注照一 = Column(String(50))
    佛光注照二 = Column(String(50))
    佛光注照三 = Column(String(50))
    佛光注照四 = Column(String(50))
    登记人 = Column(String(50))
    登记时间 = Column(String(50))
    备注 = Column(Text)
    temple_id = Column(Integer, ForeignKey("temples.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    temple = relationship("Temple", backref="fahui_users")
    records = relationship("FahuiRecord", back_populates="fahui_user")
