import logging
from pathlib import Path
from domain.value_objects.types import QuestionType
from application.survey_service import SurveyService
from application.response_service import ResponseService
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository


logger = logging.getLogger(__name__)


class SurveyCommands:
    """설문 관련 CLI 명령어를 처리하는 클래스입니다.

    Attributes:
        survey_service: 설문 서비스
        response_service: 응답 서비스
    """

    def __init__(self, data_dir: Path):
        """CLI 명령어 핸들러를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        survey_repo = CsvSurveyRepository(data_dir)
        response_repo = CsvResponseRepository(data_dir)
        self.survey_service = SurveyService(survey_repo)
        self.response_service = ResponseService(response_repo, survey_repo)

    def create_survey(self, title: str, description: str) -> str:
        """설문을 생성합니다.

        Args:
            title: 설문 제목
            description: 설문 설명

        Returns:
            생성된 설문 ID

        Raises:
            Exception: 설문 생성 실패 시
        """
        try:
            survey_id = self.survey_service.create_survey(title, description)
            logger.info(f"설문이 생성되었습니다", extra={"survey_id": survey_id})
            return survey_id
        except Exception:
            logger.exception("설문 생성 중 오류가 발생했습니다")
            raise

    def add_question(
        self, survey_id: str, text: str, question_type: str, options: list[str] | None = None
    ) -> str:
        """질문을 추가합니다.

        Args:
            survey_id: 설문 ID
            text: 질문 내용
            question_type: 질문 유형 (text/rating/choice)
            options: 객관식 선택지

        Returns:
            생성된 질문 ID

        Raises:
            Exception: 질문 추가 실패 시
        """
        try:
            q_type = QuestionType(question_type)
            question_id = self.survey_service.add_question(survey_id, text, q_type, options)
            logger.info(f"질문이 추가되었습니다", extra={"question_id": question_id})
            return question_id
        except Exception:
            logger.exception("질문 추가 중 오류가 발생했습니다")
            raise

    def get_survey(self, survey_id: str) -> dict[str, str | list[dict[str, str]]]:
        """설문을 조회합니다.

        Args:
            survey_id: 설문 ID

        Returns:
            설문 정보 딕셔너리

        Raises:
            Exception: 설문 조회 실패 시
        """
        try:
            survey = self.survey_service.get_survey(survey_id)
            questions = [
                {
                    "id": q.id,
                    "text": q.text,
                    "type": q.question_type.value,
                    "options": list(q.options) if q.options else [],
                }
                for q in survey.questions
            ]
            return {
                "id": survey.id,
                "title": survey.title,
                "description": survey.description,
                "created_at": survey.created_at.isoformat(),
                "questions": questions,
            }
        except Exception:
            logger.exception("설문 조회 중 오류가 발생했습니다")
            raise

    def list_surveys(self) -> list[dict[str, str]]:
        """모든 설문 목록을 조회합니다.

        Returns:
            설문 목록

        Raises:
            Exception: 목록 조회 실패 시
        """
        try:
            surveys = self.survey_service.get_all_surveys()
            return [
                {
                    "id": s.id,
                    "title": s.title,
                    "description": s.description,
                    "question_count": str(len(s.questions)),
                }
                for s in surveys
            ]
        except Exception:
            logger.exception("설문 목록 조회 중 오류가 발생했습니다")
            raise

    def submit_response(self, survey_id: str, respondent_id: str, answers: dict[str, str]) -> None:
        """응답을 제출합니다.

        Args:
            survey_id: 설문 ID
            respondent_id: 응답자 ID
            answers: 질문 ID와 답변 딕셔너리

        Raises:
            Exception: 응답 제출 실패 시
        """
        try:
            self.response_service.submit_response(survey_id, respondent_id, answers)
            logger.info(f"응답이 제출되었습니다", extra={"respondent_id": respondent_id})
        except Exception:
            logger.exception("응답 제출 중 오류가 발생했습니다")
            raise

    def get_results(self, survey_id: str) -> dict[str, dict[str, int | float | list[str]]]:
        """설문 결과를 조회합니다.

        Args:
            survey_id: 설문 ID

        Returns:
            질문별 결과 통계

        Raises:
            Exception: 결과 조회 실패 시
        """
        try:
            return self.response_service.get_survey_results(survey_id)
        except Exception:
            logger.exception("결과 조회 중 오류가 발생했습니다")
            raise
