# 🚀 Advanced SEO Intelligence Platform

A full-stack, production-grade SEO analysis and intelligence platform built with **FastAPI**, **React**, and **Celery**. It crawls websites, analyzes on-page SEO factors, scores pages across multiple categories, tracks issues over time, and delivers actionable reports — all through a modern, responsive dashboard.

---

## 📸 Features at a Glance

- **Website Crawler** – Recursively crawls pages, extracting links, images, metadata, and content.
- **Multi-Category SEO Scoring** – Scores each page across 6 dimensions: Technical, On-Page, Content, Links, Performance, and Mobile.
- **Issue Tracker** – Detects and categorizes SEO issues by severity (Critical → Low) and tracks their lifecycle.
- **Audit Snapshots** – Captures point-in-time SEO health scores for historical trend analysis.
- **Competitor Analysis** – Monitor and compare SEO health, word counts, and issue distributions across competitors.
- **Scheduled Scans** – Automate recurring crawls (daily, weekly, monthly) using Celery Beat.
- **Report Generation** – Export executive-ready reports in PDF (with score cards and charts), CSV, and JSON formats.
- **In-App Notifications** – Real-time bell notification drawer for completed crawls and detected issues.
- **AI Intelligence Suite** – AI-generated SEO action plans powered by OpenAI GPT with intelligent heuristic fallback, plus comprehensive Content Gap analysis (thin content, missing H1, cannibalization clusters).
- **Structured Request Logging** – Production-grade structured logging with colored console outputs, response time telemetry, and HTTP middleware.
- **JWT Authentication** – Secure user registration, login, and session management with bcrypt hashing.

---

