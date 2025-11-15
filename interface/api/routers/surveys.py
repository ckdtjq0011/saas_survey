from fastapi import APIRouter, Depends, status, Query
from loguru import logger

from interface.api.dependencies import (
    get_survey_service,
    get_current_user,
    require_manager
)
from interface.api.exceptions import handle_result
from interface.api.schemas.survey import (
    CreateSurveyRequest,
    UpdateSurveyRequest,
    SurveyResponse,
    SurveyListResponse,
    SurveyListItem,
    QuestionResponse
)
from interface.api.schemas.common import IdResponse, MessageResponse
from application.survey_service import SurveyService
from domain.entities.user import User


router = APIRouter(prefix="/surveys", tags=["설문 관리"])


@router.post(
    "",
    response_model=IdResponse,
    status_code=status.HTTP_201_CREATED,
    summary="설문 생성",
    description="새로운 설문을 생성합니다. SURVEY_MANAGER 또는 TENANT_ADMIN 권한이 필요합니다."
)
async def create_survey(
    request: CreateSurveyRequest,
    current_user: User = Depends(require_manager()),
    service: SurveyService = Depends(get_survey_service)
) -> IdResponse:
    """설문을 생성합니다.

    Args:
        request: 설문 생성 요청
        current_user: 현재 사용자
        service: 설문 서비스

    Returns:
        생성된 설문 ID
    """
    logger.info(
        f"설문 생성 요청: user_id={current_user.id}, title={request.title}"
    )

    result = service.create_survey(
        user=current_user,
        title=request.title,
        description=request.description
    )
    survey_id = handle_result(result)

    logger.info(f"설문 생성 성공: survey_id={survey_id}, owner={current_user.id}")

    return IdResponse(id=survey_id, message="설문이 생성되었습니다")


@router.get(
    "",
    response_model=SurveyListResponse,
    summary="설문 목록 조회",
    description="현재 사용자가 볼 수 있는 설문 목록을 조회합니다. 테넌트 내 설문만 조회됩니다."
)
async def list_surveys(
    search: str | None = Query(None, description="검색어 (제목, 설명)"),
    current_user: User = Depends(get_current_user),
    service: SurveyService = Depends(get_survey_service)
) -> SurveyListResponse:
    """설문 목록을 조회합니다.

    Args:
        search: 검색어 (옵션)
        current_user: 현재 사용자
        service: 설문 서비스

    Returns:
        설문 목록
    """
    logger.info(
        f"설문 목록 조회 요청: user_id={current_user.id}, search={search}"
    )

    surveys = service.get_surveys_by_user(current_user)

    if search:
        surveys = [
            s for s in surveys
            if search.lower() in s.title.lower() or search.lower() in s.description.lower()
        ]

    survey_items = [
        SurveyListItem(
            id=s.id,
            title=s.title,
            description=s.description,
            question_count=str(len(s.questions))
        )
        for s in surveys
    ]

    logger.info(
        f"설문 목록 조회 성공: user_id={current_user.id}, count={len(survey_items)}"
    )

    return SurveyListResponse(surveys=survey_items, total=len(survey_items))


@router.get(
    "/{survey_id}",
    response_model=SurveyResponse,
    summary="설문 상세 조회",
    description="특정 설문의 상세 정보를 조회합니다. 질문 목록이 포함됩니다."
)
async def get_survey(
    survey_id: str,
    current_user: User = Depends(get_current_user),
    service: SurveyService = Depends(get_survey_service)
) -> SurveyResponse:
    """설문 상세 정보를 조회합니다.

    Args:
        survey_id: 설문 ID
        current_user: 현재 사용자
        service: 설문 서비스

    Returns:
        설문 상세 정보
    """
    logger.info(
        f"설문 조회 요청: survey_id={survey_id}, user_id={current_user.id}"
    )

    result = service.get_survey(current_user, survey_id)
    survey = handle_result(result, not_found_msg="찾을 수 없")

    questions = [
        QuestionResponse(
            id=q.id,
            text=q.text,
            type=q.question_type.name,
            options=list(q.options) if q.options else []
        )
        for q in survey.questions
    ]

    logger.info(
        f"설문 조회 성공: survey_id={survey_id}, question_count={len(questions)}"
    )

    return SurveyResponse(
        id=survey.id,
        title=survey.title,
        description=survey.description,
        created_at=survey.created_at.isoformat(),
        questions=questions
    )


@router.put(
    "/{survey_id}",
    response_model=SurveyResponse,
    summary="설문 수정",
    description="설문의 제목과 설명을 수정합니다. 소유자만 수정 가능합니다."
)
async def update_survey(
    survey_id: str,
    request: UpdateSurveyRequest,
    current_user: User = Depends(require_manager()),
    service: SurveyService = Depends(get_survey_service)
) -> SurveyResponse:
    """설문을 수정합니다.

    Args:
        survey_id: 설문 ID
        request: 설문 수정 요청
        current_user: 현재 사용자
        service: 설문 서비스

    Returns:
        수정된 설문 정보
    """
    logger.info(
        f"설문 수정 요청: survey_id={survey_id}, user_id={current_user.id}"
    )

    result = service.get_survey(current_user, survey_id)
    survey = handle_result(result, not_found_msg="찾을 수 없")

    if request.title:
        survey.title = request.title
    if request.description:
        survey.description = request.description

    save_result = service.survey_repo.save(survey)
    updated_survey = handle_result(save_result)

    questions = [
        QuestionResponse(
            id=q.id,
            text=q.text,
            type=q.question_type.name,
            options=list(q.options) if q.options else []
        )
        for q in updated_survey.questions
    ]

    logger.info(f"설문 수정 성공: survey_id={survey_id}")

    return SurveyResponse(
        id=updated_survey.id,
        title=updated_survey.title,
        description=updated_survey.description,
        created_at=updated_survey.created_at.isoformat(),
        questions=questions
    )


@router.delete(
    "/{survey_id}",
    response_model=MessageResponse,
    summary="설문 삭제",
    description="설문을 삭제합니다. 소유자만 삭제 가능합니다."
)
async def delete_survey(
    survey_id: str,
    current_user: User = Depends(require_manager()),
    service: SurveyService = Depends(get_survey_service)
) -> MessageResponse:
    """설문을 삭제합니다.

    Args:
        survey_id: 설문 ID
        current_user: 현재 사용자
        service: 설문 서비스

    Returns:
        삭제 메시지
    """
    logger.info(
        f"설문 삭제 요청: survey_id={survey_id}, user_id={current_user.id}"
    )

    result = service.delete_survey(current_user, survey_id)
    handle_result(result, not_found_msg="찾을 수 없")

    logger.info(f"설문 삭제 성공: survey_id={survey_id}")

    return MessageResponse(message="설문이 삭제되었습니다")
