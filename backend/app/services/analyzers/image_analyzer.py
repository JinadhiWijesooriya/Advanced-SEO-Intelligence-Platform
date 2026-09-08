from typing import List
from app.models.page import Page
from app.models.link import Link
from app.models.image import Image
from app.services.analyzers.base import BaseAnalyzer, IssueDraft


class ImageAnalyzer(BaseAnalyzer):
    """Evaluates image accessibility: missing ALT attributes."""

    def analyze(
        self,
        page: Page,
        links: List[Link],
        images: List[Image],
    ) -> List[IssueDraft]:
        issues: List[IssueDraft] = []

        # Count images missing ALT text
        missing_alt_images = [img for img in images if not img.has_alt]
        missing_count = len(missing_alt_images)

        if missing_count > 0:
            # Build a concise sample of affected image URLs for the message
            sample_urls = [img.url for img in missing_alt_images[:3]]
            sample_str = ", ".join(f"'{u}'" for u in sample_urls)
            if missing_count > 3:
                sample_str += f" … and {missing_count - 3} more"

            issues.append(
                IssueDraft(
                    category="image",
                    severity="medium",
                    code="MISSING_IMAGE_ALT",
                    message=(
                        f"{missing_count} image(s) on this page are missing ALT attributes: "
                        f"{sample_str}."
                    ),
                    recommendation=(
                        "Add descriptive alt='...' attributes to every <img> element. "
                        "ALT text improves accessibility for screen readers and provides "
                        "contextual signals to search engine image indexing algorithms."
                    ),
                    page_id=page.id,
                )
            )

        return issues
