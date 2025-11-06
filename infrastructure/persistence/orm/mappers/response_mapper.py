"""Response 및 ResponseHistory ORM과 도메인 엔티티 간 변환 매퍼"""

from domain.entities.response import Response
from domain.entities.response_history import ResponseHistory
from infrastructure.persistence.orm.models.response import ResponseORM
from infrastructure.persistence.orm.models.response_history import ResponseHistoryORM


def response_orm_to_entity(orm: ResponseORM) -> Response:
    """ResponseORM을 Response 엔티티로 변환합니다.

    Args:
        orm: ResponseORM 인스턴스

    Returns:
        Response 엔티티
    """
    return Response(
        id=orm.id,
        survey_id=orm.survey_id,
        question_id=orm.question_id,
        answer=orm.answer,
        respondent_id=orm.respondent_id,
        answered_at=orm.answered_at,
        session_id=orm.session_id,
        time_spent_seconds=orm.time_spent_seconds
    )


def response_entity_to_orm(entity: Response) -> ResponseORM:
    """Response 엔티티를 ResponseORM으로 변환합니다.

    Args:
        entity: Response 엔티티

    Returns:
        ResponseORM 인스턴스
    """
    return ResponseORM(
        id=entity.id,
        survey_id=entity.survey_id,
        question_id=entity.question_id,
        answer=entity.answer,
        respondent_id=entity.respondent_id,
        answered_at=entity.answered_at,
        session_id=entity.session_id,
        time_spent_seconds=entity.time_spent_seconds
    )


def response_history_orm_to_entity(orm: ResponseHistoryORM) -> ResponseHistory:
    """ResponseHistoryORM을 ResponseHistory 엔티티로 변환합니다.

    Args:
        orm: ResponseHistoryORM 인스턴스

    Returns:
        ResponseHistory 엔티티
    """
    return ResponseHistory(
        id=orm.id,
        response_id=orm.response_id,
        old_answer=orm.old_answer,
        new_answer=orm.new_answer,
        updated_at=orm.updated_at,
        updated_by=orm.updated_by
    )


def response_history_entity_to_orm(entity: ResponseHistory) -> ResponseHistoryORM:
    """ResponseHistory 엔티티를 ResponseHistoryORM으로 변환합니다.

    Args:
        entity: ResponseHistory 엔티티

    Returns:
        ResponseHistoryORM 인스턴스
    """
    return ResponseHistoryORM(
        id=entity.id,
        response_id=entity.response_id,
        old_answer=entity.old_answer,
        new_answer=entity.new_answer,
        updated_at=entity.updated_at,
        updated_by=entity.updated_by
    )