"""
Reports API Endpoints - Phase 9
Provides report generation (JSON, CSV, PDF) and download functionality.
"""
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.report import Report
from app.schemas.report import Report as ReportSchema, ReportCreate

router = APIRouter()

ALLOWED_FORMATS = {"json", "csv", "pdf"}
MIME_TYPES = {
    "json": "application/json",
    "csv": "text/csv",
    "pdf": "application/pdf",
}


def _generate_report_sync(report_id: int, project_id: int, fmt: str, db_url: str):
    """Run report generation in a separate DB session (for BackgroundTasks)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.report import Report as ReportModel

    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        report = db.query(ReportModel).filter(ReportModel.id == report_id).first()
        if not report:
            return
        try:
            if fmt == "json":
                from app.services.reports.generator import generate_json_report
                path = generate_json_report(project_id, report_id, db)
            elif fmt == "csv":
                from app.services.reports.generator import generate_csv_report
                path = generate_csv_report(project_id, report_id, db)
            else:
                from app.services.reports.generator import generate_pdf_report
                path = generate_pdf_report(project_id, report_id, db)
            report.file_path = path
            report.status = "completed"
        except Exception as e:
            report.status = "failed"
            import logging
            logging.getLogger(__name__).error(f"Report generation failed: {e}")
        db.commit()
    finally:
        db.close()


@router.post(
    "/projects/{project_id}/reports",
    response_model=ReportSchema,
    summary="Generate a new SEO report",
    tags=["Reports"],
)
def create_report(
    project_id: int,
    body: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger report generation for a project.
    ormat must be one of: json, csv, pdf.
    The report is created with status=pending and generated asynchronously.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    fmt = body.format.lower().strip()
    if fmt not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Invalid format. Must be one of: {', '.join(ALLOWED_FORMATS)}")

    report = Report(
        project_id=project_id,
        format=fmt,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Dispatch generation as a background task
    from app.core.config import settings
    background_tasks.add_task(_generate_report_sync, report.id, project_id, fmt, settings.DATABASE_URL)

    return report


@router.get(
    "/projects/{project_id}/reports",
    response_model=List[ReportSchema],
    summary="List reports for a project",
    tags=["Reports"],
)
def list_reports(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reports generated for the specified project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    reports = (
        db.query(Report)
        .filter(Report.project_id == project_id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return reports


@router.get(
    "/reports/{report_id}/download",
    summary="Download a generated report file",
    tags=["Reports"],
)
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream the actual report file for download."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    # Verify ownership
    project = db.query(Project).filter(Project.id == report.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=403, detail="Access denied.")

    if report.status != "completed":
        raise HTTPException(status_code=400, detail=f"Report is not ready (status: {report.status}).")

    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk.")

    fmt = report.format.lower()
    filename = f"seo_report_{report.project_id}_{report.id}.{fmt}"
    return FileResponse(
        path=report.file_path,
        media_type=MIME_TYPES.get(fmt, "application/octet-stream"),
        filename=filename,
    )


@router.delete(
    "/reports/{report_id}",
    status_code=204,
    summary="Delete a report",
    tags=["Reports"],
)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a report record and its associated file."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    project = db.query(Project).filter(Project.id == report.project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Remove file if it exists
    if report.file_path and os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except OSError:
            pass

    db.delete(report)
    db.commit()
