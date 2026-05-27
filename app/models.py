from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    status = Column(String, default="pending") # pending, applied, failed
    applied_at = Column(DateTime, default=datetime.utcnow)
    cover_letter = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)

class Config(Base):
    __tablename__ = "config"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
