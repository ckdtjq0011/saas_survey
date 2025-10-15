from fastapi import APIRouter, Depends, HTTPException, status
from application.response_service import ResponseService
from interface.api.dependencies import get_response_service
from interface.api.schemas.response import (
    SubmitResponseRequest,
    SubmitResponseResponse,
    SurveyResultsResponse,
    QuestionResultResponse,
)


router = APIRouter(prefix="/surveys", tags=["responses"])


@router.post(
    "/{survey_id}/responses",
    response_model=SubmitResponseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="응답 제출",
    description="""
    설문에 대한 응답을 제출합니다.

    하나의 응답자가 설문의 모든 질문에 대한 답변을 한 번에 제출합니다.
    answers 객체의 키는 question_id, 값은 답변 내용입니다.

    **요청 예시:**
    ```json
    {
        "respondent_id": "patient_001",
        "answers": {
            "question-uuid-1": "5",
            "question-uuid-2": "의료진",
            "question-uuid-3": "매우 만족했습니다"
        }
    }
    ```

    **답변 형식:**
    - rating 유형: "1", "2", "3", "4", "5" (문자열)
    - choice 유형: 선택지 중 하나 (예: "의료진")
    - text 유형: 자유 텍스트 (예: "서비스가 좋았습니다")

    **응답 예시:**
    ```json
    {
        "message": "응답이 제출되었습니다",
        "respondent_id": "patient_001"
    }
    ```

    **에러:**
    - 404: 설문을 찾을 수 없음
    """
)
def submit_response(
    survey_id: str,
    request: SubmitResponseRequest,
    service: ResponseService = Depends(get_response_service)
) -> SubmitResponseResponse:
    """응답을 제출합니다.

    Args:
        survey_id: 설문 ID
        request: 응답 제출 요청
        service: 응답 서비스

    Returns:
        응답 제출 응답

    Raises:
        HTTPException: 설문을 찾을 수 없거나 응답 제출 실패 시
    """
    try:
        service.submit_response(survey_id, request.respondent_id, request.answers)
        return SubmitResponseResponse(respondent_id=request.respondent_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"응답 제출 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/{survey_id}/results",
    response_model=SurveyResultsResponse,
    summary="설문 결과 조회",
    description="""
    설문의 응답 결과를 통계로 조회합니다.

    각 질문 유형별로 다른 형식의 통계가 제공됩니다:
    - **rating**: 평균 평점과 응답 수
    - **choice**: 선택지별 응답 분포
    - **text**: 모든 텍스트 응답 목록

    **응답 예시:**
    ```json
    {
        "survey_id": "uuid-format-id",
        "results": {
            "question-uuid-1": {
                "question": "서비스에 만족하십니까?",
                "type": "rating",
                "count": 10,
                "average": 4.5,
                "distribution": null,
                "answers": null
            },
            "question-uuid-2": {
                "question": "가장 좋았던 점은?",
                "type": "choice",
                "count": 10,
                "average": null,
                "distribution": {
                    "의료진": 5,
                    "시설": 3,
                    "대기시간": 2
                },
                "answers": null
            },
            "question-uuid-3": {
                "question": "개선 사항을 작성해주세요",
                "type": "text",
                "count": 10,
                "average": null,
                "distribution": null,
                "answers": [
                    "대기 시간 단축 필요",
                    "주차 공간 확충",
                    "매우 만족합니다"
                ]
            }
        }
    }
    ```

    **에러:**
    - 404: 설문을 찾을 수 없음
    """
)
def get_survey_results(
    survey_id: str,
    service: ResponseService = Depends(get_response_service)
) -> SurveyResultsResponse:
    """설문 결과를 조회합니다.

    Args:
        survey_id: 설문 ID
        service: 응답 서비스

    Returns:
        설문 결과 응답

    Raises:
        HTTPException: 설문을 찾을 수 없거나 결과 조회 실패 시
    """
    try:
        results = service.get_survey_results(survey_id)
        formatted_results = {}
        for question_id, result in results.items():
            formatted_results[question_id] = QuestionResultResponse(
                question=result["question"],
                type=result["type"],
                count=result["count"],
                average=result.get("average"),
                distribution=result.get("distribution"),
                answers=result.get("answers")
            )
        return SurveyResultsResponse(survey_id=survey_id, results=formatted_results)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"결과 조회 중 오류가 발생했습니다: {str(e)}"
        )
