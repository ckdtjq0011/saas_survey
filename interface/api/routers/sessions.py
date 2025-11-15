from datetime import datetime
from fastapi import APIRouter, Depends, status
from loguru import logger

from interface.api.dependencies import get_survey_session_service, get_current_user
from interface.api.exceptions import handle_result
from interface.api.schemas.session import (
    SurveySessionCreate,
    SurveySessionResponse,
    SurveySessionListResponse,
    CompleteSurveySessionResponse
)
from application.survey_session_service import SurveySessionService
from domain.entities.user import User


router = APIRouter(prefix="/sessions", tags=["세션 관리"])


@router.post(
    "/surveys/{survey_id}/sessions",
    response_model=SurveySessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="응답 세션 시작"
)
async def create_session(
    survey_id: str,
    request: SurveySessionCreate,
    current_user: User = Depends(get_current_user),
    service: SurveySessionService = Depends(get_survey_session_service)
) -> SurveySessionResponse:
    """응답 세션을 시작합니다."""
    logger.info(f"세션 시작 요청: survey_id={survey_id}, respondent={request.respondent_id}")

    result = service.start_session(survey_id, request.respondent_id)
    session = handle_result(result)

    return SurveySessionResponse(
        id=session.id,
        survey_id=session.survey_id,
        respondent_id=session.respondent_id,
        started_at=session.started_at,
        completed_at=session.completed_at,
        is_completed=session.is_completed
    )


@router.get(
    "/{session_id}",
    response_model=SurveySessionResponse,
    summary="세션 조회"
)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: SurveySessionService = Depends(get_survey_session_service)
) -> SurveySessionResponse:
    """세션을 조회합니다."""
    result = service.get_session(session_id)
    session = handle_result(result)

    return SurveySessionResponse(
        id=session.id,
        survey_id=session.survey_id,
        respondent_id=session.respondent_id,
        started_at=session.started_at,
        completed_at=session.completed_at,
        is_completed=session.is_completed
    )


@router.put(
    "/{session_id}/complete",
    response_model=CompleteSurveySessionResponse,
    summary="세션 완료"
)
async def complete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: SurveySessionService = Depends(get_survey_session_service)
) -> CompleteSurveySessionResponse:
    """세션을 완료합니다."""
    result = service.complete_session(session_id)
    handle_result(result)

    return CompleteSurveySessionResponse(
        session_id=session_id,
        completed_at=datetime.now(),
        message="설문 응답이 완료되었습니다"
    )


@router.get(
    "/surveys/{survey_id}/sessions",
    response_model=SurveySessionListResponse,
    summary="세션 목록 조회"
)
async def list_sessions(
    survey_id: str,
    current_user: User = Depends(get_current_user),
    service: SurveySessionService = Depends(get_survey_session_service)
) -> SurveySessionListResponse:
    """세션 목록을 조회합니다."""
    result = service.get_sessions_by_survey(survey_id)
    sessions = handle_result(result)

    completed = sum(1 for s in sessions if s.is_completed)
    in_progress = len(sessions) - completed

    return SurveySessionListResponse(
        sessions=[
            SurveySessionResponse(
                id=s.id,
                survey_id=s.survey_id,
                respondent_id=s.respondent_id,
                started_at=s.started_at,
                completed_at=s.completed_at,
                is_completed=s.is_completed
            )
            for s in sessions
        ],
        total=len(sessions),
        completed=completed,
        in_progress=in_progress
    )
