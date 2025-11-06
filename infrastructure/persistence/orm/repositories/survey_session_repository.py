"""SQLAlchemy 기반 SurveySessionRepository 구현체"""

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from domain.repositories.survey_session_repository import SurveySessionRepository
from domain.entities.survey_session import SurveySession
from infrastructure.persistence.orm.models.survey_session import SurveySessionORM
from infrastructure.persistence.orm.mappers.survey_session_mapper import (
    survey_session_orm_to_entity,
    survey_session_entity_to_orm
)


class SqlAlchemySurveySessionRepository(SurveySessionRepository):
    """SQLAlchemy를 사용한 설문 세션 저장소 구현체입니다."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """저장소를 초기화합니다.

        Args:
            session_factory: SQLAlchemy 세션 팩토리
        """
        self.session_factory = session_factory

    def save(self, session: SurveySession) -> None:
        """세션을 저장합니다.

        Args:
            session: 저장할 세션 엔티티

        Raises:
            ValueError: 중복된 ID나 참조 오류가 있는 경우
        """
        with self.session_factory() as db_session:
            try:
                orm = survey_session_entity_to_orm(session)
                db_session.add(orm)
                db_session.commit()
            except IntegrityError as e:
                db_session.rollback()
                raise ValueError(f"세션 저장 실패: {str(e)}")

    def find_by_id(self, session_id: str) -> SurveySession | None:
        """세션 ID로 세션을 조회합니다.

        Args:
            session_id: 세션 식별자

        Returns:
            세션 엔티티 또는 None
        """
        with self.session_factory() as db_session:
            orm = db_session.query(SurveySessionORM).filter_by(id=session_id).first()
            if not orm:
                return None
            return survey_session_orm_to_entity(orm)

    def find_by_respondent_and_survey(self, respondent_id: str, survey_id: str) -> list[SurveySession]:
        """응답자 ID와 설문 ID로 세션 목록을 조회합니다.

        Args:
            respondent_id: 응답자 식별자
            survey_id: 설문 식별자

        Returns:
            세션 엔티티 목록
        """
        with self.session_factory() as db_session:
            orms = db_session.query(SurveySessionORM).filter_by(
                respondent_id=respondent_id,
                survey_id=survey_id
            ).order_by(SurveySessionORM.started_at.desc()).all()
            return [survey_session_orm_to_entity(orm) for orm in orms]

    def update_session(self, session: SurveySession) -> None:
        """세션을 수정합니다.

        Args:
            session: 수정할 세션 엔티티

        Raises:
            ValueError: 세션을 찾을 수 없는 경우
        """
        with self.session_factory() as db_session:
            orm = db_session.query(SurveySessionORM).filter_by(id=session.id).first()
            if not orm:
                raise ValueError(f"세션을 찾을 수 없습니다: {session.id}")

            # 모든 필드 업데이트
            orm.survey_id = session.survey_id
            orm.respondent_id = session.respondent_id
            orm.started_at = session.started_at
            orm.submitted_at = session.submitted_at
            orm.completed = session.completed
            orm.completion_percentage = session.completion_percentage
            orm.user_agent = session.user_agent
            orm.total_time_spent_seconds = session.total_time_spent_seconds

            db_session.commit()

    def delete_session(self, session_id: str) -> None:
        """세션을 삭제합니다.

        Args:
            session_id: 세션 식별자

        Raises:
            ValueError: 세션을 찾을 수 없는 경우
        """
        with self.session_factory() as db_session:
            orm = db_session.query(SurveySessionORM).filter_by(id=session_id).first()
            if not orm:
                raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

            db_session.delete(orm)
            db_session.commit()