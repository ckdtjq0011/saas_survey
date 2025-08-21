"""
Response API endpoints v1.
"""
from typing import List
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.models.form import FormResponse
from app.schemas.form import FormResponseCreate, FormResponse as FormResponseSchema
from app.api.dependencies import get_response_service, get_current_user, get_current_user_optional
from app.services import ResponseService
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=FormResponseSchema)
async def submit_response(
    response_data: FormResponseCreate,
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    response_service: ResponseService = Depends(get_response_service)
) -> FormResponse:
    """Submit a response to a survey."""
    # Get client info
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Extract survey_id from the first answer or require it in the schema
    # For now, we'll require it to be passed separately
    survey_id = response_data.dict().get("form_id", None)
    if not survey_id:
        # Try to get from first answer's question
        raise ValueError("Survey ID is required")
    
    # Prepare answers
    answers = []
    for answer in response_data.answers:
        answer_dict = answer.dict()
        answers.append(answer_dict)
    
    return response_service.submit_response(
        survey_id=survey_id,
        answers=answers,
        respondent_email=response_data.respondent_email,
        respondent_id=current_user.id if current_user else None,
        ip_address=client_host,
        user_agent=user_agent
    )


@router.get("/{response_id}", response_model=FormResponseSchema)
async def get_response(
    response_id: int,
    current_user: User = Depends(get_current_user_optional),
    response_service: ResponseService = Depends(get_response_service)
) -> FormResponse:
    """Get a specific response."""
    user_id = current_user.id if current_user else None
    return response_service.get_response(response_id, user_id)


@router.get("/survey/{survey_id}", response_model=List[FormResponseSchema])
async def list_survey_responses(
    survey_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    response_service: ResponseService = Depends(get_response_service)
) -> List[FormResponse]:
    """List all responses for a survey (owner only)."""
    return response_service.list_survey_responses(
        survey_id=survey_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )


class ResponseUpdate(BaseModel):
    answers: List[dict]


@router.put("/{response_id}", response_model=FormResponseSchema)
async def update_response(
    response_id: int,
    response_update: ResponseUpdate,
    current_user: User = Depends(get_current_user),
    response_service: ResponseService = Depends(get_response_service)
) -> FormResponse:
    """Update a response (respondent only)."""
    return response_service.update_response(
        response_id=response_id,
        user_id=current_user.id,
        answers=response_update.answers
    )


@router.delete("/{response_id}")
async def delete_response(
    response_id: int,
    current_user: User = Depends(get_current_user),
    response_service: ResponseService = Depends(get_response_service)
):
    """Delete a response."""
    response_service.delete_response(response_id, current_user.id)
    return {"message": "Response deleted successfully"}