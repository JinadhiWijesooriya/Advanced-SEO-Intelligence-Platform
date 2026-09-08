from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.ssrf import validate_target_url
from app.models.user import User
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    UrlValidateRequest,
    UrlValidateResponse,
)

router = APIRouter()


@router.post("/validate-url", response_model=UrlValidateResponse, summary="Validate Target URL against SSRF Protection Rules")
def validate_url(request: UrlValidateRequest):
    """Validate target URL for SSRF protection and return normalized URL or security error."""
    try:
        normalized = validate_target_url(request.url)
        return UrlValidateResponse(
            url=request.url,
            is_valid=True,
            normalized_url=normalized,
            error=None
        )
    except ValueError as e:
        return UrlValidateResponse(
            url=request.url,
            is_valid=False,
            normalized_url=None,
            error=str(e)
        )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create Website Project")
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new website project scoped to the current user after validating target URL against SSRF rules."""
    try:
        validated_url = validate_target_url(project_in.target_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSRF Protection Rejection: {str(e)}",
        )

    project = Project(
        user_id=current_user.id,
        name=project_in.name,
        target_url=validated_url,
        max_crawl_pages=project_in.max_crawl_pages,
        max_crawl_depth=project_in.max_crawl_depth,
        custom_user_agent=project_in.custom_user_agent,
        respect_robots_txt=project_in.respect_robots_txt,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=List[ProjectResponse], summary="List User Projects")
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all website projects belonging to the authenticated user."""
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )
    return projects


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get Project Details")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project by ID. Returns 404 if not found or 403 if belonging to another user."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project.",
        )
    return project


@router.put("/{project_id}", response_model=ProjectResponse, summary="Update Project Settings")
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update project settings."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this project.",
        )

    update_data = project_in.model_dump(exclude_unset=True)
    if "target_url" in update_data and update_data["target_url"]:
        try:
            update_data["target_url"] = validate_target_url(update_data["target_url"])
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SSRF Protection Rejection: {str(e)}",
            )

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Project")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a website project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this project.",
        )

    db.delete(project)
    db.commit()
    return None
