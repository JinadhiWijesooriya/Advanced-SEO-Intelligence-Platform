"""
Tests — Phase 8: Competitor Analysis
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def register_and_login() -> dict:
    uid = uuid.uuid4().hex[:8]
    email = f"comp_{uid}@seo-test.com"
    password = "CompTestPass123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def create_project(headers: dict, name: str = "Comp Test Project") -> int:
    resp = client.post(
        "/api/v1/projects",
        json={"name": name, "target_url": "https://mysite.com"},
        headers=headers,
    )
    assert resp.status_code in (200, 201)
    return resp.json()["id"]


def make_competitor_payload(project_id: int, name: str = "Competitor Site", domain: str = "competitor.com"):
    return {
        "name": name,
        "domain": domain,
        "target_url": f"https://{domain}",
        "project_id": project_id,
    }


class TestCompetitorCRUD:
    def test_add_competitor(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.post(
            f"/api/v1/projects/{project_id}/competitors",
            json=make_competitor_payload(project_id),
            headers=headers,
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["name"] == "Competitor Site"
        assert data["project_id"] == project_id

    def test_list_competitors(self):
        headers = register_and_login()
        project_id = create_project(headers)
        for i in range(2):
            client.post(
                f"/api/v1/projects/{project_id}/competitors",
                json=make_competitor_payload(project_id, name=f"Comp {i}", domain=f"comp{i}.com"),
                headers=headers,
            )
        resp = client.get(f"/api/v1/projects/{project_id}/competitors", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_delete_competitor(self):
        headers = register_and_login()
        project_id = create_project(headers)
        create_resp = client.post(
            f"/api/v1/projects/{project_id}/competitors",
            json=make_competitor_payload(project_id),
            headers=headers,
        )
        comp_id = create_resp.json()["id"]
        del_resp = client.delete(f"/api/v1/competitors/{comp_id}", headers=headers)
        assert del_resp.status_code == 204
        list_resp = client.get(f"/api/v1/projects/{project_id}/competitors", headers=headers)
        assert all(c["id"] != comp_id for c in list_resp.json())

    def test_competitor_requires_auth(self):
        headers = register_and_login()
        project_id = create_project(headers)
        resp = client.post(
            f"/api/v1/projects/{project_id}/competitors",
            json=make_competitor_payload(project_id),
        )
        assert resp.status_code == 401

    def test_competitor_forbidden_other_user(self):
        headers_a = register_and_login()
        project_id = create_project(headers_a)
        create_resp = client.post(
            f"/api/v1/projects/{project_id}/competitors",
            json=make_competitor_payload(project_id),
            headers=headers_a,
        )
        comp_id = create_resp.json()["id"]
        headers_b = register_and_login()
        del_resp = client.delete(f"/api/v1/competitors/{comp_id}", headers=headers_b)
        assert del_resp.status_code in (403, 404)

    def test_nonexistent_project_competitor(self):
        headers = register_and_login()
        resp = client.post(
            "/api/v1/projects/999999/competitors",
            json=make_competitor_payload(999999),
            headers=headers,
        )
        assert resp.status_code == 404

