"""
Report Generator Service
Generates JSON, CSV, and PDF reports from SEO project audit data.
"""
import csv
import io
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.services.scoring_engine import SEOScoringEngine, determine_health_grade
from app.models.page import Page
from app.models.seo_issue import SEOIssue
from app.models.crawl_job import CrawlJob

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "../../../../storage/reports")


def _ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def _get_report_data(project_id: int, db: Session) -> Dict[str, Any]:
    """Fetch all data needed for generating reports."""
    engine = SEOScoringEngine(db)
    summary = engine.get_project_seo_summary(project_id)

    # Fetch pages for this project's latest crawl
    latest_crawl = (
        db.query(CrawlJob)
        .filter(CrawlJob.project_id == project_id)
        .order_by(CrawlJob.id.desc())
        .first()
    )
    pages = []
    issues = []
    if latest_crawl:
        pages = db.query(Page).filter(Page.crawl_job_id == latest_crawl.id).all()
        issues = db.query(SEOIssue).filter(SEOIssue.crawl_job_id == latest_crawl.id).all()

    return {"summary": summary, "pages": pages, "issues": issues}


# ---------------------------------------------------------------------------
# JSON Report
# ---------------------------------------------------------------------------

def generate_json_report(project_id: int, report_id: int, db: Session) -> str:
    """Generate a JSON report and return the file path."""
    _ensure_reports_dir()
    data = _get_report_data(project_id, db)
    summary = data["summary"]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_id": project_id,
        "overall_score": summary["overall_score"],
        "health_grade": summary["health_grade"],
        "audited_pages": summary["audited_pages"],
        "category_scores": summary["category_scores"],
        "page_health": summary["page_health"],
        "issue_counts": summary["issue_counts"],
        "top_issues": summary["top_issues"],
    }

    file_path = os.path.join(REPORTS_DIR, f"{report_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return file_path


# ---------------------------------------------------------------------------
# CSV Report
# ---------------------------------------------------------------------------

def generate_csv_report(project_id: int, report_id: int, db: Session) -> str:
    """Generate a CSV report and return the file path."""
    _ensure_reports_dir()
    data = _get_report_data(project_id, db)
    summary = data["summary"]
    pages = data["pages"]
    issues = data["issues"]

    file_path = os.path.join(REPORTS_DIR, f"{report_id}.csv")
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # ---- Summary Section ----
        writer.writerow(["=== SEO Audit Summary ==="])
        writer.writerow(["Generated At", datetime.now(timezone.utc).isoformat()])
        writer.writerow(["Project ID", project_id])
        writer.writerow(["Overall Score", summary["overall_score"]])
        writer.writerow(["Health Grade", summary["health_grade"]])
        writer.writerow(["Audited Pages", summary["audited_pages"]])
        writer.writerow([])

        # ---- Category Scores ----
        writer.writerow(["=== Category Scores ==="])
        writer.writerow(["Category", "Score"])
        for cat, score in summary["category_scores"].items():
            writer.writerow([cat.title(), score])
        writer.writerow([])

        # ---- Pages Section ----
        writer.writerow(["=== Crawled Pages ==="])
        writer.writerow(["URL", "Status Code", "Title", "Word Count", "Response Time (ms)", "Depth"])
        for page in pages:
            writer.writerow([
                page.url,
                page.status_code,
                page.title or "",
                page.word_count,
                page.response_time_ms,
                page.depth,
            ])
        writer.writerow([])

        # ---- Issues Section ----
        writer.writerow(["=== SEO Issues ==="])
        writer.writerow(["Code", "Category", "Severity", "Status", "Message", "Recommendation", "Page URL"])
        for issue in issues:
            writer.writerow([
                issue.code,
                issue.category,
                issue.severity,
                issue.status,
                issue.message,
                issue.recommendation,
                issue.page_url if hasattr(issue, "page_url") else "",
            ])

    return file_path


# ---------------------------------------------------------------------------
# PDF Report
# ---------------------------------------------------------------------------

def generate_pdf_report(project_id: int, report_id: int, db: Session) -> str:
    """Generate a professional PDF report using ReportLab and return the file path."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    _ensure_reports_dir()
    data = _get_report_data(project_id, db)
    summary = data["summary"]
    issues = data["issues"]

    file_path = os.path.join(REPORTS_DIR, f"{report_id}.pdf")

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=16,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#334155"),
        leading=14,
    )

    story = []
    grade = summary["health_grade"]
    overall = summary["overall_score"]
    generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

    # ---- Cover / Header ----
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("SEO Intelligence Platform", title_style))
    story.append(Paragraph(f"Full Audit Report &bull; Project #{project_id}", subtitle_style))
    story.append(Paragraph(f"Generated on {generated_at}", subtitle_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e40af")))
    story.append(Spacer(1, 0.5 * cm))

    # ---- Score Summary ----
    grade_color = {"A": "#16a34a", "B": "#65a30d", "C": "#ca8a04", "D": "#ea580c", "F": "#dc2626"}.get(grade, "#64748b")
    summary_data = [
        ["Overall Score", "Health Grade", "Audited Pages", "Total Issues"],
        [
            f"{overall}/100",
            grade,
            str(summary["audited_pages"]),
            str(summary["issue_counts"]["total"]),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 18),
        ("TEXTCOLOR", (1, 1), (1, 1), colors.HexColor(grade_color)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWHEIGHT", (0, 1), (-1, 1), 40),
        ("ROWHEIGHT", (0, 0), (-1, 0), 24),
        ("TOPPADDING", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5 * cm))

    # ---- Category Scores ----
    story.append(Paragraph("Category Scores", section_header_style))
    cat_scores = summary["category_scores"]
    cat_rows = [["Category", "Score", "Status"]]
    for cat, score in cat_scores.items():
        status = "Good" if score >= 80 else "Warning" if score >= 60 else "Critical"
        cat_rows.append([cat.title(), f"{score}/100", status])

    cat_table = Table(cat_rows, colWidths=[5 * cm, 5 * cm, 6 * cm])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWHEIGHT", (0, 0), (-1, -1), 22),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(cat_table)

    # ---- Top Issues ----
    story.append(Paragraph("Top SEO Issues", section_header_style))
    top_issues = summary["top_issues"]
    if top_issues:
        issue_rows = [["Code", "Category", "Severity", "Count", "Recommendation"]]
        for iss in top_issues:
            rec = iss.get("recommendation", "")
            if len(rec) > 80:
                rec = rec[:77] + "..."
            issue_rows.append([
                iss.get("code", ""),
                iss.get("category", "").title(),
                iss.get("severity", "").upper(),
                str(iss.get("count", 0)),
                rec,
            ])
        sev_colors = {"CRITICAL": "#dc2626", "HIGH": "#ea580c", "MEDIUM": "#ca8a04", "LOW": "#16a34a"}
        issue_table = Table(issue_rows, colWidths=[3 * cm, 2.5 * cm, 2.5 * cm, 1.5 * cm, 6.5 * cm])
        ts = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (4, 1), (4, -1), "LEFT"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWHEIGHT", (0, 0), (-1, -1), 20),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("WORDWRAP", (4, 1), (4, -1), True),
        ]
        for row_idx, iss in enumerate(top_issues, start=1):
            sev = iss.get("severity", "").upper()
            hex_c = sev_colors.get(sev, "#64748b")
            ts.append(("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.HexColor(hex_c)))
            ts.append(("FONTNAME", (2, row_idx), (2, row_idx), "Helvetica-Bold"))
        issue_table.setStyle(TableStyle(ts))
        story.append(issue_table)
    else:
        story.append(Paragraph("No issues found — the site is in excellent SEO health.", body_style))

    # ---- Footer ----
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Generated by Advanced SEO Intelligence Platform — Confidential",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER)
    ))

    doc.build(story)
    return file_path
