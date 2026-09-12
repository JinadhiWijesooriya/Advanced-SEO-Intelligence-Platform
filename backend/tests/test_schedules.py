"""
Tests — Phase 8: Scheduled Scans
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def register_and_login() -> dict:
    uid = uuid.uuid4().hex[:8]
    email = f"sched_{uid}@seo-test.com"
    password = "SchedTestPass123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def create_project(headers: dict) -> int:
    resp = client.post(
        "/api/v1/projects",
        json={"name": "Schedule Test", "target_url": "https://example.com"},
        headers=headers,
    )
    assert resp.status_code in (200, 201)
    return resp.json()["id"]


SCHEDULE_DAILY = {"frequency": "daily", "enabled": True, "project_id": 0}
SCHEDULE_WEEKLY = {"frequency": "weekly", "enabled": True, "project_id": 0}


class TestScheduleCRUD:
    def test_get_schedule_no_schedule(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.get(f"/api/v1/projects/{project_id}/schedule", headers=headers)
        # Either 200 with null or 404 are acceptable when no schedule exists
        assert resp.status_code in (200, 404)

    def test_create_schedule(self):
        headers = register_and_login()
        project_id = create_project(headers)
        payload = {**SCHEDULE_DAILY, "project_id": project_id}
        resp = client.post(
            f"/api/v1/projects/{project_id}/schedule",
            json=payload,
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["frequency"] == "daily"
        assert data["enabled"] is True
        assert data["project_id"] == project_id

    def test_upsert_schedule(self):
        """Creating a second schedule should update the first (upsert)."""
        headers = register_and_login()
        project_id = create_project(headers)
        payload_daily = {**SCHEDULE_DAILY, "project_id": project_id}
        client.post(f"/api/v1/projects/{project_id}/schedule", json=payload_daily, headers=headers)
        payload_weekly = {**SCHEDULE_WEEKLY, "project_id": project_id}
        resp = client.post(
            f"/api/v1/projects/{project_id}/schedule",
            json=payload_weekly,
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["frequency"] == "weekly"

    def test_get_schedule_after_creation(self):
        headers = register_and_login()
        project_id = create_project(headers)
        payload = {**SCHEDULE_DAILY, "project_id": project_id}
        client.post(f"/api/v1/projects/{project_id}/schedule", json=payload, headers=headers)
        resp = client.get(f"/api/v1/projects/{project_id}/schedule", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None
        assert data["frequency"] == "daily"

    def test_delete_schedule(self):
        headers = register_and_login()
        project_id = create_project(headers)
        payload = {**SCHEDULE_DAILY, "project_id": project_id}
        create_resp = client.post(
            f"/api/v1/projects/{project_id}/schedule",
            json=payload,
            headers=headers,
        )
        schedule_id = create_resp.json()["id"]
        del_resp = client.delete(f"/api/v1/schedules/{schedule_id}", headers=headers)
        assert del_resp.status_code == 204

    def test_schedule_requires_auth(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.post(
            f"/api/v1/projects/{project_id}/schedule",
            json={**SCHEDULE_DAILY, "project_id": project_id},
        )
        assert resp.status_code == 401

    def test_schedule_invalid_frequency(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.post(
            f"/api/v1/projects/{project_id}/schedule",
            json={"frequency": "hourly", "enabled": True, "project_id": project_id},
            headers=headers,
        )
        # Should be rejected by Pydantic validation
        assert resp.status_code == 422

    def test_next_run_at_is_set(self):
        headers = register_and_login()
        project_id = create_project(headers)
        payload = {**SCHEDULE_WEEKLY, "project_id": project_id}
        resp = client.post(
            f"/api/v1/projects/{project_id}/schedule",
            json=payload,
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        # next_run_at should be set automatically
        assert resp.json().get("next_run_at") is not None
