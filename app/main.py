from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.startup import initialize_app
from app.db.base import engine, Base
from app.api import forms, users, responses, surveys, survey_responses, auth, export

# Initialize application (validate configuration, etc.)
initialize_app()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
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

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(forms.router, prefix=f"{settings.API_V1_STR}/forms", tags=["forms"])
app.include_router(responses.router, prefix=f"{settings.API_V1_STR}/responses", tags=["responses"])
app.include_router(export.router, prefix="/export", tags=["export"])

# Public test endpoints (simplified API)
app.include_router(surveys.router, prefix="/surveys", tags=["surveys"])
app.include_router(survey_responses.router, prefix="/responses", tags=["survey_responses"])


@app.get("/")
def root():
    return {"message": "Welcome to SaaS Survey API", "version": settings.VERSION}


@app.get("/health")
def health_check():
    return {"status": "healthy"}