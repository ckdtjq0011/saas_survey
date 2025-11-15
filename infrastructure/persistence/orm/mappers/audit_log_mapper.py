"""감사 로그 엔티티와 ORM 모델 간 매퍼"""

from domain.entities.audit_log import AuditLog
from domain.value_objects.audit_action import AuditAction
from infrastructure.persistence.orm.models.audit_log import AuditLogORM


def audit_log_entity_to_orm(entity: AuditLog) -> AuditLogORM:
    """AuditLog 엔티티를 ORM 모델로 변환합니다.

    Args:
        entity: AuditLog 엔티티

    Returns:
        AuditLogORM 모델
    """
    return AuditLogORM(
        id=entity.id,
        timestamp=entity.timestamp,
        tenant_id=entity.tenant_id,
        user_id=entity.user_id,
        action=entity.action.value,
        resource_type=entity.resource_type,
        resource_id=entity.resource_id,
        result=entity.result,
        ip_address=entity.ip_address,
        details=entity.details
    )


def audit_log_orm_to_entity(orm: AuditLogORM) -> AuditLog:
    """ORM 모델을 AuditLog 엔티티로 변환합니다.

    Args:
        orm: AuditLogORM 모델

    Returns:
        AuditLog 엔티티
    """
    return AuditLog(
        id=orm.id,
        timestamp=orm.timestamp,
        tenant_id=orm.tenant_id,
        user_id=orm.user_id,
        action=AuditAction(orm.action),
        resource_type=orm.resource_type,
        resource_id=orm.resource_id,
        result=orm.result,
        ip_address=orm.ip_address,
        details=orm.details
    )
