from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.crawl_job import CrawlJob
from app.models.page import Page
from app.models.crawl_task import CrawlTask
from app.services.crawler import WebCrawlerService
from app.workers.tasks import dispatch_crawl_job
from app.schemas.crawl import (
    CrawlJobResponse,
    PageResponse,
    PageDetailResponse,
    PageListResponse,
)
from app.schemas.task import CrawlTaskListResponse

router = APIRouter()


def execute_background_crawl(job_id: int):
    """Background task runner for executing crawler service."""
    db = SessionLocal()
    try:
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if job:
            crawler = WebCrawlerService(db, job)
            crawler.run_crawl()
    except Exception as e:
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/projects/{project_id}/crawl", response_model=CrawlJobResponse, status_code=status.HTTP_202_ACCEPTED, summary="Start Website Crawl Audit")
def start_project_crawl(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a background web crawl audit for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Check for active running job
    active_job = (
        db.query(CrawlJob)
        .filter(CrawlJob.project_id == project_id, CrawlJob.status.in_(["pending", "running"]))
        .first()
    )
    if active_job:
        return active_job

    # Create new CrawlJob
    crawl_job = CrawlJob(
        project_id=project_id,
        status="pending",
        total_urls=1,
        processed_urls=0,
        failed_urls=0,
    )
    db.add(crawl_job)
    db.commit()
    db.refresh(crawl_job)

    # Dispatch via Celery or fallback to BackgroundTasks
    dispatch_crawl_job(crawl_job.id, project_id, background_tasks)

    return crawl_job


@router.get("/crawls/{crawl_id}", response_model=CrawlJobResponse, summary="Get Crawl Job Status & Metrics")
def get_crawl_status(
    crawl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get live progress metrics for a crawl job."""
    crawl_job = db.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
    if not crawl_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crawl job not found.")
    
    if crawl_job.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return crawl_job


@router.post("/crawls/{crawl_id}/stop", response_model=CrawlJobResponse, summary="Stop In-Progress Crawl")
def stop_crawl_job(
    crawl_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop an ongoing crawl job."""
    crawl_job = db.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
    if not crawl_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crawl job not found.")
    
    if crawl_job.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if crawl_job.status in ["running", "pending"]:
        crawl_job.status = "stopped"
        db.commit()
        db.refresh(crawl_job)

    return crawl_job


@router.get("/projects/{project_id}/pages", response_model=PageListResponse, summary="List Crawled Pages for Project")
def list_project_pages(
    project_id: int,
    query: Optional[str] = Query(None, description="Search URL or title"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated list of crawled pages for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    q = db.query(Page).filter(Page.project_id == project_id)

    if query:
        q = q.filter((Page.url.ilike(f"%{query}%")) | (Page.title.ilike(f"%{query}%")))
    if status_code:
        q = q.filter(Page.status_code == status_code)

    total = q.count()
    pages = q.order_by(Page.crawled_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return PageListResponse(
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/pages/{page_id}", response_model=PageDetailResponse, summary="Get Crawled Page Details")
def get_page_details(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full details of a crawled page, including extracted links and images."""
    page_obj = db.query(Page).filter(Page.id == page_id).first()
    if not page_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found.")
    if page_obj.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return page_obj


@router.get("/crawls/{crawl_id}/tasks", response_model=CrawlTaskListResponse, summary="Get Individual URL Crawl Tasks")
def get_crawl_tasks(
    crawl_id: int,
    task_status: Optional[str] = Query(None, alias="status", description="Filter by status (pending, in_progress, completed, failed)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all distributed URL task statuses and retry attempts for a crawl job."""
    crawl_job = db.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
    if not crawl_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crawl job not found.")

    project = db.query(Project).filter(Project.id == crawl_job.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    q = db.query(CrawlTask).filter(CrawlTask.crawl_job_id == crawl_id)
    if task_status:
        q = q.filter(CrawlTask.status == task_status)

    total = q.count()
    tasks = q.order_by(CrawlTask.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return CrawlTaskListResponse(tasks=tasks, total=total)
