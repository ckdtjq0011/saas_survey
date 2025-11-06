import shutil
import tempfile
import uuid
from pathlib import Path
from datetime import datetime, timedelta
import pytest
from interface.cli.commands import Commands
from infrastructure.persistence.csv_tenant_repository import CsvTenantRepository
from infrastructure.persistence.csv_user_repository import CsvUserRepository
from infrastructure.persistence.csv_session_repository import CsvSessionRepository
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository
from infrastructure.persistence.csv_survey_session_repository import CsvSurveySessionRepository
from infrastructure.persistence.csv_response_history_repository import CsvResponseHistoryRepository
from infrastructure.persistence.csv_category_repository import CsvCategoryRepository
from application.auth_service import AuthService
from application.survey_service import SurveyService
from application.response_service import ResponseService
from application.survey_session_service import SurveySessionService
from domain.entities.tenant import Tenant
from domain.entities.user import User
from domain.entities.session import Session
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.entities.response import Response
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType


@pytest.fixture(scope="function")
def temp_data_dir():
    """테스트용 임시 데이터 디렉토리를 생성합니다.

    각 테스트마다 독립적인 임시 디렉토리를 생성하고,
    테스트 완료 후 (성공/실패 관계없이) 자동으로 정리합니다.

    Yields:
        임시 디렉토리 Path 객체
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        # 테스트 성공/실패 관계없이 반드시 정리
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                # 정리 실패 시에도 테스트는 계속 진행
                print(f"Warning: 임시 디렉토리 정리 실패: {temp_dir}, 에러: {e}")


@pytest.fixture(scope="function")
def survey_commands(temp_data_dir):
    """테스트용 Commands 인스턴스를 생성합니다.

    각 테스트마다 독립적인 Commands 인스턴스를 생성합니다.

    Args:
        temp_data_dir: 임시 데이터 디렉토리 픽스처

    Returns:
        Commands 인스턴스
    """
    return Commands(temp_data_dir)


@pytest.fixture(scope="function")
def tenant_repo(temp_data_dir):
    """테스트용 Tenant Repository를 생성합니다.

    각 테스트마다 독립적인 Repository 인스턴스를 생성합니다.
    테스트 완료 후 CSV 파일은 temp_data_dir과 함께 자동 삭제됩니다.
    """
    repo = CsvTenantRepository(temp_data_dir)
    yield repo
    # 명시적 정리: CSV 파일 존재 확인 후 삭제
    csv_file = temp_data_dir / "tenants.csv"
    if csv_file.exists():
        csv_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def user_repo(temp_data_dir):
    """테스트용 User Repository를 생성합니다.

    각 테스트마다 독립적인 Repository 인스턴스를 생성합니다.
    """
    repo = CsvUserRepository(temp_data_dir)
    yield repo
    csv_file = temp_data_dir / "users.csv"
    if csv_file.exists():
        csv_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def session_repo(temp_data_dir):
    """테스트용 Session Repository를 생성합니다.

    각 테스트마다 독립적인 Repository 인스턴스를 생성합니다.
    """
    repo = CsvSessionRepository(temp_data_dir)
    yield repo
    csv_file = temp_data_dir / "sessions.csv"
    if csv_file.exists():
        csv_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def survey_repo(temp_data_dir):
    """테스트용 Survey Repository를 생성합니다.

    각 테스트마다 독립적인 Repository 인스턴스를 생성합니다.
    """
    repo = CsvSurveyRepository(temp_data_dir)
    yield repo
    for csv_file in [temp_data_dir / "surveys.csv", temp_data_dir / "questions.csv"]:
        if csv_file.exists():
            csv_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def response_repo(temp_data_dir):
    """테스트용 Response Repository를 생성합니다.

    각 테스트마다 독립적인 Repository 인스턴스를 생성합니다.
    """
    repo = CsvResponseRepository(temp_data_dir)
    yield repo
    csv_file = temp_data_dir / "responses.csv"
    if csv_file.exists():
        csv_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def category_repo(temp_data_dir):
    """테스트용 Category Repository를 생성합니다.

    각 테스트마다 독립적인 Repository 인스턴스를 생성합니다.
    """
    repo = CsvCategoryRepository(temp_data_dir)
    yield repo
    csv_file = temp_data_dir / "categories.csv"
    if csv_file.exists():
        csv_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def response_history_repo(temp_data_dir):
    """테스트용 Response History Repository를 생성합니다.

    각 테스트마다 독립적인 Repository 인스턴스를 생성합니다.
    """
    repo = CsvResponseHistoryRepository(temp_data_dir)
    yield repo
    csv_file = temp_data_dir / "response_histories.csv"
    if csv_file.exists():
        csv_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def survey_session_repo(temp_data_dir):
    """테스트용 Survey Session Repository를 생성합니다.

    각 테스트마다 독립적인 Repository 인스턴스를 생성합니다.
    """
    repo = CsvSurveySessionRepository(temp_data_dir)
    yield repo
    csv_file = temp_data_dir / "survey_sessions.csv"
    if csv_file.exists():
        csv_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def category_repo(temp_data_dir):
    """테스트용 Category Repository를 생성합니다.

    각 테스트마다 독립적인 Repository 인스턴스를 생성합니다.
    """
    repo = CsvCategoryRepository(temp_data_dir)
    yield repo
    csv_file = temp_data_dir / "categories.csv"
    if csv_file.exists():
        csv_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def auth_service(tenant_repo, user_repo, session_repo):
    """테스트용 Auth Service를 생성합니다.

    각 테스트마다 독립적인 Service 인스턴스를 생성합니다.
    """
    return AuthService(tenant_repo, user_repo, session_repo)


@pytest.fixture(scope="function")
def survey_service(survey_repo):
    """테스트용 Survey Service를 생성합니다.

    각 테스트마다 독립적인 Service 인스턴스를 생성합니다.
    """
    return SurveyService(survey_repo)


@pytest.fixture(scope="function")
def response_service(response_repo, response_history_repo, survey_repo, category_repo):
    """테스트용 Response Service를 생성합니다.

    각 테스트마다 독립적인 Service 인스턴스를 생성합니다.
    """
    return ResponseService(response_repo, response_history_repo, survey_repo, category_repo)


@pytest.fixture(scope="function")
def survey_session_service(survey_session_repo, survey_repo):
    """테스트용 Survey Session Service를 생성합니다.

    각 테스트마다 독립적인 Service 인스턴스를 생성합니다.
    """
    return SurveySessionService(survey_session_repo, survey_repo)


@pytest.fixture(scope="function")
def sample_tenant(tenant_repo):
    """샘플 테넌트를 생성합니다.

    각 테스트마다 새로운 테넌트를 생성합니다.
    테스트 완료 후 Repository와 함께 자동 정리됩니다.
    """
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="테스트회사",
        created_at=datetime.now(),
        is_active=True,
    )
    tenant_repo.save_tenant(tenant)
    return tenant


@pytest.fixture(scope="function")
def sample_admin_user(user_repo, sample_tenant):
    """샘플 TENANT_ADMIN 사용자를 생성합니다.

    각 테스트마다 새로운 관리자를 생성합니다.
    """
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=sample_tenant.id,
        username="admin",
        email="admin@test.com",
        password_hash="$2b$12$dummy_hash",
        role=Role.TENANT_ADMIN,
        created_at=datetime.now(),
        is_active=True,
    )
    user_repo.save_user(user)
    return user


@pytest.fixture(scope="function")
def sample_manager_user(user_repo, sample_tenant):
    """샘플 SURVEY_MANAGER 사용자를 생성합니다.

    각 테스트마다 새로운 매니저를 생성합니다.
    """
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=sample_tenant.id,
        username="manager",
        email="manager@test.com",
        password_hash="$2b$12$dummy_hash",
        role=Role.SURVEY_MANAGER,
        created_at=datetime.now(),
        is_active=True,
    )
    user_repo.save_user(user)
    return user


@pytest.fixture(scope="function")
def sample_respondent_user(user_repo, sample_tenant):
    """샘플 RESPONDENT 사용자를 생성합니다.

    각 테스트마다 새로운 응답자를 생성합니다.
    """
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=sample_tenant.id,
        username="respondent",
        email="respondent@test.com",
        password_hash="$2b$12$dummy_hash",
        role=Role.RESPONDENT,
        created_at=datetime.now(),
        is_active=True,
    )
    user_repo.save_user(user)
    return user


@pytest.fixture(scope="function")
def sample_session(session_repo, sample_admin_user, sample_tenant):
    """샘플 세션을 생성합니다.

    각 테스트마다 새로운 세션을 생성합니다.
    """
    session = Session(
        id=str(uuid.uuid4()),
        user_id=sample_admin_user.id,
        tenant_id=sample_tenant.id,
        api_key="test_api_key_12345",
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
    )
    session_repo.save_session(session)
    return session


@pytest.fixture(scope="function")
def sample_survey(survey_repo, sample_tenant, sample_admin_user):
    """샘플 설문을 생성합니다.

    각 테스트마다 새로운 설문을 생성합니다.
    """
    survey = Survey(
        id=str(uuid.uuid4()),
        tenant_id=sample_tenant.id,
        owner_id=sample_admin_user.id,
        title="만족도 조사",
        description="테스트 설문입니다",
        created_at=datetime.now(),
        questions=(),
    )
    survey_repo.save_survey(survey)
    return survey


@pytest.fixture(scope="function")
def sample_questions(survey_repo, sample_survey):
    """샘플 질문들을 생성합니다 (TEXT, RATING, MULTIPLE_CHOICE).

    각 테스트마다 새로운 질문 3개를 생성합니다.
    """
    questions = []

    q1 = Question(
        id=str(uuid.uuid4()),
        survey_id=sample_survey.id,
        text="의견을 입력하세요",
        question_type=QuestionType.TEXT,
        options=None,
    )
    survey_repo.save_question(q1)
    questions.append(q1)

    q2 = Question(
        id=str(uuid.uuid4()),
        survey_id=sample_survey.id,
        text="만족도는?",
        question_type=QuestionType.RATING,
        options=None,
    )
    survey_repo.save_question(q2)
    questions.append(q2)

    q3 = Question(
        id=str(uuid.uuid4()),
        survey_id=sample_survey.id,
        text="선호하는 옵션은?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=("옵션A", "옵션B", "옵션C"),
    )
    survey_repo.save_question(q3)
    questions.append(q3)

    return questions


@pytest.fixture(scope="function")
def sample_session_id():
    """샘플 세션 ID를 생성합니다."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def sample_response(response_repo, sample_survey, sample_questions, sample_respondent_user, sample_session_id):
    """샘플 응답을 생성합니다.

    각 테스트마다 새로운 응답을 생성합니다.
    """
    response = Response(
        id=str(uuid.uuid4()),
        survey_id=sample_survey.id,
        question_id=sample_questions[0].id,
        answer="좋은 서비스입니다",
        respondent_id=sample_respondent_user.id,
        answered_at=datetime.now(),
        session_id=sample_session_id,
        time_spent_seconds=10,
    )
    response_repo.save(response)
    return response


def create_session_and_time_data(survey_repo, survey_id):
    """테스트용 세션 ID와 time_spent_data를 생성하는 helper 함수입니다.

    Args:
        survey_repo: Survey Repository
        survey_id: 설문 ID

    Returns:
        (session_id, time_spent_data) 튜플
    """
    session_id = str(uuid.uuid4())

    questions = survey_repo.find_questions_by_survey_id(survey_id)
    time_spent_data = {q.id: 5 for q in questions}

    return session_id, time_spent_data
