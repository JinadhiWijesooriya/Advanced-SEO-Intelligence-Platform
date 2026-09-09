"""
Competitor Analysis API Endpoints - Phase 8
Manages competitor domains for benchmark analysis.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.competitor import Competitor
from app.schemas.intelligence import Competitor as CompetitorSchema, CompetitorCreate, CompetitorUpdate

router = APIRouter()


@router.post(
    "/projects/{project_id}/competitors",
    response_model=CompetitorSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add a competitor",
    tags=["Competitor Analysis"],
)
def create_competitor(
    project_id: int,
    competitor_in: CompetitorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a competitor domain to benchmark against a project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    from urllib.parse import urlparse
    parsed = urlparse(competitor_in.target_url)
    domain = parsed.netloc or competitor_in.domain

    competitor = Competitor(
        project_id=project_id,
        name=competitor_in.name,
        domain=domain or competitor_in.domain,
        target_url=competitor_in.target_url,
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


@router.get(
    "/projects/{project_id}/competitors",
    response_model=List[CompetitorSchema],
    summary="List project competitors",
    tags=["Competitor Analysis"],
)
def list_competitors(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all competitors for a project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    competitors = (
        db.query(Competitor)
        .filter(Competitor.project_id == project_id)
        .order_by(Competitor.created_at.desc())
        .all()
    )
    return competitors


@router.put(
    "/competitors/{competitor_id}",
    response_model=CompetitorSchema,
    summary="Update competitor",
    tags=["Competitor Analysis"],
)
def update_competitor(
    competitor_id: int,
    competitor_in: CompetitorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update competitor details."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found.")

    project = db.query(Project).filter(Project.id == competitor.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized.")

    update_data = competitor_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(competitor, field, value)

    db.commit()
    db.refresh(competitor)
    return competitor


@router.delete(
    "/competitors/{competitor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete competitor",
    tags=["Competitor Analysis"],
)
def delete_competitor(
    competitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a competitor from a project."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found.")

    project = db.query(Project).filter(Project.id == competitor.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized.")

    db.delete(competitor)
    db.commit()


@router.post(
    "/competitors/{competitor_id}/audit",
    summary="Trigger benchmark audit for a competitor",
    tags=["Competitor Analysis"],
)
def audit_competitor(
    competitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a crawl audit for the competitor domain."""
    from app.models.crawl_job import CrawlJob
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found.")

    project = db.query(Project).filter(Project.id == competitor.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized.")

    job = CrawlJob(project_id=project.id, status="pending", total_urls=0, processed_urls=0)
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.workers.tasks import dispatch_crawl_job
    dispatch_crawl_job(job.id, project.id)

    competitor.latest_crawl_job_id = job.id
    db.commit()

    return {"message": "Competitor audit started.", "crawl_job_id": job.id}
