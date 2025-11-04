import uuid
from datetime import datetime
from domain.entities.category import Category
from domain.entities.user import User
from domain.value_objects.role import Role
from domain.value_objects.result import Success, Failure, Result
from domain.repositories.category_repository import CategoryRepository


class CategoryService:
    """범주 관련 유스케이스를 처리하는 서비스입니다.

    Attributes:
        category_repository: 범주 저장소
    """

    def __init__(self, category_repository: CategoryRepository):
        """서비스를 초기화합니다.

        Args:
            category_repository: 범주 저장소 구현체
        """
        self.category_repository = category_repository

    def create_category(
        self,
        user: User,
        name: str,
        description: str,
        parent_id: str | None = None,
        order: int = 0
    ) -> Result[str, str]:
        """새 범주를 생성합니다.

        Args:
            user: 사용자 엔티티
            name: 범주 이름
            description: 범주 설명
            parent_id: 상위 범주 식별자 (None이면 최상위 범주)
            order: 표시 순서

        Returns:
            Success[범주 ID] 또는 Failure[에러 메시지]
        """
        if user.role != Role.TENANT_ADMIN:
            return Failure("범주 관리는 테넌트 관리자만 가능합니다")

        if parent_id:
            parent = self.category_repository.find_category_by_id(parent_id)
            if not parent:
                return Failure(f"상위 범주를 찾을 수 없습니다: {parent_id}")

            if parent.tenant_id != user.tenant_id:
                return Failure("다른 테넌트의 범주에 접근할 수 없습니다")

            if not parent.is_top_level():
                return Failure("3단계 이상의 계층은 지원하지 않습니다")

        category_id = str(uuid.uuid4())
        category = Category(
            id=category_id,
            tenant_id=user.tenant_id,
            name=name,
            description=description,
            parent_id=parent_id,
            order=order,
            is_active=True,
            created_at=datetime.now(),
        )
        self.category_repository.save_category(category)
        return Success(category_id)

    def update_category(self, user: User, category_id: str, **updates) -> Result[None, str]:
        """범주 정보를 수정합니다.

        Args:
            user: 사용자 엔티티
            category_id: 범주 식별자
            **updates: 수정할 필드 (name, description, order, is_active)

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        if user.role != Role.TENANT_ADMIN:
            return Failure("범주 관리는 테넌트 관리자만 가능합니다")

        category = self.category_repository.find_category_by_id(category_id)
        if not category:
            return Failure(f"범주를 찾을 수 없습니다: {category_id}")

        if category.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 범주에 접근할 수 없습니다")

        if "is_active" in updates and updates["is_active"] is False:
            if self.category_repository.has_subcategories(category_id):
                subcategories = self.category_repository.find_by_parent_id(category_id, user.tenant_id)
                for subcat in subcategories:
                    if subcat.is_active:
                        self.category_repository.update_category(subcat.id, is_active=False)

        try:
            self.category_repository.update_category(category_id, **updates)
            return Success(None)
        except ValueError as e:
            return Failure(str(e))

    def delete_category(self, user: User, category_id: str) -> Result[None, str]:
        """범주를 삭제합니다.

        Args:
            user: 사용자 엔티티
            category_id: 범주 식별자

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        if user.role != Role.TENANT_ADMIN:
            return Failure("범주 관리는 테넌트 관리자만 가능합니다")

        category = self.category_repository.find_category_by_id(category_id)
        if not category:
            return Failure(f"범주를 찾을 수 없습니다: {category_id}")

        if category.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 범주에 접근할 수 없습니다")

        if self.category_repository.has_subcategories(category_id):
            return Failure("하위 범주가 있는 범주는 삭제할 수 없습니다")

        try:
            self.category_repository.delete_category(category_id)
            return Success(None)
        except ValueError as e:
            return Failure(str(e))

    def list_categories(self, user: User, parent_id: str | None = None) -> Result[list[Category], str]:
        """범주 목록을 조회합니다.

        Args:
            user: 사용자 엔티티
            parent_id: 상위 범주 식별자 (None이면 최상위 범주)

        Returns:
            Success[범주 목록] 또는 Failure[에러 메시지]
        """
        if parent_id:
            parent = self.category_repository.find_category_by_id(parent_id)
            if not parent:
                return Failure(f"상위 범주를 찾을 수 없습니다: {parent_id}")

            if parent.tenant_id != user.tenant_id:
                return Failure("다른 테넌트의 범주에 접근할 수 없습니다")

        categories = self.category_repository.find_by_parent_id(parent_id, user.tenant_id)
        active_categories = [c for c in categories if c.is_active]
        return Success(active_categories)

    def get_category(self, user: User, category_id: str) -> Result[Category, str]:
        """범주를 조회합니다.

        Args:
            user: 사용자 엔티티
            category_id: 범주 식별자

        Returns:
            Success[범주 엔티티] 또는 Failure[에러 메시지]
        """
        category = self.category_repository.find_category_by_id(category_id)
        if not category:
            return Failure(f"범주를 찾을 수 없습니다: {category_id}")

        if category.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 범주에 접근할 수 없습니다")

        return Success(category)

    def get_all_categories(self, user: User) -> Result[list[Category], str]:
        """모든 범주를 조회합니다.

        Args:
            user: 사용자 엔티티

        Returns:
            Success[범주 목록] 또는 Failure[에러 메시지]
        """
        all_categories = self.category_repository.find_by_tenant_id(user.tenant_id)
        active_categories = [c for c in all_categories if c.is_active]
        return Success(active_categories)
