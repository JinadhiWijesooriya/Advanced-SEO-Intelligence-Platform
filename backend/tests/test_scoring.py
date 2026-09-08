import uuid
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.main import app
from app.services.scoring_engine import (
    calculate_page_scores,
    determine_health_grade,
    SEOScoringEngine,
    WEIGHTS,
)
from app.core.database import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.crawl_job import CrawlJob
from app.models.page import Page
from app.models.seo_issue import SEOIssue
from app.models.seo_result import SEOResult

client = TestClient(app)


# --------------------------------------------------------------------------
# Unit Tests for Scoring Logic
# --------------------------------------------------------------------------

def test_calculate_page_scores_zero_issues():
    """A page with no issues should get 100 on every category and overall."""
    scores = calculate_page_scores([])
    assert scores["overall_score"] == 100.0
    assert scores["technical_score"] == 100.0
    assert scores["onpage_score"] == 100.0
    assert scores["content_score"] == 100.0
    assert scores["link_score"] == 100.0
    assert scores["performance_score"] == 100.0
    assert scores["mobile_score"] == 100.0


def test_calculate_page_scores_deductions():
    """Verify deductions match specification rules."""
    # Critical deduction = -25 on technical
    critical_issue = SimpleNamespace(category="technical", severity="critical", status="open")
    scores = calculate_page_scores([critical_issue])
    assert scores["technical_score"] == 75.0
    # Expected overall: 75*0.25 + 100*0.25 + 100*0.20 + 100*0.15 + 100*0.10 + 100*0.05
    # = 18.75 + 25 + 20 + 15 + 10 + 5 = 93.75 -> 93.8
    assert scores["overall_score"] == 93.8

    # High deduction = -15 on onpage
    high_issue = SimpleNamespace(category="onpage", severity="high", status="open")
    scores_high = calculate_page_scores([high_issue])
    assert scores_high["onpage_score"] == 85.0

    # Medium deduction = -8 on content
    med_issue = SimpleNamespace(category="content", severity="medium", status="open")
    scores_med = calculate_page_scores([med_issue])
    assert scores_med["content_score"] == 92.0

    # Low deduction = -3 on link
    low_issue = SimpleNamespace(category="link", severity="low", status="open")
    scores_low = calculate_page_scores([low_issue])
    assert scores_low["link_score"] == 97.0


def test_resolved_issues_do_not_penalize_score():
    """Resolved issues should not incur score deductions."""
    resolved_issue = SimpleNamespace(category="technical", severity="critical", status="resolved")
    scores = calculate_page_scores([resolved_issue])
    assert scores["technical_score"] == 100.0
    assert scores["overall_score"] == 100.0


def test_category_score_cannot_drop_below_zero():
    """Category scores should be clamped at 0.0 even with excessive penalties."""
    many_criticals = [
        SimpleNamespace(category="technical", severity="critical", status="open")
        for _ in range(10)
    ]  # 10 * 25 = 250 deduction
    scores = calculate_page_scores(many_criticals)
    assert scores["technical_score"] == 0.0
    # Overall score with 0 technical (weight 0.25): 0 + 25 + 20 + 15 + 10 + 5 = 75.0
    assert scores["overall_score"] == 75.0


def test_determine_health_grades():
    """Health grades correctly map to score thresholds."""
    assert determine_health_grade(95.0) == "A"
    assert determine_health_grade(90.0) == "A"
    assert determine_health_grade(85.5) == "B"
    assert determine_health_grade(80.0) == "B"
    assert determine_health_grade(75.0) == "C"
    assert determine_health_grade(70.0) == "C"
    assert determine_health_grade(65.0) == "D"
    assert determine_health_grade(60.0) == "D"
    assert determine_health_grade(59.9) == "F"
    assert determine_health_grade(20.0) == "F"


# --------------------------------------------------------------------------
# Integration & API Tests
# --------------------------------------------------------------------------

def _create_authenticated_client():
    unique_id = uuid.uuid4().hex[:8]
    email = f"phase6_{unique_id}@seo-platform.com"
    pwd = "SecurePassword123!"
    reg = client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
    assert reg.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login.json()["access_token"]
    auth_client = TestClient(app)
    auth_client.headers.update({"Authorization": f"Bearer {token}"})
    return auth_client, email


