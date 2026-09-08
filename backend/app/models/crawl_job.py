from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, running, completed, failed, stopped
    total_urls = Column(Integer, default=0, nullable=False)
    processed_urls = Column(Integer, default=0, nullable=False)
    failed_urls = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    project = relationship("Project", back_populates="crawl_jobs")
    pages = relationship("Page", back_populates="crawl_job", cascade="all, delete-orphan")
    seo_issues = relationship("SEOIssue", back_populates="crawl_job", cascade="all, delete-orphan")
    tasks = relationship("CrawlTask", back_populates="crawl_job", cascade="all, delete-orphan")

