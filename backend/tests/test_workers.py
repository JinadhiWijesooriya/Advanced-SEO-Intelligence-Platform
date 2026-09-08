import uuid
from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.crawl_job import CrawlJob
from app.models.crawl_task import CrawlTask
from app.workers.celery_app import celery_app
from app.workers.tasks import dispatch_crawl_job

client = TestClient(app)


def _get_auth_headers():
    unique = uuid.uuid4().hex[:8]
    email = f"worker_test_{unique}@seo-platform.com"
    pwd = "WorkerPassword123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": pwd})
    res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_celery_app_configuration():
    """Verify Celery app initialization, serializers and configuration."""
    assert celery_app.main == "seo_platform_workers"
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.task_track_started is True
    assert celery_app.conf.worker_prefetch_multiplier == 1


def test_dispatch_fallback():
    """Verify dispatch_crawl_job falls back to BackgroundTasks or direct when Celery is not active."""
    bg_tasks = BackgroundTasks()
    mode = dispatch_crawl_job(crawl_job_id=999, project_id=888, background_tasks=bg_tasks)
    assert mode == "background_tasks"
    assert len(bg_tasks.tasks) == 1


def test_crawl_task_model_persistence():
    """Verify CrawlTask ORM persistence and status transitions."""
    headers = _get_auth_headers()
    proj_resp = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Task Test Project", "target_url": "https://example.com"},
    )
    proj_id = proj_resp.json()["id"]

    db = SessionLocal()
    try:
        crawl = CrawlJob(project_id=proj_id, status="running")
        db.add(crawl)
        db.commit()
        db.refresh(crawl)

        # 1. Create a pending task
        task = CrawlTask(
            crawl_job_id=crawl.id,
            url="https://example.com/blog",
            status="pending",
            attempts=0,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        assert task.id is not None
        assert task.status == "pending"
        assert task.attempts == 0

        # 2. Transition to in_progress
        task.status = "in_progress"
        task.attempts += 1
        db.commit()
        db.refresh(task)
        assert task.status == "in_progress"
        assert task.attempts == 1

        # 3. Transition to completed
        task.status = "completed"
        db.commit()
        db.refresh(task)
        assert task.status == "completed"

        # 4. Test API GET /api/v1/crawls/{crawl_id}/tasks
        api_resp = client.get(
            f"/api/v1/crawls/{crawl.id}/tasks",
            headers=headers,
        )
        assert api_resp.status_code == 200
        data = api_resp.json()
        assert data["total"] == 1
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["url"] == "https://example.com/blog"
        assert data["tasks"][0]["status"] == "completed"
        assert data["tasks"][0]["attempts"] == 1

        # 5. Filter by status
        filter_resp = client.get(
            f"/api/v1/crawls/{crawl.id}/tasks?status=failed",
            headers=headers,
        )
        assert filter_resp.status_code == 200
        assert filter_resp.json()["total"] == 0

    finally:
        db.close()
