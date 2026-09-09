from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ---------------------------------------------------------------------------
# Audit Snapshot Schemas
# ---------------------------------------------------------------------------

class AuditSnapshotBase(BaseModel):
    overall_score: float = 100.0
    technical_score: float = 100.0
    onpage_score: float = 100.0
    content_score: float = 100.0
    link_score: float = 100.0
    performance_score: float = 100.0
    mobile_score: float = 100.0
    issue_count: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    page_count: int = 0


class AuditSnapshotCreate(AuditSnapshotBase):
    project_id: int
    crawl_job_id: int


class AuditSnapshot(AuditSnapshotBase):
    id: int
    project_id: int
    crawl_job_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Competitor Schemas
# ---------------------------------------------------------------------------

class CompetitorBase(BaseModel):
    name: str
    domain: str
    target_url: str


class CompetitorCreate(CompetitorBase):
    project_id: int


class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    target_url: Optional[str] = None
    latest_score: Optional[float] = None
    latest_page_count: Optional[int] = None
    latest_issue_count: Optional[int] = None


class Competitor(CompetitorBase):
    id: int
    project_id: int
    latest_score: Optional[float] = None
    latest_page_count: Optional[int] = None
    latest_issue_count: Optional[int] = None
    latest_crawl_job_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Scheduled Scan Schemas
# ---------------------------------------------------------------------------

class ScheduledScanBase(BaseModel):
    frequency: str = Field(..., description="'daily', 'weekly', 'monthly'")
    enabled: bool = True


class ScheduledScanCreate(ScheduledScanBase):
    project_id: int


class ScheduledScanUpdate(BaseModel):
    frequency: Optional[str] = None
    enabled: Optional[bool] = None
    next_run_at: Optional[datetime] = None


class ScheduledScan(ScheduledScanBase):
    id: int
    project_id: int
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
