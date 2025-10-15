from pathlib import Path
from application.survey_service import SurveyService
from application.response_service import ResponseService
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository


DATA_DIR = Path("data")


def get_survey_service() -> SurveyService:
    """SurveyService 인스턴스를 생성합니다.

    Returns:
        SurveyService 인스턴스
    """
    survey_repo = CsvSurveyRepository(DATA_DIR)
    return SurveyService(survey_repo)


def get_response_service() -> ResponseService:
    """ResponseService 인스턴스를 생성합니다.

    Returns:
        ResponseService 인스턴스
    """
    survey_repo = CsvSurveyRepository(DATA_DIR)
    response_repo = CsvResponseRepository(DATA_DIR)
    return ResponseService(response_repo, survey_repo)
