from abc import ABC, abstractmethod
from domain.entities.response_history import ResponseHistory


class ResponseHistoryRepository(ABC):
    """응답 수정 이력 저장소 인터페이스입니다."""

    @abstractmethod
    def save(self, history: ResponseHistory) -> None:
        """수정 이력을 저장합니다.

        Args:
            history: 저장할 이력 엔티티
        """
        pass

    @abstractmethod
    def find_by_response_id(self, response_id: str) -> list[ResponseHistory]:
        """응답 ID로 수정 이력 목록을 조회합니다.

        Args:
            response_id: 응답 식별자

        Returns:
            이력 엔티티 목록 (시간순 정렬)
        """
        pass
