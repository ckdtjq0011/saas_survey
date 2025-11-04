from abc import ABC, abstractmethod
from domain.entities.survey_session import SurveySession


class SurveySessionRepository(ABC):
    """설문 세션 저장소 인터페이스입니다."""

    @abstractmethod
    def save(self, session: SurveySession) -> None:
        """세션을 저장합니다.

        Args:
            session: 저장할 세션 엔티티
        """
        pass

    @abstractmethod
    def find_by_id(self, session_id: str) -> SurveySession | None:
        """세션 ID로 세션을 조회합니다.

        Args:
            session_id: 세션 식별자

        Returns:
            세션 엔티티 또는 None
        """
        pass

    @abstractmethod
    def find_by_respondent_and_survey(self, respondent_id: str, survey_id: str) -> list[SurveySession]:
        """응답자 ID와 설문 ID로 세션 목록을 조회합니다.

        Args:
            respondent_id: 응답자 식별자
            survey_id: 설문 식별자

        Returns:
            세션 엔티티 목록
        """
        pass

    @abstractmethod
    def update_session(self, session: SurveySession) -> None:
        """세션을 수정합니다.

        Args:
            session: 수정할 세션 엔티티

        Raises:
            ValueError: 세션을 찾을 수 없는 경우
        """
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        """세션을 삭제합니다.

        Args:
            session_id: 세션 식별자

        Raises:
            ValueError: 세션을 찾을 수 없는 경우
        """
        pass
