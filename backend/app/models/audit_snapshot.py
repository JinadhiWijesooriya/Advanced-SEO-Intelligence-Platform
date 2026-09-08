from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class AuditSnapshot(Base):
    __tablename__ = "audit_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    crawl_job_id = Column(Integer, ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    overall_score = Column(Float, nullable=False, default=100.0)
    technical_score = Column(Float, nullable=False, default=100.0)
    onpage_score = Column(Float, nullable=False, default=100.0)
    content_score = Column(Float, nullable=False, default=100.0)
    link_score = Column(Float, nullable=False, default=100.0)
    performance_score = Column(Float, nullable=False, default=100.0)
    mobile_score = Column(Float, nullable=False, default=100.0)

    issue_count = Column(Integer, nullable=False, default=0)
    critical_issues = Column(Integer, nullable=False, default=0)
    high_issues = Column(Integer, nullable=False, default=0)
    medium_issues = Column(Integer, nullable=False, default=0)
    low_issues = Column(Integer, nullable=False, default=0)
    page_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    project = relationship("Project", back_populates="snapshots")
    crawl_job = relationship("CrawlJob")
