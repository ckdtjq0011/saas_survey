from pathlib import Path
from datetime import datetime
from application.survey_service import SurveyService
from application.response_service import ResponseService
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository
from domain.entities.user import User
from domain.value_objects.role import Role


DATA_DIR = Path("data")


def get_anonymous_user() -> User:
    """API 익명 사용자를 반환합니다.

    Returns:
        익명 사용자 엔티티
    """
    return User(
        id="api_anonymous",
        tenant_id="api_tenant",
        username="api_user",
        email="api@system.com",
        password_hash="$2b$12$dummy_hash_for_api_anonymous_user",
        role=Role.SURVEY_MANAGER,
        created_at=datetime.now(),
        is_active=True
    )


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
