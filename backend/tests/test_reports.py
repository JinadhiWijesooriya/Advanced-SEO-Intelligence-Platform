"""
Tests — Phase 9: Reports (JSON, CSV, PDF generation)
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def register_and_login() -> dict:
    uid = uuid.uuid4().hex[:8]
    email = f"rep_{uid}@seo-test.com"
    password = "ReportTestPass123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def create_project(headers: dict) -> int:
    resp = client.post(
        "/api/v1/projects",
        json={"name": "Reports Test Project", "target_url": "https://example.com"},
        headers=headers,
    )
    assert resp.status_code in (200, 201)
    return resp.json()["id"]


class TestReportCreation:
    def test_create_json_report(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.post(
            f"/api/v1/projects/{project_id}/reports",
            json={"format": "json", "project_id": project_id},
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["format"] == "json"
        assert data["project_id"] == project_id
        assert data["status"] in ("pending", "completed")

    def test_create_csv_report(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.post(
            f"/api/v1/projects/{project_id}/reports",
            json={"format": "csv", "project_id": project_id},
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["format"] == "csv"

    def test_create_pdf_report(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.post(
            f"/api/v1/projects/{project_id}/reports",
            json={"format": "pdf", "project_id": project_id},
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["format"] == "pdf"

    def test_invalid_format_rejected(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.post(
            f"/api/v1/projects/{project_id}/reports",
            json={"format": "xlsx", "project_id": project_id},
            headers=headers,
        )
        assert resp.status_code == 400

    def test_report_requires_auth(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.post(
            f"/api/v1/projects/{project_id}/reports",
            json={"format": "json", "project_id": project_id},
        )
        assert resp.status_code == 401


class TestReportList:
    def test_list_reports_empty(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.get(f"/api/v1/projects/{project_id}/reports", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_reports_after_creation(self):
        headers = register_and_login()
        project_id = create_project(headers)
        client.post(
            f"/api/v1/projects/{project_id}/reports",
            json={"format": "json", "project_id": project_id},
            headers=headers,
        )
        resp = client.get(f"/api/v1/projects/{project_id}/reports", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestReportDelete:
    def test_delete_report(self):
        headers = register_and_login()
        project_id = create_project(headers)
        create_resp = client.post(
            f"/api/v1/projects/{project_id}/reports",
            json={"format": "json", "project_id": project_id},
            headers=headers,
        )
        report_id = create_resp.json()["id"]
        del_resp = client.delete(f"/api/v1/reports/{report_id}", headers=headers)
        assert del_resp.status_code == 204

    def test_delete_nonexistent_report(self):
        headers = register_and_login()
        resp = client.delete("/api/v1/reports/999999", headers=headers)
        assert resp.status_code == 404
