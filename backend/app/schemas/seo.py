from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CategoryScores(BaseModel):
    technical: float
    onpage: float
    content: float
    link: float
    performance: float
    mobile: float


class PageHealthSummary(BaseModel):
    healthy: int
    warning: int
    critical: int


class TopIssueSummary(BaseModel):
    code: str
    category: str
    severity: str
    message: str
    recommendation: str
    count: int


class ProjectSEOSummaryResponse(BaseModel):
    project_id: int
    crawl_job_id: Optional[int] = None
    crawl_status: str
    audited_pages: int
    overall_score: float
    health_grade: str
    category_scores: CategoryScores
    page_health: PageHealthSummary
    issue_counts: Dict[str, Any]
    top_issues: List[TopIssueSummary]


class PageSEOScoreResponse(BaseModel):
    id: int
    page_id: int
    project_id: int
    crawl_job_id: int
    overall_score: float
    technical_score: float
    onpage_score: float
    content_score: float
    link_score: float
    performance_score: float
    mobile_score: float
    created_at: datetime
    url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
