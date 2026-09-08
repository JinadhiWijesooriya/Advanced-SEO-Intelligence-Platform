from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    target_url = Column(String(1024), nullable=False)
    max_crawl_pages = Column(Integer, default=100, nullable=False)
    max_crawl_depth = Column(Integer, default=3, nullable=False)
    custom_user_agent = Column(String(255), default="SEOIntelligenceBot/1.0", nullable=False)
    respect_robots_txt = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner = relationship("User", back_populates="projects")
    crawl_jobs = relationship("CrawlJob", back_populates="project", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="project", cascade="all, delete-orphan")
    seo_issues = relationship("SEOIssue", back_populates="project", cascade="all, delete-orphan")
    snapshots = relationship("AuditSnapshot", back_populates="project", cascade="all, delete-orphan", order_by="AuditSnapshot.created_at.desc()")
    competitors = relationship("Competitor", back_populates="project", cascade="all, delete-orphan")
    schedule = relationship("ScheduledScan", back_populates="project", uselist=False, cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="project", cascade="all, delete-orphan")


