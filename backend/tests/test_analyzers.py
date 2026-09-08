import json
import uuid
from types import SimpleNamespace
from fastapi.testclient import TestClient

from app.main import app
from app.services.analyzers.technical_analyzer import TechnicalAnalyzer
from app.services.analyzers.onpage_analyzer import OnPageAnalyzer
from app.services.analyzers.content_analyzer import ContentAnalyzer
from app.services.analyzers.image_analyzer import ImageAnalyzer

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers – build lightweight stubs for unit tests (no DB needed)
# ---------------------------------------------------------------------------

def make_page(**kwargs) -> SimpleNamespace:
    """Build a lightweight Page-like namespace with sensible defaults."""
    defaults = {
        "id": 1,
        "project_id": 1,
        "crawl_job_id": 1,
        "url": "https://example.com/page",
        "status_code": 200,
        "title": "Example Page Title That Is Good",
        "meta_description": "This is a fine meta description for testing purposes.",
        "canonical_url": "https://example.com/page",
        "h1_tags": json.dumps(["Example H1"]),
        "word_count": 500,
        "response_time_ms": 800,
        "depth": 0,
        "content_type": "text/html",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_image(has_alt: bool = True, url: str = "https://example.com/img.jpg") -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        page_id=1,
        url=url,
        has_alt=has_alt,
        alt_text="alt text" if has_alt else None,
    )