## 🏗️ Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Task Queue & Scheduler | [Celery](https://docs.celeryq.dev/) + [Redis](https://redis.io/) + Celery Beat |
| AI Intelligence | [OpenAI API](https://platform.openai.com/) + Heuristic Suggestion Engine |
| Auth | JWT via [PyJWT](https://pyjwt.readthedocs.io/) + [Passlib/bcrypt](https://passlib.readthedocs.io/) |
| Crawler | [HTTPX](https://www.python-httpx.org/) + [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) + [lxml](https://lxml.de/) |
| PDF Reports | [ReportLab](https://www.reportlab.com/) |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) |
| Testing | [pytest](https://pytest.org/) + [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) (105 tests) |
| Server | [Uvicorn](https://www.uvicorn.org/) |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | [React 19](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/) |
| Build Tool | [Vite](https://vite.dev/) |
| Styling | [Tailwind CSS v4](https://tailwindcss.com/) |
| Charts | [Recharts](https://recharts.org/) |
| Icons | [Lucide React](https://lucide.dev/) |
| HTTP Client | [Axios](https://axios-http.com/) |

---

## 📁 Project Structure

```
Advanced-SEO-Intelligence-Platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py          # Registration & login
│   │   │       │   ├── projects.py      # Project CRUD
│   │   │       │   ├── crawls.py        # Crawl job management
│   │   │       │   ├── issues.py        # SEO issue tracker
│   │   │       │   ├── seo.py           # Scoring & summaries
│   │   │       │   ├── snapshots.py     # Audit snapshots (Phase 8)
│   │   │       │   ├── competitors.py   # Competitor analysis (Phase 8)
│   │   │       │   ├── schedules.py     # Scheduled scans (Phase 8)
│   │   │       │   ├── reports.py       # PDF/CSV/JSON reports (Phase 9)
│   │   │       │   ├── notifications.py # Real-time alerts (Phase 9)
│   │   │       │   ├── ai.py            # AI Intelligence & content gaps (Phase 10)
│   │   │       │   └── health.py        # Health check
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py               # App settings & environment variables
│   │   │   ├── database.py             # DB session & engine
│   │   │   ├── logging_config.py       # Structured logging configuration
│   │   │   ├── security.py             # JWT & password hashing
│   │   │   └── ssrf.py                 # SSRF protection
│   │   ├── middleware/
│   │   │   └── logging_middleware.py   # Request timing & telemetry
│   │   ├── models/                     # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── crawl_job.py
│   │   │   ├── crawl_task.py
│   │   │   ├── page.py
│   │   │   ├── link.py
│   │   │   ├── image.py
│   │   │   ├── seo_issue.py
│   │   │   ├── seo_result.py
│   │   │   ├── audit_snapshot.py
│   │   │   ├── competitor.py
│   │   │   ├── scheduled_scan.py
│   │   │   ├── report.py
│   │   │   └── notification.py
│   │   ├── schemas/                    # Pydantic schemas
│   │   ├── services/
│   │   │   ├── crawler.py              # Core web crawler
│   │   │   ├── scoring_engine.py       # SEO scoring logic
│   │   │   ├── analyzers/             # Modular analyzers
│   │   │   │   ├── technical_analyzer.py
│   │   │   │   ├── onpage_analyzer.py
│   │   │   │   ├── content_analyzer.py
│   │   │   │   ├── link_analyzer.py
│   │   │   │   ├── image_analyzer.py
│   │   │   │   └── engine.py           # Orchestrates all analyzers
│   │   │   └── ai/                    # AI Intelligence services
│   │   │       ├── recommendation_engine.py
│   │   │       └── content_gap_analyzer.py
│   │   ├── workers/
│   │   │   ├── celery_app.py           # Celery + Beat periodic scheduler
│   │   │   └── tasks.py               # Background task definitions
│   │   └── main.py                    # FastAPI app entry point
│   ├── alembic/                       # DB migration scripts
│   ├── tests/                         # Full pytest test suite (105 tests)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/                  # Login & Register forms
│   │   │   ├── projects/              # Project list & modal
│   │   │   ├── crawl/                 # Crawl monitor UI
│   │   │   ├── dashboard/             # Project dashboard
│   │   │   ├── issues/                # Issue list
│   │   │   ├── pages/                 # Page list
│   │   │   ├── history/               # Historical snapshots & trends (Phase 8)
│   │   │   ├── competitors/           # Competitor benchmarking (Phase 8)
│   │   │   ├── schedule/              # Scan schedule configuration (Phase 8)
│   │   │   ├── reports/               # Report generation & exports (Phase 9)
│   │   │   ├── notifications/         # Notification bell & drawer (Phase 9)
│   │   │   └── ai/                    # AI Recommendations & Content Gaps (Phase 10)
│   │   ├── context/
│   │   │   └── AuthContext.tsx        # Global auth state
│   │   ├── services/
│   │   │   └── api.ts                 # Axios API client
│   │   ├── App.tsx                    # App layout, router & roadmap
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml                 # Development multi-container stack
├── docker-compose.prod.yml            # Production container stack
└── README.md
```

---

## ⚡ Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **Redis** (for Celery task queue)

---

### 1. Clone the Repository

```bash
git clone https://github.com/JinadhiWijesooriya/Advanced-SEO-Intelligence-Platform.git
cd Advanced-SEO-Intelligence-Platform
```

---

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env   # Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

### 3. Start the Celery Worker

In a **separate terminal** (with the venv activated):

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

> **Note:** Redis must be running on `localhost:6379` (default). Start it with `redis-server` or via Docker:
> ```bash
> docker run -d -p 6379:6379 redis:7-alpine
> ```

---

### 4. Start Celery Beat (Scheduled Scans)

In another terminal (with venv activated):

```bash
cd backend
celery -A app.workers.celery_app beat --loglevel=info
```

---

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

### 🐳 Full-Stack Docker Deployment

Run all services (API, Celery worker, Celery beat, Redis, Frontend) with a single command:

```bash
# Development (with source code mounts & hot reload)
docker compose up --build

# Production stack (optimized multi-stage builds & memory limits)
docker compose -f docker-compose.prod.yml up -d
```

---

## 🔑 Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./seo_platform.db

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI Intelligence (Phase 10 — Optional)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
AI_MAX_TOKENS=1000

# Structured Logging (Phase 10)
LOG_LEVEL=INFO
LOG_FORMAT=colored   # "colored" for terminal, "json" for production aggregators
```

---

## 🧪 Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_auth.py -v
```

---

## 📡 API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login and get JWT token |
| `GET` | `/api/v1/projects` | List all projects |
| `POST` | `/api/v1/projects` | Create a new project |
| `POST` | `/api/v1/projects/{id}/crawls` | Start a new crawl job |
| `GET` | `/api/v1/crawls/{id}/status` | Get crawl status & progress |
| `GET` | `/api/v1/projects/{id}/issues` | List SEO issues |
| `PATCH` | `/api/v1/issues/{id}` | Update issue status |
| `GET` | `/api/v1/projects/{id}/seo-summary` | Get aggregated SEO scores |
| `GET` | `/api/v1/projects/{id}/snapshots` | List audit snapshots (Phase 8) |
| `POST` | `/api/v1/projects/{id}/competitors` | Add competitor domain (Phase 8) |
| `GET` | `/api/v1/projects/{id}/competitors` | List competitors (Phase 8) |
| `POST` | `/api/v1/projects/{id}/schedule` | Set scan schedule (Phase 8) |
| `GET` | `/api/v1/projects/{id}/schedule` | Get scan schedule (Phase 8) |
| `POST` | `/api/v1/projects/{id}/reports` | Generate PDF/CSV/JSON report (Phase 9) |
| `GET` | `/api/v1/projects/{id}/reports` | List generated reports (Phase 9) |
| `GET` | `/api/v1/reports/{id}/download` | Download report file (Phase 9) |
| `GET` | `/api/v1/notifications` | List user notifications (Phase 9) |
| `PATCH` | `/api/v1/notifications/{id}/read` | Mark notification as read (Phase 9) |
| `GET` | `/api/v1/projects/{id}/ai/recommendations` | Get AI SEO action plan (Phase 10) |
| `POST` | `/api/v1/projects/{id}/ai/regenerate` | Re-analyze AI suggestions (Phase 10) |
| `GET` | `/api/v1/projects/{id}/ai/content-gaps` | Content gap & cannibalization analysis (Phase 10) |
| `GET` | `/api/v1/health` | Health check |

Full interactive API documentation available at `/docs` (Swagger UI) and `/redoc`.

---

## 🧠 SEO Scoring Model

Each crawled page is scored across **6 weighted categories**:

| Category | Weight | What it covers |
|----------|--------|---------------|
| Technical | 25% | HTTP status, redirects, canonical tags, robots.txt, sitemaps |
| On-Page | 25% | Title, meta description, heading structure, URL format |
| Content | 20% | Word count, keyword density, content quality signals |
| Links | 15% | Internal/external link ratios, broken links, anchor text |
| Performance | 10% | Page size, resource count, load hints |
| Mobile | 5% | Viewport meta, mobile-friendliness signals |

**Overall Score** = Weighted sum of all category scores (0–100).  
**Health Grade**: A (≥90) · B (≥80) · C (≥70) · D (≥60) · F (<60)

---

## 🔒 Security

- All passwords are hashed using **bcrypt**.
- API routes are protected with **JWT Bearer tokens**.
- **SSRF protection** is enforced on the crawler — private/internal IP ranges are blocked.
- Environment-based configuration — no secrets in source code.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 👤 Author

**Jinadhi Wijesooriya**  
GitHub: [@JinadhiWijesooriya](https://github.com/JinadhiWijesooriya)
