"""
Scheduled Scans API Endpoints - Phase 8
Manages recurring automated scan schedules for projects.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.scheduled_scan import ScheduledScan
from app.schemas.intelligence import ScheduledScan as ScheduledScanSchema, ScheduledScanCreate, ScheduledScanUpdate

router = APIRouter()


def _compute_next_run(frequency: str) -> datetime:
    now = datetime.now(timezone.utc)
    if frequency == "daily":
        return now + timedelta(days=1)
    elif frequency == "weekly":
        return now + timedelta(weeks=1)
    elif frequency == "monthly":
        return now + timedelta(days=30)
    return now + timedelta(days=1)


@router.post(
    "/projects/{project_id}/schedule",
    response_model=ScheduledScanSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update scheduled scan",
    tags=["Scheduled Scans"],
)
def upsert_schedule(
    project_id: int,
    schedule_in: ScheduledScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update the recurring scan schedule for a project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Upsert: if schedule exists, update it
    schedule = db.query(ScheduledScan).filter(ScheduledScan.project_id == project_id).first()
    if schedule:
        schedule.frequency = schedule_in.frequency
        schedule.enabled = schedule_in.enabled
        schedule.next_run_at = _compute_next_run(schedule_in.frequency)
    else:
        schedule = ScheduledScan(
            project_id=project_id,
            frequency=schedule_in.frequency,
            enabled=schedule_in.enabled,
            next_run_at=_compute_next_run(schedule_in.frequency),
        )
        db.add(schedule)

    db.commit()
    db.refresh(schedule)
    return schedule


@router.get(
    "/projects/{project_id}/schedule",
    response_model=Optional[ScheduledScanSchema],
    summary="Get project schedule",
    tags=["Scheduled Scans"],
)
def get_schedule(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the recurring scan schedule for a project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    schedule = db.query(ScheduledScan).filter(ScheduledScan.project_id == project_id).first()
    return schedule


@router.put(
    "/schedules/{schedule_id}",
    response_model=ScheduledScanSchema,
    summary="Update scheduled scan",
    tags=["Scheduled Scans"],
)
def update_schedule(
    schedule_id: int,
    schedule_in: ScheduledScanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a scheduled scan configuration."""
    schedule = db.query(ScheduledScan).filter(ScheduledScan.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")

    project = db.query(Project).filter(Project.id == schedule.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized.")

    update_data = schedule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    # Recompute next run if frequency changed
    if "frequency" in update_data and not schedule_in.next_run_at:
        schedule.next_run_at = _compute_next_run(schedule.frequency)

    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete(
    "/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete scheduled scan",
    tags=["Scheduled Scans"],
)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a scheduled scan."""
    schedule = db.query(ScheduledScan).filter(ScheduledScan.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")

    project = db.query(Project).filter(Project.id == schedule.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=403, detail="Not authorized.")

    db.delete(schedule)
    db.commit()
