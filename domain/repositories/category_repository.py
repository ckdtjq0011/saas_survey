from abc import ABC, abstractmethod
from domain.entities.category import Category


class CategoryRepository(ABC):
    """범주 저장소 인터페이스입니다."""

    @abstractmethod
    def save_category(self, category: Category) -> None:
        """범주를 저장합니다.

        Args:
            category: 저장할 범주 엔티티
        """
        pass

    @abstractmethod
    def find_category_by_id(self, category_id: str) -> Category | None:
        """ID로 범주를 조회합니다.

        Args:
            category_id: 범주 식별자

        Returns:
            범주 엔티티 또는 None
        """
        pass

    @abstractmethod
    def find_all_categories(self) -> list[Category]:
        """모든 범주를 조회합니다.

        Returns:
            범주 엔티티 목록
        """
        pass

    @abstractmethod
    def find_by_tenant_id(self, tenant_id: str) -> list[Category]:
        """테넌트 ID로 범주 목록을 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            범주 엔티티 목록
        """
        pass

    @abstractmethod
    def find_by_parent_id(self, parent_id: str | None, tenant_id: str) -> list[Category]:
        """상위 범주 ID로 하위 범주 목록을 조회합니다.

        Args:
            parent_id: 상위 범주 식별자 (None이면 최상위 범주)
            tenant_id: 테넌트 식별자

        Returns:
            범주 엔티티 목록 (order 순으로 정렬)
        """
        pass

    @abstractmethod
    def update_category(self, category_id: str, **updates) -> None:
        """범주 정보를 수정합니다.

        Args:
            category_id: 범주 식별자
            **updates: 수정할 필드 (name, description, order, is_active 등)

        Raises:
            ValueError: 범주를 찾을 수 없는 경우
        """
        pass

    @abstractmethod
    def delete_category(self, category_id: str) -> None:
        """범주를 삭제합니다.

        Args:
            category_id: 범주 식별자

        Raises:
            ValueError: 범주를 찾을 수 없는 경우
        """
        pass

    @abstractmethod
    def has_subcategories(self, category_id: str) -> bool:
        """범주에 하위 범주가 있는지 확인합니다.

        Args:
            category_id: 범주 식별자

        Returns:
            하위 범주가 있으면 True, 없으면 False
        """
        pass
