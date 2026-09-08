from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.seo_issue import SEOIssue
from app.models.page import Page
from app.schemas.issue import (
    SEOIssueResponse,
    SEOIssueUpdateInput,
    SEOIssueListResponse,
    IssueSummaryResponse,
    IssueSeveritySummary,
    IssueCategorySummary,
)

router = APIRouter()


def _get_project_or_404(
    project_id: int,
    db: Session,
    current_user: User,
) -> Project:
    """Retrieve a project belonging to the authenticated user or raise 404."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


def _build_issue_response(issue: SEOIssue, db: Session) -> SEOIssueResponse:
    """Enrich issue with page URL if a page_id is set."""
    page_url: Optional[str] = None
    if issue.page_id:
        page = db.query(Page).filter(Page.id == issue.page_id).first()
        if page:
            page_url = page.url
    return SEOIssueResponse(
        id=issue.id,
        project_id=issue.project_id,
        page_id=issue.page_id,
        crawl_job_id=issue.crawl_job_id,
        category=issue.category,
        severity=issue.severity,
        code=issue.code,
        message=issue.message,
        recommendation=issue.recommendation,
        status=issue.status,
        created_at=issue.created_at,
        page_url=page_url,
    )


@router.get(
    "/projects/{project_id}/issues",
    response_model=SEOIssueListResponse,
    summary="List SEO Issues for a Project",
    description=(
        "Returns a paginated, filterable list of SEO issues detected for a project. "
        "Supports filtering by severity, category, issue status, and keyword search."
    ),
)
def list_project_issues(
    project_id: int,
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, medium, low"),
    category: Optional[str] = Query(None, description="Filter by category: technical, onpage, content, link, image, performance"),
    issue_status: Optional[str] = Query(None, alias="status", description="Filter by status: open, resolved, ignored"),
    search: Optional[str] = Query(None, description="Search in issue message or code"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Number of results per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SEOIssueListResponse:
    _get_project_or_404(project_id, db, current_user)

    query = db.query(SEOIssue).filter(SEOIssue.project_id == project_id)

    if severity:
        query = query.filter(SEOIssue.severity == severity)
    if category:
        query = query.filter(SEOIssue.category == category)
    if issue_status:
        query = query.filter(SEOIssue.status == issue_status)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (SEOIssue.message.ilike(search_term)) | (SEOIssue.code.ilike(search_term))
        )

    # Severity ordering: critical > high > medium > low
    severity_order = case(
        (SEOIssue.severity == "critical", 1),
        (SEOIssue.severity == "high", 2),
        (SEOIssue.severity == "medium", 3),
        (SEOIssue.severity == "low", 4),
        else_=5,
    )
    query = query.order_by(severity_order, SEOIssue.created_at.desc())

    total = query.count()
    offset = (page - 1) * page_size
    raw_issues: List[SEOIssue] = query.offset(offset).limit(page_size).all()

    issues = [_build_issue_response(issue, db) for issue in raw_issues]

    return SEOIssueListResponse(
        total=total,
        page=page,
        page_size=page_size,
        issues=issues,
    )


@router.get(
    "/projects/{project_id}/issues/summary",
    response_model=IssueSummaryResponse,
    summary="Get Issue Summary for a Project",
    description=(
        "Returns aggregated issue counts broken down by severity level and issue category. "
        "Useful for dashboard KPI cards showing overall site health."
    ),
)
def get_issue_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IssueSummaryResponse:
    _get_project_or_404(project_id, db, current_user)

    all_issues: List[SEOIssue] = (
        db.query(SEOIssue)
        .filter(SEOIssue.project_id == project_id)
        .all()
    )

    total_open = sum(1 for i in all_issues if i.status == "open")
    total_resolved = sum(1 for i in all_issues if i.status == "resolved")
    total_ignored = sum(1 for i in all_issues if i.status == "ignored")

    # Severity counts (open issues only)
    open_issues = [i for i in all_issues if i.status == "open"]
    by_severity = IssueSeveritySummary(
        critical=sum(1 for i in open_issues if i.severity == "critical"),
        high=sum(1 for i in open_issues if i.severity == "high"),
        medium=sum(1 for i in open_issues if i.severity == "medium"),
        low=sum(1 for i in open_issues if i.severity == "low"),
    )

    by_category = IssueCategorySummary(
        technical=sum(1 for i in open_issues if i.category == "technical"),
        onpage=sum(1 for i in open_issues if i.category == "onpage"),
        content=sum(1 for i in open_issues if i.category == "content"),
        link=sum(1 for i in open_issues if i.category == "link"),
        image=sum(1 for i in open_issues if i.category == "image"),
        performance=sum(1 for i in open_issues if i.category == "performance"),
    )

    return IssueSummaryResponse(
        total_open=total_open,
        total_resolved=total_resolved,
        total_ignored=total_ignored,
        by_severity=by_severity,
        by_category=by_category,
    )


@router.put(
    "/issues/{issue_id}",
    response_model=SEOIssueResponse,
    summary="Update SEO Issue Status",
    description="Update the resolution status of a SEO issue (open, resolved, ignored).",
)
def update_issue_status(
    issue_id: int,
    body: SEOIssueUpdateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SEOIssueResponse:
    VALID_STATUSES = {"open", "resolved", "ignored"}
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{body.status}'. Must be one of: {', '.join(VALID_STATUSES)}.",
        )

    issue = db.query(SEOIssue).filter(SEOIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SEO issue not found.",
        )

    # Verify ownership through parent project
    project = (
        db.query(Project)
        .filter(Project.id == issue.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    issue.status = body.status
    db.commit()
    db.refresh(issue)

    return _build_issue_response(issue, db)
