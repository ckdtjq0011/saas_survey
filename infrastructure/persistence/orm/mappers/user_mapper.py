"""User ORM과 도메인 엔티티 간 변환 매퍼"""

from domain.entities.user import User
from domain.value_objects.role import Role
from infrastructure.persistence.orm.models.user import UserORM


def user_orm_to_entity(orm: UserORM) -> User:
    """UserORM을 User 엔티티로 변환합니다.

    Args:
        orm: UserORM 인스턴스

    Returns:
        User 엔티티
    """
    return User(
        id=orm.id,
        tenant_id=orm.tenant_id,
        username=orm.username,
        email=orm.email,
        password_hash=orm.password_hash,
        role=Role(orm.role),
        created_at=orm.created_at,
        is_active=orm.is_active
    )


def user_entity_to_orm(entity: User) -> UserORM:
    """User 엔티티를 UserORM으로 변환합니다.

    Args:
        entity: User 엔티티

    Returns:
        UserORM 인스턴스
    """
    return UserORM(
        id=entity.id,
        tenant_id=entity.tenant_id,
        username=entity.username,
        email=entity.email,
        password_hash=entity.password_hash,
        role=entity.role.value,
        created_at=entity.created_at,
        is_active=entity.is_active
    )