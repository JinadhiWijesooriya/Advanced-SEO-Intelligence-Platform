from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CrawlTaskResponse(BaseModel):
    id: int
    crawl_job_id: int
    url: str
    status: str  # pending, in_progress, completed, failed
    attempts: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CrawlTaskListResponse(BaseModel):
    tasks: List[CrawlTaskResponse]
    total: int
