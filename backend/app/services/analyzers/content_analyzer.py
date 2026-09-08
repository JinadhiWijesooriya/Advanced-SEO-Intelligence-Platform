from typing import List
from app.models.page import Page
from app.models.link import Link
from app.models.image import Image
from app.services.analyzers.base import BaseAnalyzer, IssueDraft

THIN_CONTENT_THRESHOLD = 300  # words


class ContentAnalyzer(BaseAnalyzer):
    """Evaluates content quality signals: word count / thin content detection."""

    def analyze(
        self,
        page: Page,
        links: List[Link],
        images: List[Image],
    ) -> List[IssueDraft]:
        issues: List[IssueDraft] = []

        # Only evaluate content for successful 2xx HTML pages
        if page.status_code != 200:
            return issues

        # Thin Content Detection (< 300 words)
        if (page.word_count or 0) < THIN_CONTENT_THRESHOLD:
            issues.append(
                IssueDraft(
                    category="content",
                    severity="medium",
                    code="THIN_CONTENT",
                    message=(
                        f"Page contains only {page.word_count or 0} words "
                        f"(minimum recommended: {THIN_CONTENT_THRESHOLD} words)."
                    ),
                    recommendation=(
                        "Expand page content with helpful, unique information that "
                        "addresses user intent. Aim for at least 300 words of substantive "
                        "content to signal topical depth to search engines."
                    ),
                    page_id=page.id,
                )
            )

        return issues
