from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router
from app.middleware.logging_middleware import RequestLoggingMiddleware

# Initialise structured logging before anything else
setup_logging()

# Create database tables automatically for initial SQLite setup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description=(
        "Advanced SEO Intelligence Platform API — Production-grade full-stack SEO audit, "
        "monitoring & crawling engine with AI-powered recommendations."
    ),
)

# Request / response logging middleware (Phase 10)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }


@app.get("/api/health", tags=["Health"])
def health_alias():
    """Alias for top-level health check endpoint."""
    from app.api.v1.endpoints.health import check_health
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        return check_health(db=db)
    finally:
        db.close()

