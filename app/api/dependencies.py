"""
Common dependencies for API endpoints.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.repositories import SurveyRepository, ResponseRepository, UserRepository
from app.services import SurveyService, ResponseService, AuthService, ExportService
from app.models.user import User

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Repository dependencies
def get_survey_repository(db: Session = Depends(get_db)) -> SurveyRepository:
    """Get survey repository instance."""
    return SurveyRepository(db)


def get_response_repository(db: Session = Depends(get_db)) -> ResponseRepository:
    """Get response repository instance."""
    return ResponseRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


# Service dependencies
def get_survey_service(
    survey_repo: SurveyRepository = Depends(get_survey_repository),
    response_repo: ResponseRepository = Depends(get_response_repository)
) -> SurveyService:
    """Get survey service instance."""
    return SurveyService(survey_repo, response_repo)


def get_response_service(
    survey_repo: SurveyRepository = Depends(get_survey_repository),
    response_repo: ResponseRepository = Depends(get_response_repository)
) -> ResponseService:
    """Get response service instance."""
    return ResponseService(survey_repo, response_repo)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """Get auth service instance."""
    return AuthService(user_repo)


def get_export_service(
    survey_repo: SurveyRepository = Depends(get_survey_repository),
    response_repo: ResponseRepository = Depends(get_response_repository)
) -> ExportService:
    """Get export service instance."""
    return ExportService(survey_repo, response_repo)


# Authentication dependencies
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user."""
    return auth_service.get_current_user(token)


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not token:
        return None
    try:
        return auth_service.get_current_user(token)
    except HTTPException:
        return None