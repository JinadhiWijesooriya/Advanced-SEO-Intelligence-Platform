"""
AI Intelligence API Endpoints — Phase 10

Exposes rule-based + optional OpenAI-powered SEO recommendations
and content gap analysis through the REST API.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.services.ai.recommendation_engine import AIRecommendationEngine, AISuggestion
from app.services.ai.content_gap_analyzer import ContentGapAnalyzer, ContentGap, ContentGapReport

router = APIRouter()


# ---------------------------------------------------------------------------
# Response schemas (inline Pydantic — no separate schema file needed)
# ---------------------------------------------------------------------------

class AISuggestionOut(BaseModel):
    id: str
    category: str
    priority: str
    title: str
    description: str
    action: str
    impact_estimate: str
    affected_pages: int
    affected_urls: List[str]
    ai_enhanced: bool
    openai_detail: Optional[str]

    class Config:
        from_attributes = True


class AIRecommendationsResponse(BaseModel):
    project_id: int
    ai_mode: str           # "openai" or "rule-based"
    total_suggestions: int
    suggestions: List[AISuggestionOut]


class ContentGapPageOut(BaseModel):
    url: str
    detail: str


class ContentGapOut(BaseModel):
    id: str
    gap_type: str
    severity: str
    title: str
    description: str
    recommendation: str
    affected_count: int
    pages: List[ContentGapPageOut]


class ContentGapReportOut(BaseModel):
    project_id: int
    total_pages_analyzed: int
    thin_content_count: int
    missing_h1_count: int
    cannibalization_clusters: int
    content_health_score: float
    gaps: List[ContentGapOut]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/projects/{project_id}/ai-recommendations",
    response_model=AIRecommendationsResponse,
    summary="Get AI-powered SEO recommendations",
    tags=["AI Intelligence"],
)
def get_ai_recommendations(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate prioritised AI recommendations for a project based on
    the issues found in the latest completed crawl.

    The engine runs rule-based analysis by default (always available).
    If OPENAI_API_KEY is configured, the top critical/high findings are
    additionally enriched with GPT-powered natural-language explanations.
    """
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    engine = AIRecommendationEngine(db)
    suggestions = engine.generate(project_id)
    ai_mode = engine.get_ai_mode()

    return AIRecommendationsResponse(
        project_id=project_id,
        ai_mode=ai_mode,
        total_suggestions=len(suggestions),
        suggestions=[
            AISuggestionOut(
                id=s.id,
                category=s.category,
                priority=s.priority,
                title=s.title,
                description=s.description,
                action=s.action,
                impact_estimate=s.impact_estimate,
                affected_pages=s.affected_pages,
                affected_urls=s.affected_urls,
                ai_enhanced=s.ai_enhanced,
                openai_detail=s.openai_detail,
            )
            for s in suggestions
        ],
    )


@router.post(
    "/projects/{project_id}/ai-recommendations/regenerate",
    response_model=AIRecommendationsResponse,
    summary="Force-regenerate AI recommendations",
    tags=["AI Intelligence"],
)
def regenerate_ai_recommendations(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Re-run the AI analysis pipeline immediately.
    Useful after resolving issues or updating content.
    """
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    engine = AIRecommendationEngine(db)
    suggestions = engine.generate(project_id)
    ai_mode = engine.get_ai_mode()

    return AIRecommendationsResponse(
        project_id=project_id,
        ai_mode=ai_mode,
        total_suggestions=len(suggestions),
        suggestions=[
            AISuggestionOut(
                id=s.id,
                category=s.category,
                priority=s.priority,
                title=s.title,
                description=s.description,
                action=s.action,
                impact_estimate=s.impact_estimate,
                affected_pages=s.affected_pages,
                affected_urls=s.affected_urls,
                ai_enhanced=s.ai_enhanced,
                openai_detail=s.openai_detail,
            )
            for s in suggestions
        ],
    )


@router.get(
    "/projects/{project_id}/content-gaps",
    response_model=ContentGapReportOut,
    summary="Get content gap analysis",
    tags=["AI Intelligence"],
)
def get_content_gaps(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyse crawled pages for content improvement opportunities:
    thin content, missing headings, keyword cannibalization,
    and underoptimised high-authority pages.
    """
    project = db.query(Project).filter(
        Project.id == project_id, Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    analyzer = ContentGapAnalyzer(db)
    report = analyzer.analyze(project_id)

    return ContentGapReportOut(
        project_id=project_id,
        total_pages_analyzed=report.total_pages_analyzed,
        thin_content_count=report.thin_content_count,
        missing_h1_count=report.missing_h1_count,
        cannibalization_clusters=report.cannibalization_clusters,
        content_health_score=report.content_health_score,
        gaps=[
            ContentGapOut(
                id=g.id,
                gap_type=g.gap_type,
                severity=g.severity,
                title=g.title,
                description=g.description,
                recommendation=g.recommendation,
                affected_count=g.affected_count,
                pages=[ContentGapPageOut(url=p["url"], detail=p["detail"]) for p in g.pages],
            )
            for g in report.gaps
        ],
    )
