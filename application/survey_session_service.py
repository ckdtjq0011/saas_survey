import uuid
from datetime import datetime
from domain.entities.survey_session import SurveySession
from domain.entities.user import User
from domain.value_objects.result import Success, Failure, Result
from domain.repositories.survey_session_repository import SurveySessionRepository
from domain.repositories.survey_repository import SurveyRepository


class SurveySessionService:
    """설문 세션 관련 유스케이스를 처리하는 서비스입니다.

    Attributes:
        session_repository: 세션 저장소
        survey_repository: 설문 저장소
    """

    def __init__(
        self,
        session_repository: SurveySessionRepository,
        survey_repository: SurveyRepository,
    ):
        """서비스를 초기화합니다.

        Args:
            session_repository: 세션 저장소 구현체
            survey_repository: 설문 저장소 구현체
        """
        self.session_repository = session_repository
        self.survey_repository = survey_repository

    def start_session(self, user: User, survey_id: str, user_agent: str) -> Result[str, str]:
        """설문 세션을 시작합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자
            user_agent: 브라우저/디바이스 정보

        Returns:
            Success[세션 ID] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        session_id = str(uuid.uuid4())
        session = SurveySession(
            id=session_id,
            survey_id=survey_id,
            respondent_id=user.id,
            started_at=datetime.now(),
            submitted_at=None,
            completed=False,
            completion_percentage=0,
            user_agent=user_agent,
            total_time_spent_seconds=0,
        )

        self.session_repository.save(session)
        return Success(session_id)

    def update_progress(self, session_id: str, completion_percentage: int) -> Result[None, str]:
        """세션의 진행률을 업데이트합니다.

        Args:
            session_id: 세션 식별자
            completion_percentage: 진행률 (0-100)

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        session = self.session_repository.find_by_id(session_id)
        if not session:
            return Failure(f"세션을 찾을 수 없습니다: {session_id}")

        if completion_percentage < 0 or completion_percentage > 100:
            return Failure("진행률은 0-100 사이여야 합니다")

        updated_session = SurveySession(
            id=session.id,
            survey_id=session.survey_id,
            respondent_id=session.respondent_id,
            started_at=session.started_at,
            submitted_at=session.submitted_at,
            completed=session.completed,
            completion_percentage=completion_percentage,
            user_agent=session.user_agent,
            total_time_spent_seconds=session.total_time_spent_seconds,
        )

        self.session_repository.update_session(updated_session)
        return Success(None)

    def complete_session(self, session_id: str, total_time_seconds: int) -> Result[None, str]:
        """세션을 완료 처리합니다.

        Args:
            session_id: 세션 식별자
            total_time_seconds: 총 소요 시간 (초)

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        session = self.session_repository.find_by_id(session_id)
        if not session:
            return Failure(f"세션을 찾을 수 없습니다: {session_id}")

        if total_time_seconds < 0:
            return Failure("소요 시간은 음수가 될 수 없습니다")

        updated_session = SurveySession(
            id=session.id,
            survey_id=session.survey_id,
            respondent_id=session.respondent_id,
            started_at=session.started_at,
            submitted_at=datetime.now(),
            completed=True,
            completion_percentage=100,
            user_agent=session.user_agent,
            total_time_spent_seconds=total_time_seconds,
        )

        self.session_repository.update_session(updated_session)
        return Success(None)

    def get_session(self, session_id: str) -> Result[SurveySession, str]:
        """세션 정보를 조회합니다.

        Args:
            session_id: 세션 식별자

        Returns:
            Success[SurveySession] 또는 Failure[에러 메시지]
        """
        session = self.session_repository.find_by_id(session_id)
        if not session:
            return Failure(f"세션을 찾을 수 없습니다: {session_id}")

        return Success(session)

    def get_user_sessions(self, user: User, survey_id: str) -> Result[list[SurveySession], str]:
        """사용자의 특정 설문에 대한 세션 목록을 조회합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자

        Returns:
            Success[세션 목록] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        sessions = self.session_repository.find_by_respondent_and_survey(user.id, survey_id)
        return Success(sessions)
