from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportBase(BaseModel):
    format: str

class ReportCreate(ReportBase):
    project_id: int
    crawl_job_id: Optional[int] = None

class ReportInDBBase(ReportBase):
    id: int
    project_id: int
    crawl_job_id: Optional[int] = None
    file_path: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class Report(ReportInDBBase):
    pass
