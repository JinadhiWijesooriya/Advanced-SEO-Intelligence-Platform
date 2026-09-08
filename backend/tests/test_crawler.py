import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.crawler import normalize_url, is_same_domain, is_crawlable_media_url

client = TestClient(app)


def get_authenticated_user_headers():
    unique_id = uuid.uuid4().hex[:8]
    email = f"crawler_user_{unique_id}@seo-platform.com"
    password = "Password123!"

    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_crawler_utility_functions():
    # URL normalization
    assert normalize_url("https://example.com/page#section") == "https://example.com/page"
    assert normalize_url("HTTP://EXAMPLE.COM/about/") == "http://example.com/about/"

    # Same domain check
    assert is_same_domain("https://example.com", "https://example.com/contact") is True
    assert is_same_domain("https://example.com", "https://www.example.com/blog") is True
    assert is_same_domain("https://example.com", "https://another-domain.com") is False

    # Media URL check
    assert is_crawlable_media_url("https://example.com/image.png") is False
    assert is_crawlable_media_url("https://example.com/document.pdf") is False
    assert is_crawlable_media_url("https://example.com/page") is True


def test_crawl_job_api_endpoints():
    headers = get_authenticated_user_headers()

    # 1. Create project
    proj_resp = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Crawl Test Site",
            "target_url": "https://example.com",
            "max_crawl_pages": 5,
            "max_crawl_depth": 1,
        },
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Trigger crawl
    crawl_resp = client.post(f"/api/v1/projects/{project_id}/crawl", headers=headers)
    assert crawl_resp.status_code == 202
    job_data = crawl_resp.json()
    assert job_data["project_id"] == project_id
    assert job_data["status"] in ("pending", "running", "completed")
    crawl_id = job_data["id"]

    # 3. Get crawl status
    status_resp = client.get(f"/api/v1/crawls/{crawl_id}", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["id"] == crawl_id

    # 4. Stop crawl job
    stop_resp = client.post(f"/api/v1/crawls/{crawl_id}/stop", headers=headers)
    assert stop_resp.status_code == 200

    # 5. Get project pages list
    pages_resp = client.get(f"/api/v1/projects/{project_id}/pages", headers=headers)
    assert pages_resp.status_code == 200
    pdata = pages_resp.json()
    assert "total" in pdata
    assert "pages" in pdata
