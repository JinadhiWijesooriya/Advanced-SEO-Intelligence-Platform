from typing import List, Dict, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.seo_result import SEOResult
from app.models.seo_issue import SEOIssue
from app.models.page import Page
from app.models.crawl_job import CrawlJob


# Category weights as defined in specification (Section 11)
WEIGHTS = {
    "technical": 0.25,
    "onpage": 0.25,
    "content": 0.20,
    "link": 0.15,
    "performance": 0.10,
    "mobile": 0.05,
}

# Penalty deductions per issue severity
SEVERITY_DEDUCTIONS = {
    "critical": 25.0,
    "high": 15.0,
    "medium": 8.0,
    "low": 3.0,
}


def calculate_page_scores(issues: List[Any]) -> Dict[str, float]:
    """
    Calculates category and overall scores from a list of issue objects
    or draft dictionaries.
    Each category starts at 100.0 and receives penalties based on issue severity,
    capped at a floor of 0.0.
    """
    category_penalties: Dict[str, float] = defaultdict(float)

    for issue in issues:
        # Support both ORM SEOIssue and mock/dict objects
        category = getattr(issue, "category", None) or (issue.get("category") if isinstance(issue, dict) else "onpage")
        severity = getattr(issue, "severity", None) or (issue.get("severity") if isinstance(issue, dict) else "medium")
        status = getattr(issue, "status", "open") or (issue.get("status", "open") if isinstance(issue, dict) else "open")

        # Only open issues incur score penalties
        if status != "resolved":
            deduction = SEVERITY_DEDUCTIONS.get(severity.lower(), 5.0)
            category_penalties[category.lower()] += deduction

    # Calculate category scores (100 - penalties, min 0.0)
    scores: Dict[str, float] = {}
    for cat in ["technical", "onpage", "content", "link", "performance", "mobile"]:
        penalty = category_penalties.get(cat, 0.0)
        # Cap deduction so category does not fall below 0
        cat_score = max(0.0, min(100.0, 100.0 - penalty))
        scores[f"{cat}_score"] = round(cat_score, 1)

    # Calculate weighted overall score
    overall = (
        scores["technical_score"] * WEIGHTS["technical"]
        + scores["onpage_score"] * WEIGHTS["onpage"]
        + scores["content_score"] * WEIGHTS["content"]
        + scores["link_score"] * WEIGHTS["link"]
        + scores["performance_score"] * WEIGHTS["performance"]
        + scores["mobile_score"] * WEIGHTS["mobile"]
    )
    scores["overall_score"] = round(max(0.0, min(100.0, overall)), 1)
    return scores


def determine_health_grade(score: float) -> str:
    """Returns letter grade corresponding to an overall SEO score."""
    if score >= 90.0:
        return "A"
    elif score >= 80.0:
        return "B"
    elif score >= 70.0:
        return "C"
    elif score >= 60.0:
        return "D"
    return "F"


