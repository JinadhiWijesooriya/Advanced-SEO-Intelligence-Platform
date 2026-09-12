"""
AI Recommendation Engine — Phase 10

A two-tier SEO intelligence system:
  Tier 1 (always active): Rule-based pattern analysis of crawled SEO issues,
           producing prioritised, actionable fix suggestions with impact estimates.
  Tier 2 (optional):      OpenAI Chat Completions enhancement that enriches the
           rule-based suggestions with natural-language explanations and examples
           when OPENAI_API_KEY is configured.

No paid API key is ever required — the engine degrades gracefully to Tier 1.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models.crawl_job import CrawlJob
from app.models.page import Page
from app.models.seo_issue import SEOIssue

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AISuggestion:
    """A single prioritised AI recommendation."""
    id: str                          # Unique slug, e.g. "fix-missing-title"
    category: str                    # technical | onpage | content | link | image | performance
    priority: str                    # critical | high | medium | quick_win
    title: str
    description: str
    action: str                      # Specific step the developer should take
    impact_estimate: str             # e.g. "High — affects 23 pages"
    affected_pages: int
    affected_urls: List[str] = field(default_factory=list)
    ai_enhanced: bool = False        # True if enriched by OpenAI
    openai_detail: Optional[str] = None


# ---------------------------------------------------------------------------
# Rule catalogue — maps issue codes → recommendation blueprints
# ---------------------------------------------------------------------------

_RULE_CATALOGUE: Dict[str, Dict[str, Any]] = {
    # ── Technical ──────────────────────────────────────────────────────────
    "HTTP_ERROR": {
        "category": "technical",
        "priority": "critical",
        "title": "Fix HTTP Error Pages",
        "description": "Pages returning 4xx/5xx status codes are excluded from search index and hurt crawl budget.",
        "action": "Identify the root cause of each failing URL. Set up proper 301 redirects for moved content or restore deleted pages. Monitor Server Error logs for 5xx causes.",
        "impact_key": "google_crawl_budget",
    },
    "REDIRECT_CHAIN": {
        "category": "technical",
        "priority": "high",
        "title": "Resolve Redirect Chains",
        "description": "Multiple sequential redirects waste PageRank and slow page load time.",
        "action": "Update all internal links to point directly to the final destination URL. Consolidate chains into single 301 redirects.",
        "impact_key": "page_speed",
    },
    "MISSING_CANONICAL": {
        "category": "technical",
        "priority": "high",
        "title": "Add Canonical Tags",
        "description": "Pages without canonical tags are at risk of duplicate-content penalties.",
        "action": "Add <link rel=\"canonical\" href=\"https://yoursite.com/page\"> to the <head> of every HTML page, pointing to the preferred URL.",
        "impact_key": "duplicate_content",
    },
    "SLOW_RESPONSE": {
        "category": "technical",
        "priority": "high",
        "title": "Improve Server Response Time",
        "description": "Pages taking > 2 s to respond negatively impact Core Web Vitals (TTFB) and rankings.",
        "action": "Enable server-side caching (Redis/Varnish), optimise database queries, enable HTTP/2, and consider a CDN for static assets.",
        "impact_key": "core_web_vitals",
    },
    # ── On-Page ────────────────────────────────────────────────────────────
    "MISSING_TITLE": {
        "category": "onpage",
        "priority": "critical",
        "title": "Add Missing Title Tags",
        "description": "Title tags are the #1 on-page ranking signal. Missing titles cause significant ranking losses.",
        "action": "Write a descriptive, keyword-rich <title> of 50–60 characters for every page. Include the primary keyword near the beginning.",
        "impact_key": "ranking_signal",
    },
    "SHORT_TITLE": {
        "category": "onpage",
        "priority": "medium",
        "title": "Lengthen Short Title Tags",
        "description": "Titles under 30 characters miss keyword opportunities and appear thin to search engines.",
        "action": "Expand titles to 50–60 characters by including the primary keyword, brand name, or value proposition. Avoid keyword stuffing.",
        "impact_key": "ctr",
    },
    "LONG_TITLE": {
        "category": "onpage",
        "priority": "medium",
        "title": "Trim Overlong Title Tags",
        "description": "Titles exceeding 60 characters are truncated in SERPs, losing click-through impact.",
        "action": "Rewrite titles to stay within 50–60 characters. Move the primary keyword earlier in the string to preserve it if truncated.",
        "impact_key": "ctr",
    },
    "DUPLICATE_TITLE": {
        "category": "onpage",
        "priority": "high",
        "title": "Eliminate Duplicate Title Tags",
        "description": "Duplicate titles confuse search engines about which page to rank for a given query.",
        "action": "Audit all pages with shared titles. Rewrite each to be unique, accurate, and keyword-relevant for that specific page.",
        "impact_key": "ranking_clarity",
    },
    "MISSING_META_DESCRIPTION": {
        "category": "onpage",
        "priority": "medium",
        "title": "Write Missing Meta Descriptions",
        "description": "Missing meta descriptions mean Google auto-generates snippets, which typically lowers CTR.",
        "action": "Write a compelling 120–160 character meta description for each page. Include the primary keyword and a clear call to action.",
        "impact_key": "ctr",
    },
    "DUPLICATE_META_DESCRIPTION": {
        "category": "onpage",
        "priority": "medium",
        "title": "Differentiate Duplicate Meta Descriptions",
        "description": "Shared meta descriptions across pages signal thin content and reduce SERP appeal.",
        "action": "Write unique meta descriptions for every page. Each should summarise that page's unique value proposition.",
        "impact_key": "ctr",
    },
    "MISSING_H1": {
        "category": "onpage",
        "priority": "high",
        "title": "Add Missing H1 Headings",
        "description": "The H1 is the primary content signal for a page's topic. Missing H1s weaken topical authority.",
        "action": "Add exactly one <h1> tag to every page that clearly states the page's primary topic. Include the target keyword.",
        "impact_key": "topical_authority",
    },
    "MULTIPLE_H1": {
        "category": "onpage",
        "priority": "medium",
        "title": "Fix Multiple H1 Tags",
        "description": "Multiple H1s dilute the topical signal and suggest poor content structure.",
        "action": "Reduce each page to exactly one H1 tag representing the main topic. Convert additional H1s to H2 or H3 as appropriate.",
        "impact_key": "content_structure",
    },
    # ── Content ────────────────────────────────────────────────────────────
    "THIN_CONTENT": {
        "category": "content",
        "priority": "high",
        "title": "Expand Thin Content Pages",
        "description": "Pages with < 300 words are typically classified as thin content and may be de-ranked or excluded.",
        "action": "Add substantive, original content. Aim for at least 600–1000 words on landing pages. Include relevant subheadings, FAQs, and structured data.",
        "impact_key": "content_quality",
    },
    # ── Links ──────────────────────────────────────────────────────────────
    "BROKEN_LINK": {
        "category": "link",
        "priority": "critical",
        "title": "Fix Broken Internal Links",
        "description": "Broken links harm user experience, waste crawl budget, and block PageRank flow.",
        "action": "Use the crawled link data to identify all 404-target URLs. Update or remove each broken link. Set up 301 redirects for legacy URLs.",
        "impact_key": "crawl_budget",
    },
    # ── Images ─────────────────────────────────────────────────────────────
    "MISSING_ALT": {
        "category": "image",
        "priority": "medium",
        "title": "Add Alt Text to Images",
        "description": "Images without alt text miss image search rankings and fail accessibility standards (WCAG 2.1).",
        "action": "Add descriptive alt attributes to all <img> tags. Use concise, keyword-relevant descriptions (< 125 characters). Decorative images should use alt=\"\".",
        "impact_key": "image_seo",
    },
}

# Mapping of impact keys to human-readable impact labels
_IMPACT_LABELS: Dict[str, str] = {
    "google_crawl_budget": "🔴 Directly reduces crawlable pages",
    "page_speed": "🟡 Slows page delivery & PageRank flow",
    "duplicate_content": "🔴 Risks duplicate-content penalty",
    "core_web_vitals": "🔴 Hurts Core Web Vitals ranking factor",
    "ranking_signal": "🔴 Missing strongest on-page ranking signal",
    "ctr": "🟡 Reduces click-through rate from SERPs",
    "ranking_clarity": "🟡 Confuses search engine page selection",
    "topical_authority": "🔴 Weakens page topical relevance signal",
    "content_structure": "🟡 Degrades content hierarchy clarity",
    "content_quality": "🔴 High risk of thin-content penalty",
    "crawl_budget": "🔴 Wastes crawl budget & blocks PageRank",
    "image_seo": "🟢 Missed image ranking + accessibility issue",
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AIRecommendationEngine:
    """
    Analyses the SEO issues of the latest crawl for a project and produces
    prioritised, actionable AI suggestions.

    Usage:
        engine = AIRecommendationEngine(db)
        suggestions = engine.generate(project_id)
    """

    def __init__(self, db: Session):
        self.db = db
        self._openai_available = self._check_openai()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, project_id: int) -> List[AISuggestion]:
        """Return a ranked list of AI suggestions for the project."""
        latest_crawl = self._get_latest_crawl(project_id)
        if not latest_crawl:
            return []

        issues = self._load_open_issues(latest_crawl.id)
        if not issues:
            return self._no_issues_suggestions(project_id)

        suggestions = self._build_rule_based_suggestions(issues, project_id)

        # Optionally enrich with OpenAI (best-effort, never blocks return)
        if self._openai_available:
            suggestions = self._enrich_with_openai(suggestions, project_id)

        return self._rank_suggestions(suggestions)

    def get_ai_mode(self) -> str:
        """Returns 'openai' if OpenAI enrichment is active, else 'rule-based'."""
        return "openai" if self._openai_available else "rule-based"

    # ------------------------------------------------------------------
    # Rule-based analysis
    # ------------------------------------------------------------------

    def _build_rule_based_suggestions(
        self, issues: List[SEOIssue], project_id: int
    ) -> List[AISuggestion]:
        # Aggregate by issue code
        code_groups: Dict[str, List[SEOIssue]] = defaultdict(list)
        for issue in issues:
            code_groups[issue.code].append(issue)

        suggestions: List[AISuggestion] = []

        for code, group in code_groups.items():
            blueprint = _RULE_CATALOGUE.get(code)
            if blueprint is None:
                # Fallback for codes not in catalogue
                blueprint = self._generate_fallback_blueprint(code, group[0])

            # Collect affected URLs (first 10 unique URLs)
            affected_urls: List[str] = []
            for iss in group:
                url = getattr(iss, "page_url", None)
                if not url and getattr(iss, "page", None):
                    url = getattr(iss.page, "url", None)
                if url and url not in affected_urls:
                    affected_urls.append(url)
                if len(affected_urls) >= 10:
                    break

            impact_key = blueprint.get("impact_key", "")
            impact_label = _IMPACT_LABELS.get(impact_key, "🟡 SEO impact")
            impact_str = f"{impact_label} — affects {len(group)} page{'s' if len(group) != 1 else ''}"

            suggestion = AISuggestion(
                id=f"fix-{code.lower().replace('_', '-')}",
                category=blueprint["category"],
                priority=blueprint["priority"],
                title=blueprint["title"],
                description=blueprint["description"],
                action=blueprint["action"],
                impact_estimate=impact_str,
                affected_pages=len(group),
                affected_urls=affected_urls,
                ai_enhanced=False,
            )
            suggestions.append(suggestion)

        return suggestions

    def _generate_fallback_blueprint(
        self, code: str, sample_issue: SEOIssue
    ) -> Dict[str, Any]:
        """Generate a generic blueprint for unknown issue codes."""
        priority_map = {"critical": "critical", "high": "high", "medium": "medium", "low": "quick_win"}
        return {
            "category": sample_issue.category,
            "priority": priority_map.get(sample_issue.severity, "medium"),
            "title": f"Fix: {code.replace('_', ' ').title()}",
            "description": sample_issue.message,
            "action": sample_issue.recommendation,
            "impact_key": "",
        }

    def _no_issues_suggestions(self, project_id: int) -> List[AISuggestion]:
        """Return positive suggestions when no issues are detected."""
        return [
            AISuggestion(
                id="maintain-seo-health",
                category="technical",
                priority="quick_win",
                title="🎉 Excellent SEO Health — Maintain Your Standards",
                description="No open issues detected in the latest crawl. Your site is well-optimised.",
                action=(
                    "Schedule a weekly crawl to catch regressions early. "
                    "Consider expanding your content strategy to target new keyword clusters, "
                    "and monitor Core Web Vitals in Google Search Console."
                ),
                impact_estimate="🟢 Site is in excellent SEO condition",
                affected_pages=0,
                affected_urls=[],
            )
        ]

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def _rank_suggestions(self, suggestions: List[AISuggestion]) -> List[AISuggestion]:
        """Sort by priority tier then affected page count descending."""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "quick_win": 3}
        return sorted(
            suggestions,
            key=lambda s: (priority_order.get(s.priority, 9), -s.affected_pages),
        )

    # ------------------------------------------------------------------
    # OpenAI enrichment (Tier 2 — optional)
    # ------------------------------------------------------------------

    @staticmethod
    def _check_openai() -> bool:
        """Return True if the OpenAI client can be imported and an API key is set."""
        try:
            from app.core.config import settings
            if not getattr(settings, "OPENAI_API_KEY", ""):
                return False
            import openai  # noqa: F401
            return True
        except ImportError:
            return False

    def _enrich_with_openai(
        self, suggestions: List[AISuggestion], project_id: int
    ) -> List[AISuggestion]:
        """
        Best-effort OpenAI enrichment for the top 5 critical/high suggestions.
        Never raises — falls back to rule-based on any error.
        """
        try:
            import openai
            from app.core.config import settings

            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            top = [s for s in suggestions if s.priority in ("critical", "high")][:5]

            for sug in top:
                prompt = (
                    f"You are an expert SEO consultant. A site audit found the issue: '{sug.title}'. "
                    f"Description: {sug.description}. "
                    f"In 2-3 concise sentences, explain WHY this issue specifically harms search rankings "
                    f"and provide ONE highly specific, technical improvement example the developer can implement immediately."
                )
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.4,
                )
                sug.openai_detail = response.choices[0].message.content.strip()
                sug.ai_enhanced = True

        except Exception as exc:
            logger.warning(f"[AIEngine] OpenAI enrichment failed (non-fatal): {exc}")

        return suggestions

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

    def _load_open_issues(self, crawl_job_id: int) -> List[SEOIssue]:
        return (
            self.db.query(SEOIssue)
            .options(joinedload(SEOIssue.page))
            .filter(SEOIssue.crawl_job_id == crawl_job_id, SEOIssue.status == "open")
            .all()
        )
