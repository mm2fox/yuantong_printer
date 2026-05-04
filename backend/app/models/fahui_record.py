from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class FahuiRecord(Base):
    __tablename__ = "fahui_records"

    id = Column(Integer, primary_key=True, index=True)
    fahui_user_id = Column(Integer, ForeignKey("fahui_users.id", ondelete="SET NULL"), nullable=True)
    fahui_id = Column(Integer, nullable=True)
    fahui_name = Column(String(100))
    座次 = Column(String(50))
    amount = Column(Float, default=0)
    paiwei_type = Column(String(20))
    yanwang = Column(Integer, default=0)
    xm1 = Column(String(50))
    xm2 = Column(String(50))
    xm3 = Column(String(50))
    xm4 = Column(String(50))
    xm5 = Column(String(50))
    xm6 = Column(String(50))
    xm7 = Column(String(50))
    xm8 = Column(String(50))
    xm9 = Column(String(50))
    xm10 = Column(String(50))
    xm = Column(String(50))
    djdate = Column(String(50))
    经办人 = Column(String(50))
    prt = Column(Integer, default=0)
    remarks = Column(Text)
    施主姓名 = Column(String(50))
    施主编号 = Column(String(50))
    temple_id = Column(Integer, ForeignKey("temples.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    fahui_user = relationship("FahuiUser", back_populates="records")
    temple = relationship("Temple", backref="fahui_records")
