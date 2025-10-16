from abc import ABC, abstractmethod
from domain.entities.session import Session


class SessionRepository(ABC):
    """세션 저장소 인터페이스입니다."""

    @abstractmethod
    def save_session(self, session: Session) -> None:
        """세션을 저장합니다.

        Args:
            session: 저장할 세션 엔티티
        """
        pass

    @abstractmethod
    def find_session_by_api_key(self, api_key: str) -> Session | None:
        """API 키로 세션을 조회합니다.

        Args:
            api_key: API 키

        Returns:
            세션 엔티티 또는 None
        """
        pass

    @abstractmethod
    def find_session_by_user_id(self, user_id: str) -> Session | None:
        """사용자 ID로 세션을 조회합니다.

        Args:
            user_id: 사용자 식별자

        Returns:
            세션 엔티티 또는 None
        """
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        """세션을 삭제합니다.

        Args:
            session_id: 세션 식별자
        """
        pass
