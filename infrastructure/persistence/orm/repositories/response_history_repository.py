"""SQLAlchemy 기반 ResponseHistoryRepository 구현체"""

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from domain.repositories.response_history_repository import ResponseHistoryRepository
from domain.entities.response_history import ResponseHistory
from infrastructure.persistence.orm.models.response_history import ResponseHistoryORM
from infrastructure.persistence.orm.mappers.response_mapper import (
    response_history_orm_to_entity,
    response_history_entity_to_orm
)


class SqlAlchemyResponseHistoryRepository(ResponseHistoryRepository):
    """SQLAlchemy를 사용한 응답 수정 이력 저장소 구현체입니다."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """저장소를 초기화합니다.

        Args:
            session_factory: SQLAlchemy 세션 팩토리
        """
        self.session_factory = session_factory

    def save(self, history: ResponseHistory) -> None:
        """수정 이력을 저장합니다.

        Args:
            history: 저장할 이력 엔티티

        Raises:
            ValueError: 중복된 ID나 참조 오류가 있는 경우
        """
        with self.session_factory() as session:
            try:
                orm = response_history_entity_to_orm(history)
                session.add(orm)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"수정 이력 저장 실패: {str(e)}")

    def find_by_response_id(self, response_id: str) -> list[ResponseHistory]:
        """응답 ID로 수정 이력 목록을 조회합니다.

        Args:
            response_id: 응답 식별자

        Returns:
            이력 엔티티 목록 (시간순 정렬)
        """
        with self.session_factory() as session:
            orms = session.query(ResponseHistoryORM).filter_by(
                response_id=response_id
            ).order_by(ResponseHistoryORM.updated_at).all()
            return [response_history_orm_to_entity(orm) for orm in orms]