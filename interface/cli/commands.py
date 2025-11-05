from pathlib import Path
from loguru import logger
from domain.entities.user import User
from domain.value_objects.types import QuestionType
from domain.value_objects.role import Role
from application.survey_service import SurveyService
from application.response_service import ResponseService
from application.survey_session_service import SurveySessionService
from application.auth_service import AuthService
from application.category_service import CategoryService
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository
from infrastructure.persistence.csv_survey_session_repository import CsvSurveySessionRepository
from infrastructure.persistence.csv_response_history_repository import CsvResponseHistoryRepository
from infrastructure.persistence.csv_tenant_repository import CsvTenantRepository
from infrastructure.persistence.csv_user_repository import CsvUserRepository
from infrastructure.persistence.csv_session_repository import CsvSessionRepository
from infrastructure.persistence.csv_category_repository import CsvCategoryRepository


class Commands:
    """CLI 명령어를 처리하는 클래스입니다.

    Attributes:
        survey_service: 설문 서비스
        response_service: 응답 서비스
        survey_session_service: 설문 세션 서비스
        auth_service: 인증 서비스
        category_service: 범주 서비스
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
        survey_session_repo = CsvSurveySessionRepository(data_dir)
        response_history_repo = CsvResponseHistoryRepository(data_dir)
        tenant_repo = CsvTenantRepository(data_dir)
        user_repo = CsvUserRepository(data_dir)
        session_repo = CsvSessionRepository(data_dir)
        category_repo = CsvCategoryRepository(data_dir)

        self.survey_service = SurveyService(survey_repo)
        self.response_service = ResponseService(response_repo, response_history_repo, survey_repo, category_repo)
        self.survey_session_service = SurveySessionService(survey_session_repo, survey_repo)
        self.auth_service = AuthService(tenant_repo, user_repo, session_repo)
        self.category_service = CategoryService(category_repo)
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
        self,
        user: User,
        survey_id: str,
        text: str,
        question_type: str,
        options: list[str] | None = None,
        category_id: str | None = None
    ) -> tuple[bool, str]:
        """질문을 추가합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 ID
            text: 질문 내용
            question_type: 질문 유형
            options: 객관식 선택지
            category_id: 범주 ID

        Returns:
            (성공 여부, 질문 ID 또는 에러 메시지)
        """
        try:
            q_type = QuestionType.from_value(question_type)
            result = self.survey_service.add_question(user, survey_id, text, q_type, options, category_id)

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

    def submit_response(
        self,
        user: User,
        survey_id: str,
        answers: dict[str, str],
        session_id: str,
        time_spent_data: dict[str, int],
    ) -> tuple[bool, str]:
        """응답을 제출합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 ID
            answers: 질문 ID와 답변 딕셔너리
            session_id: 세션 ID
            time_spent_data: 질문 ID와 소요 시간(초) 딕셔너리

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            result = self.response_service.submit_response(
                user, survey_id, answers, session_id, time_spent_data
            )

            if result.is_success():
                logger.info("응답 제출 완료", extra={"user_id": user.id, "session_id": session_id})
                return True, ""
            else:
                logger.warning(f"응답 제출 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("응답 제출 중 오류 발생")
            raise

    def get_results(self, user: User, survey_id: str) -> tuple[bool, str, dict[str, list[dict[str, str | int | dict]]] | None]:
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

            raw_results = result.value
            formatted_results = []
            for question_id, data in raw_results.items():
                result_item = {
                    "question": data["question"],
                    "answer_distribution": data.get("distribution", {}),
                }
                if data["type"] == QuestionType.TEXT.value:
                    result_item["answer_distribution"] = {
                        answer: 1 for answer in data.get("answers", [])
                    }

                formatted_results.append(result_item)

            return True, "", {"results": formatted_results}
        except Exception:
            logger.exception("결과 조회 중 오류 발생")
            raise

    def update_survey(self, user: User, survey_id: str, title: str, description: str) -> tuple[bool, str]:
        """설문을 수정합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 ID
            title: 새 제목
            description: 새 설명

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            result = self.survey_service.update_survey(user, survey_id, title=title, description=description)

            if result.is_success():
                logger.info("설문 수정 완료", extra={"survey_id": survey_id})
                return True, ""
            else:
                logger.warning(f"설문 수정 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("설문 수정 중 오류 발생")
            raise

    def delete_survey(self, user: User, survey_id: str) -> tuple[bool, str]:
        """설문을 삭제합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 ID

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            result = self.survey_service.delete_survey(user, survey_id)

            if result.is_success():
                logger.info("설문 삭제 완료", extra={"survey_id": survey_id})
                return True, ""
            else:
                logger.warning(f"설문 삭제 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("설문 삭제 중 오류 발생")
            raise

    def update_question(self, user: User, question_id: str, text: str, options: list[str] | None = None) -> tuple[bool, str]:
        """질문을 수정합니다.

        Args:
            user: 사용자 엔티티
            question_id: 질문 ID
            text: 새 질문 내용
            options: 새 선택지 (객관식인 경우)

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            updates = {"text": text}
            if options is not None:
                updates["options"] = tuple(options)

            result = self.survey_service.update_question(user, question_id, **updates)

            if result.is_success():
                logger.info("질문 수정 완료", extra={"question_id": question_id})
                return True, ""
            else:
                logger.warning(f"질문 수정 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("질문 수정 중 오류 발생")
            raise

    def delete_question(self, user: User, question_id: str) -> tuple[bool, str]:
        """질문을 삭제합니다.

        Args:
            user: 사용자 엔티티
            question_id: 질문 ID

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            result = self.survey_service.delete_question(user, question_id)

            if result.is_success():
                logger.info("질문 삭제 완료", extra={"question_id": question_id})
                return True, ""
            else:
                logger.warning(f"질문 삭제 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("질문 삭제 중 오류 발생")
            raise

    def update_response(self, user: User, response_id: str, answer: str) -> tuple[bool, str]:
        """응답을 수정합니다.

        Args:
            user: 사용자 엔티티
            response_id: 응답 ID
            answer: 새 답변

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            result = self.response_service.update_response(user, response_id, answer)

            if result.is_success():
                logger.info("응답 수정 완료", extra={"response_id": response_id})
                return True, ""
            else:
                logger.warning(f"응답 수정 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("응답 수정 중 오류 발생")
            raise

    def delete_response(self, user: User, response_id: str) -> tuple[bool, str]:
        """응답을 삭제합니다.

        Args:
            user: 사용자 엔티티
            response_id: 응답 ID

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            result = self.response_service.delete_response(user, response_id)

            if result.is_success():
                logger.info("응답 삭제 완료", extra={"response_id": response_id})
                return True, ""
            else:
                logger.warning(f"응답 삭제 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("응답 삭제 중 오류 발생")
            raise

    def create_category(
        self, user: User, name: str, description: str, parent_id: str | None = None, order: int = 0
    ) -> tuple[bool, str]:
        """범주를 생성합니다.

        Args:
            user: 사용자 엔티티
            name: 범주 이름
            description: 범주 설명
            parent_id: 상위 범주 ID
            order: 표시 순서

        Returns:
            (성공 여부, 범주 ID 또는 에러 메시지)
        """
        try:
            result = self.category_service.create_category(user, name, description, parent_id, order)

            if result.is_success():
                logger.info("범주 생성 완료", extra={"category_id": result.value})
                return True, result.value
            else:
                logger.warning(f"범주 생성 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("범주 생성 중 오류 발생")
            raise

    def list_categories(self, user: User, parent_id: str | None = None) -> tuple[bool, list | str]:
        """범주 목록을 조회합니다.

        Args:
            user: 사용자 엔티티
            parent_id: 상위 범주 ID (None이면 최상위)

        Returns:
            (성공 여부, 범주 목록 또는 에러 메시지)
        """
        try:
            result = self.category_service.list_categories(user, parent_id)

            if result.is_success():
                return True, result.value
            else:
                logger.warning(f"범주 목록 조회 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("범주 목록 조회 중 오류 발생")
            raise

    def list_all_categories(self, user: User) -> tuple[bool, list | str]:
        """모든 범주를 조회합니다.

        Args:
            user: 사용자 엔티티

        Returns:
            (성공 여부, 범주 목록 또는 에러 메시지)
        """
        try:
            result = self.category_service.get_all_categories(user)

            if result.is_success():
                return True, result.value
            else:
                logger.warning(f"범주 목록 조회 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("범주 목록 조회 중 오류 발생")
            raise

    def get_category(self, user: User, category_id: str) -> tuple[bool, str, dict | None]:
        """범주를 조회합니다.

        Args:
            user: 사용자 엔티티
            category_id: 범주 ID

        Returns:
            (성공 여부, 에러 메시지, 범주 정보)
        """
        try:
            result = self.category_service.get_category(user, category_id)

            if result.is_success():
                category = result.value
                return True, "", {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "parent_id": category.parent_id,
                    "order": category.order,
                    "is_active": category.is_active,
                }
            else:
                logger.warning(f"범주 조회 실패: {result.error}")
                return False, result.error, None
        except Exception:
            logger.exception("범주 조회 중 오류 발생")
            raise

    def update_category(self, user: User, category_id: str, **updates) -> tuple[bool, str]:
        """범주를 수정합니다.

        Args:
            user: 사용자 엔티티
            category_id: 범주 ID
            **updates: 수정할 필드

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            result = self.category_service.update_category(user, category_id, **updates)

            if result.is_success():
                logger.info("범주 수정 완료", extra={"category_id": category_id})
                return True, ""
            else:
                logger.warning(f"범주 수정 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("범주 수정 중 오류 발생")
            raise

    def delete_category(self, user: User, category_id: str) -> tuple[bool, str]:
        """범주를 삭제합니다.

        Args:
            user: 사용자 엔티티
            category_id: 범주 ID

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            result = self.category_service.delete_category(user, category_id)

            if result.is_success():
                logger.info("범주 삭제 완료", extra={"category_id": category_id})
                return True, ""
            else:
                logger.warning(f"범주 삭제 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("범주 삭제 중 오류 발생")
            raise

    def start_survey_session(self, user: User, survey_id: str, user_agent: str) -> tuple[bool, str]:
        """설문 세션을 시작합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 ID
            user_agent: 브라우저/디바이스 정보

        Returns:
            (성공 여부, 세션 ID 또는 에러 메시지)
        """
        try:
            result = self.survey_session_service.start_session(user, survey_id, user_agent)

            if result.is_success():
                session_id = result.value
                logger.info("설문 세션 시작", extra={"user_id": user.id, "session_id": session_id})
                return True, session_id
            else:
                logger.warning(f"설문 세션 시작 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("설문 세션 시작 중 오류 발생")
            raise

    def complete_survey_session(self, session_id: str, total_time_seconds: int) -> tuple[bool, str]:
        """설문 세션을 완료 처리합니다.

        Args:
            session_id: 세션 ID
            total_time_seconds: 총 소요 시간 (초)

        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            result = self.survey_session_service.complete_session(session_id, total_time_seconds)

            if result.is_success():
                logger.info("설문 세션 완료", extra={"session_id": session_id})
                return True, ""
            else:
                logger.warning(f"설문 세션 완료 실패: {result.error}")
                return False, result.error
        except Exception:
            logger.exception("설문 세션 완료 중 오류 발생")
            raise

    def get_response_history(self, user: User, response_id: str) -> tuple[bool, str, list[dict[str, str]] | None]:
        """응답 수정 이력을 조회합니다.

        Args:
            user: 사용자 엔티티
            response_id: 응답 ID

        Returns:
            (성공 여부, 에러 메시지, 이력 목록)
        """
        try:
            result = self.response_service.get_response_history(user, response_id)

            if result.is_success():
                histories = result.value
                history_dicts = [h.to_dict() for h in histories]
                logger.info("응답 이력 조회 완료", extra={"response_id": response_id})
                return True, "", history_dicts
            else:
                logger.warning(f"응답 이력 조회 실패: {result.error}")
                return False, result.error, None
        except Exception:
            logger.exception("응답 이력 조회 중 오류 발생")
            raise

    def export_results(self, user: User, survey_id: str) -> tuple[bool, str, tuple[str, str] | None]:
        """설문 결과를 CSV 파일로 내보냅니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 ID

        Returns:
            (성공 여부, 에러 메시지, (raw_csv_path, summary_csv_path) 튜플)
        """
        try:
            result = self.response_service.export_results_to_csv(user, survey_id)

            if result.is_success():
                raw_path, summary_path = result.value
                logger.info("설문 결과 export 완료", extra={"survey_id": survey_id, "raw_path": raw_path, "summary_path": summary_path})
                return True, "", (raw_path, summary_path)
            else:
                logger.warning(f"설문 결과 export 실패: {result.error}")
                return False, result.error, None
        except Exception:
            logger.exception("설문 결과 export 중 오류 발생")
            raise
