"""Session ORM과 도메인 엔티티 간 변환 매퍼"""

from domain.entities.session import Session
from infrastructure.persistence.orm.models.session import SessionORM


def session_orm_to_entity(orm: SessionORM) -> Session:
    """SessionORM을 Session 엔티티로 변환합니다.

    Args:
        orm: SessionORM 인스턴스

    Returns:
        Session 엔티티
    """
    return Session(
        id=orm.id,
        user_id=orm.user_id,
        tenant_id=orm.tenant_id,
        api_key=orm.api_key,
        expires_at=orm.expires_at,
        created_at=orm.created_at
    )


def session_entity_to_orm(entity: Session) -> SessionORM:
    """Session 엔티티를 SessionORM으로 변환합니다.

    Args:
        entity: Session 엔티티

    Returns:
        SessionORM 인스턴스
    """
    return SessionORM(
        id=entity.id,
        user_id=entity.user_id,
        tenant_id=entity.tenant_id,
        api_key=entity.api_key,
        expires_at=entity.expires_at,
        created_at=entity.created_at
    )