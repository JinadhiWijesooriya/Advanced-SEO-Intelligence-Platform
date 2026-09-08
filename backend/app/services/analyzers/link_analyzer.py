from typing import List
from app.models.page import Page
from app.models.link import Link
from app.models.image import Image
from app.services.analyzers.base import BaseAnalyzer, IssueDraft


class LinkAnalyzer(BaseAnalyzer):
    """Evaluates link health: broken internal links based on recorded status codes."""

    def analyze(
        self,
        page: Page,
        links: List[Link],
        images: List[Image],
    ) -> List[IssueDraft]:
        issues: List[IssueDraft] = []

        for link in links:
            if link.link_type != "internal":
                continue

            # A link is considered broken if it's explicitly flagged or has 4xx/5xx status
            is_broken = getattr(link, "is_broken", False)
            status_code = getattr(link, "status_code", None)

            broken_by_status = status_code is not None and status_code >= 400
            if is_broken or broken_by_status:
                code_info = f" (HTTP {status_code})" if status_code else ""
                issues.append(
                    IssueDraft(
                        category="link",
                        severity="high",
                        code="BROKEN_INTERNAL_LINK",
                        message=(
                            f"Internal link to '{link.target_url}' is broken{code_info}."
                        ),
                        recommendation=(
                            "Fix the broken link by updating the href to the correct "
                            "destination URL, or set up a 301 redirect from the old path. "
                            "Broken internal links waste crawl budget and harm user experience."
                        ),
                        page_id=page.id,
                    )
                )

        return issues
