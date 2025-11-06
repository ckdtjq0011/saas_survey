"""SQLAlchemy 기반 SurveyRepository 구현체"""

from typing import Any
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from domain.repositories.survey_repository import SurveyRepository
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.value_objects.types import QuestionType
from infrastructure.persistence.orm.models.survey import SurveyORM, QuestionORM
from infrastructure.persistence.orm.mappers.survey_mapper import (
    survey_orm_to_entity,
    survey_entity_to_orm,
    question_orm_to_entity,
    question_entity_to_orm
)


class SqlAlchemySurveyRepository(SurveyRepository):
    """SQLAlchemy를 사용한 설문 저장소 구현체입니다."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """저장소를 초기화합니다.

        Args:
            session_factory: SQLAlchemy 세션 팩토리
        """
        self.session_factory = session_factory

    def save_survey(self, survey: Survey) -> None:
        """설문을 저장합니다.

        Args:
            survey: 저장할 설문 엔티티

        Raises:
            ValueError: 중복된 ID가 있는 경우
        """
        with self.session_factory() as session:
            try:
                orm = survey_entity_to_orm(survey, include_questions=True)
                session.add(orm)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"설문 저장 실패: {str(e)}")

    def save_question(self, question: Question) -> None:
        """질문을 저장합니다.

        Args:
            question: 저장할 질문 엔티티

        Raises:
            ValueError: 중복된 ID가 있는 경우
        """
        with self.session_factory() as session:
            try:
                orm = question_entity_to_orm(question)
                session.add(orm)
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"질문 저장 실패: {str(e)}")

    def find_survey_by_id(self, survey_id: str) -> Survey | None:
        """ID로 설문을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            설문 엔티티 또는 None
        """
        with self.session_factory() as session:
            orm = session.query(SurveyORM).filter_by(id=survey_id).first()
            if not orm:
                return None
            return survey_orm_to_entity(orm, include_questions=True)

    def find_all_surveys(self) -> list[Survey]:
        """모든 설문을 조회합니다.

        Returns:
            설문 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(SurveyORM).order_by(SurveyORM.created_at.desc()).all()
            return [survey_orm_to_entity(orm, include_questions=True) for orm in orms]

    def find_questions_by_survey_id(self, survey_id: str) -> list[Question]:
        """설문 ID로 질문 목록을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            질문 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(QuestionORM).filter_by(
                survey_id=survey_id
            ).order_by(QuestionORM.order).all()
            return [question_orm_to_entity(orm) for orm in orms]

    def find_by_owner_id(self, owner_id: str) -> list[Survey]:
        """소유자 ID로 설문 목록을 조회합니다.

        Args:
            owner_id: 소유자 식별자

        Returns:
            설문 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(SurveyORM).filter_by(
                owner_id=owner_id
            ).order_by(SurveyORM.created_at.desc()).all()
            return [survey_orm_to_entity(orm, include_questions=True) for orm in orms]

    def find_by_tenant_id(self, tenant_id: str) -> list[Survey]:
        """테넌트 ID로 설문 목록을 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            설문 엔티티 목록
        """
        with self.session_factory() as session:
            orms = session.query(SurveyORM).filter_by(
                tenant_id=tenant_id
            ).order_by(SurveyORM.created_at.desc()).all()
            return [survey_orm_to_entity(orm, include_questions=True) for orm in orms]

    def update_survey(self, survey_id: str, **updates: Any) -> None:
        """설문 정보를 수정합니다.

        Args:
            survey_id: 설문 식별자
            **updates: 수정할 필드 (title, description 등)

        Raises:
            ValueError: 설문을 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(SurveyORM).filter_by(id=survey_id).first()
            if not orm:
                raise ValueError(f"설문을 찾을 수 없습니다: {survey_id}")

            # 허용된 필드만 업데이트
            allowed_fields = {"title", "description"}
            for key, value in updates.items():
                if key in allowed_fields and hasattr(orm, key):
                    setattr(orm, key, value)

            session.commit()

    def update_question(self, question_id: str, **updates: Any) -> None:
        """질문 정보를 수정합니다.

        Args:
            question_id: 질문 식별자
            **updates: 수정할 필드 (text, options 등)

        Raises:
            ValueError: 질문을 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(QuestionORM).filter_by(id=question_id).first()
            if not orm:
                raise ValueError(f"질문을 찾을 수 없습니다: {question_id}")

            # 허용된 필드만 업데이트
            allowed_fields = {"text", "question_type", "order", "is_required", "options", "category_id"}
            OPTIONS_DELIMITER = "\x1f"

            for key, value in updates.items():
                if key in allowed_fields:
                    if key == "options":
                        # 리스트/튜플을 문자열로 변환
                        if isinstance(value, (list, tuple)):
                            value = OPTIONS_DELIMITER.join(value) if value else None
                    elif key == "question_type":
                        # QuestionType enum을 문자열로 변환
                        if isinstance(value, QuestionType):
                            value = value.value

                    if hasattr(orm, key):
                        setattr(orm, key, value)

            session.commit()

    def delete_survey(self, survey_id: str) -> None:
        """설문을 삭제합니다.

        Args:
            survey_id: 설문 식별자

        Raises:
            ValueError: 설문을 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(SurveyORM).filter_by(id=survey_id).first()
            if not orm:
                raise ValueError(f"설문을 찾을 수 없습니다: {survey_id}")

            session.delete(orm)
            session.commit()

    def delete_question(self, question_id: str) -> None:
        """질문을 삭제합니다.

        Args:
            question_id: 질문 식별자

        Raises:
            ValueError: 질문을 찾을 수 없는 경우
        """
        with self.session_factory() as session:
            orm = session.query(QuestionORM).filter_by(id=question_id).first()
            if not orm:
                raise ValueError(f"질문을 찾을 수 없습니다: {question_id}")

            session.delete(orm)
            session.commit()