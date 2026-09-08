from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, projects, crawls, issues, seo, snapshots, competitors, schedules

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(crawls.router, tags=["Crawls & Pages"])
api_router.include_router(issues.router, tags=["SEO Issues"])
api_router.include_router(seo.router, tags=["SEO Scoring & Summary"])
api_router.include_router(snapshots.router, tags=["Historical Snapshots"])
api_router.include_router(competitors.router, tags=["Competitor Analysis"])
api_router.include_router(schedules.router, tags=["Scheduled Scans"])

