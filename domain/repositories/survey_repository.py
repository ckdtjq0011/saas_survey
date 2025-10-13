from abc import ABC, abstractmethod
from domain.entities.survey import Survey
from domain.entities.question import Question


class SurveyRepository(ABC):
    """설문 저장소 인터페이스입니다."""

    @abstractmethod
    def save_survey(self, survey: Survey) -> None:
        """설문을 저장합니다.

        Args:
            survey: 저장할 설문 엔티티
        """
        pass

    @abstractmethod
    def save_question(self, question: Question) -> None:
        """질문을 저장합니다.

        Args:
            question: 저장할 질문 엔티티
        """
        pass

    @abstractmethod
    def find_survey_by_id(self, survey_id: str) -> Survey | None:
        """ID로 설문을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            설문 엔티티 또는 None
        """
        pass

    @abstractmethod
    def find_all_surveys(self) -> list[Survey]:
        """모든 설문을 조회합니다.

        Returns:
            설문 엔티티 목록
        """
        pass

    @abstractmethod
    def find_questions_by_survey_id(self, survey_id: str) -> list[Question]:
        """설문 ID로 질문 목록을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            질문 엔티티 목록
        """
        pass
