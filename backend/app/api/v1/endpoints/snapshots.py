from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.audit_snapshot import AuditSnapshot
from app.schemas.intelligence import AuditSnapshot as AuditSnapshotSchema

router = APIRouter()

@router.get("/projects/{project_id}/snapshots", response_model=List[AuditSnapshotSchema], summary="List project snapshots")
def list_snapshots(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all historical snapshots for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project.")

    snapshots = db.query(AuditSnapshot).filter(AuditSnapshot.project_id == project_id).order_by(AuditSnapshot.created_at.desc()).all()
    return snapshots

@router.get("/snapshots/{snapshot_id}", response_model=AuditSnapshotSchema, summary="Get a snapshot")
def get_snapshot(
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a specific snapshot."""
    snapshot = db.query(AuditSnapshot).filter(AuditSnapshot.id == snapshot_id).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found.")
        
    project = db.query(Project).filter(Project.id == snapshot.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this snapshot.")
        
    return snapshot
