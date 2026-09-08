from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    crawl_job_id = Column(Integer, ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(1024), nullable=False, index=True)
    status_code = Column(Integer, nullable=False)
    title = Column(String(512), nullable=True)
    meta_description = Column(Text, nullable=True)
    canonical_url = Column(String(1024), nullable=True)
    h1_tags = Column(Text, nullable=True)  # JSON or newline delimited string
    word_count = Column(Integer, default=0, nullable=False)
    response_time_ms = Column(Integer, default=0, nullable=False)
    depth = Column(Integer, default=0, nullable=False)
    content_type = Column(String(100), nullable=True)
    crawled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="pages")
    crawl_job = relationship("CrawlJob", back_populates="pages")
    links = relationship("Link", back_populates="page", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="page", cascade="all, delete-orphan")
    seo_issues = relationship("SEOIssue", back_populates="page", cascade="all, delete-orphan")
    seo_result = relationship("SEOResult", back_populates="page", uselist=False, cascade="all, delete-orphan")

