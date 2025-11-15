"""SQLAlchemy 기반 AuditLogRepository 구현체"""

from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from domain.entities.audit_log import AuditLog
from domain.repositories.audit_log_repository import AuditLogRepository
from domain.value_objects.audit_action import AuditAction
from infrastructure.persistence.orm.models.audit_log import AuditLogORM
from infrastructure.persistence.orm.mappers.audit_log_mapper import (
    audit_log_entity_to_orm,
    audit_log_orm_to_entity
)


class SqlAlchemyAuditLogRepository(AuditLogRepository):
    """SQLAlchemy를 사용한 감사 로그 저장소 구현체입니다."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """저장소를 초기화합니다.

        Args:
            session_factory: SQLAlchemy 세션 팩토리
        """
        self.session_factory = session_factory

    def save(self, audit_log: AuditLog) -> None:
        """감사 로그를 저장합니다.

        Args:
            audit_log: 저장할 감사 로그 엔티티
        """
        with self.session_factory() as db_session:
            orm = audit_log_entity_to_orm(audit_log)
            db_session.add(orm)
            db_session.commit()

    def find_by_tenant(
        self,
        tenant_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """테넌트별 감사 로그를 조회합니다.

        Args:
            tenant_id: 테넌트 식별자
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            감사 로그 목록
        """
        with self.session_factory() as db_session:
            query = db_session.query(AuditLogORM).filter_by(tenant_id=tenant_id)

            if start_date:
                query = query.filter(AuditLogORM.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLogORM.timestamp <= end_date)

            orms = query.order_by(AuditLogORM.timestamp.desc()).limit(limit).all()
            return [audit_log_orm_to_entity(orm) for orm in orms]

    def find_by_user(
        self,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """사용자별 감사 로그를 조회합니다.

        Args:
            user_id: 사용자 식별자
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            감사 로그 목록
        """
        with self.session_factory() as db_session:
            query = db_session.query(AuditLogORM).filter_by(user_id=user_id)

            if start_date:
                query = query.filter(AuditLogORM.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLogORM.timestamp <= end_date)

            orms = query.order_by(AuditLogORM.timestamp.desc()).limit(limit).all()
            return [audit_log_orm_to_entity(orm) for orm in orms]

    def find_by_action(
        self,
        action: AuditAction,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """액션별 감사 로그를 조회합니다.

        Args:
            action: 액션 타입
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            감사 로그 목록
        """
        with self.session_factory() as db_session:
            query = db_session.query(AuditLogORM).filter_by(action=action.value)

            if start_date:
                query = query.filter(AuditLogORM.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLogORM.timestamp <= end_date)

            orms = query.order_by(AuditLogORM.timestamp.desc()).limit(limit).all()
            return [audit_log_orm_to_entity(orm) for orm in orms]

    def count(self) -> int:
        """전체 감사 로그 개수를 반환합니다.

        Returns:
            감사 로그 개수
        """
        with self.session_factory() as db_session:
            return db_session.query(AuditLogORM).count()
