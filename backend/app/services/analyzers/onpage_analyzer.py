import json
from typing import List
from app.models.page import Page
from app.models.link import Link
from app.models.image import Image
from app.services.analyzers.base import BaseAnalyzer, IssueDraft


class OnPageAnalyzer(BaseAnalyzer):
    """Evaluates on-page SEO factors: title tag, meta description, and H1 headings."""

    def analyze(
        self,
        page: Page,
        links: List[Link],
        images: List[Image]
    ) -> List[IssueDraft]:
        issues: List[IssueDraft] = []

        # Only evaluate on-page content for successful HTML responses
        if page.status_code != 200:
            return issues

        # 1. Page Title Tag Checks
        title = (page.title or "").strip()
        if not title:
            issues.append(
                IssueDraft(
                    category="onpage",
                    severity="high",
                    code="MISSING_TITLE",
                    message="Page is missing a <title> tag.",
                    recommendation="Add a descriptive, concise <title> tag containing primary keywords (30-60 characters).",
                    page_id=page.id,
                )
            )
        else:
            title_len = len(title)
            if title_len < 30 or title_len > 60:
                issues.append(
                    IssueDraft(
                        category="onpage",
                        severity="medium",
                        code="TITLE_LENGTH_INVALID",
                        message=f"Title length is {title_len} characters (recommended: 30-60 characters).",
                        recommendation="Adjust title tag length to ensure it is not truncated on search engine result pages (SERPs).",
                        page_id=page.id,
                    )
                )

        # 2. Meta Description Checks
        meta_desc = (page.meta_description or "").strip()
        if not meta_desc:
            issues.append(
                IssueDraft(
                    category="onpage",
                    severity="medium",
                    code="MISSING_META_DESCRIPTION",
                    message="Page is missing a meta description.",
                    recommendation="Add a compelling <meta name='description' content='...'> tag between 120-160 characters to maximize click-through rates.",
                    page_id=page.id,
                )
            )

        # 3. H1 Heading Checks
        h1_list = []
        if page.h1_tags:
            try:
                h1_list = json.loads(page.h1_tags)
            except Exception:
                h1_list = [h.strip() for h in page.h1_tags.split("\n") if h.strip()]

        if not h1_list:
            issues.append(
                IssueDraft(
                    category="onpage",
                    severity="high",
                    code="MISSING_H1",
                    message="Page is missing a primary <h1> heading tag.",
                    recommendation="Ensure the page has exactly one <h1> heading summarizing the main topic of the page.",
                    page_id=page.id,
                )
            )
        elif len(h1_list) > 1:
            issues.append(
                IssueDraft(
                    category="onpage",
                    severity="low",
                    code="MULTIPLE_H1",
                    message=f"Page has {len(h1_list)} <h1> headings.",
                    recommendation="Structure document headings hierarchically using a single <h1> for the page title and <h2>/<h3> for subsections.",
                    page_id=page.id,
                )
            )

        return issues
