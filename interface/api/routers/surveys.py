from fastapi import APIRouter, Depends, HTTPException, status
from application.survey_service import SurveyService
from domain.value_objects.types import QuestionType
from interface.api.dependencies import get_survey_service
from interface.api.schemas.survey import (
    CreateSurveyRequest,
    CreateSurveyResponse,
    AddQuestionRequest,
    AddQuestionResponse,
    SurveyResponse,
    SurveyListResponse,
    SurveyListItem,
    QuestionResponse,
)


router = APIRouter(prefix="/surveys", tags=["surveys"])


@router.post(
    "",
    response_model=CreateSurveyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="설문 생성",
    description="""
    새로운 설문을 생성합니다.

    **요청 예시:**
    ```json
    {
        "title": "2024년 병원 만족도 조사",
        "description": "환자 경험 개선을 위한 설문입니다"
    }
    ```

    **응답 예시:**
    ```json
    {
        "survey_id": "uuid-format-id",
        "message": "설문이 생성되었습니다"
    }
    ```

    생성된 설문 ID는 질문 추가, 응답 제출 등에 사용됩니다.
    """
)
def create_survey(
    request: CreateSurveyRequest,
    service: SurveyService = Depends(get_survey_service)
) -> CreateSurveyResponse:
    """설문을 생성합니다.

    Args:
        request: 설문 생성 요청
        service: 설문 서비스

    Returns:
        설문 생성 응답

    Raises:
        HTTPException: 설문 생성 실패 시
    """
    try:
        survey_id = service.create_survey(request.title, request.description)
        return CreateSurveyResponse(survey_id=survey_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설문 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "",
    response_model=SurveyListResponse,
    summary="설문 목록 조회",
    description="""
    시스템에 등록된 모든 설문 목록을 조회합니다.

    **응답 예시:**
    ```json
    {
        "surveys": [
            {
                "id": "uuid-format-id",
                "title": "2024년 병원 만족도 조사",
                "description": "환자 경험 개선을 위한 설문입니다",
                "question_count": "3"
            }
        ],
        "total": 1
    }
    ```

    각 설문의 기본 정보와 질문 수를 확인할 수 있습니다.
    """
)
def list_surveys(
    service: SurveyService = Depends(get_survey_service)
) -> SurveyListResponse:
    """설문 목록을 조회합니다.

    Args:
        service: 설문 서비스

    Returns:
        설문 목록 응답

    Raises:
        HTTPException: 목록 조회 실패 시
    """
    try:
        surveys = service.get_all_surveys()
        survey_items = [
            SurveyListItem(
                id=s.id,
                title=s.title,
                description=s.description,
                question_count=str(len(s.questions))
            )
            for s in surveys
        ]
        return SurveyListResponse(surveys=survey_items, total=len(survey_items))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설문 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/{survey_id}",
    response_model=SurveyResponse,
    summary="설문 상세 조회",
    description="""
    특정 설문의 상세 정보를 조회합니다.

    설문의 기본 정보와 함께 모든 질문 목록을 포함합니다.
    각 질문의 유형(text/rating/choice)과 옵션 정보를 확인할 수 있습니다.

    **응답 예시:**
    ```json
    {
        "id": "uuid-format-id",
        "title": "병원 만족도 조사",
        "description": "환자 경험 개선을 위한 설문",
        "created_at": "2025-10-13T17:03:46.901022",
        "questions": [
            {
                "id": "question-uuid",
                "text": "서비스에 만족하십니까?",
                "type": "rating",
                "options": []
            },
            {
                "id": "question-uuid-2",
                "text": "가장 좋았던 점은?",
                "type": "choice",
                "options": ["의료진", "시설", "대기시간"]
            }
        ]
    }
    ```

    **에러:**
    - 404: 설문을 찾을 수 없음
    """
)
def get_survey(
    survey_id: str,
    service: SurveyService = Depends(get_survey_service)
) -> SurveyResponse:
    """설문 상세 정보를 조회합니다.

    Args:
        survey_id: 설문 ID
        service: 설문 서비스

    Returns:
        설문 상세 응답

    Raises:
        HTTPException: 설문을 찾을 수 없거나 조회 실패 시
    """
    try:
        survey = service.get_survey(survey_id)
        questions = [
            QuestionResponse(
                id=q.id,
                text=q.text,
                type=q.question_type.value,
                options=list(q.options) if q.options else []
            )
            for q in survey.questions
        ]
        return SurveyResponse(
            id=survey.id,
            title=survey.title,
            description=survey.description,
            created_at=survey.created_at.isoformat(),
            questions=questions
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설문 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post(
    "/{survey_id}/questions",
    response_model=AddQuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="질문 추가",
    description="""
    설문에 새로운 질문을 추가합니다.

    **질문 유형:**
    - `text`: 텍스트 답변 (자유 입력)
    - `rating`: 평점 답변 (1-5)
    - `choice`: 객관식 답변 (options 필수)

    **평점형 질문 예시:**
    ```json
    {
        "text": "서비스에 만족하십니까?",
        "question_type": "rating"
    }
    ```

    **객관식 질문 예시:**
    ```json
    {
        "text": "가장 좋았던 점은?",
        "question_type": "choice",
        "options": ["의료진", "시설", "대기시간", "진료"]
    }
    ```

    **텍스트형 질문 예시:**
    ```json
    {
        "text": "개선 사항을 작성해주세요",
        "question_type": "text"
    }
    ```

    **에러:**
    - 404: 설문을 찾을 수 없음
    - 422: 잘못된 question_type 또는 choice 유형인데 options 미제공
    """
)
def add_question(
    survey_id: str,
    request: AddQuestionRequest,
    service: SurveyService = Depends(get_survey_service)
) -> AddQuestionResponse:
    """설문에 질문을 추가합니다.

    Args:
        survey_id: 설문 ID
        request: 질문 추가 요청
        service: 설문 서비스

    Returns:
        질문 추가 응답

    Raises:
        HTTPException: 설문을 찾을 수 없거나 질문 추가 실패 시
    """
    try:
        question_type = QuestionType(request.question_type)
        question_id = service.add_question(
            survey_id,
            request.text,
            question_type,
            request.options
        )
        return AddQuestionResponse(question_id=question_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"질문 추가 중 오류가 발생했습니다: {str(e)}"
        )
