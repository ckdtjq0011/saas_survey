from abc import ABC, abstractmethod
from domain.entities.response import Response


class ResponseRepository(ABC):
    """응답 저장소 인터페이스입니다."""

    @abstractmethod
    def save(self, response: Response) -> None:
        """응답을 저장합니다.

        Args:
            response: 저장할 응답 엔티티
        """
        pass

    @abstractmethod
    def find_by_survey_id(self, survey_id: str) -> list[Response]:
        """설문 ID로 응답 목록을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            응답 엔티티 목록
        """
        pass

    @abstractmethod
    def find_by_question_id(self, question_id: str) -> list[Response]:
        """질문 ID로 응답 목록을 조회합니다.

        Args:
            question_id: 질문 식별자

        Returns:
            응답 엔티티 목록
        """
        pass
