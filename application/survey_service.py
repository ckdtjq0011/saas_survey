import uuid
from datetime import datetime
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.entities.user import User
from domain.value_objects.types import QuestionType
from domain.value_objects.result import Success, Failure, Result
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

    def create_survey(self, user: User, title: str, description: str) -> Result[str, str]:
        """새 설문을 생성합니다.

        Args:
            user: 사용자 엔티티
            title: 설문 제목
            description: 설문 설명

        Returns:
            Success[설문 ID] 또는 Failure[에러 메시지]
        """
        if not user.role.can_create_survey():
            return Failure("설문 생성 권한이 없습니다")

        survey_id = str(uuid.uuid4())
        survey = Survey(
            id=survey_id,
            tenant_id=user.tenant_id,
            owner_id=user.id,
            title=title,
            description=description,
            created_at=datetime.now(),
            questions=(),
        )
        self.survey_repository.save_survey(survey)
        return Success(survey_id)

    def add_question(
        self,
        user: User,
        survey_id: str,
        text: str,
        question_type: QuestionType,
        options: list[str] | None = None,
        category_id: str | None = None
    ) -> Result[str, str]:
        """설문에 질문을 추가합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자
            text: 질문 내용
            question_type: 질문 유형
            options: 객관식 선택지
            category_id: 범주 식별자

        Returns:
            Success[질문 ID] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        is_owner = survey.owner_id == user.id
        if not user.role.can_manage_survey(is_owner):
            return Failure("설문 관리 권한이 없습니다")

        question_id = str(uuid.uuid4())
        question = Question(
            id=question_id,
            survey_id=survey_id,
            text=text,
            question_type=question_type,
            options=tuple(options) if options else None,
            category_id=category_id,
        )
        self.survey_repository.save_question(question)
        return Success(question_id)

    def get_survey(self, user: User, survey_id: str) -> Result[Survey, str]:
        """설문을 조회합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자

        Returns:
            Success[설문 엔티티] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        return Success(survey)

    def get_surveys_by_user(self, user: User) -> list[Survey]:
        """사용자가 접근 가능한 모든 설문을 조회합니다.

        Args:
            user: 사용자 엔티티

        Returns:
            설문 엔티티 목록
        """
        all_surveys = self.survey_repository.find_all_surveys()
        return [s for s in all_surveys if s.tenant_id == user.tenant_id]

    def update_survey(self, user: User, survey_id: str, **updates) -> Result[None, str]:
        """설문 정보를 수정합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자
            **updates: 수정할 필드 (title, description)

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        is_owner = survey.owner_id == user.id
        if not user.role.can_manage_survey(is_owner):
            return Failure("설문 관리 권한이 없습니다")

        self.survey_repository.update_survey(survey_id, **updates)
        return Success(None)

    def update_question(self, user: User, question_id: str, **updates) -> Result[None, str]:
        """질문 정보를 수정합니다.

        Args:
            user: 사용자 엔티티
            question_id: 질문 식별자
            **updates: 수정할 필드 (text, options)

        Returns:
            Success[None] 또는 Failure[에러 메시지]

        Raises:
            ValueError: 질문을 찾을 수 없는 경우
        """
        all_surveys = self.survey_repository.find_all_surveys()
        target_survey = None
        for survey in all_surveys:
            for question in survey.questions:
                if question.id == question_id:
                    target_survey = survey
                    break
            if target_survey:
                break

        if not target_survey:
            return Failure(f"질문을 찾을 수 없습니다: {question_id}")

        if target_survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 질문에 접근할 수 없습니다")

        is_owner = target_survey.owner_id == user.id
        if not user.role.can_manage_survey(is_owner):
            return Failure("질문 관리 권한이 없습니다")

        self.survey_repository.update_question(question_id, **updates)
        return Success(None)

    def delete_survey(self, user: User, survey_id: str) -> Result[None, str]:
        """설문을 삭제합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        is_owner = survey.owner_id == user.id
        if not user.role.can_manage_survey(is_owner):
            return Failure("설문 삭제 권한이 없습니다")

        self.survey_repository.delete_survey(survey_id)
        return Success(None)

    def delete_question(self, user: User, question_id: str) -> Result[None, str]:
        """질문을 삭제합니다.

        Args:
            user: 사용자 엔티티
            question_id: 질문 식별자

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        all_surveys = self.survey_repository.find_all_surveys()
        target_survey = None
        for survey in all_surveys:
            for question in survey.questions:
                if question.id == question_id:
                    target_survey = survey
                    break
            if target_survey:
                break

        if not target_survey:
            return Failure(f"질문을 찾을 수 없습니다: {question_id}")

        if target_survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 질문에 접근할 수 없습니다")

        is_owner = target_survey.owner_id == user.id
        if not user.role.can_manage_survey(is_owner):
            return Failure("질문 삭제 권한이 없습니다")

        self.survey_repository.delete_question(question_id)
        return Success(None)
