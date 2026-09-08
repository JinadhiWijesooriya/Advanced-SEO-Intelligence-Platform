from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    crawl_job_id = Column(Integer, ForeignKey("crawl_jobs.id", ondelete="SET NULL"), nullable=True)
    
    format = Column(String, index=True, nullable=False)  # pdf, csv, json
    file_path = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, completed, failed
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="reports")
