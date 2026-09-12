"""
Tests — Phase 10: AI Recommendation Engine & Content Gap Analyzer
"""
import json
import uuid
from types import SimpleNamespace
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai.recommendation_engine import AIRecommendationEngine, AISuggestion
from app.services.ai.content_gap_analyzer import ContentGapAnalyzer

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_and_login() -> dict:
    uid = uuid.uuid4().hex[:8]
    email = f"ai_{uid}@seo-test.com"
    password = "AITestPass123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def create_project(headers: dict) -> int:
    resp = client.post(
        "/api/v1/projects",
        json={"name": "AI Test Project", "target_url": "https://example.com"},
        headers=headers,
    )
    assert resp.status_code in (200, 201)
    return resp.json()["id"]


def make_issue(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "project_id": 1,
        "crawl_job_id": 1,
        "page_id": 1,
        "page_url": "https://example.com/page",
        "category": "onpage",
        "severity": "high",
        "code": "MISSING_TITLE",
        "message": "Page is missing a <title> tag.",
        "recommendation": "Add a descriptive title tag.",
        "status": "open",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Unit tests — AI Recommendation Engine (no DB, mock objects)
# ---------------------------------------------------------------------------

class TestRecommendationEngineLogic:
    """Tests rule-based logic without a live DB."""

    def test_rank_critical_before_high(self):
        from app.services.ai.recommendation_engine import AIRecommendationEngine, AISuggestion
        suggestions = [
            AISuggestion(id="a", category="onpage", priority="high",
                         title="High", description="", action="", impact_estimate="",
                         affected_pages=5, affected_urls=[]),
            AISuggestion(id="b", category="technical", priority="critical",
                         title="Critical", description="", action="", impact_estimate="",
                         affected_pages=1, affected_urls=[]),
        ]
        # Create a minimal engine that just calls _rank_suggestions
        engine = object.__new__(AIRecommendationEngine)
        ranked = engine._rank_suggestions(suggestions)
        assert ranked[0].priority == "critical"
        assert ranked[1].priority == "high"

    def test_rank_same_priority_by_affected_pages_desc(self):
        from app.services.ai.recommendation_engine import AIRecommendationEngine, AISuggestion
        suggestions = [
            AISuggestion(id="a", category="onpage", priority="high",
                         title="A", description="", action="", impact_estimate="",
                         affected_pages=3, affected_urls=[]),
            AISuggestion(id="b", category="onpage", priority="high",
                         title="B", description="", action="", impact_estimate="",
                         affected_pages=10, affected_urls=[]),
        ]
        engine = object.__new__(AIRecommendationEngine)
        ranked = engine._rank_suggestions(suggestions)
        assert ranked[0].affected_pages == 10

    def test_fallback_blueprint_uses_issue_fields(self):
        from app.services.ai.recommendation_engine import AIRecommendationEngine
        engine = object.__new__(AIRecommendationEngine)
        sample = make_issue(category="content", severity="medium",
                             code="CUSTOM_RULE", message="Custom msg",
                             recommendation="Fix it")
        blueprint = engine._generate_fallback_blueprint("CUSTOM_RULE", sample)
        assert blueprint["category"] == "content"
        assert blueprint["priority"] == "medium"
        assert "Custom msg" in blueprint["description"]

    def test_no_issues_returns_positive_suggestion(self):
        from app.services.ai.recommendation_engine import AIRecommendationEngine
        engine = object.__new__(AIRecommendationEngine)
        result = engine._no_issues_suggestions(project_id=1)
        assert len(result) == 1
        assert result[0].priority == "quick_win"
        assert result[0].affected_pages == 0

    def test_openai_not_available_without_key(self):
        """Engine should return False for OpenAI availability when no key is set."""
        from app.core.config import settings
        original_key = settings.OPENAI_API_KEY
        settings.OPENAI_API_KEY = ""
        try:
            from app.services.ai.recommendation_engine import AIRecommendationEngine
            available = AIRecommendationEngine._check_openai()
            assert available is False
        finally:
            settings.OPENAI_API_KEY = original_key


class TestContentGapAnalyzerLogic:
    """Tests content gap logic without a live DB."""

    def _make_page(self, **kwargs) -> SimpleNamespace:
        defaults = {
            "id": 1,
            "url": "https://example.com/page",
            "status_code": 200,
            "title": "Sample Page Title",
            "meta_description": "A good meta description.",
            "h1_tags": json.dumps(["Sample H1"]),
            "word_count": 600,
            "depth": 1,
            "content_type": "text/html",
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def _get_analyzer(self):
        return object.__new__(ContentGapAnalyzer)

    def test_thin_content_detected(self):
        analyzer = self._get_analyzer()
        pages = [
            self._make_page(word_count=50, url="https://example.com/thin"),
            self._make_page(word_count=200, url="https://example.com/thin2"),
            self._make_page(word_count=1000, url="https://example.com/rich"),
        ]
        gap, count = analyzer._analyze_thin_content(pages)
        assert gap is not None
        assert count == 2
        assert gap.gap_type == "thin_content"

    def test_no_thin_content_returns_none(self):
        analyzer = self._get_analyzer()
        pages = [self._make_page(word_count=500), self._make_page(word_count=800)]
        gap, count = analyzer._analyze_thin_content(pages)
        assert gap is None
        assert count == 0

    def test_missing_h1_detected(self):
        analyzer = self._get_analyzer()
        pages = [
            self._make_page(h1_tags=json.dumps([])),        # missing H1
            self._make_page(h1_tags=json.dumps(["Good H1"])),
        ]
        gap, missing_count = analyzer._analyze_missing_headings(pages)
        assert gap is not None
        assert missing_count == 1

    def test_multiple_h1_detected(self):
        analyzer = self._get_analyzer()
        pages = [self._make_page(h1_tags=json.dumps(["H1 One", "H1 Two"]))]
        gap, _ = analyzer._analyze_missing_headings(pages)
        assert gap is not None

    def test_no_heading_issues_returns_none(self):
        analyzer = self._get_analyzer()
        pages = [self._make_page(h1_tags=json.dumps(["Perfect H1"]))]
        gap, count = analyzer._analyze_missing_headings(pages)
        assert gap is None

    def test_cannibalization_detected(self):
        analyzer = self._get_analyzer()
        pages = [
            self._make_page(title="Best Python Tutorial 2024", url="https://example.com/p1"),
            self._make_page(title="Best Python Tutorial 2024 Guide", url="https://example.com/p2"),
            self._make_page(title="Completely Different Topic", url="https://example.com/p3"),
        ]
        gap, clusters = analyzer._analyze_keyword_cannibalization(pages)
        assert gap is not None
        assert clusters >= 1

    def test_no_cannibalization_unique_titles(self):
        analyzer = self._get_analyzer()
        pages = [
            self._make_page(title="Python Tutorial", url="https://example.com/p1"),
            self._make_page(title="JavaScript Guide", url="https://example.com/p2"),
            self._make_page(title="React Hooks Explained", url="https://example.com/p3"),
        ]
        gap, clusters = analyzer._analyze_keyword_cannibalization(pages)
        assert clusters == 0

    def test_health_score_perfect_no_issues(self):
        analyzer = self._get_analyzer()
        score = analyzer._compute_health_score(10, 0, 0, 0)
        assert score == 100.0

    def test_health_score_decreases_with_problems(self):
        analyzer = self._get_analyzer()
        good = analyzer._compute_health_score(10, 0, 0, 0)
        bad = analyzer._compute_health_score(10, 5, 5, 2)
        assert bad < good


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestAIEndpoints:
    def test_ai_recommendations_no_crawl(self):
        """Should return 200 with empty suggestions when no crawl has been done."""
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.get(f"/api/v1/projects/{project_id}/ai-recommendations", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == project_id
        assert data["ai_mode"] in ("openai", "rule-based")
        assert isinstance(data["suggestions"], list)

    def test_ai_recommendations_requires_auth(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.get(f"/api/v1/projects/{project_id}/ai-recommendations")
        assert resp.status_code == 401

    def test_ai_recommendations_wrong_project(self):
        headers = register_and_login()
        resp = client.get("/api/v1/projects/999999/ai-recommendations", headers=headers)
        assert resp.status_code == 404

    def test_content_gaps_no_crawl(self):
        """Should return 200 with zero gaps when no crawl has been done."""
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.get(f"/api/v1/projects/{project_id}/content-gaps", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == project_id
        assert data["total_pages_analyzed"] == 0
        assert isinstance(data["gaps"], list)

    def test_content_gaps_requires_auth(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.get(f"/api/v1/projects/{project_id}/content-gaps")
        assert resp.status_code == 401

    def test_regenerate_recommendations(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.post(
            f"/api/v1/projects/{project_id}/ai-recommendations/regenerate",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "suggestions" in data
        assert "ai_mode" in data
