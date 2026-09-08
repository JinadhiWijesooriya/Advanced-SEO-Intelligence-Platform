import json
import time
import urllib.robotparser
from datetime import datetime, timezone
from typing import Set, Tuple, List, Optional
from urllib.parse import urlparse, urljoin, urlunparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.core.ssrf import validate_target_url
from app.models.project import Project
from app.models.crawl_job import CrawlJob
from app.models.page import Page
from app.models.link import Link
from app.models.image import Image
from app.models.crawl_task import CrawlTask
from app.services.analyzers.engine import SEOAnalyzerEngine


def normalize_url(url: str) -> str:
    """Normalize URL by stripping whitespace, trailing fragments, and standardizing path."""
    url = url.strip()
    parsed = urlparse(url)
    # Remove fragment (#...)
    normalized_path = parsed.path if parsed.path else "/"
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        normalized_path,
        parsed.params,
        parsed.query,
        ""  # fragment removed
    ))
    return normalized


def is_same_domain(base_url: str, target_url: str) -> bool:
    """Check if target_url belongs to the same domain / hostname as base_url."""
    base_host = urlparse(base_url).hostname or ""
    target_host = urlparse(target_url).hostname or ""
    
    base_host = base_host.lower().lstrip("www.")
    target_host = target_host.lower().lstrip("www.")
    return base_host == target_host


def is_crawlable_media_url(url: str) -> bool:
    """Return False if URL clearly points to non-HTML static file asset."""
    ignored_extensions = (
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf",
        ".zip", ".tar", ".gz", ".mp3", ".mp4", ".avi", ".css", ".js", ".json", ".xml", ".txt"
    )
    parsed = urlparse(url)
    path = parsed.path.lower()
    return not any(path.endswith(ext) for ext in ignored_extensions)


