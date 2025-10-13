import uuid
from datetime import datetime
from collections import Counter
from domain.entities.response import Response
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

    def submit_response(self, survey_id: str, respondent_id: str, answers: dict[str, str]) -> None:
        """설문 응답을 제출합니다.

        Args:
            survey_id: 설문 식별자
            respondent_id: 응답자 식별자
            answers: 질문 ID와 답변의 딕셔너리

        Raises:
            ValueError: 설문을 찾을 수 없는 경우
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            raise ValueError(f"설문을 찾을 수 없습니다: {survey_id}")

        for question_id, answer in answers.items():
            response_id = str(uuid.uuid4())
            response = Response(
                id=response_id,
                survey_id=survey_id,
                question_id=question_id,
                answer=answer,
                respondent_id=respondent_id,
                created_at=datetime.now(),
            )
            self.response_repository.save(response)

    def get_survey_results(self, survey_id: str) -> dict[str, dict[str, int | float | list[str]]]:
        """설문 결과를 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            질문 ID별 결과 통계

        Raises:
            ValueError: 설문을 찾을 수 없는 경우
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            raise ValueError(f"설문을 찾을 수 없습니다: {survey_id}")

        results = {}
        for question in survey.questions:
            responses = self.response_repository.find_by_question_id(question.id)
            answers = [r.answer for r in responses]

            if question.question_type.value == "rating":
                ratings = [int(a) for a in answers if a.isdigit()]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
                results[question.id] = {
                    "question": question.text,
                    "type": question.question_type.value,
                    "count": len(ratings),
                    "average": round(avg_rating, 2),
                }
            elif question.question_type.value == "choice":
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

        return results
