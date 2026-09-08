from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class SEOResult(Base):
    __tablename__ = "seo_results"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    crawl_job_id = Column(Integer, ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    overall_score = Column(Float, default=100.0, nullable=False)
    technical_score = Column(Float, default=100.0, nullable=False)
    onpage_score = Column(Float, default=100.0, nullable=False)
    content_score = Column(Float, default=100.0, nullable=False)
    link_score = Column(Float, default=100.0, nullable=False)
    performance_score = Column(Float, default=100.0, nullable=False)
    mobile_score = Column(Float, default=100.0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    page = relationship("Page", back_populates="seo_result")
    project = relationship("Project")
    crawl_job = relationship("CrawlJob")
