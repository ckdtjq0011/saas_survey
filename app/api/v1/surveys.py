"""
Survey API endpoints v1.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.models.form import Form
from app.schemas.form import FormCreate, FormUpdate, Form as FormSchema
from app.api.dependencies import get_survey_service, get_current_user_optional, get_current_user
from app.services import SurveyService
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=FormSchema)
async def create_survey(
    survey_data: FormCreate,
    current_user: User = Depends(get_current_user),
    survey_service: SurveyService = Depends(get_survey_service)
) -> Form:
    """Create a new survey."""
    questions = [q.dict() for q in survey_data.questions] if survey_data.questions else []
    
    return survey_service.create_survey(
        title=survey_data.title,
        description=survey_data.description,
        owner_id=current_user.id,
        questions=questions,
        is_active=survey_data.is_active,
        is_public=survey_data.is_public,
        accepts_responses=survey_data.accepts_responses,
        requires_login=survey_data.requires_login,
        limit_one_response=survey_data.limit_one_response,
        show_progress_bar=survey_data.show_progress_bar,
        shuffle_questions=survey_data.shuffle_questions,
        confirmation_message=survey_data.confirmation_message
    )


@router.get("/", response_model=List[FormSchema])
async def list_surveys(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    my_surveys_only: bool = Query(False),
    current_user: Optional[User] = Depends(get_current_user_optional),
    survey_service: SurveyService = Depends(get_survey_service)
) -> List[Form]:
    """List surveys."""
    user_id = current_user.id if current_user else None
    
    return survey_service.list_surveys(
        user_id=user_id,
        my_surveys_only=my_surveys_only,
        skip=skip,
        limit=limit
    )


@router.get("/{survey_id}", response_model=FormSchema)
async def get_survey(
    survey_id: int,
    survey_service: SurveyService = Depends(get_survey_service)
) -> Form:
    """Get a survey by ID."""
    return survey_service.get_survey(survey_id)


@router.get("/s/{share_token}", response_model=FormSchema)
async def get_survey_by_token(
    share_token: str,
    survey_service: SurveyService = Depends(get_survey_service)
) -> Form:
    """Get a survey by share token."""
    return survey_service.get_survey_by_token(share_token)


@router.put("/{survey_id}", response_model=FormSchema)
async def update_survey(
    survey_id: int,
    survey_update: FormUpdate,
    current_user: User = Depends(get_current_user),
    survey_service: SurveyService = Depends(get_survey_service)
) -> Form:
    """Update a survey."""
    update_data = survey_update.dict(exclude_unset=True)
    
    return survey_service.update_survey(
        survey_id=survey_id,
        user_id=current_user.id,
        **update_data
    )


@router.delete("/{survey_id}")
async def delete_survey(
    survey_id: int,
    current_user: User = Depends(get_current_user),
    survey_service: SurveyService = Depends(get_survey_service)
):
    """Delete a survey."""
    survey_service.delete_survey(survey_id, current_user.id)
    return {"message": "Survey deleted successfully"}


@router.post("/{survey_id}/duplicate", response_model=FormSchema)
async def duplicate_survey(
    survey_id: int,
    current_user: User = Depends(get_current_user),
    survey_service: SurveyService = Depends(get_survey_service)
) -> Form:
    """Duplicate a survey."""
    return survey_service.duplicate_survey(survey_id, current_user.id)


@router.get("/{survey_id}/statistics")
async def get_survey_statistics(
    survey_id: int,
    current_user: User = Depends(get_current_user),
    survey_service: SurveyService = Depends(get_survey_service)
):
    """Get survey statistics."""
    return survey_service.get_survey_statistics(survey_id, current_user.id)