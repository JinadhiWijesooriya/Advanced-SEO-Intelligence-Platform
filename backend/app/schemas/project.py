from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.core.ssrf import validate_target_url


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Project or target site name")
    target_url: str = Field(..., description="Target website root URL")
    max_crawl_pages: int = Field(default=100, ge=1, le=10000, description="Max pages to crawl per audit")
    max_crawl_depth: int = Field(default=3, ge=1, le=10, description="Max crawl depth hierarchy")
    custom_user_agent: str = Field(default="SEOIntelligenceBot/1.0", max_length=255)
    respect_robots_txt: bool = Field(default=True)


class ProjectCreate(ProjectBase):
    @field_validator("target_url")
    @classmethod
    def validate_url_ssrf(cls, v: str) -> str:
        try:
            return validate_target_url(v)
        except ValueError as e:
            raise ValueError(f"SSRF Security Violation / Invalid URL: {str(e)}")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_url: Optional[str] = None
    max_crawl_pages: Optional[int] = Field(None, ge=1, le=10000)
    max_crawl_depth: Optional[int] = Field(None, ge=1, le=10)
    custom_user_agent: Optional[str] = Field(None, max_length=255)
    respect_robots_txt: Optional[bool] = None

    @field_validator("target_url")
    @classmethod
    def validate_url_ssrf(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            return validate_target_url(v)
        except ValueError as e:
            raise ValueError(f"SSRF Security Violation / Invalid URL: {str(e)}")


class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UrlValidateRequest(BaseModel):
    url: str


class UrlValidateResponse(BaseModel):
    url: str
    is_valid: bool
    normalized_url: Optional[str] = None
    error: Optional[str] = None