def test_get_seo_summary_empty_project():
    """Projects without crawls return clean baseline 100.0 summary."""
    auth_client, _ = _create_authenticated_client()
    proj_resp = auth_client.post(
        "/api/v1/projects",
        json={"name": "Empty Project", "target_url": "https://example.com"},
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    summary_resp = auth_client.get(f"/api/v1/projects/{proj_id}/seo-summary")
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    assert data["project_id"] == proj_id
    assert data["audited_pages"] == 0
    assert data["overall_score"] == 100.0
    assert data["health_grade"] == "A"
    assert data["category_scores"]["technical"] == 100.0


def test_scoring_engine_and_summary_api():
    """End-to-end test of SEOScoringEngine calculation and API summary."""
    auth_client, email = _create_authenticated_client()
    proj_resp = auth_client.post(
        "/api/v1/projects",
        json={"name": "Scoring Project", "target_url": "https://example.com"},
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    db = SessionLocal()
    try:
        # Create a mock crawl job
        crawl = CrawlJob(
            project_id=proj_id,
            status="completed",
            total_urls=2,
            processed_urls=2,
        )
        db.add(crawl)
        db.commit()
        db.refresh(crawl)

        # Page 1: Perfect (no issues)
        page1 = Page(
            project_id=proj_id,
            crawl_job_id=crawl.id,
            url="https://scoring-example.com/",
            status_code=200,
            title="Home Page Valid Title Length Perfect",
            meta_description="A good description that explains the home page content clearly.",
            word_count=500,
            response_time_ms=150,
        )
        # Page 2: Has issues
        page2 = Page(
            project_id=proj_id,
            crawl_job_id=crawl.id,
            url="https://scoring-example.com/bad",
            status_code=500,
            title=None,
            meta_description=None,
            word_count=50,
            response_time_ms=2500,
        )
        db.add(page1)
        db.add(page2)
        db.commit()
        db.refresh(page1)
        db.refresh(page2)

        # Create issues for page 2
        issue1 = SEOIssue(
            project_id=proj_id,
            page_id=page2.id,
            crawl_job_id=crawl.id,
            category="technical",
            severity="critical",
            code="SERVER_ERROR",
            message="HTTP 500 error",
            recommendation="Fix server configuration",
            status="open",
        )
        issue2 = SEOIssue(
            project_id=proj_id,
            page_id=page2.id,
            crawl_job_id=crawl.id,
            category="onpage",
            severity="high",
            code="MISSING_TITLE",
            message="Title is missing",
            recommendation="Add a title tag",
            status="open",
        )
        db.add(issue1)
        db.add(issue2)
        db.commit()

        # Run scoring engine
        engine = SEOScoringEngine(db)
        saved = engine.calculate_and_save_crawl_scores(crawl.id, proj_id)
        assert saved == 2

        # Verify page 1 score
        res1 = db.query(SEOResult).filter_by(page_id=page1.id).first()
        assert res1 is not None
        assert res1.overall_score == 100.0

        # Verify page 2 score (technical: 75.0, onpage: 85.0)
        res2 = db.query(SEOResult).filter_by(page_id=page2.id).first()
        assert res2 is not None
        assert res2.technical_score == 75.0
        assert res2.onpage_score == 85.0
        assert res2.overall_score < 100.0

        # Test GET /projects/{id}/seo-summary
        summary_resp = auth_client.get(f"/api/v1/projects/{proj_id}/seo-summary")
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["audited_pages"] == 2
        assert summary["overall_score"] < 100.0
        assert summary["issue_counts"]["total"] == 2
        assert summary["issue_counts"]["by_severity"]["critical"] == 1
        assert summary["issue_counts"]["by_severity"]["high"] == 1
        assert len(summary["top_issues"]) > 0

        # Test GET /pages/{id}/seo
        page_seo_resp = auth_client.get(f"/api/v1/pages/{page2.id}/seo")
        assert page_seo_resp.status_code == 200
        pdata = page_seo_resp.json()
        assert pdata["page_id"] == page2.id
        assert pdata["technical_score"] == 75.0
        assert pdata["onpage_score"] == 85.0

    finally:
        db.close()
