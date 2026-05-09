from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from ..core.database import Base

class VersionInfo(Base):
    __tablename__ = "version_info"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50))
    git_commit = Column(String(100))
    git_branch = Column(String(100))
    git_author = Column(String(100))
    git_message = Column(Text)
    git_date = Column(String(100))
    build_time = Column(DateTime, default=datetime.utcnow)
    change_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
