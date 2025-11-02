from abc import ABC, abstractmethod
from domain.entities.user import User


class UserRepository(ABC):
    """사용자 저장소 인터페이스입니다."""

    @abstractmethod
    def save_user(self, user: User) -> None:
        """사용자를 저장합니다.

        Args:
            user: 저장할 사용자 엔티티
        """
        pass

    @abstractmethod
    def find_user_by_id(self, user_id: str) -> User | None:
        """ID로 사용자를 조회합니다.

        Args:
            user_id: 사용자 식별자

        Returns:
            사용자 엔티티 또는 None
        """
        pass

    @abstractmethod
    def find_user_by_username(self, username: str, tenant_id: str) -> User | None:
        """사용자명으로 사용자를 조회합니다.

        Args:
            username: 사용자명
            tenant_id: 테넌트 식별자

        Returns:
            사용자 엔티티 또는 None
        """
        pass

    @abstractmethod
    def find_users_by_tenant(self, tenant_id: str) -> list[User]:
        """테넌트의 모든 사용자를 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            사용자 엔티티 목록
        """
        pass

    @abstractmethod
    def update_user(self, user_id: str, **updates) -> None:
        """사용자 정보를 수정합니다.

        Args:
            user_id: 사용자 식별자
            **updates: 수정할 필드 (email, password_hash, role, is_active 등)

        Raises:
            ValueError: 사용자를 찾을 수 없는 경우
        """
        pass

    @abstractmethod
    def delete_user(self, user_id: str) -> None:
        """사용자를 삭제합니다.

        Args:
            user_id: 사용자 식별자

        Raises:
            ValueError: 사용자를 찾을 수 없는 경우
        """
        pass
