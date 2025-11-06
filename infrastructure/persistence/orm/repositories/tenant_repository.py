"""SQLAlchemy 기반 TenantRepository 구현체"""

from typing import Any
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from domain.repositories.tenant_repository import TenantRepository
from domain.entities.tenant import Tenant
from infrastructure.persistence.orm.models.tenant import TenantORM
from infrastructure.persistence.orm.mappers.tenant_mapper import (
    tenant_orm_to_entity,
    tenant_entity_to_orm
)


class SqlAlchemyTenantRepository(TenantRepository):
    """SQLAlchemy를 사용한 테넌트 저장소 구현체입니다."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """저장소를 초기화합니다.

        Args:
            session_factory: SQLAlchemy 세션 팩토리
        """
        self.session_factory = session_factory

    def save_tenant(self, tenant: Tenant) -> None:
        """테넌트를 저장합니다.

        Args:
            tenant: 저장할 테넌트 엔티티

        Raises:
            ValueError: 중복된 ID가 있는 경우
        """
        with self.session_factory() as session:
            try:
                orm = tenant_entity_to_orm(tenant)
                session.add(orm)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"테넌트 저장 실패: {str(e)}")

    def find_tenant_by_id(self, tenant_id: str) -> Tenant | None:
        """ID로 테넌트를 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            테넌트 엔티티 또는 None
        """
        with self.session_factory() as session:
            orm = session.query(TenantORM).filter_by(id=tenant_id).first()
            if not orm:
                return None
            return tenant_orm_to_entity(orm)

    def find_all_tenants(self) -> list[Tenant]:
        """모든 테넌트를 조회합니다.

        Returns:
            테넌트 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(TenantORM).order_by(TenantORM.created_at).all()
            return [tenant_orm_to_entity(orm) for orm in orms]

    def update_tenant(self, tenant_id: str, **updates: Any) -> None:
        """테넌트 정보를 수정합니다.

        Args:
            tenant_id: 테넌트 식별자
            **updates: 수정할 필드 (name, is_active 등)

        Raises:
            ValueError: 테넌트를 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(TenantORM).filter_by(id=tenant_id).first()
            if not orm:
                raise ValueError(f"테넌트를 찾을 수 없습니다: {tenant_id}")

            # 허용된 필드만 업데이트
            allowed_fields = {"name", "is_active"}
            for key, value in updates.items():
                if key in allowed_fields and hasattr(orm, key):
                    setattr(orm, key, value)

            session.commit()

    def delete_tenant(self, tenant_id: str) -> None:
        """테넌트를 삭제합니다.

        Args:
            tenant_id: 테넌트 식별자

        Raises:
            ValueError: 테넌트를 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(TenantORM).filter_by(id=tenant_id).first()
            if not orm:
                raise ValueError(f"테넌트를 찾을 수 없습니다: {tenant_id}")

            session.delete(orm)
            session.commit()