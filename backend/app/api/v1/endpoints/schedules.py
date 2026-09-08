from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.scheduled_scan import ScheduledScan
from app.schemas.intelligence import ScheduledScan as ScheduledScanSchema, ScheduledScanCreate, ScheduledScanUpdate

router = APIRouter()

@router.post("/projects/{project_id}/schedules", response_model=ScheduledScanSchema, status_code=status.HTTP_201_CREATED, summary="Create scheduled scan")
def create_schedule(
    project_id: int,
    schedule_in: ScheduledScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a scheduled scan for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")

    schedule = ScheduledScan(
        project_id=project_id,
        frequency=schedule_in.frequency,
        day_of_week=schedule_in.day_of_week,
        day_of_month=schedule_in.day_of_month,
        time_of_day=schedule_in.time_of_day,
        is_active=schedule_in.is_active
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

@router.get("/projects/{project_id}/schedules", response_model=List[ScheduledScanSchema], summary="List scheduled scans")
def list_schedules(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all scheduled scans for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")

    schedules = db.query(ScheduledScan).filter(ScheduledScan.project_id == project_id).all()
    return schedules

@router.put("/schedules/{schedule_id}", response_model=ScheduledScanSchema, summary="Update scheduled scan")
def update_schedule(
    schedule_id: int,
    schedule_in: ScheduledScanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a scheduled scan."""
    schedule = db.query(ScheduledScan).filter(ScheduledScan.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
        
    project = db.query(Project).filter(Project.id == schedule.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this schedule.")

    update_data = schedule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)
    return schedule

@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete scheduled scan")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a scheduled scan."""
    schedule = db.query(ScheduledScan).filter(ScheduledScan.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
        
    project = db.query(Project).filter(Project.id == schedule.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this schedule.")

    db.delete(schedule)
    db.commit()
    return None
