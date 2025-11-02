from pathlib import Path
from loguru import logger
from domain.entities.user import User
from domain.value_objects.types import QuestionType
from domain.value_objects.role import Role
from application.survey_service import SurveyService
from application.response_service import ResponseService
from application.auth_service import AuthService
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository
from infrastructure.persistence.csv_tenant_repository import CsvTenantRepository
from infrastructure.persistence.csv_user_repository import CsvUserRepository
from infrastructure.persistence.csv_session_repository import CsvSessionRepository


class Commands:
    """CLI 명령어를 처리하는 클래스입니다.

    Attributes:
        survey_service: 설문 서비스
        response_service: 응답 서비스
        auth_service: 인증 서비스
    """

    def __init__(self, data_dir: Path, debug: bool = False):
        """CLI 명령어 핸들러를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
            debug: 디버그 모드 활성화
        """
        self.data_dir = data_dir
        self.debug = debug

        survey_repo = CsvSurveyRepository(data_dir)
        response_repo = CsvResponseRepository(data_dir)
        tenant_repo = CsvTenantRepository(data_dir)
        user_repo = CsvUserRepository(data_dir)
        session_repo = CsvSessionRepository(data_dir)

        self.survey_service = SurveyService(survey_repo)
        self.response_service = ResponseService(response_repo, survey_repo)
        self.auth_service = AuthService(tenant_repo, user_repo, session_repo)
        self.tenant_repo = tenant_repo
        self.user_repo = user_repo

    def register_tenant(self, name: str) -> str:
        """테넌트를 등록합니다.

        Args:
            name: 테넌트 이름

        Returns:
            생성된 테넌트 ID
        """
        tenant_id = self.auth_service.register_tenant(name)
        logger.info("테넌트 등록 완료", extra={"tenant_id": tenant_id})
        return tenant_id

    def list_tenants(self) -> list[dict[str, str]]:
        """모든 테넌트 목록을 조회합니다.

        Returns:
            테넌트 목록
        """
        try:
            tenants = self.tenant_repo.find_all_tenants()

            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "created_at": t.created_at.isoformat(),
                    "is_active": str(t.is_active),
                }
                for t in tenants
            ]
        except Exception:
            logger.exception("테넌트 목록 조회 중 오류 발생")
            raise

    def register_user(
        self, tenant_id: str, username: str, email: str, password: str, role: str
    ) -> tuple[bool, str]:
        """사용자를 등록합니다.

        Args:
            tenant_id: 테넌트 ID
            username: 사용자명
            email: 이메일
            password: 비밀번호
            role: 역할 (tenant_admin/survey_manager/respondent)

        Returns:
            (성공 여부, 사용자 ID 또는 에러 메시지)
        """
        try:
            role_enum = Role(role)
            result = self.auth_service.register_user(tenant_id, username, email, password, role_enum)

            if result.is_success():
                logger.info("사용자 등록 완료", extra={"user_id": result.value})
                return True, result.value
            else:
                logger.warning(f"사용자 등록 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("사용자 등록 중 오류 발생")
            raise

    def login(self, username: str, password: str, tenant_id: str) -> tuple[bool, str, User | None]:
        """로그인을 처리합니다.

        Args:
            username: 사용자명
            password: 비밀번호
            tenant_id: 테넌트 ID

        Returns:
            (성공 여부, API 키 또는 에러 메시지, User 엔티티)
        """
        try:
            result = self.auth_service.login(username, password, tenant_id)

            if result.is_success():
                api_key = result.value
                session_result = self.auth_service.validate_session(api_key)

                if session_result.is_success():
                    user, _ = session_result.value
                    logger.info("로그인 성공", extra={"username": username})
                    return True, api_key, user
                else:
                    return False, session_result.error, None
            else:
                logger.warning(f"로그인 실패: {result.error}")
                return False, result.error, None
        except Exception:
            logger.exception("로그인 중 오류 발생")
            raise

    def logout(self, api_key: str) -> bool:
        """로그아웃을 처리합니다.

        Args:
            api_key: API 키

        Returns:
            성공 여부
        """
        try:
            result = self.auth_service.logout(api_key)
            if result.is_success():
                logger.info("로그아웃 성공")
                return True
            else:
                logger.warning(f"로그아웃 실패: {result.error}")
                return False
        except Exception:
            logger.exception("로그아웃 중 오류 발생")
            raise

    def validate_session(self, api_key: str) -> tuple[bool, str, User | None]:
        """세션을 검증합니다.

        Args:
            api_key: API 키

        Returns:
            (성공 여부, 에러 메시지, User 엔티티)
        """
        try:
            result = self.auth_service.validate_session(api_key)

            if result.is_success():
                user, _ = result.value
                return True, "", user
            else:
                return False, result.error, None
        except Exception:
            logger.exception("세션 검증 중 오류 발생")
            raise

    def create_survey(self, user: User, title: str, description: str) -> tuple[bool, str]:
        """설문을 생성합니다.

        Args:
            user: 사용자 엔티티
            title: 설문 제목
            description: 설문 설명

        Returns:
            (성공 여부, 설문 ID 또는 에러 메시지)
        """
        try:
            result = self.survey_service.create_survey(user, title, description)

            if result.is_success():
                logger.info("설문 생성 완료", extra={"survey_id": result.value})
                return True, result.value
            else:
                logger.warning(f"설문 생성 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("설문 생성 중 오류 발생")
            raise

    def add_question(
        self, user: User, survey_id: str, text: str, question_type: str, options: list[str] | None = None
    ) -> tuple[bool, str]:
        """질문을 추가합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 ID
            text: 질문 내용
            question_type: 질문 유형
            options: 객관식 선택지

        Returns:
            (성공 여부, 질문 ID 또는 에러 메시지)
        """
        try:
            q_type = QuestionType(question_type)
            result = self.survey_service.add_question(user, survey_id, text, q_type, options)

            if result.is_success():
                logger.info("질문 추가 완료", extra={"question_id": result.value})
                return True, result.value
            else:
                logger.warning(f"질문 추가 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("질문 추가 중 오류 발생")
            raise

    def get_survey(self, user: User, survey_id: str) -> tuple[bool, str, dict[str, str | list[dict[str, str]]] | None]:
        """설문을 조회합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 ID

        Returns:
            (성공 여부, 에러 메시지, 설문 정보)
        """
        try:
            result = self.survey_service.get_survey(user, survey_id)

            if result.is_failure():
                logger.warning(f"설문 조회 실패: {result.error}")
                return False, result.error, None

            survey = result.value
            questions = [
                {
                    "id": q.id,
                    "text": q.text,
                    "type": q.question_type.value,
                    "options": list(q.options) if q.options else [],
                }
                for q in survey.questions
            ]
            survey_data = {
                "id": survey.id,
                "tenant_id": survey.tenant_id,
                "owner_id": survey.owner_id,
                "title": survey.title,
                "description": survey.description,
                "created_at": survey.created_at.isoformat(),
                "questions": questions,
            }
            return True, "", survey_data
        except Exception:
            logger.exception("설문 조회 중 오류 발생")
            raise

    def list_surveys(self, user: User) -> list[dict[str, str]]:
        """사용자가 접근 가능한 설문 목록을 조회합니다.

        Args:
            user: 사용자 엔티티

        Returns:
            설문 목록
        """
        try:
            surveys = self.survey_service.get_surveys_by_user(user)
            return [
                {
                    "id": s.id,
                    "title": s.title,
                    "description": s.description,
                    "owner_id": s.owner_id,
                    "question_count": str(len(s.questions)),
                }
                for s in surveys
            ]
        except Exception:
            logger.exception("설문 목록 조회 중 오류 발생")
            raise

    def submit_response(self, user: User, survey_id: str, answers: dict[str, str]) -> tuple[bool, str]:
        """응답을 제출합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 ID
            answers: 질문 ID와 답변 딕셔너리

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            result = self.response_service.submit_response(user, survey_id, answers)

            if result.is_success():
                logger.info("응답 제출 완료", extra={"user_id": user.id})
                return True, ""
            else:
                logger.warning(f"응답 제출 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("응답 제출 중 오류 발생")
            raise

    def get_results(self, user: User, survey_id: str) -> tuple[bool, str, dict[str, dict[str, int | float | list[str]]] | None]:
        """설문 결과를 조회합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 ID

        Returns:
            (성공 여부, 에러 메시지, 결과 데이터)
        """
        try:
            result = self.response_service.get_survey_results(user, survey_id)

            if result.is_failure():
                logger.warning(f"결과 조회 실패: {result.error}")
                return False, result.error, None

            return True, "", result.value
        except Exception:
            logger.exception("결과 조회 중 오류 발생")
            raise
