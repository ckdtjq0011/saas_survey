"""SQLAlchemy 기반 ResponseRepository 구현체"""

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from domain.repositories.response_repository import ResponseRepository
from domain.entities.response import Response
from infrastructure.persistence.orm.models.response import ResponseORM
from infrastructure.persistence.orm.mappers.response_mapper import (
    response_orm_to_entity,
    response_entity_to_orm
)


class SqlAlchemyResponseRepository(ResponseRepository):
    """SQLAlchemy를 사용한 응답 저장소 구현체입니다."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """저장소를 초기화합니다.

        Args:
            session_factory: SQLAlchemy 세션 팩토리
        """
        self.session_factory = session_factory

    def save(self, response: Response) -> None:
        """응답을 저장합니다.

        Args:
            response: 저장할 응답 엔티티

        Raises:
            ValueError: 중복된 ID나 참조 오류가 있는 경우
        """
        with self.session_factory() as session:
            try:
                orm = response_entity_to_orm(response)
                session.add(orm)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"응답 저장 실패: {str(e)}")

    def find_by_survey_id(self, survey_id: str) -> list[Response]:
        """설문 ID로 응답 목록을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            응답 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(ResponseORM).filter_by(
                survey_id=survey_id
            ).order_by(ResponseORM.answered_at).all()
            return [response_orm_to_entity(orm) for orm in orms]

    def find_by_question_id(self, question_id: str) -> list[Response]:
        """질문 ID로 응답 목록을 조회합니다.

        Args:
            question_id: 질문 식별자

        Returns:
            응답 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(ResponseORM).filter_by(
                question_id=question_id
            ).order_by(ResponseORM.answered_at).all()
            return [response_orm_to_entity(orm) for orm in orms]

    def find_by_respondent_id(self, respondent_id: str) -> list[Response]:
        """응답자 ID로 응답 목록을 조회합니다.

        Args:
            respondent_id: 응답자 식별자

        Returns:
            응답 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(ResponseORM).filter_by(
                respondent_id=respondent_id
            ).order_by(ResponseORM.answered_at).all()
            return [response_orm_to_entity(orm) for orm in orms]

    def update_response(self, response_id: str, answer: str) -> None:
        """응답을 수정합니다.

        Args:
            response_id: 응답 식별자
            answer: 새로운 답변

        Raises:
            ValueError: 응답을 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(ResponseORM).filter_by(id=response_id).first()
            if not orm:
                raise ValueError(f"응답을 찾을 수 없습니다: {response_id}")

            orm.answer = answer
            session.commit()

    def delete_response(self, response_id: str) -> None:
        """응답을 삭제합니다.

        Args:
            response_id: 응답 식별자

        Raises:
            ValueError: 응답을 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(ResponseORM).filter_by(id=response_id).first()
            if not orm:
                raise ValueError(f"응답을 찾을 수 없습니다: {response_id}")

            session.delete(orm)
            session.commit()

    def delete_by_survey_id(self, survey_id: str) -> None:
        """설문의 모든 응답을 삭제합니다.

        Args:
            survey_id: 설문 식별자
        """
        with self.session_factory() as session:
            session.query(ResponseORM).filter_by(survey_id=survey_id).delete()
            session.commit()