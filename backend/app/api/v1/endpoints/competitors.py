from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.competitor import Competitor
from app.schemas.intelligence import Competitor as CompetitorSchema, CompetitorCreate, CompetitorUpdate
from app.core.ssrf import validate_target_url

router = APIRouter()

@router.post("/projects/{project_id}/competitors", response_model=CompetitorSchema, status_code=status.HTTP_201_CREATED, summary="Add a competitor")
def create_competitor(
    project_id: int,
    competitor_in: CompetitorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a competitor to a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")

    try:
        validated_url = validate_target_url(competitor_in.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {str(e)}")

    competitor = Competitor(
        project_id=project_id,
        url=validated_url,
        name=competitor_in.name,
        is_active=competitor_in.is_active
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor

@router.get("/projects/{project_id}/competitors", response_model=List[CompetitorSchema], summary="List project competitors")
def list_competitors(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all competitors for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")

    competitors = db.query(Competitor).filter(Competitor.project_id == project_id).order_by(Competitor.created_at.desc()).all()
    return competitors

@router.put("/competitors/{competitor_id}", response_model=CompetitorSchema, summary="Update competitor")
def update_competitor(
    competitor_id: int,
    competitor_in: CompetitorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a competitor."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found.")
        
    project = db.query(Project).filter(Project.id == competitor.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this competitor.")

    update_data = competitor_in.model_dump(exclude_unset=True)
    if "url" in update_data and update_data["url"]:
        try:
            update_data["url"] = validate_target_url(update_data["url"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid URL: {str(e)}")

    for field, value in update_data.items():
        setattr(competitor, field, value)

    db.commit()
    db.refresh(competitor)
    return competitor

@router.delete("/competitors/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete competitor")
def delete_competitor(
    competitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a competitor."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found.")
        
    project = db.query(Project).filter(Project.id == competitor.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this competitor.")

    db.delete(competitor)
    db.commit()
    return None
