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
        category_id: str | None = None,
        is_required: bool = True
    ) -> Result[str, str]:
        """설문에 질문을 추가합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자
            text: 질문 내용
            question_type: 질문 유형
            options: 객관식 선택지
            category_id: 범주 식별자
            is_required: 필수 응답 여부

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

        # 기존 질문들의 order 값 중 최대값을 찾아 다음 순서 결정
        existing_questions = self.survey_repository.find_questions_by_survey_id(survey_id)
        next_order = 0
        if existing_questions:
            max_order = max(q.order for q in existing_questions)
            next_order = max_order + 1

        question_id = str(uuid.uuid4())
        question = Question(
            id=question_id,
            survey_id=survey_id,
            text=text,
            question_type=question_type,
            order=next_order,
            is_required=is_required,
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

    def reorder_questions(self, user: User, survey_id: str, question_orders: dict[str, int]) -> Result[None, str]:
        """설문의 질문 순서를 재배열합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자
            question_orders: {질문ID: 순서} 형식의 딕셔너리

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

        # 각 질문의 순서 업데이트
        for question in survey.questions:
            if question.id in question_orders:
                new_order = question_orders[question.id]
                if new_order < 0:
                    return Failure(f"잘못된 순서 값: {new_order}")
                self.survey_repository.update_question(question.id, order=str(new_order))

        return Success(None)

    def move_question_up(self, user: User, question_id: str) -> Result[None, str]:
        """질문을 한 칸 위로 이동합니다.

        Args:
            user: 사용자 엔티티
            question_id: 질문 식별자

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        # 해당 질문이 속한 설문 찾기
        all_surveys = self.survey_repository.find_all_surveys()
        target_survey = None
        target_question = None

        for survey in all_surveys:
            for question in survey.questions:
                if question.id == question_id:
                    target_survey = survey
                    target_question = question
                    break
            if target_survey:
                break

        if not target_survey or not target_question:
            return Failure(f"질문을 찾을 수 없습니다: {question_id}")

        if target_survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 질문에 접근할 수 없습니다")

        is_owner = target_survey.owner_id == user.id
        if not user.role.can_manage_survey(is_owner):
            return Failure("설문 관리 권한이 없습니다")

        # 정렬된 질문 목록 가져오기
        questions = sorted(target_survey.questions, key=lambda q: q.order)
        current_index = next((i for i, q in enumerate(questions) if q.id == question_id), None)

        if current_index is None:
            return Failure("질문 순서를 찾을 수 없습니다")

        if current_index == 0:
            return Failure("이미 첫 번째 질문입니다")

        # 이전 질문과 순서 교환
        prev_question = questions[current_index - 1]
        self.survey_repository.update_question(question_id, order=str(prev_question.order))
        self.survey_repository.update_question(prev_question.id, order=str(target_question.order))

        return Success(None)

    def move_question_down(self, user: User, question_id: str) -> Result[None, str]:
        """질문을 한 칸 아래로 이동합니다.

        Args:
            user: 사용자 엔티티
            question_id: 질문 식별자

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        # 해당 질문이 속한 설문 찾기
        all_surveys = self.survey_repository.find_all_surveys()
        target_survey = None
        target_question = None

        for survey in all_surveys:
            for question in survey.questions:
                if question.id == question_id:
                    target_survey = survey
                    target_question = question
                    break
            if target_survey:
                break

        if not target_survey or not target_question:
            return Failure(f"질문을 찾을 수 없습니다: {question_id}")

        if target_survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 질문에 접근할 수 없습니다")

        is_owner = target_survey.owner_id == user.id
        if not user.role.can_manage_survey(is_owner):
            return Failure("설문 관리 권한이 없습니다")

        # 정렬된 질문 목록 가져오기
        questions = sorted(target_survey.questions, key=lambda q: q.order)
        current_index = next((i for i, q in enumerate(questions) if q.id == question_id), None)

        if current_index is None:
            return Failure("질문 순서를 찾을 수 없습니다")

        if current_index == len(questions) - 1:
            return Failure("이미 마지막 질문입니다")

        # 다음 질문과 순서 교환
        next_question = questions[current_index + 1]
        self.survey_repository.update_question(question_id, order=str(next_question.order))
        self.survey_repository.update_question(next_question.id, order=str(target_question.order))

        return Success(None)
