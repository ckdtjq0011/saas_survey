import csv
from pathlib import Path
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.repositories.survey_repository import SurveyRepository


class CsvSurveyRepository(SurveyRepository):
    """CSV 파일 기반 설문 저장소 구현입니다.

    Attributes:
        data_dir: CSV 파일이 저장될 디렉토리 경로
        surveys_file: surveys.csv 파일 경로
        questions_file: questions.csv 파일 경로
    """

    def __init__(self, data_dir: Path):
        """CSV 저장소를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = data_dir
        self.surveys_file = data_dir / "surveys.csv"
        self.questions_file = data_dir / "questions.csv"
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        """CSV 파일이 없으면 생성합니다."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.surveys_file.exists():
            with open(self.surveys_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "title", "description", "created_at"])
                writer.writeheader()

        if not self.questions_file.exists():
            with open(self.questions_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "survey_id", "text", "question_type", "options"])
                writer.writeheader()

    def save_survey(self, survey: Survey) -> None:
        """설문을 CSV에 저장합니다.

        Args:
            survey: 저장할 설문 엔티티
        """
        with open(self.surveys_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "title", "description", "created_at"])
            writer.writerow(survey.to_dict())

    def save_question(self, question: Question) -> None:
        """질문을 CSV에 저장합니다.

        Args:
            question: 저장할 질문 엔티티
        """
        with open(self.questions_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "survey_id", "text", "question_type", "options"])
            writer.writerow(question.to_dict())

    def find_survey_by_id(self, survey_id: str) -> Survey | None:
        """ID로 설문을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            설문 엔티티 또는 None
        """
        with open(self.surveys_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["id"] == survey_id:
                    questions = self.find_questions_by_survey_id(survey_id)
                    return Survey.from_dict(row, tuple(questions))
        return None

    def find_all_surveys(self) -> list[Survey]:
        """모든 설문을 조회합니다.

        Returns:
            설문 엔티티 목록
        """
        surveys = []
        with open(self.surveys_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                questions = self.find_questions_by_survey_id(row["id"])
                surveys.append(Survey.from_dict(row, tuple(questions)))
        return surveys

    def find_questions_by_survey_id(self, survey_id: str) -> list[Question]:
        """설문 ID로 질문 목록을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            질문 엔티티 목록
        """
        questions = []
        with open(self.questions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["survey_id"] == survey_id:
                    questions.append(Question.from_dict(row))
        return questions
