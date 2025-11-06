"""SurveySession ORM과 도메인 엔티티 간 변환 매퍼"""

from domain.entities.survey_session import SurveySession
from infrastructure.persistence.orm.models.survey_session import SurveySessionORM


def survey_session_orm_to_entity(orm: SurveySessionORM) -> SurveySession:
    """SurveySessionORM을 SurveySession 엔티티로 변환합니다.

    Args:
        orm: SurveySessionORM 인스턴스

    Returns:
        SurveySession 엔티티
    """
    return SurveySession(
        id=orm.id,
        survey_id=orm.survey_id,
        respondent_id=orm.respondent_id,
        started_at=orm.started_at,
        submitted_at=orm.submitted_at,
        completed=orm.completed,
        completion_percentage=orm.completion_percentage,
        user_agent=orm.user_agent,
        total_time_spent_seconds=orm.total_time_spent_seconds
    )


def survey_session_entity_to_orm(entity: SurveySession) -> SurveySessionORM:
    """SurveySession 엔티티를 SurveySessionORM으로 변환합니다.

    Args:
        entity: SurveySession 엔티티

    Returns:
        SurveySessionORM 인스턴스
    """
    return SurveySessionORM(
        id=entity.id,
        survey_id=entity.survey_id,
        respondent_id=entity.respondent_id,
        started_at=entity.started_at,
        submitted_at=entity.submitted_at,
        completed=entity.completed,
        completion_percentage=entity.completion_percentage,
        user_agent=entity.user_agent,
        total_time_spent_seconds=entity.total_time_spent_seconds
    )