from typing import List
from urllib.parse import urlparse
from app.models.page import Page
from app.models.link import Link
from app.models.image import Image
from app.services.analyzers.base import BaseAnalyzer, IssueDraft


class TechnicalAnalyzer(BaseAnalyzer):
    """Evaluates technical SEO signals: HTTP status codes, HTTPS protocol, canonical tags, response latency."""

    def analyze(
        self,
        page: Page,
        links: List[Link],
        images: List[Image]
    ) -> List[IssueDraft]:
        issues: List[IssueDraft] = []

        # 1. Server Errors (5xx)
        if page.status_code >= 500:
            issues.append(
                IssueDraft(
                    category="technical",
                    severity="critical",
                    code="SERVER_ERROR",
                    message=f"Page returned server error HTTP {page.status_code}.",
                    recommendation="Investigate web server or backend application logs to resolve internal server exceptions.",
                    page_id=page.id,
                )
            )
        # 2. Client Errors (4xx)
        elif page.status_code >= 400:
            issues.append(
                IssueDraft(
                    category="technical",
                    severity="high",
                    code="CLIENT_ERROR",
                    message=f"Page returned client error HTTP {page.status_code}.",
                    recommendation="Fix broken target URL or set up 301 redirects for deleted resources.",
                    page_id=page.id,
                )
            )

        # 3. Non-HTTPS Protocol
        parsed = urlparse(page.url)
        if parsed.scheme.lower() == "http":
            issues.append(
                IssueDraft(
                    category="technical",
                    severity="high",
                    code="NON_HTTPS_URL",
                    message="Page is served over insecure HTTP connection.",
                    recommendation="Migrate to HTTPS and install a valid SSL/TLS certificate to protect data and preserve search rankings.",
                    page_id=page.id,
                )
            )

        # 4. Missing Canonical Tag (Only for successful 2xx pages)
        if 200 <= page.status_code < 300:
            if not page.canonical_url or not page.canonical_url.strip():
                issues.append(
                    IssueDraft(
                        category="technical",
                        severity="medium",
                        code="MISSING_CANONICAL",
                        message="Page lacks a self-referential or target canonical link tag.",
                        recommendation="Add a <link rel='canonical' href='...'> tag in the <head> section to prevent duplicate content issues.",
                        page_id=page.id,
                    )
                )

        # 5. Slow Response Time (> 2000 ms)
        if page.response_time_ms > 2000:
            issues.append(
                IssueDraft(
                    category="performance",
                    severity="medium",
                    code="SLOW_RESPONSE_TIME",
                    message=f"Page response time is slow ({page.response_time_ms} ms).",
                    recommendation="Optimize server processing, enable caching, and reduce database latency to bring response time under 1,000 ms.",
                    page_id=page.id,
                )
            )

        return issues
