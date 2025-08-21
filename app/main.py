from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.startup import initialize_app
from app.db.base import engine, Base
from app.api.v1 import api_router

# Initialize application (validate configuration, etc.)
initialize_app()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Google Forms-like Survey Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Keep legacy endpoints for backward compatibility (optional)
# You can remove these once you've migrated all clients to v1
from app.api import surveys, survey_responses
app.include_router(surveys.router, prefix="/legacy/surveys", tags=["legacy"])
app.include_router(survey_responses.router, prefix="/legacy/responses", tags=["legacy"])


@app.get("/")
def root():
    return {
        "message": "Welcome to SaaS Survey API",
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.VERSION}