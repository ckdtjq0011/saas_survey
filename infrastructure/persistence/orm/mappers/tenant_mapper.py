"""Tenant ORM과 도메인 엔티티 간 변환 매퍼"""

from domain.entities.tenant import Tenant
from infrastructure.persistence.orm.models.tenant import TenantORM


def tenant_orm_to_entity(orm: TenantORM) -> Tenant:
    """TenantORM을 Tenant 엔티티로 변환합니다.

    Args:
        orm: TenantORM 인스턴스

    Returns:
        Tenant 엔티티
    """
    return Tenant(
        id=orm.id,
        name=orm.name,
        created_at=orm.created_at,
        is_active=orm.is_active
    )


def tenant_entity_to_orm(entity: Tenant) -> TenantORM:
    """Tenant 엔티티를 TenantORM으로 변환합니다.

    Args:
        entity: Tenant 엔티티

    Returns:
        TenantORM 인스턴스
    """
    return TenantORM(
        id=entity.id,
        name=entity.name,
        created_at=entity.created_at,
        is_active=entity.is_active
    )