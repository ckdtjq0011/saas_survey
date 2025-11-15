from fastapi import APIRouter, Depends, Response
from loguru import logger

from interface.api.dependencies import get_response_service, require_manager
from interface.api.exceptions import handle_result
from interface.api.schemas.response import SurveyResultsResponse, QuestionResultResponse
from application.response_service import ResponseService
from domain.entities.user import User


router = APIRouter(prefix="/results", tags=["결과/통계"])


@router.get(
    "/surveys/{survey_id}/results",
    response_model=SurveyResultsResponse,
    summary="설문 결과 조회"
)
async def get_survey_results(
    survey_id: str,
    current_user: User = Depends(require_manager()),
    service: ResponseService = Depends(get_response_service)
) -> SurveyResultsResponse:
    """설문 결과를 조회합니다."""
    logger.info(f"결과 조회 요청: survey_id={survey_id}")

    results = service.get_survey_results(survey_id)

    return SurveyResultsResponse(
        survey_id=survey_id,
        results={
            qid: QuestionResultResponse(
                question=res["question"],
                type=res["type"],
                count=res["count"],
                average=res.get("average"),
                distribution=res.get("distribution"),
                answers=res.get("answers")
            )
            for qid, res in results.items()
        }
    )


@router.get(
    "/surveys/{survey_id}/export/csv",
    summary="CSV 내보내기"
)
async def export_csv(
    survey_id: str,
    current_user: User = Depends(require_manager()),
    service: ResponseService = Depends(get_response_service)
) -> Response:
    """설문 결과를 CSV로 내보냅니다."""
    logger.info(f"CSV 내보내기 요청: survey_id={survey_id}")

    result = service.export_to_csv(survey_id)
    csv_path = handle_result(result)

    with open(csv_path, "r", encoding="utf-8") as f:
        csv_content = f.read()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=survey_{survey_id}_results.csv"}
    )
