from abc import ABC, abstractmethod
from datetime import datetime

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

    @abstractmethod
    def find_expired_sessions(self, current_time: datetime) -> list[Session]:
        """만료된 세션들을 조회합니다.

        Args:
            current_time: 현재 시각

        Returns:
            만료된 세션 목록
        """
        pass

    @abstractmethod
    def delete_sessions_bulk(self, session_ids: list[str]) -> int:
        """세션들을 일괄 삭제하고 삭제된 개수를 반환합니다.

        Args:
            session_ids: 삭제할 세션 식별자 목록

        Returns:
            삭제된 세션 개수
        """
        pass

    @abstractmethod
    def count_sessions(self) -> int:
        """전체 세션 개수를 반환합니다.

        Returns:
            세션 개수
        """
        pass

    @abstractmethod
    def count_expired_sessions(self, current_time: datetime) -> int:
        """만료된 세션 개수를 반환합니다.

        Args:
            current_time: 현재 시각

        Returns:
            만료된 세션 개수
        """
        pass