def register_and_login() -> dict:
    """Register a unique user and return auth headers."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"phase5_{unique_id}@seo-platform.com"
    password = "SecurePhase5Pass!"

    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_project(headers: dict) -> int:
    """Create a test project and return its ID."""
    resp = client.post(
        "/api/v1/projects",
        json={
            "name": f"Phase5 Project {uuid.uuid4().hex[:6]}",
            "target_url": "https://example.com",
            "max_crawl_pages": 1,
            "max_crawl_depth": 1,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# TechnicalAnalyzer Unit Tests
# ---------------------------------------------------------------------------

class TestTechnicalAnalyzer:
    def setup_method(self):
        self.analyzer = TechnicalAnalyzer()

    def _analyze(self, page):
        return self.analyzer.analyze(page, [], [])

    def test_server_error_5xx_is_critical(self):
        page = make_page(status_code=500)
        issues = self._analyze(page)
        assert any(i.code == "SERVER_ERROR" for i in issues)
        issue = next(i for i in issues if i.code == "SERVER_ERROR")
        assert issue.severity == "critical"
        assert issue.category == "technical"

    def test_client_error_4xx_is_high(self):
        page = make_page(status_code=404)
        issues = self._analyze(page)
        assert any(i.code == "CLIENT_ERROR" for i in issues)
        issue = next(i for i in issues if i.code == "CLIENT_ERROR")
        assert issue.severity == "high"

    def test_non_https_url_is_high(self):
        page = make_page(url="http://example.com/page", canonical_url="http://example.com/page")
        issues = self._analyze(page)
        assert any(i.code == "NON_HTTPS_URL" for i in issues)

    def test_https_url_no_non_https_issue(self):
        page = make_page(url="https://example.com/page")
        issues = self._analyze(page)
        assert not any(i.code == "NON_HTTPS_URL" for i in issues)

    def test_missing_canonical_on_2xx_page(self):
        page = make_page(canonical_url=None)
        issues = self._analyze(page)
        assert any(i.code == "MISSING_CANONICAL" for i in issues)

    def test_canonical_present_no_issue(self):
        page = make_page(canonical_url="https://example.com/page")
        issues = self._analyze(page)
        assert not any(i.code == "MISSING_CANONICAL" for i in issues)

    def test_slow_response_time_medium(self):
        page = make_page(response_time_ms=3500)
        issues = self._analyze(page)
        assert any(i.code == "SLOW_RESPONSE_TIME" for i in issues)
        issue = next(i for i in issues if i.code == "SLOW_RESPONSE_TIME")
        assert issue.severity == "medium"
        assert issue.category == "performance"

    def test_fast_response_no_issue(self):
        page = make_page(response_time_ms=400)
        issues = self._analyze(page)
        assert not any(i.code == "SLOW_RESPONSE_TIME" for i in issues)

    def test_no_issues_on_perfect_page(self):
        page = make_page()
        issues = self._analyze(page)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# OnPageAnalyzer Unit Tests
# ---------------------------------------------------------------------------

class TestOnPageAnalyzer:
    def setup_method(self):
        self.analyzer = OnPageAnalyzer()

    def _analyze(self, page):
        return self.analyzer.analyze(page, [], [])

    def test_missing_title_is_high(self):
        page = make_page(title=None)
        issues = self._analyze(page)
        assert any(i.code == "MISSING_TITLE" for i in issues)
        issue = next(i for i in issues if i.code == "MISSING_TITLE")
        assert issue.severity == "high"

    def test_title_too_short_medium(self):
        page = make_page(title="Hi")
        issues = self._analyze(page)
        assert any(i.code == "TITLE_LENGTH_INVALID" for i in issues)

    def test_title_too_long_medium(self):
        page = make_page(title="A" * 70)
        issues = self._analyze(page)
        assert any(i.code == "TITLE_LENGTH_INVALID" for i in issues)

    def test_title_valid_length_no_issue(self):
        page = make_page(title="A" * 45)
        issues = self._analyze(page)
        assert not any(i.code in ("MISSING_TITLE", "TITLE_LENGTH_INVALID") for i in issues)

    def test_missing_meta_description_medium(self):
        page = make_page(meta_description=None)
        issues = self._analyze(page)
        assert any(i.code == "MISSING_META_DESCRIPTION" for i in issues)

    def test_missing_h1_high(self):
        page = make_page(h1_tags=None)
        issues = self._analyze(page)
        assert any(i.code == "MISSING_H1" for i in issues)
        issue = next(i for i in issues if i.code == "MISSING_H1")
        assert issue.severity == "high"

    def test_multiple_h1_low(self):
        page = make_page(h1_tags=json.dumps(["H1 One", "H1 Two"]))
        issues = self._analyze(page)
        assert any(i.code == "MULTIPLE_H1" for i in issues)
        issue = next(i for i in issues if i.code == "MULTIPLE_H1")
        assert issue.severity == "low"

    def test_onpage_skipped_for_non_200(self):
        page = make_page(status_code=404)
        issues = self._analyze(page)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# ContentAnalyzer Unit Tests
# ---------------------------------------------------------------------------

class TestContentAnalyzer:
    def setup_method(self):
        self.analyzer = ContentAnalyzer()

    def _analyze(self, page):
        return self.analyzer.analyze(page, [], [])

    def test_thin_content_is_medium(self):
        page = make_page(word_count=50)
        issues = self._analyze(page)
        assert any(i.code == "THIN_CONTENT" for i in issues)
        issue = next(i for i in issues if i.code == "THIN_CONTENT")
        assert issue.severity == "medium"
        assert issue.category == "content"

    def test_adequate_content_no_issue(self):
        page = make_page(word_count=600)
        issues = self._analyze(page)
        assert not any(i.code == "THIN_CONTENT" for i in issues)

    def test_thin_content_skipped_for_non_200(self):
        page = make_page(status_code=500, word_count=0)
        issues = self._analyze(page)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# ImageAnalyzer Unit Tests
# ---------------------------------------------------------------------------

class TestImageAnalyzer:
    def setup_method(self):
        self.analyzer = ImageAnalyzer()

    def test_missing_alt_is_medium(self):
        page = make_page()
        img_no_alt = make_image(has_alt=False, url="https://example.com/hero.jpg")
        issues = self.analyzer.analyze(page, [], [img_no_alt])
        assert any(i.code == "MISSING_IMAGE_ALT" for i in issues)
        issue = next(i for i in issues if i.code == "MISSING_IMAGE_ALT")
        assert issue.severity == "medium"

    def test_all_images_have_alt_no_issue(self):
        page = make_page()
        img_with_alt = make_image(has_alt=True)
        issues = self.analyzer.analyze(page, [], [img_with_alt])
        assert not any(i.code == "MISSING_IMAGE_ALT" for i in issues)

    def test_no_images_no_issue(self):
        page = make_page()
        issues = self.analyzer.analyze(page, [], [])
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Issues API Integration Tests
# ---------------------------------------------------------------------------

def test_issues_list_empty_for_new_project():
    """Issues list should be empty for a brand-new project with no crawl."""
    headers = register_and_login()
    project_id = create_project(headers)

    resp = client.get(f"/api/v1/projects/{project_id}/issues", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["issues"] == []


def test_issue_summary_zeros_for_new_project():
    """Summary should return zeros for project with no issues."""
    headers = register_and_login()
    project_id = create_project(headers)

    resp = client.get(f"/api/v1/projects/{project_id}/issues/summary", headers=headers)
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["total_open"] == 0
    assert summary["total_resolved"] == 0
    assert summary["total_ignored"] == 0
    assert summary["by_severity"]["critical"] == 0
    assert summary["by_severity"]["high"] == 0


def test_issues_require_auth():
    """Unauthenticated requests to issues endpoints must return 401."""
    resp = client.get("/api/v1/projects/1/issues")
    assert resp.status_code == 401


def test_update_issue_status_not_found():
    """Updating a non-existent issue should return 404."""
    headers = register_and_login()
    resp = client.put(
        "/api/v1/issues/999999",
        json={"status": "resolved"},
        headers=headers,
    )
    assert resp.status_code == 404


def test_issues_project_isolation():
    """Requesting issues for another user's project should return 404."""
    headers = register_and_login()
    resp = client.get("/api/v1/projects/999999/issues", headers=headers)
    assert resp.status_code == 404
