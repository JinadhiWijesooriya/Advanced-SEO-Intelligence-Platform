from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class SEOIssue(Base):
    __tablename__ = "seo_issues"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=True, index=True)
    crawl_job_id = Column(Integer, ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # technical, onpage, content, link, performance
    severity = Column(String(20), nullable=False, index=True)  # critical, high, medium, low
    code = Column(String(100), nullable=False, index=True)      # e.g. MISSING_TITLE, THIN_CONTENT
    message = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    status = Column(String(20), default="open", nullable=False, index=True)  # open, resolved, ignored
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    project = relationship("Project", back_populates="seo_issues")
    page = relationship("Page", back_populates="seo_issues")
    crawl_job = relationship("CrawlJob", back_populates="seo_issues")
