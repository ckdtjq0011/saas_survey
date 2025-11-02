import uuid
from datetime import datetime
from collections import Counter
from domain.entities.response import Response
from domain.entities.user import User
from domain.value_objects.result import Success, Failure, Result
from domain.value_objects.types import QuestionType
from domain.repositories.response_repository import ResponseRepository
from domain.repositories.survey_repository import SurveyRepository


class ResponseService:
    """응답 관련 유스케이스를 처리하는 서비스입니다.

    Attributes:
        response_repository: 응답 저장소
        survey_repository: 설문 저장소
    """

    def __init__(self, response_repository: ResponseRepository, survey_repository: SurveyRepository):
        """서비스를 초기화합니다.

        Args:
            response_repository: 응답 저장소 구현체
            survey_repository: 설문 저장소 구현체
        """
        self.response_repository = response_repository
        self.survey_repository = survey_repository

    def submit_response(self, user: User, survey_id: str, answers: dict[str, str]) -> Result[None, str]:
        """설문 응답을 제출합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자
            answers: 질문 ID와 답변의 딕셔너리

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        question_map = {q.id: q for q in survey.questions}

        for question_id, answer in answers.items():
            question = question_map.get(question_id)
            if not question:
                return Failure(f"질문을 찾을 수 없습니다: {question_id}")

            validation_result = self._validate_answer(question, answer)
            if validation_result.is_failure():
                return validation_result

            response_id = str(uuid.uuid4())
            response = Response(
                id=response_id,
                survey_id=survey_id,
                question_id=question_id,
                answer=answer,
                respondent_id=user.id,
                created_at=datetime.now(),
            )
            self.response_repository.save(response)

        return Success(None)

    def _validate_answer(self, question, answer: str) -> Result[None, str]:
        """답변을 검증합니다.

        Args:
            question: Question 엔티티
            answer: 답변

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        from domain.value_objects.types import QuestionType

        if question.question_type == QuestionType.RATING:
            if not answer.isdigit():
                return Failure(f"평점은 숫자여야 합니다: {answer}")

            rating = int(answer)
            if rating < 1 or rating > 5:
                return Failure(f"평점은 1-5 사이여야 합니다: {rating}")

        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            if not question.options:
                return Failure("객관식 질문에 선택지가 없습니다")

            if answer not in question.options:
                return Failure(f"유효하지 않은 선택지입니다: {answer}. 가능한 선택지: {', '.join(question.options)}")

        return Success(None)

    def get_survey_results(self, user: User, survey_id: str) -> Result[dict[str, dict[str, int | float | list[str]]], str]:
        """설문 결과를 조회합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자

        Returns:
            Success[질문 ID별 결과 통계] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        is_owner = survey.owner_id == user.id
        if not user.role.can_view_results(is_owner):
            return Failure("결과 조회 권한이 없습니다")

        results = {}
        for question in survey.questions:
            responses = self.response_repository.find_by_question_id(question.id)
            answers = [r.answer for r in responses]

            if question.question_type == QuestionType.RATING:
                ratings = [int(a) for a in answers if a.isdigit()]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
                counter = Counter([str(r) for r in ratings])
                results[question.id] = {
                    "question": question.text,
                    "type": question.question_type.value,
                    "count": len(ratings),
                    "average": round(avg_rating, 2),
                    "distribution": dict(counter),
                }
            elif question.question_type == QuestionType.MULTIPLE_CHOICE:
                counter = Counter(answers)
                results[question.id] = {
                    "question": question.text,
                    "type": question.question_type.value,
                    "count": len(answers),
                    "distribution": dict(counter),
                }
            else:
                results[question.id] = {
                    "question": question.text,
                    "type": question.question_type.value,
                    "count": len(answers),
                    "answers": answers,
                }

        return Success(results)

    def update_response(self, user: User, response_id: str, answer: str) -> Result[None, str]:
        """응답을 수정합니다.

        Args:
            user: 사용자 엔티티
            response_id: 응답 식별자
            answer: 새로운 답변

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        all_responses = []
        all_surveys = self.survey_repository.find_all_surveys()
        for survey in all_surveys:
            responses = self.response_repository.find_by_survey_id(survey.id)
            all_responses.extend(responses)

        target_response = None
        for resp in all_responses:
            if resp.id == response_id:
                target_response = resp
                break

        if not target_response:
            return Failure(f"응답을 찾을 수 없습니다: {response_id}")

        survey = self.survey_repository.find_survey_by_id(target_response.survey_id)
        if not survey:
            return Failure("응답에 해당하는 설문을 찾을 수 없습니다")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 응답에 접근할 수 없습니다")

        if target_response.respondent_id != user.id and not user.role.can_manage_survey(survey.owner_id == user.id):
            return Failure("응답 수정 권한이 없습니다")

        self.response_repository.update_response(response_id, answer)
        return Success(None)

    def delete_response(self, user: User, response_id: str) -> Result[None, str]:
        """응답을 삭제합니다.

        Args:
            user: 사용자 엔티티
            response_id: 응답 식별자

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        all_responses = []
        all_surveys = self.survey_repository.find_all_surveys()
        for survey in all_surveys:
            responses = self.response_repository.find_by_survey_id(survey.id)
            all_responses.extend(responses)

        target_response = None
        for resp in all_responses:
            if resp.id == response_id:
                target_response = resp
                break

        if not target_response:
            return Failure(f"응답을 찾을 수 없습니다: {response_id}")

        survey = self.survey_repository.find_survey_by_id(target_response.survey_id)
        if not survey:
            return Failure("응답에 해당하는 설문을 찾을 수 없습니다")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 응답에 접근할 수 없습니다")

        if target_response.respondent_id != user.id and not user.role.can_manage_survey(survey.owner_id == user.id):
            return Failure("응답 삭제 권한이 없습니다")

        self.response_repository.delete_response(response_id)
        return Success(None)
