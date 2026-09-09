"""
SEO Analyzer Engine – master coordinator for all per-page and site-wide SEO rules.

Runs automatically at the end of every crawl job and can also be invoked on-demand.
"""
from collections import defaultdict
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJob
from app.models.page import Page
from app.models.link import Link
from app.models.image import Image
from app.models.seo_issue import SEOIssue
from app.services.analyzers.base import IssueDraft
from app.services.analyzers.technical_analyzer import TechnicalAnalyzer
from app.services.analyzers.onpage_analyzer import OnPageAnalyzer
from app.services.analyzers.content_analyzer import ContentAnalyzer
from app.services.analyzers.link_analyzer import LinkAnalyzer
from app.services.analyzers.image_analyzer import ImageAnalyzer


class SEOAnalyzerEngine:
    """
    Coordinates all modular SEO analyzers.

    Workflow:
    1. Load all pages for the crawl job.
    2. Run per-page analyzers on each page.
    3. Detect site-wide duplicate title/meta-description issues.
    4. Persist all issues to `seo_issues` table.
    """

    def __init__(self, db: Session):
        self.db = db
        self._per_page_analyzers = [
            TechnicalAnalyzer(),
            OnPageAnalyzer(),
            ContentAnalyzer(),
            LinkAnalyzer(),
            ImageAnalyzer(),
        ]

    def run_for_crawl_job(self, crawl_job: CrawlJob) -> int:
        """
        Execute the full analysis pipeline for a completed crawl job.

        Returns the total number of SEOIssue records created.
        """
        project_id = crawl_job.project_id
        crawl_job_id = crawl_job.id

        # Purge any stale issues for this crawl job (re-analysis support)
        self.db.query(SEOIssue).filter(
            SEOIssue.crawl_job_id == crawl_job_id
        ).delete(synchronize_session=False)
        self.db.flush()

        # Load pages belonging to this crawl job
        pages: List[Page] = (
            self.db.query(Page)
            .filter(Page.crawl_job_id == crawl_job_id)
            .all()
        )

        all_drafts: List[IssueDraft] = []

        # --- Per-page rule evaluation ---
        for page in pages:
            links: List[Link] = page.links
            images: List[Image] = page.images

            for analyzer in self._per_page_analyzers:
                drafts = analyzer.analyze(page, links, images)
                all_drafts.extend(drafts)

        # --- Site-wide duplicate detection ---
        all_drafts.extend(self._detect_duplicate_titles(pages, project_id))
        all_drafts.extend(self._detect_duplicate_meta_descriptions(pages, project_id))

        # --- Persist issues ---
        issue_count = 0
        for draft in all_drafts:
            issue = SEOIssue(
                project_id=project_id,
                page_id=draft.page_id,
                crawl_job_id=crawl_job_id,
                category=draft.category,
                severity=draft.severity,
                code=draft.code,
                message=draft.message,
                recommendation=draft.recommendation,
                status="open",
            )
            self.db.add(issue)
            issue_count += 1

        self.db.commit()

        # --- Compute & Persist Page SEOResults ---
        try:
            from app.services.scoring_engine import SEOScoringEngine
            scorer = SEOScoringEngine(self.db)
            scorer.calculate_and_save_crawl_scores(crawl_job_id, project_id)

            # Phase 8: Generate Audit Snapshot (using correct model field names)
            summary = scorer.get_project_seo_summary(project_id)
            from app.models.audit_snapshot import AuditSnapshot
            by_sev = summary["issue_counts"]["by_severity"]
            snapshot = AuditSnapshot(
                project_id=project_id,
                crawl_job_id=crawl_job_id,
                overall_score=summary["overall_score"],
                technical_score=summary["category_scores"]["technical"],
                onpage_score=summary["category_scores"]["onpage"],
                content_score=summary["category_scores"]["content"],
                link_score=summary["category_scores"]["link"],
                performance_score=summary["category_scores"]["performance"],
                mobile_score=summary["category_scores"]["mobile"],
                issue_count=summary["issue_counts"]["total"],
                critical_issues=by_sev.get("critical", 0),
                high_issues=by_sev.get("high", 0),
                medium_issues=by_sev.get("medium", 0),
                low_issues=by_sev.get("low", 0),
                page_count=summary["audited_pages"],
            )
            self.db.add(snapshot)
            self.db.commit()

            # Phase 9: Create in-app Notification for the project owner
            try:
                from app.models.project import Project
                from app.models.notification import Notification
                project = self.db.query(Project).filter(Project.id == project_id).first()
                if project:
                    grade = summary["health_grade"]
                    score = summary["overall_score"]
                    notif = Notification(
                        user_id=project.user_id,
                        type="crawl_complete",
                        message=(
                            f"Crawl completed for \"{project.name}\". "
                            f"Overall SEO score: {score}/100 (Grade {grade}). "
                            f"{summary['issue_counts']['total']} issues found across "
                            f"{summary['audited_pages']} pages."
                        ),
                    )
                    self.db.add(notif)
                    self.db.commit()
            except Exception as notif_err:
                import logging
                logging.getLogger(__name__).warning(f"Failed to create notification for crawl {crawl_job_id}: {notif_err}")

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to calculate scores or snapshots for crawl {crawl_job_id}: {e}")

        return issue_count


    # ------------------------------------------------------------------
    # Site-wide duplicate detection helpers
    # ------------------------------------------------------------------

    def _detect_duplicate_titles(
        self, pages: List[Page], project_id: int
    ) -> List[IssueDraft]:
        """Flag all pages that share an identical non-empty title with another page."""
        title_map: dict = defaultdict(list)
        for page in pages:
            title = (page.title or "").strip()
            if title and page.status_code == 200:
                title_map[title.lower()].append(page)

        drafts: List[IssueDraft] = []
        for title_key, dup_pages in title_map.items():
            if len(dup_pages) < 2:
                continue
            for page in dup_pages:
                drafts.append(
                    IssueDraft(
                        category="onpage",
                        severity="high",
                        code="DUPLICATE_TITLE",
                        message=(
                            f"Title tag '{page.title}' is shared by "
                            f"{len(dup_pages)} pages across the site."
                        ),
                        recommendation=(
                            "Each page should have a unique <title> tag that accurately "
                            "describes its specific content. Duplicate titles confuse search "
                            "engines and dilute click-through rates in search results."
                        ),
                        page_id=page.id,
                    )
                )
        return drafts

    def _detect_duplicate_meta_descriptions(
        self, pages: List[Page], project_id: int
    ) -> List[IssueDraft]:
        """Flag all pages that share an identical non-empty meta description."""
        meta_map: dict = defaultdict(list)
        for page in pages:
            desc = (page.meta_description or "").strip()
            if desc and page.status_code == 200:
                meta_map[desc.lower()].append(page)

        drafts: List[IssueDraft] = []
        for desc_key, dup_pages in meta_map.items():
            if len(dup_pages) < 2:
                continue
            for page in dup_pages:
                drafts.append(
                    IssueDraft(
                        category="onpage",
                        severity="medium",
                        code="DUPLICATE_META_DESCRIPTION",
                        message=(
                            f"Meta description '{(page.meta_description or '')[:80]}...' "
                            f"is shared by {len(dup_pages)} pages."
                        ),
                        recommendation=(
                            "Write unique, compelling meta descriptions for every page. "
                            "Each description should accurately summarize the page's content "
                            "and include relevant keywords to improve search result CTR."
                        ),
                        page_id=page.id,
                    )
                )
        return drafts
