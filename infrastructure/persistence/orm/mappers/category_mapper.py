"""Category ORM과 도메인 엔티티 간 변환 매퍼"""

from domain.entities.category import Category
from infrastructure.persistence.orm.models.category import CategoryORM


def category_orm_to_entity(orm: CategoryORM) -> Category:
    """CategoryORM을 Category 엔티티로 변환합니다.

    Args:
        orm: CategoryORM 인스턴스

    Returns:
        Category 엔티티
    """
    return Category(
        id=orm.id,
        tenant_id=orm.tenant_id,
        name=orm.name,
        description=orm.description,
        parent_id=orm.parent_id,
        order=orm.order,
        is_active=orm.is_active,
        created_at=orm.created_at
    )


def category_entity_to_orm(entity: Category) -> CategoryORM:
    """Category 엔티티를 CategoryORM으로 변환합니다.

    Args:
        entity: Category 엔티티

    Returns:
        CategoryORM 인스턴스
    """
    return CategoryORM(
        id=entity.id,
        tenant_id=entity.tenant_id,
        name=entity.name,
        description=entity.description,
        parent_id=entity.parent_id,
        order=entity.order,
        is_active=entity.is_active,
        created_at=entity.created_at
    )