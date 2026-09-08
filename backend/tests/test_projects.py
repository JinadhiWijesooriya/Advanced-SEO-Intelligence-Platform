import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_authenticated_user_headers():
    unique_id = uuid.uuid4().hex[:8]
    email = f"project_user_{unique_id}@seo-platform.com"
    password = "Password123!"

    # Register
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    # Login
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email


def test_url_validation_ssrf_endpoint():
    # Test valid URL
    resp = client.post("/api/v1/projects/validate-url", json={"url": "https://example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["error"] is None

    # Test SSRF blocked URLs
    for blocked_url in ["http://127.0.0.1", "http://localhost", "http://169.254.169.254", "http://10.0.0.1"]:
        resp = client.post("/api/v1/projects/validate-url", json={"url": blocked_url})
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert data["error"] is not None


def test_project_crud_flow_and_ssrf_blocking():
    headers, email = get_authenticated_user_headers()

    # 1. Attempt creating project with SSRF target (should fail with 422 validation error)
    ssrf_response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Malicious Target",
            "target_url": "http://127.0.0.1",
            "max_crawl_pages": 50,
            "max_crawl_depth": 2,
        },
    )
    assert ssrf_response.status_code in (400, 422)

    # 2. Create valid project
    create_resp = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "E-Commerce Site",
            "target_url": "https://example.com",
            "max_crawl_pages": 250,
            "max_crawl_depth": 4,
            "custom_user_agent": "MyCustomBot/2.0",
            "respect_robots_txt": True,
        },
    )
    assert create_resp.status_code == 201
    proj_data = create_resp.json()
    assert proj_data["name"] == "E-Commerce Site"
    assert proj_data["target_url"] == "https://example.com"
    assert proj_data["max_crawl_pages"] == 250
    assert proj_data["max_crawl_depth"] == 4
    project_id = proj_data["id"]

    # 3. List projects
    list_resp = client.get("/api/v1/projects", headers=headers)
    assert list_resp.status_code == 200
    projects = list_resp.json()
    assert len(projects) >= 1
    assert any(p["id"] == project_id for p in projects)

    # 4. Get single project details
    get_resp = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == project_id

    # 5. Update project settings
    update_resp = client.put(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={
            "name": "Updated E-Commerce Site",
            "max_crawl_pages": 500,
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated E-Commerce Site"
    assert update_resp.json()["max_crawl_pages"] == 500

    # 6. User Isolation Check (User B should not access User A's project)
    headers_b, email_b = get_authenticated_user_headers()
    user_b_get = client.get(f"/api/v1/projects/{project_id}", headers=headers_b)
    assert user_b_get.status_code == 403

    user_b_update = client.put(
        f"/api/v1/projects/{project_id}",
        headers=headers_b,
        json={"name": "Hacked Name"},
    )
    assert user_b_update.status_code == 403

    user_b_delete = client.delete(f"/api/v1/projects/{project_id}", headers=headers_b)
    assert user_b_delete.status_code == 403

    # 7. Delete project by owner
    del_resp = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert del_resp.status_code == 204

    # Confirm deleted
    get_del_resp = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_del_resp.status_code == 404