class WebCrawlerService:
    def __init__(self, db: Session, crawl_job: CrawlJob):
        self.db = db
        self.crawl_job = crawl_job
        self.project: Project = crawl_job.project
        self.robot_parser: Optional[urllib.robotparser.RobotFileParser] = None

        # User-agent configuration
        self.user_agent = self.project.custom_user_agent or "SEOIntelligenceBot/1.0"
        self.headers = {"User-Agent": self.user_agent}

    def init_robots_txt(self):
        """Fetch and parse target site robots.txt if enabled."""
        if not self.project.respect_robots_txt:
            return
        
        parsed_root = urlparse(self.project.target_url)
        robots_url = f"{parsed_root.scheme}://{parsed_root.netloc}/robots.txt"
        
        try:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            self.robot_parser = rp
        except Exception:
            self.robot_parser = None

    def is_url_allowed_by_robots(self, url: str) -> bool:
        if not self.project.respect_robots_txt or not self.robot_parser:
            return True
        try:
            return self.robot_parser.can_fetch(self.user_agent, url)
        except Exception:
            return True

    def run_crawl(self):
        """Execute the breadth-first crawl job loop."""
        self.crawl_job.status = "running"
        self.crawl_job.started_at = datetime.now(timezone.utc)
        self.db.commit()

        self.init_robots_txt()

        start_url = normalize_url(self.project.target_url)
        visited_urls: Set[str] = set()
        queue: List[Tuple[str, int]] = [(start_url, 0)]  # (url, depth)

        # Record initial root crawl task
        start_task = (
            self.db.query(CrawlTask)
            .filter_by(crawl_job_id=self.crawl_job.id, url=start_url)
            .first()
        )
        if not start_task:
            self.db.add(
                CrawlTask(
                    crawl_job_id=self.crawl_job.id,
                    url=start_url,
                    status="pending",
                    attempts=0,
                )
            )
            self.db.commit()

        max_pages = self.project.max_crawl_pages or 100
        max_depth = self.project.max_crawl_depth or 3

        processed_count = 0
        failed_count = 0

        # HTTP client with timeout and follow redirects
        with httpx.Client(headers=self.headers, timeout=10.0, follow_redirects=True) as client:
            while queue and processed_count < max_pages:
                # Check if job cancellation/stop requested in DB
                self.db.refresh(self.crawl_job)
                if self.crawl_job.status == "stopped":
                    break

                current_url, depth = queue.pop(0)

                if current_url in visited_urls:
                    continue

                visited_urls.add(current_url)

                # Track active CrawlTask
                current_task = (
                    self.db.query(CrawlTask)
                    .filter_by(crawl_job_id=self.crawl_job.id, url=current_url)
                    .first()
                )
                if not current_task:
                    current_task = CrawlTask(
                        crawl_job_id=self.crawl_job.id,
                        url=current_url,
                    )
                    self.db.add(current_task)
                current_task.status = "in_progress"
                current_task.attempts += 1
                self.db.commit()

                # Security check (SSRF)
                try:
                    validate_target_url(current_url)
                except ValueError as ssrf_err:
                    failed_count += 1
                    current_task.status = "failed"
                    current_task.error_message = f"SSRF Check Failed: {str(ssrf_err)[:300]}"
                    self.db.commit()
                    continue

                # Robots.txt compliance check
                if not self.is_url_allowed_by_robots(current_url):
                    current_task.status = "failed"
                    current_task.error_message = "Disallowed by robots.txt"
                    self.db.commit()
                    continue

                start_time = time.time()
                try:
                    response = client.get(current_url)
                    response_time_ms = int((time.time() - start_time) * 1000)
                    status_code = response.status_code
                    content_type = response.headers.get("content-type", "")

                    if "text/html" not in content_type.lower() and response.status_code == 200:
                        # Non-HTML page (e.g. raw file), store basic page info and continue
                        page_record = Page(
                            project_id=self.project.id,
                            crawl_job_id=self.crawl_job.id,
                            url=current_url,
                            status_code=status_code,
                            depth=depth,
                            content_type=content_type[:100],
                            response_time_ms=response_time_ms,
                        )
                        self.db.add(page_record)
                        current_task.status = "completed"
                        processed_count += 1
                        continue

                    # Parse HTML
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Title
                    title_elem = soup.find("title")
                    title = title_elem.get_text(strip=True) if title_elem else None

                    # Meta Description
                    meta_desc_elem = soup.find("meta", attrs={"name": "description"})
                    meta_desc = meta_desc_elem.get("content", "").strip() if meta_desc_elem else None

                    # Canonical URL
                    canonical_elem = soup.find("link", attrs={"rel": "canonical"})
                    canonical_url = canonical_elem.get("href", "").strip() if canonical_elem else None

                    # H1 Headings
                    h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all("h1") if h1.get_text(strip=True)]
                    h1_json = json.dumps(h1_tags) if h1_tags else None

                    # Word count calculation from visible body text
                    body = soup.find("body")
                    if body:
                        # Remove script/style tags
                        for s in body(["script", "style", "noscript"]):
                            s.extract()
                        text = body.get_text(separator=" ", strip=True)
                        word_count = len(text.split())
                    else:
                        word_count = 0

                    page_record = Page(
                        project_id=self.project.id,
                        crawl_job_id=self.crawl_job.id,
                        url=current_url,
                        status_code=status_code,
                        title=title[:512] if title else None,
                        meta_description=meta_desc,
                        canonical_url=canonical_url[:1024] if canonical_url else None,
                        h1_tags=h1_json,
                        word_count=word_count,
                        response_time_ms=response_time_ms,
                        depth=depth,
                        content_type=content_type[:100],
                    )
                    self.db.add(page_record)
                    self.db.flush()  # obtain page_record.id

                    # Extract Links & queue internal URLs if within max_depth
                    for a_tag in soup.find_all("a", href=True):
                        raw_href = a_tag["href"].strip()
                        if not raw_href or raw_href.startswith(("javascript:", "mailto:", "tel:", "#")):
                            continue

                        absolute_target = normalize_url(urljoin(current_url, raw_href))
                        is_internal = is_same_domain(self.project.target_url, absolute_target)
                        link_type = "internal" if is_internal else "external"
                        anchor_text = a_tag.get_text(strip=True)[:500]

                        link_record = Link(
                            page_id=page_record.id,
                            source_url=current_url,
                            target_url=absolute_target[:1024],
                            link_type=link_type,
                            anchor_text=anchor_text if anchor_text else None,
                        )
                        self.db.add(link_record)

                        # Queue internal links for crawling if depth permits
                        if is_internal and depth < max_depth and absolute_target not in visited_urls:
                            if is_crawlable_media_url(absolute_target):
                                if absolute_target not in [u for u, _ in queue]:
                                    queue.append((absolute_target, depth + 1))
                                    existing_subtask = (
                                        self.db.query(CrawlTask)
                                        .filter_by(crawl_job_id=self.crawl_job.id, url=absolute_target)
                                        .first()
                                    )
                                    if not existing_subtask:
                                        self.db.add(
                                            CrawlTask(
                                                crawl_job_id=self.crawl_job.id,
                                                url=absolute_target,
                                                status="pending",
                                                attempts=0,
                                            )
                                        )

                    # Extract Images
                    for img_tag in soup.find_all("img", src=True):
                        raw_src = img_tag["src"].strip()
                        if not raw_src:
                            continue
                        img_url = urljoin(current_url, raw_src)
                        alt_text = img_tag.get("alt", None)
                        has_alt = bool(alt_text and alt_text.strip())

                        img_record = Image(
                            page_id=page_record.id,
                            url=img_url[:1024],
                            alt_text=alt_text.strip() if has_alt else None,
                            has_alt=has_alt,
                        )
                        self.db.add(img_record)

                    current_task.status = "completed"
                    processed_count += 1

                except Exception as e:
                    failed_count += 1
                    current_task.status = "failed"
                    current_task.error_message = str(e)[:400]
                    # Record page with 0 status code or error
                    page_record = Page(
                        project_id=self.project.id,
                        crawl_job_id=self.crawl_job.id,
                        url=current_url,
                        status_code=0,
                        depth=depth,
                        response_time_ms=int((time.time() - start_time) * 1000),
                    )
                    self.db.add(page_record)

                # Periodically update crawl job stats in DB
                self.crawl_job.processed_urls = processed_count
                self.crawl_job.failed_urls = failed_count
                self.crawl_job.total_urls = len(visited_urls) + len(queue)
                self.db.commit()

        # Update final job state
        if self.crawl_job.status != "stopped":
            self.crawl_job.status = "completed"
        self.crawl_job.completed_at = datetime.now(timezone.utc)
        self.crawl_job.processed_urls = processed_count
        self.crawl_job.failed_urls = failed_count
        self.crawl_job.total_urls = processed_count + failed_count
        self.db.commit()

        # Run the SEO Analyzer Engine automatically upon crawl completion
        if self.crawl_job.status == "completed":
            try:
                engine = SEOAnalyzerEngine(db=self.db)
                engine.run_for_crawl_job(self.crawl_job)
            except Exception as analysis_err:
                # Never let analysis failure crash the crawl record
                print(f"[SEOAnalyzerEngine] Error during analysis: {analysis_err}")


def run_crawler_job(crawl_job_id: int, project_id: Optional[int] = None):
    """Entry point for Celery workers and BackgroundTasks to execute a crawl."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(CrawlJob).filter(CrawlJob.id == crawl_job_id).first()
        if job:
            crawler = WebCrawlerService(db, job)
            crawler.run_crawl()
    except Exception as e:
        job = db.query(CrawlJob).filter(CrawlJob.id == crawl_job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()
