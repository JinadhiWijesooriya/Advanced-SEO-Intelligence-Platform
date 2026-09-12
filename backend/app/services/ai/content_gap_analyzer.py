"""
Content Gap Analyzer — Phase 10

Analyses crawled page data to surface content improvement opportunities:
  - Thin content pages (< 300 words)
  - Pages missing structured heading hierarchy
  - Keyword cannibalization patterns (similar title clusters)
  - Untapped depth opportunities (shallow crawl depth pages with high link count)
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJob
from app.models.page import Page


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ContentGap:
    """A single content improvement opportunity."""
    id: str
    gap_type: str           # thin_content | missing_headings | cannibalization | shallow_depth
    severity: str           # high | medium | low
    title: str
    description: str
    recommendation: str
    affected_count: int
    pages: List[Dict]       # [{url, detail}]


@dataclass
class ContentGapReport:
    gaps: List[ContentGap]
    total_pages_analyzed: int
    thin_content_count: int
    missing_h1_count: int
    cannibalization_clusters: int
    content_health_score: float   # 0–100


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class ContentGapAnalyzer:
    """
    Analyses crawled pages to detect content quality and keyword strategy gaps.

    Usage:
        analyzer = ContentGapAnalyzer(db)
        report = analyzer.analyze(project_id)
    """

    THIN_CONTENT_THRESHOLD = 300      # words
    SIMILARITY_THRESHOLD = 0.75       # title similarity for cannibalization

    def __init__(self, db: Session):
        self.db = db

    def analyze(self, project_id: int) -> ContentGapReport:
        """Run full content gap analysis for the project's latest crawl."""
        crawl = self._get_latest_crawl(project_id)
        if not crawl:
            return ContentGapReport(
                gaps=[],
                total_pages_analyzed=0,
                thin_content_count=0,
                missing_h1_count=0,
                cannibalization_clusters=0,
                content_health_score=100.0,
            )

        pages = self._load_html_pages(crawl.id)
        if not pages:
            return ContentGapReport(
                gaps=[],
                total_pages_analyzed=0,
                thin_content_count=0,
                missing_h1_count=0,
                cannibalization_clusters=0,
                content_health_score=100.0,
            )

        gaps: List[ContentGap] = []

        # --- Run each analysis module ---
        thin_gap, thin_count = self._analyze_thin_content(pages)
        if thin_gap:
            gaps.append(thin_gap)

        heading_gap, missing_h1_count = self._analyze_missing_headings(pages)
        if heading_gap:
            gaps.append(heading_gap)

        cannibal_gap, cluster_count = self._analyze_keyword_cannibalization(pages)
        if cannibal_gap:
            gaps.append(cannibal_gap)

        depth_gap = self._analyze_shallow_opportunities(pages)
        if depth_gap:
            gaps.append(depth_gap)

        # --- Compute health score ---
        total = len(pages)
        health_score = self._compute_health_score(
            total, thin_count, missing_h1_count, cluster_count
        )

        return ContentGapReport(
            gaps=gaps,
            total_pages_analyzed=total,
            thin_content_count=thin_count,
            missing_h1_count=missing_h1_count,
            cannibalization_clusters=cluster_count,
            content_health_score=round(health_score, 1),
        )

    # ------------------------------------------------------------------
    # Analysis modules
    # ------------------------------------------------------------------

    def _analyze_thin_content(
        self, pages: List[Page]
    ) -> tuple[Optional[ContentGap], int]:
        """Flag HTML pages with word count below the threshold."""
        thin_pages = [
            p for p in pages
            if (p.word_count or 0) < self.THIN_CONTENT_THRESHOLD
            and p.status_code == 200
        ]
        if not thin_pages:
            return None, 0

        page_list = [
            {"url": p.url, "detail": f"{p.word_count or 0} words"}
            for p in thin_pages[:20]
        ]
        gap = ContentGap(
            id="thin-content",
            gap_type="thin_content",
            severity="high",
            title=f"Thin Content Detected on {len(thin_pages)} Pages",
            description=(
                f"{len(thin_pages)} of your crawled pages contain fewer than "
                f"{self.THIN_CONTENT_THRESHOLD} words. Google's quality guidelines "
                "classify these as 'thin content' and may exclude them from ranking."
            ),
            recommendation=(
                "Expand each thin page with original, authoritative content. "
                "Aim for 600–1,500 words on landing pages. "
                "Add FAQs, how-to sections, or supporting visuals. "
                "Consider consolidating very thin pages via canonical or 301 redirect "
                "to a richer hub page."
            ),
            affected_count=len(thin_pages),
            pages=page_list,
        )
        return gap, len(thin_pages)

    def _analyze_missing_headings(
        self, pages: List[Page]
    ) -> tuple[Optional[ContentGap], int]:
        """Detect pages missing H1 or with broken heading hierarchy."""
        problem_pages = []
        for page in pages:
            if page.status_code != 200:
                continue
            h1_tags = []
            try:
                h1_tags = json.loads(page.h1_tags) if page.h1_tags else []
            except (json.JSONDecodeError, TypeError):
                pass

            if not h1_tags:
                problem_pages.append({"url": page.url, "detail": "No H1 tag found"})
            elif len(h1_tags) > 1:
                problem_pages.append({"url": page.url, "detail": f"{len(h1_tags)} H1 tags (should be 1)"})

        if not problem_pages:
            return None, 0

        missing_count = sum(1 for p in problem_pages if "No H1" in p["detail"])
        gap = ContentGap(
            id="missing-headings",
            gap_type="missing_headings",
            severity="high" if missing_count > 0 else "medium",
            title=f"Heading Structure Issues on {len(problem_pages)} Pages",
            description=(
                f"{len(problem_pages)} pages have heading structure problems "
                f"({missing_count} missing H1, "
                f"{len(problem_pages) - missing_count} with multiple H1s). "
                "Poor heading hierarchy dilutes topical signals and harms accessibility."
            ),
            recommendation=(
                "Ensure every page has exactly one H1 tag containing the primary keyword. "
                "Structure subsequent headings as H2 (major sections) and H3 (subsections). "
                "Never skip heading levels (e.g., H1 → H3). "
                "Tools like Screaming Frog can bulk-audit heading structures."
            ),
            affected_count=len(problem_pages),
            pages=problem_pages[:20],
        )
        return gap, missing_count

    def _analyze_keyword_cannibalization(
        self, pages: List[Page]
    ) -> tuple[Optional[ContentGap], int]:
        """
        Detect clusters of pages with highly similar title tags — a proxy signal
        for keyword cannibalization where multiple pages compete for the same query.
        """
        pages_with_titles = [
            p for p in pages
            if p.title and p.status_code == 200
        ]
        if len(pages_with_titles) < 2:
            return None, 0

        clusters: List[List[Page]] = []
        visited = set()

        for i, page_a in enumerate(pages_with_titles):
            if i in visited:
                continue
            cluster = [page_a]
            for j, page_b in enumerate(pages_with_titles):
                if j <= i or j in visited:
                    continue
                similarity = SequenceMatcher(
                    None,
                    page_a.title.lower(),
                    page_b.title.lower(),
                ).ratio()
                if similarity >= self.SIMILARITY_THRESHOLD:
                    cluster.append(page_b)
                    visited.add(j)
            if len(cluster) >= 2:
                clusters.append(cluster)
                visited.add(i)

        if not clusters:
            return None, 0

        cluster_pages = [
            {"url": p.url, "detail": f'Title: "{p.title}"'}
            for cluster in clusters
            for p in cluster
        ][:20]

        gap = ContentGap(
            id="keyword-cannibalization",
            gap_type="cannibalization",
            severity="medium",
            title=f"Potential Keyword Cannibalization — {len(clusters)} Title Clusters",
            description=(
                f"{len(clusters)} clusters of pages share very similar title tags "
                f"(≥ {int(self.SIMILARITY_THRESHOLD * 100)}% text similarity). "
                "When multiple pages target the same keyword, they compete against each "
                "other in search results, splitting ranking authority."
            ),
            recommendation=(
                "Review each cluster and decide on a single 'winner' page per topic. "
                "Consolidate weaker pages into the winner via 301 redirect, or differentiate "
                "them by targeting distinct keyword variants. Use Google Search Console to "
                "identify which URL Google already prefers for the target query."
            ),
            affected_count=len(cluster_pages),
            pages=cluster_pages,
        )
        return gap, len(clusters)

    def _analyze_shallow_opportunities(
        self, pages: List[Page]
    ) -> Optional[ContentGap]:
        """
        Identify high-priority pages at depth 0–1 that are content-light —
        these represent the highest-value pages with the most improvement potential.
        """
        opportunity_pages = [
            p for p in pages
            if p.depth is not None
            and p.depth <= 1
            and (p.word_count or 0) < 500
            and p.status_code == 200
        ]
        if len(opportunity_pages) < 2:
            return None

        page_list = [
            {"url": p.url, "detail": f"Depth {p.depth} — {p.word_count or 0} words"}
            for p in opportunity_pages[:15]
        ]
        return ContentGap(
            id="shallow-depth-opportunities",
            gap_type="shallow_depth",
            severity="medium",
            title=f"High-Value Pages Under-Optimised ({len(opportunity_pages)} pages)",
            description=(
                f"{len(opportunity_pages)} pages at crawl depth 0–1 (your most linked-to, "
                "authoritative pages) have fewer than 500 words. "
                "These pages receive the most internal PageRank yet are content-light, "
                "leaving significant ranking potential unused."
            ),
            recommendation=(
                "Prioritise content expansion on shallow-depth pages first — they have the "
                "highest link equity and provide the most impactful ranking improvements per "
                "hour of work. Add original sections, statistics, case studies, or FAQs. "
                "Internally link from these expanded pages to deeper content to distribute equity."
            ),
            affected_count=len(opportunity_pages),
            pages=page_list,
        )

    # ------------------------------------------------------------------
    # Health score computation
    # ------------------------------------------------------------------

    def _compute_health_score(
        self,
        total: int,
        thin_count: int,
        missing_h1_count: int,
        cannibal_clusters: int,
    ) -> float:
        if total == 0:
            return 100.0
        score = 100.0
        score -= (thin_count / total) * 40        # thin content up to -40
        score -= (missing_h1_count / total) * 30  # missing H1 up to -30
        score -= min(cannibal_clusters * 5, 20)   # cannibalization up to -20
        return max(0.0, min(100.0, score))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_latest_crawl(self, project_id: int) -> Optional[CrawlJob]:
        return (
            self.db.query(CrawlJob)
            .filter(CrawlJob.project_id == project_id, CrawlJob.status == "completed")
            .order_by(CrawlJob.id.desc())
            .first()
        )

    def _load_html_pages(self, crawl_job_id: int) -> List[Page]:
        return (
            self.db.query(Page)
            .filter(Page.crawl_job_id == crawl_job_id)
            .all()
        )
