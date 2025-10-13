import uuid
from datetime import datetime
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.value_objects.types import QuestionType
from domain.repositories.survey_repository import SurveyRepository


class SurveyService:
    """설문 관련 유스케이스를 처리하는 서비스입니다.

    Attributes:
        survey_repository: 설문 저장소
    """

    def __init__(self, survey_repository: SurveyRepository):
        """서비스를 초기화합니다.

        Args:
            survey_repository: 설문 저장소 구현체
        """
        self.survey_repository = survey_repository

    def create_survey(self, title: str, description: str) -> str:
        """새 설문을 생성합니다.

        Args:
            title: 설문 제목
            description: 설문 설명

        Returns:
            생성된 설문의 ID
        """
        survey_id = str(uuid.uuid4())
        survey = Survey(
            id=survey_id,
            title=title,
            description=description,
            created_at=datetime.now(),
            questions=(),
        )
        self.survey_repository.save_survey(survey)
        return survey_id

    def add_question(
        self, survey_id: str, text: str, question_type: QuestionType, options: list[str] | None = None
    ) -> str:
        """설문에 질문을 추가합니다.

        Args:
            survey_id: 설문 식별자
            text: 질문 내용
            question_type: 질문 유형
            options: 객관식 선택지

        Returns:
            생성된 질문의 ID

        Raises:
            ValueError: 설문을 찾을 수 없는 경우
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            raise ValueError(f"설문을 찾을 수 없습니다: {survey_id}")

        question_id = str(uuid.uuid4())
        question = Question(
            id=question_id,
            survey_id=survey_id,
            text=text,
            question_type=question_type,
            options=tuple(options) if options else None,
        )
        self.survey_repository.save_question(question)
        return question_id

    def get_survey(self, survey_id: str) -> Survey:
        """설문을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            설문 엔티티

        Raises:
            ValueError: 설문을 찾을 수 없는 경우
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            raise ValueError(f"설문을 찾을 수 없습니다: {survey_id}")
        return survey

    def get_all_surveys(self) -> list[Survey]:
        """모든 설문을 조회합니다.

        Returns:
            설문 엔티티 목록
        """
        return self.survey_repository.find_all_surveys()