class SEOScoringEngine:
    """
    Manages calculation and persistence of page-level SEOResult records,
    and produces aggregated site-level SEO summaries.
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_and_save_crawl_scores(
        self, crawl_job_id: int, project_id: int
    ) -> int:
        """
        Calculates and persists SEOResult records for all pages belonging to a crawl job.
        Idempotent: Replaces any previous scores for this crawl job.
        """
        # 1. Wipe previous seo_results for this crawl_job_id to avoid duplicates
        self.db.query(SEOResult).filter(SEOResult.crawl_job_id == crawl_job_id).delete()
        self.db.commit()

        # 2. Fetch all pages for this crawl job
        pages = self.db.query(Page).filter(Page.crawl_job_id == crawl_job_id).all()
        if not pages:
            return 0

        # 3. Fetch all open issues for this crawl job grouped by page_id
        issues = (
            self.db.query(SEOIssue)
            .filter(
                SEOIssue.crawl_job_id == crawl_job_id,
                SEOIssue.status != "resolved",
            )
            .all()
        )

        issues_by_page: Dict[Optional[int], List[SEOIssue]] = defaultdict(list)
        for issue in issues:
            issues_by_page[issue.page_id].append(issue)

        # 4. Generate SEOResult for each page
        saved_count = 0
        for page in pages:
            page_issues = issues_by_page.get(page.id, [])
            scores = calculate_page_scores(page_issues)

            result = SEOResult(
                page_id=page.id,
                project_id=project_id,
                crawl_job_id=crawl_job_id,
                overall_score=scores["overall_score"],
                technical_score=scores["technical_score"],
                onpage_score=scores["onpage_score"],
                content_score=scores["content_score"],
                link_score=scores["link_score"],
                performance_score=scores["performance_score"],
                mobile_score=scores["mobile_score"],
            )
            self.db.add(result)
            saved_count += 1

        self.db.commit()
        return saved_count

    def get_project_seo_summary(self, project_id: int) -> Dict[str, Any]:
        """
        Returns full aggregate SEO summary for a project based on its most recent audit data.
        """
        # Find latest crawl job with results
        latest_crawl = (
            self.db.query(CrawlJob)
            .filter(CrawlJob.project_id == project_id)
            .order_by(CrawlJob.id.desc())
            .first()
        )

        if not latest_crawl:
            return self._empty_summary(project_id)

        # Query all SEOResult for this project (or latest crawl)
        results = (
            self.db.query(SEOResult)
            .filter(SEOResult.crawl_job_id == latest_crawl.id)
            .all()
        )

        if not results:
            return self._empty_summary(project_id, crawl_job_id=latest_crawl.id)

        page_count = len(results)
        avg_overall = sum(r.overall_score for r in results) / page_count
        avg_technical = sum(r.technical_score for r in results) / page_count
        avg_onpage = sum(r.onpage_score for r in results) / page_count
        avg_content = sum(r.content_score for r in results) / page_count
        avg_link = sum(r.link_score for r in results) / page_count
        avg_perf = sum(r.performance_score for r in results) / page_count
        avg_mobile = sum(r.mobile_score for r in results) / page_count

        overall_score = round(avg_overall, 1)

        # Page health distribution
        healthy_pages = sum(1 for r in results if r.overall_score >= 80.0)
        warning_pages = sum(1 for r in results if 60.0 <= r.overall_score < 80.0)
        critical_pages = sum(1 for r in results if r.overall_score < 60.0)

        # Issue statistics
        all_issues = (
            self.db.query(SEOIssue)
            .filter(SEOIssue.project_id == project_id, SEOIssue.crawl_job_id == latest_crawl.id)
            .all()
        )

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        category_counts = {
            "technical": 0,
            "onpage": 0,
            "content": 0,
            "link": 0,
            "performance": 0,
            "mobile": 0,
        }
        status_counts = {"open": 0, "resolved": 0, "ignored": 0}

        # Track top repeated issues
        issue_freq: Dict[str, Dict[str, Any]] = {}

        for issue in all_issues:
            sev = (issue.severity or "medium").lower()
            cat = (issue.category or "onpage").lower()
            st = (issue.status or "open").lower()

            if sev in severity_counts:
                severity_counts[sev] += 1
            if cat in category_counts:
                category_counts[cat] += 1
            if st in status_counts:
                status_counts[st] += 1

            if issue.status != "resolved":
                key = issue.code
                if key not in issue_freq:
                    issue_freq[key] = {
                        "code": issue.code,
                        "category": issue.category,
                        "severity": issue.severity,
                        "message": issue.message,
                        "recommendation": issue.recommendation,
                        "count": 0,
                    }
                issue_freq[key]["count"] += 1

        top_issues = sorted(
            issue_freq.values(),
            key=lambda x: (
                0 if x["severity"] == "critical" else 1 if x["severity"] == "high" else 2,
                -x["count"],
            ),
        )[:5]

        return {
            "project_id": project_id,
            "crawl_job_id": latest_crawl.id,
            "crawl_status": latest_crawl.status,
            "audited_pages": page_count,
            "overall_score": overall_score,
            "health_grade": determine_health_grade(overall_score),
            "category_scores": {
                "technical": round(avg_technical, 1),
                "onpage": round(avg_onpage, 1),
                "content": round(avg_content, 1),
                "link": round(avg_link, 1),
                "performance": round(avg_perf, 1),
                "mobile": round(avg_mobile, 1),
            },
            "page_health": {
                "healthy": healthy_pages,
                "warning": warning_pages,
                "critical": critical_pages,
            },
            "issue_counts": {
                "total": len(all_issues),
                "by_severity": severity_counts,
                "by_category": category_counts,
                "by_status": status_counts,
            },
            "top_issues": top_issues,
        }

    def _empty_summary(self, project_id: int, crawl_job_id: Optional[int] = None) -> Dict[str, Any]:
        """Returns baseline empty structure for projects not yet crawled."""
        return {
            "project_id": project_id,
            "crawl_job_id": crawl_job_id,
            "crawl_status": "none",
            "audited_pages": 0,
            "overall_score": 100.0,
            "health_grade": "A",
            "category_scores": {
                "technical": 100.0,
                "onpage": 100.0,
                "content": 100.0,
                "link": 100.0,
                "performance": 100.0,
                "mobile": 100.0,
            },
            "page_health": {
                "healthy": 0,
                "warning": 0,
                "critical": 0,
            },
            "issue_counts": {
                "total": 0,
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "by_category": {
                    "technical": 0,
                    "onpage": 0,
                    "content": 0,
                    "link": 0,
                    "performance": 0,
                    "mobile": 0,
                },
                "by_status": {"open": 0, "resolved": 0, "ignored": 0},
            },
            "top_issues": [],
        }
