from dataclasses import dataclass
from typing import List, Optional
from app.models.page import Page
from app.models.link import Link
from app.models.image import Image


@dataclass
class IssueDraft:
    category: str       # technical, onpage, content, link, performance
    severity: str       # critical, high, medium, low
    code: str           # e.g. MISSING_TITLE
    message: str
    recommendation: str
    page_id: Optional[int] = None


class BaseAnalyzer:
    """Abstract base class for modular SEO rule analyzers."""

    def analyze(
        self,
        page: Page,
        links: List[Link],
        images: List[Image]
    ) -> List[IssueDraft]:
        raise NotImplementedError("Subclasses must implement analyze method.")
