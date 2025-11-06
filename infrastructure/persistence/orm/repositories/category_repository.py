"""SQLAlchemy 기반 CategoryRepository 구현체"""

from typing import Any
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from domain.repositories.category_repository import CategoryRepository
from domain.entities.category import Category
from infrastructure.persistence.orm.models.category import CategoryORM
from infrastructure.persistence.orm.mappers.category_mapper import (
    category_orm_to_entity,
    category_entity_to_orm
)


class SqlAlchemyCategoryRepository(CategoryRepository):
    """SQLAlchemy를 사용한 범주 저장소 구현체입니다."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """저장소를 초기화합니다.

        Args:
            session_factory: SQLAlchemy 세션 팩토리
        """
        self.session_factory = session_factory

    def save_category(self, category: Category) -> None:
        """범주를 저장합니다.

        Args:
            category: 저장할 범주 엔티티

        Raises:
            ValueError: 중복된 ID나 참조 오류가 있는 경우
        """
        with self.session_factory() as session:
            try:
                orm = category_entity_to_orm(category)
                session.add(orm)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"범주 저장 실패: {str(e)}")

    def find_category_by_id(self, category_id: str) -> Category | None:
        """ID로 범주를 조회합니다.

        Args:
            category_id: 범주 식별자

        Returns:
            범주 엔티티 또는 None
        """
        with self.session_factory() as session:
            orm = session.query(CategoryORM).filter_by(id=category_id).first()
            if not orm:
                return None
            return category_orm_to_entity(orm)

    def find_all_categories(self) -> list[Category]:
        """모든 범주를 조회합니다.

        Returns:
            범주 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(CategoryORM).order_by(
                CategoryORM.order,
                CategoryORM.name
            ).all()
            return [category_orm_to_entity(orm) for orm in orms]

    def find_by_tenant_id(self, tenant_id: str) -> list[Category]:
        """테넌트 ID로 범주 목록을 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            범주 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(CategoryORM).filter_by(
                tenant_id=tenant_id
            ).order_by(
                CategoryORM.order,
                CategoryORM.name
            ).all()
            return [category_orm_to_entity(orm) for orm in orms]

    def find_by_parent_id(self, parent_id: str | None, tenant_id: str) -> list[Category]:
        """상위 범주 ID로 하위 범주 목록을 조회합니다.

        Args:
            parent_id: 상위 범주 식별자 (None이면 최상위 범주)
            tenant_id: 테넌트 식별자

        Returns:
            범주 엔티티 목록 (order 순으로 정렬)
        """
        with self.session_factory() as session:
            query = session.query(CategoryORM).filter_by(tenant_id=tenant_id)

            if parent_id is None:
                # 최상위 범주 조회
                query = query.filter(CategoryORM.parent_id.is_(None))
            else:
                # 특정 범주의 하위 범주 조회
                query = query.filter_by(parent_id=parent_id)

            orms = query.order_by(CategoryORM.order, CategoryORM.name).all()
            return [category_orm_to_entity(orm) for orm in orms]

    def update_category(self, category_id: str, **updates: Any) -> None:
        """범주 정보를 수정합니다.

        Args:
            category_id: 범주 식별자
            **updates: 수정할 필드 (name, description, order, is_active 등)

        Raises:
            ValueError: 범주를 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(CategoryORM).filter_by(id=category_id).first()
            if not orm:
                raise ValueError(f"범주를 찾을 수 없습니다: {category_id}")

            # 허용된 필드만 업데이트
            allowed_fields = {"name", "description", "parent_id", "order", "is_active"}
            for key, value in updates.items():
                if key in allowed_fields and hasattr(orm, key):
                    setattr(orm, key, value)

            session.commit()

    def delete_category(self, category_id: str) -> None:
        """범주를 삭제합니다.

        Args:
            category_id: 범주 식별자

        Raises:
            ValueError: 범주를 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(CategoryORM).filter_by(id=category_id).first()
            if not orm:
                raise ValueError(f"범주를 찾을 수 없습니다: {category_id}")

            session.delete(orm)
            session.commit()

    def has_subcategories(self, category_id: str) -> bool:
        """범주에 하위 범주가 있는지 확인합니다.

        Args:
            category_id: 범주 식별자

        Returns:
            하위 범주가 있으면 True, 없으면 False
        """
        with self.session_factory() as session:
            count = session.query(CategoryORM).filter_by(
                parent_id=category_id
            ).count()
            return count > 0