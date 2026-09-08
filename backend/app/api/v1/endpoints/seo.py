from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.page import Page
from app.models.seo_result import SEOResult
from app.models.crawl_job import CrawlJob
from app.models.seo_issue import SEOIssue
from app.services.scoring_engine import SEOScoringEngine, calculate_page_scores
from app.schemas.seo import (
    ProjectSEOSummaryResponse,
    PageSEOScoreResponse,
)

router = APIRouter()


def _get_project_or_404(project_id: int, db: Session, current_user: User) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not owned by user.",
        )
    return project


@router.get("/projects/{project_id}/seo-summary", response_model=ProjectSEOSummaryResponse)
def get_project_seo_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns high-level aggregate SEO audit summary, health grade,
    category score breakdowns, page health distribution, and top critical issues.
    """
    _get_project_or_404(project_id, db, current_user)
    scoring_engine = SEOScoringEngine(db)
    summary = scoring_engine.get_project_seo_summary(project_id)
    return summary


@router.get("/pages/{page_id}/seo", response_model=PageSEOScoreResponse)
def get_page_seo_score(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns calculated SEO scores (overall + category breakdown) for a specific crawled page.
    """
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found.",
        )

    _get_project_or_404(page.project_id, db, current_user)

    # Fetch existing result or compute dynamically
    result = db.query(SEOResult).filter(SEOResult.page_id == page_id).first()
    if not result:
        issues = db.query(SEOIssue).filter(SEOIssue.page_id == page_id).all()
        scores = calculate_page_scores(issues)
        result = SEOResult(
            page_id=page.id,
            project_id=page.project_id,
            crawl_job_id=page.crawl_job_id,
            overall_score=scores["overall_score"],
            technical_score=scores["technical_score"],
            onpage_score=scores["onpage_score"],
            content_score=scores["content_score"],
            link_score=scores["link_score"],
            performance_score=scores["performance_score"],
            mobile_score=scores["mobile_score"],
        )
        db.add(result)
        db.commit()
        db.refresh(result)

    return PageSEOScoreResponse(
        id=result.id,
        page_id=result.page_id,
        project_id=result.project_id,
        crawl_job_id=result.crawl_job_id,
        overall_score=result.overall_score,
        technical_score=result.technical_score,
        onpage_score=result.onpage_score,
        content_score=result.content_score,
        link_score=result.link_score,
        performance_score=result.performance_score,
        mobile_score=result.mobile_score,
        created_at=result.created_at,
        url=page.url,
    )


@router.post("/projects/{project_id}/recalculate-scores", response_model=ProjectSEOSummaryResponse)
def recalculate_project_scores(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recalculates and persists scores for the latest crawl of a project.
    """
    _get_project_or_404(project_id, db, current_user)

    latest_crawl = (
        db.query(CrawlJob)
        .filter(CrawlJob.project_id == project_id)
        .order_by(CrawlJob.id.desc())
        .first()
    )
    if latest_crawl:
        scoring_engine = SEOScoringEngine(db)
        scoring_engine.calculate_and_save_crawl_scores(latest_crawl.id, project_id)

    scoring_engine = SEOScoringEngine(db)
    return scoring_engine.get_project_seo_summary(project_id)
