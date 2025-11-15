from fastapi import APIRouter, Depends, status
from loguru import logger

from interface.api.dependencies import get_survey_service, require_manager
from interface.api.exceptions import handle_result
from interface.api.schemas.survey import (
    AddQuestionRequest,
    UpdateQuestionRequest,
    ReorderQuestionsRequest
)
from interface.api.schemas.common import IdResponse, MessageResponse
from application.survey_service import SurveyService
from domain.entities.user import User
from domain.value_objects.types import QuestionType


router = APIRouter(prefix="/questions", tags=["질문 관리"])


@router.post(
    "/surveys/{survey_id}/questions",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
    summary="질문 추가",
    description="설문에 새로운 질문을 추가합니다."
)
async def add_question(
    survey_id: str,
    request: AddQuestionRequest,
    current_user: User = Depends(require_manager()),
    service: SurveyService = Depends(get_survey_service)
) -> IdResponse:
    """질문을 추가합니다."""
    logger.info(f"질문 추가 요청: survey_id={survey_id}, user_id={current_user.id}")

    result = service.add_question(
        user=current_user,
        survey_id=survey_id,
        text=request.text,
        question_type=QuestionType[request.question_type],
        options=request.options
    )
    question_id = handle_result(result)

    logger.info(f"질문 추가 성공: question_id={question_id}")
    return IdResponse(id=question_id, message="질문이 추가되었습니다")


@router.put(
    "/{question_id}",
    response_model=MessageResponse,
    summary="질문 수정"
)
async def update_question(
    question_id: str,
    request: UpdateQuestionRequest,
    current_user: User = Depends(require_manager()),
    service: SurveyService = Depends(get_survey_service)
) -> MessageResponse:
    """질문을 수정합니다."""
    logger.info(f"질문 수정 요청: question_id={question_id}")

    result = service.update_question(
        user=current_user,
        question_id=question_id,
        text=request.text,
        question_type=QuestionType[request.question_type] if request.question_type else None,
        options=request.options,
        is_required=request.is_required,
        category_id=request.category_id
    )
    handle_result(result)

    logger.info(f"질문 수정 성공: question_id={question_id}")
    return MessageResponse(message="질문이 수정되었습니다")


@router.delete(
    "/{question_id}",
    response_model=MessageResponse,
    summary="질문 삭제"
)
async def delete_question(
    question_id: str,
    current_user: User = Depends(require_manager()),
    service: SurveyService = Depends(get_survey_service)
) -> MessageResponse:
    """질문을 삭제합니다."""
    logger.info(f"질문 삭제 요청: question_id={question_id}")

    result = service.delete_question(current_user, question_id)
    handle_result(result)

    logger.info(f"질문 삭제 성공: question_id={question_id}")
    return MessageResponse(message="질문이 삭제되었습니다")


@router.post(
    "/{question_id}/move-up",
    response_model=MessageResponse,
    summary="질문 순서 올리기"
)
async def move_question_up(
    question_id: str,
    current_user: User = Depends(require_manager()),
    service: SurveyService = Depends(get_survey_service)
) -> MessageResponse:
    """질문 순서를 위로 이동합니다."""
    result = service.move_question_up(current_user, question_id)
    handle_result(result)
    return MessageResponse(message="질문 순서가 변경되었습니다")


@router.post(
    "/{question_id}/move-down",
    response_model=MessageResponse,
    summary="질문 순서 내리기"
)
async def move_question_down(
    question_id: str,
    current_user: User = Depends(require_manager()),
    service: SurveyService = Depends(get_survey_service)
) -> MessageResponse:
    """질문 순서를 아래로 이동합니다."""
    result = service.move_question_down(current_user, question_id)
    handle_result(result)
    return MessageResponse(message="질문 순서가 변경되었습니다")
