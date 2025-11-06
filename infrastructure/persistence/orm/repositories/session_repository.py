"""SQLAlchemy 기반 SessionRepository 구현체"""

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from domain.repositories.session_repository import SessionRepository
from domain.entities.session import Session as SessionEntity
from infrastructure.persistence.orm.models.session import SessionORM
from infrastructure.persistence.orm.mappers.session_mapper import (
    session_orm_to_entity,
    session_entity_to_orm
)


class SqlAlchemySessionRepository(SessionRepository):
    """SQLAlchemy를 사용한 세션 저장소 구현체입니다."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """저장소를 초기화합니다.

        Args:
            session_factory: SQLAlchemy 세션 팩토리
        """
        self.session_factory = session_factory

    def save_session(self, session: SessionEntity) -> None:
        """세션을 저장합니다.

        Args:
            session: 저장할 세션 엔티티

        Raises:
            ValueError: 중복된 API 키가 있는 경우
        """
        with self.session_factory() as db_session:
            try:
                orm = session_entity_to_orm(session)
                db_session.add(orm)
                db_session.commit()
            except IntegrityError as e:
                db_session.rollback()
                raise ValueError(f"세션 저장 실패: {str(e)}")

    def find_session_by_api_key(self, api_key: str) -> SessionEntity | None:
        """API 키로 세션을 조회합니다.

        Args:
            api_key: API 키

        Returns:
            세션 엔티티 또는 None
        """
        with self.session_factory() as db_session:
            orm = db_session.query(SessionORM).filter_by(api_key=api_key).first()
            if not orm:
                return None
            return session_orm_to_entity(orm)

    def find_session_by_user_id(self, user_id: str) -> SessionEntity | None:
        """사용자 ID로 세션을 조회합니다.

        Args:
            user_id: 사용자 식별자

        Returns:
            세션 엔티티 또는 None
        """
        with self.session_factory() as db_session:
            # 가장 최근 세션 반환
            orm = db_session.query(SessionORM).filter_by(
                user_id=user_id
            ).order_by(SessionORM.created_at.desc()).first()
            if not orm:
                return None
            return session_orm_to_entity(orm)

    def delete_session(self, session_id: str) -> None:
        """세션을 삭제합니다.

        Args:
            session_id: 세션 식별자
        """
        with self.session_factory() as db_session:
            orm = db_session.query(SessionORM).filter_by(id=session_id).first()
            if orm:
                db_session.delete(orm)
                db_session.commit()