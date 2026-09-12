"""
Tests — Phase 9: In-App Notifications
"""
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.models.notification import Notification

client = TestClient(app)


def register_and_login() -> tuple[dict, int]:
    """Returns (auth_headers, user_id)."""
    uid = uuid.uuid4().hex[:8]
    email = f"notif_{uid}@seo-test.com"
    password = "NotifTestPass123!"
    reg_resp = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]
    user_id = reg_resp.json()["id"]
    return {"Authorization": f"Bearer {token}"}, user_id


def seed_notification(user_id: int, message: str = "Test notification", unread: bool = True) -> int:
    """Directly insert a notification into the DB for testing."""
    db: Session = SessionLocal()
    try:
        notif = Notification(
            user_id=user_id,
            type="test_event",
            message=message,
            read_at=None if unread else datetime.now(timezone.utc),
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif.id
    finally:
        db.close()


class TestNotificationList:
    def test_list_notifications_empty(self):
        headers, _ = register_and_login()
        resp = client.get("/api/v1/notifications", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_notifications_with_data(self):
        headers, user_id = register_and_login()
        seed_notification(user_id, "SEO crawl complete")
        seed_notification(user_id, "Issue found")
        resp = client.get("/api/v1/notifications", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_unread_only_filter(self):
        headers, user_id = register_and_login()
        seed_notification(user_id, "Unread one", unread=True)
        seed_notification(user_id, "Already read", unread=False)
        resp = client.get("/api/v1/notifications?unread_only=true", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        # All returned notifications should have read_at = null
        assert all(n["read_at"] is None for n in data)

    def test_notifications_require_auth(self):
        resp = client.get("/api/v1/notifications")
        assert resp.status_code == 401


class TestNotificationUnreadCount:
    def test_unread_count_zero(self):
        headers, _ = register_and_login()
        resp = client.get("/api/v1/notifications/unread-count", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 0

    def test_unread_count_increments(self):
        headers, user_id = register_and_login()
        seed_notification(user_id)
        seed_notification(user_id)
        resp = client.get("/api/v1/notifications/unread-count", headers=headers)
        assert resp.json()["unread_count"] == 2


class TestMarkNotificationRead:
    def test_mark_single_notification_read(self):
        headers, user_id = register_and_login()
        notif_id = seed_notification(user_id)
        resp = client.put(f"/api/v1/notifications/{notif_id}/read", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["read_at"] is not None

    def test_mark_nonexistent_notification(self):
        headers, _ = register_and_login()
        resp = client.put("/api/v1/notifications/999999/read", headers=headers)
        assert resp.status_code == 404

    def test_mark_all_read(self):
        headers, user_id = register_and_login()
        seed_notification(user_id)
        seed_notification(user_id)
        resp = client.put("/api/v1/notifications/read-all", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["marked_read"] >= 2
        # Verify count is now zero
        count_resp = client.get("/api/v1/notifications/unread-count", headers=headers)
        assert count_resp.json()["unread_count"] == 0


class TestDeleteNotification:
    def test_delete_notification(self):
        headers, user_id = register_and_login()
        notif_id = seed_notification(user_id)
        del_resp = client.delete(f"/api/v1/notifications/{notif_id}", headers=headers)
        assert del_resp.status_code == 204

    def test_delete_nonexistent_notification(self):
        headers, _ = register_and_login()
        resp = client.delete("/api/v1/notifications/999999", headers=headers)
        assert resp.status_code == 404
