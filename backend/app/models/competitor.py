from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    domain: str = Column(String(255), nullable=False)
    target_url: str = Column(String(1024), nullable=False)
    
    latest_score = Column(Float, nullable=True)
    latest_page_count = Column(Integer, nullable=True)
    latest_issue_count = Column(Integer, nullable=True)
    latest_crawl_job_id = Column(Integer, ForeignKey("crawl_jobs.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="competitors")
    latest_crawl = relationship("CrawlJob")
