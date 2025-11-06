"""Survey 및 Question ORM과 도메인 엔티티 간 변환 매퍼"""

from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.value_objects.types import QuestionType
from infrastructure.persistence.orm.models.survey import SurveyORM, QuestionORM


# Options delimiter - ASCII 31 (Unit Separator)
OPTIONS_DELIMITER = "\x1f"


def question_orm_to_entity(orm: QuestionORM) -> Question:
    """QuestionORM을 Question 엔티티로 변환합니다.

    Args:
        orm: QuestionORM 인스턴스

    Returns:
        Question 엔티티
    """
    options = None
    if orm.options:
        # Backward compatibility: 파이프(|) 구분자 지원
        if OPTIONS_DELIMITER in orm.options:
            options = tuple(orm.options.split(OPTIONS_DELIMITER))
        elif "|" in orm.options:
            options = tuple(orm.options.split("|"))
        else:
            # 단일 옵션인 경우
            options = (orm.options,) if orm.options.strip() else None

    return Question(
        id=orm.id,
        survey_id=orm.survey_id,
        text=orm.text,
        question_type=QuestionType(orm.question_type),
        order=orm.order,
        is_required=orm.is_required,
        options=options,
        category_id=orm.category_id
    )


def question_entity_to_orm(entity: Question) -> QuestionORM:
    """Question 엔티티를 QuestionORM으로 변환합니다.

    Args:
        entity: Question 엔티티

    Returns:
        QuestionORM 인스턴스
    """
    options_str = None
    if entity.options:
        options_str = OPTIONS_DELIMITER.join(entity.options)

    return QuestionORM(
        id=entity.id,
        survey_id=entity.survey_id,
        text=entity.text,
        question_type=entity.question_type.value,
        order=entity.order,
        is_required=entity.is_required,
        options=options_str,
        category_id=entity.category_id
    )


def survey_orm_to_entity(orm: SurveyORM, include_questions: bool = True) -> Survey:
    """SurveyORM을 Survey 엔티티로 변환합니다.

    Args:
        orm: SurveyORM 인스턴스
        include_questions: 질문 포함 여부

    Returns:
        Survey 엔티티
    """
    questions = ()
    if include_questions and orm.questions:
        questions = tuple(question_orm_to_entity(q) for q in orm.questions)

    return Survey(
        id=orm.id,
        tenant_id=orm.tenant_id,
        owner_id=orm.owner_id,
        title=orm.title,
        description=orm.description,
        created_at=orm.created_at,
        questions=questions
    )


def survey_entity_to_orm(entity: Survey, include_questions: bool = True) -> SurveyORM:
    """Survey 엔티티를 SurveyORM으로 변환합니다.

    Args:
        entity: Survey 엔티티
        include_questions: 질문 포함 여부

    Returns:
        SurveyORM 인스턴스
    """
    orm = SurveyORM(
        id=entity.id,
        tenant_id=entity.tenant_id,
        owner_id=entity.owner_id,
        title=entity.title,
        description=entity.description,
        created_at=entity.created_at
    )

    if include_questions and entity.questions:
        orm.questions = [question_entity_to_orm(q) for q in entity.questions]

    return orm