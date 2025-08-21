"""
API v1 endpoints.
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .surveys import router as surveys_router
from .responses import router as responses_router
from .exports import router as exports_router

# Create main v1 router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(surveys_router, prefix="/surveys", tags=["surveys"])
api_router.include_router(responses_router, prefix="/responses", tags=["responses"])
api_router.include_router(exports_router, prefix="/exports", tags=["exports"])

__all__ = ["api_router"]