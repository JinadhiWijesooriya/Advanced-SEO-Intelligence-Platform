"""
Tests — Phase 8: Historical Snapshots
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def register_and_login() -> dict:
    uid = uuid.uuid4().hex[:8]
    email = f"snap_{uid}@seo-test.com"
    password = "SnapTestPass123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def create_project(headers: dict) -> int:
    resp = client.post(
        "/api/v1/projects",
        json={"name": "Snapshot Test", "target_url": "https://example.com"},
        headers=headers,
    )
    assert resp.status_code in (200, 201)
    return resp.json()["id"]


class TestSnapshotList:
    def test_empty_snapshots_returns_list(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.get(f"/api/v1/projects/{project_id}/snapshots", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_snapshots_require_auth(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.get(f"/api/v1/projects/{project_id}/snapshots")
        assert resp.status_code == 401

    def test_snapshots_forbidden_other_user(self):
        headers_a = register_and_login()
        project_id = create_project(headers_a)
        # Different user tries to access
        headers_b = register_and_login()
        resp = client.get(f"/api/v1/projects/{project_id}/snapshots", headers=headers_b)
        # Should get 404 (project not found for that user) or 403
        assert resp.status_code in (403, 404)

    def test_get_nonexistent_project_snapshots(self):
        headers = register_and_login()
        resp = client.get("/api/v1/projects/999999/snapshots", headers=headers)
        assert resp.status_code == 404

    def test_get_nonexistent_snapshot(self):
        headers = register_and_login()
        resp = client.get("/api/v1/snapshots/999999", headers=headers)
        assert resp.status_code == 404
