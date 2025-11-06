"""SQLAlchemy 기반 UserRepository 구현체"""

from typing import Any
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from domain.repositories.user_repository import UserRepository
from domain.entities.user import User
from domain.value_objects.role import Role
from infrastructure.persistence.orm.models.user import UserORM
from infrastructure.persistence.orm.mappers.user_mapper import (
    user_orm_to_entity,
    user_entity_to_orm
)


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy를 사용한 사용자 저장소 구현체입니다."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """저장소를 초기화합니다.

        Args:
            session_factory: SQLAlchemy 세션 팩토리
        """
        self.session_factory = session_factory

    def save_user(self, user: User) -> None:
        """사용자를 저장합니다.

        Args:
            user: 저장할 사용자 엔티티

        Raises:
            ValueError: 중복된 사용자명이나 ID가 있는 경우
        """
        with self.session_factory() as session:
            try:
                orm = user_entity_to_orm(user)
                session.add(orm)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"사용자 저장 실패: {str(e)}")

    def find_user_by_id(self, user_id: str) -> User | None:
        """ID로 사용자를 조회합니다.

        Args:
            user_id: 사용자 식별자

        Returns:
            사용자 엔티티 또는 None
        """
        with self.session_factory() as session:
            orm = session.query(UserORM).filter_by(id=user_id).first()
            if not orm:
                return None
            return user_orm_to_entity(orm)

    def find_user_by_username(self, username: str, tenant_id: str) -> User | None:
        """사용자명으로 사용자를 조회합니다.

        Args:
            username: 사용자명
            tenant_id: 테넌트 식별자

        Returns:
            사용자 엔티티 또는 None
        """
        with self.session_factory() as session:
            orm = session.query(UserORM).filter_by(
                username=username,
                tenant_id=tenant_id
            ).first()
            if not orm:
                return None
            return user_orm_to_entity(orm)

    def find_users_by_tenant(self, tenant_id: str) -> list[User]:
        """테넌트의 모든 사용자를 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            사용자 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(UserORM).filter_by(
                tenant_id=tenant_id
            ).order_by(UserORM.created_at).all()
            return [user_orm_to_entity(orm) for orm in orms]

    def update_user(self, user_id: str, **updates: Any) -> None:
        """사용자 정보를 수정합니다.

        Args:
            user_id: 사용자 식별자
            **updates: 수정할 필드 (email, password_hash, role, is_active 등)

        Raises:
            ValueError: 사용자를 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(UserORM).filter_by(id=user_id).first()
            if not orm:
                raise ValueError(f"사용자를 찾을 수 없습니다: {user_id}")

            # 허용된 필드만 업데이트
            allowed_fields = {"email", "password_hash", "role", "is_active"}
            for key, value in updates.items():
                if key in allowed_fields:
                    if key == "role":
                        # Role enum을 문자열로 변환
                        if isinstance(value, Role):
                            value = value.value
                    if hasattr(orm, key):
                        setattr(orm, key, value)

            session.commit()

    def delete_user(self, user_id: str) -> None:
        """사용자를 삭제합니다.

        Args:
            user_id: 사용자 식별자

        Raises:
            ValueError: 사용자를 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(UserORM).filter_by(id=user_id).first()
            if not orm:
                raise ValueError(f"사용자를 찾을 수 없습니다: {user_id}")

            session.delete(orm)
            session.commit()