from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime

# Audit Snapshot Schemas
class AuditSnapshotBase(BaseModel):
    snapshot_type: str = Field(..., description="Type of snapshot, e.g., 'weekly', 'manual', 'competitor'")

class AuditSnapshotCreate(AuditSnapshotBase):
    project_id: int
    score_technical: Optional[float] = None
    score_onpage: Optional[float] = None
    score_content: Optional[float] = None
    score_links: Optional[float] = None
    score_performance: Optional[float] = None
    score_mobile: Optional[float] = None
    overall_score: Optional[float] = None
    metrics_summary: Optional[Dict[str, Any]] = None
    issues_summary: Optional[Dict[str, int]] = None

class AuditSnapshotUpdate(BaseModel):
    pass

class AuditSnapshotInDBBase(AuditSnapshotBase):
    id: int
    project_id: int
    created_at: datetime
    score_technical: Optional[float] = None
    score_onpage: Optional[float] = None
    score_content: Optional[float] = None
    score_links: Optional[float] = None
    score_performance: Optional[float] = None
    score_mobile: Optional[float] = None
    overall_score: Optional[float] = None
    metrics_summary: Optional[Dict[str, Any]] = None
    issues_summary: Optional[Dict[str, int]] = None

    class Config:
        from_attributes = True

class AuditSnapshot(AuditSnapshotInDBBase):
    pass

# Competitor Schemas
class CompetitorBase(BaseModel):
    url: str
    name: Optional[str] = None
    is_active: bool = True

class CompetitorCreate(CompetitorBase):
    project_id: int

class CompetitorUpdate(BaseModel):
    url: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
    last_crawled_at: Optional[datetime] = None
    latest_score: Optional[float] = None

class CompetitorInDBBase(CompetitorBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    last_crawled_at: Optional[datetime] = None
    latest_score: Optional[float] = None

    class Config:
        from_attributes = True

class Competitor(CompetitorInDBBase):
    pass

# Scheduled Scan Schemas
class ScheduledScanBase(BaseModel):
    frequency: str = Field(..., description="'daily', 'weekly', 'monthly'")
    day_of_week: Optional[int] = Field(None, description="0=Monday, 6=Sunday. Only for 'weekly'")
    day_of_month: Optional[int] = Field(None, description="1-31. Only for 'monthly'")
    time_of_day: str = Field(..., description="HH:MM format, e.g., '02:00'")
    is_active: bool = True

class ScheduledScanCreate(ScheduledScanBase):
    project_id: int

class ScheduledScanUpdate(BaseModel):
    frequency: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    time_of_day: Optional[str] = None
    is_active: Optional[bool] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None

class ScheduledScanInDBBase(ScheduledScanBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScheduledScan(ScheduledScanInDBBase):
    pass
