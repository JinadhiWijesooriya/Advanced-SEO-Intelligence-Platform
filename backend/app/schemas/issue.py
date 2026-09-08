from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class SEOIssueResponse(BaseModel):
    id: int
    project_id: int
    page_id: Optional[int]
    crawl_job_id: int
    category: str
    severity: str
    code: str
    message: str
    recommendation: str
    status: str
    created_at: datetime

    # Optional page URL for display purposes (joined from Page model)
    page_url: Optional[str] = None

    model_config = {"from_attributes": True}


class SEOIssueUpdateInput(BaseModel):
    status: str  # open, resolved, ignored


class SEOIssueListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    issues: List[SEOIssueResponse]


class IssueSeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class IssueCategorySummary(BaseModel):
    technical: int = 0
    onpage: int = 0
    content: int = 0
    link: int = 0
    image: int = 0
    performance: int = 0


class IssueSummaryResponse(BaseModel):
    total_open: int
    total_resolved: int
    total_ignored: int
    by_severity: IssueSeveritySummary
    by_category: IssueCategorySummary
