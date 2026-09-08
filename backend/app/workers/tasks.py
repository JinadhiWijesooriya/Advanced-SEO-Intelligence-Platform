import logging
from app.workers.celery_app import celery_app
from app.core.config import settings
from app.services.crawler import run_crawler_job

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def crawl_website_task(self, crawl_job_id: int, project_id: int):
    """
    Celery background worker task for website crawl execution.
    Retries with exponential backoff on network/transient failures.
    """
    try:
        logger.info(f"Starting Celery crawl task for job={crawl_job_id}, project={project_id}")
        run_crawler_job(crawl_job_id, project_id)
        return {"status": "completed", "crawl_job_id": crawl_job_id}
    except Exception as exc:
        logger.error(f"Error in Celery crawl task for job {crawl_job_id}: {exc}")
        countdown = 10 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


def dispatch_crawl_job(crawl_job_id: int, project_id: int, background_tasks=None) -> str:
    """
    Dispatches a crawl job via Celery worker if enabled and reachable.
    Gracefully falls back to in-process FastAPI BackgroundTasks if Redis is
    offline or USE_CELERY is False.
    """
    if settings.USE_CELERY:
        try:
            crawl_website_task.delay(crawl_job_id, project_id)
            return "celery"
        except Exception as e:
            logger.warning(f"Celery dispatch failed ({e}). Falling back to BackgroundTasks.")

    if background_tasks is not None:
        background_tasks.add_task(run_crawler_job, crawl_job_id, project_id)
        return "background_tasks"

    # Synchronous execution fallback (e.g. inside tests or scripts)
    run_crawler_job(crawl_job_id, project_id)
    return "direct"


@celery_app.task(bind=True)
def process_scheduled_scans(self):
    from datetime import datetime, timezone, timedelta
    from app.core.database import SessionLocal
    from app.models.scheduled_scan import ScheduledScan
    from app.models.project import Project
    from app.models.crawl_job import CrawlJob
    
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # Initialize next_run_at for any scans that are missing it
        uninitialized_scans = db.query(ScheduledScan).filter(
            ScheduledScan.is_active == True,
            ScheduledScan.next_run_at == None
        ).all()
        for scan in uninitialized_scans:
            scan.next_run_at = now  # Run immediately
        db.commit()

        scans = db.query(ScheduledScan).filter(
            ScheduledScan.is_active == True,
            ScheduledScan.next_run_at <= now
        ).all()
        
        for scan in scans:
            project = db.query(Project).filter(Project.id == scan.project_id).first()
            if not project:
                continue
                
            # Create a crawl job
            job = CrawlJob(
                project_id=project.id,
                status="pending",
                total_urls=0,
                processed_urls=0
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            
            # Dispatch
            dispatch_crawl_job(job.id, project.id)
            
            # Update last run and next run
            scan.last_run_at = now
            
            # Calculate next run
            try:
                hour, minute = map(int, scan.time_of_day.split(':'))
            except ValueError:
                hour, minute = 0, 0
                
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                if scan.frequency == 'daily':
                    next_run += timedelta(days=1)
                elif scan.frequency == 'weekly':
                    while next_run <= now or (scan.day_of_week is not None and next_run.weekday() != scan.day_of_week):
                        next_run += timedelta(days=1)
                elif scan.frequency == 'monthly':
                    while next_run <= now or (scan.day_of_month is not None and next_run.day != scan.day_of_month):
                        next_run += timedelta(days=1)
                        
            scan.next_run_at = next_run
            db.commit()
    except Exception as e:
        logger.error(f"Error processing scheduled scans: {e}")
    finally:
        db.close()
