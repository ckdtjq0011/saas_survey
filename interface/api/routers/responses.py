from fastapi import APIRouter, Depends, status
from loguru import logger

from interface.api.dependencies import get_response_service, get_current_user
from interface.api.exceptions import handle_result
from interface.api.schemas.response import (
    SubmitResponseRequest,
    SubmitResponseResponse,
    UpdateResponseRequest,
    ResponseListResponse,
    ResponseDetailResponse,
    ResponseHistoryResponse
)
from application.response_service import ResponseService
from domain.entities.user import User


router = APIRouter(prefix="/responses", tags=["응답 관리"])


@router.post(
    "/surveys/{survey_id}/responses",
    response_model=SubmitResponseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="응답 제출"
)
async def submit_responses(
    survey_id: str,
    request: SubmitResponseRequest,
    current_user: User = Depends(get_current_user),
    service: ResponseService = Depends(get_response_service)
) -> SubmitResponseResponse:
    """설문 응답을 제출합니다."""
    logger.info(f"응답 제출 요청: survey_id={survey_id}, respondent={request.respondent_id}")

    result = service.submit_responses(
        survey_id=survey_id,
        respondent_id=request.respondent_id,
        answers=request.answers,
        session_id=request.session_id,
        time_spent_data=request.time_spent_data
    )
    handle_result(result)

    logger.info(f"응답 제출 성공: survey_id={survey_id}")
    return SubmitResponseResponse(
        message="응답이 제출되었습니다",
        respondent_id=request.respondent_id
    )


@router.get(
    "/surveys/{survey_id}/responses",
    response_model=ResponseListResponse,
    summary="응답 목록 조회"
)
async def list_responses(
    survey_id: str,
    current_user: User = Depends(get_current_user),
    service: ResponseService = Depends(get_response_service)
) -> ResponseListResponse:
    """설문의 모든 응답을 조회합니다."""
    result = service.response_repo.find_by_survey(survey_id)
    responses = handle_result(result)

    return ResponseListResponse(
        responses=[
            ResponseDetailResponse(
                id=r.id,
                survey_id=r.survey_id,
                question_id=r.question_id,
                answer=r.answer,
                respondent_id=r.respondent_id,
                answered_at=r.answered_at.isoformat(),
                session_id=r.session_id,
                time_spent_seconds=r.time_spent_seconds
            )
            for r in responses
        ],
        total=len(responses)
    )


@router.put(
    "/{response_id}",
    response_model=SubmitResponseResponse,
    summary="응답 수정"
)
async def update_response(
    response_id: str,
    request: UpdateResponseRequest,
    current_user: User = Depends(get_current_user),
    service: ResponseService = Depends(get_response_service)
) -> SubmitResponseResponse:
    """응답을 수정합니다."""
    result = service.update_response(
        response_id=response_id,
        new_answer=request.answer,
        modified_by=current_user.id
    )
    handle_result(result)

    return SubmitResponseResponse(
        message="응답이 수정되었습니다",
        respondent_id=current_user.id
    )


@router.get(
    "/{response_id}/history",
    response_model=list[ResponseHistoryResponse],
    summary="응답 수정 이력 조회"
)
async def get_response_history(
    response_id: str,
    current_user: User = Depends(get_current_user),
    service: ResponseService = Depends(get_response_service)
) -> list[ResponseHistoryResponse]:
    """응답 수정 이력을 조회합니다."""
    result = service.response_history_repo.find_by_response(response_id)
    histories = handle_result(result)

    return [
        ResponseHistoryResponse(
            id=h.id,
            response_id=h.response_id,
            old_answer=h.old_answer,
            new_answer=h.new_answer,
            modified_at=h.modified_at.isoformat(),
            modified_by=h.modified_by
        )
        for h in histories
    ]
