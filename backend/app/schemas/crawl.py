from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class CrawlJobResponse(BaseModel):
    id: int
    project_id: int
    status: str
    total_urls: int
    processed_urls: int
    failed_urls: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LinkResponse(BaseModel):
    id: int
    source_url: str
    target_url: str
    link_type: str
    anchor_text: Optional[str] = None
    status_code: Optional[int] = None
    is_broken: bool

    model_config = ConfigDict(from_attributes=True)


class ImageResponse(BaseModel):
    id: int
    url: str
    alt_text: Optional[str] = None
    has_alt: bool

    model_config = ConfigDict(from_attributes=True)


class PageResponse(BaseModel):
    id: int
    project_id: int
    crawl_job_id: int
    url: str
    status_code: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    h1_tags: Optional[str] = None
    word_count: int
    response_time_ms: int
    depth: int
    content_type: Optional[str] = None
    crawled_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PageDetailResponse(PageResponse):
    links: List[LinkResponse] = []
    images: List[ImageResponse] = []


class PageListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: List[PageResponse]
