import csv
import logging
from pathlib import Path
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.repositories.survey_repository import SurveyRepository


logger = logging.getLogger(__name__)


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
                writer = csv.DictWriter(f, fieldnames=["id", "tenant_id", "owner_id", "title", "description", "created_at"])
                writer.writeheader()

        if not self.questions_file.exists():
            with open(self.questions_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "survey_id", "text", "question_type", "order", "is_required", "options", "category_id"])
                writer.writeheader()

    def save_survey(self, survey: Survey) -> None:
        """설문을 CSV에 저장합니다.

        Args:
            survey: 저장할 설문 엔티티
        """
        with open(self.surveys_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "tenant_id", "owner_id", "title", "description", "created_at"])
            writer.writerow(survey.to_dict())
            f.flush()

    def save_question(self, question: Question) -> None:
        """질문을 CSV에 저장합니다.

        Args:
            question: 저장할 질문 엔티티
        """
        with open(self.questions_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "survey_id", "text", "question_type", "order", "is_required", "options", "category_id"])
            writer.writerow(question.to_dict())
            f.flush()

    def find_survey_by_id(self, survey_id: str) -> Survey | None:
        """ID로 설문을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            설문 엔티티 또는 None
        """
        survey_id = survey_id.strip()

        with open(self.surveys_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_id = row["id"].strip()
                if row_id == survey_id:
                    questions = self.find_questions_by_survey_id(survey_id)
                    return Survey.from_dict(row, tuple(questions))

        logger.warning(f"설문을 찾을 수 없습니다", extra={"survey_id": survey_id})
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
                if not row or not row.get("id"):
                    continue
                try:
                    questions = self.find_questions_by_survey_id(row["id"])
                    surveys.append(Survey.from_dict(row, tuple(questions)))
                except (KeyError, ValueError) as e:
                    logger.warning(f"손상된 설문 데이터를 건너뜁니다", extra={"error": str(e), "row": row})
                    continue
        return surveys

    def find_questions_by_survey_id(self, survey_id: str) -> list[Question]:
        """설문 ID로 질문 목록을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            질문 엔티티 목록 (order 필드로 정렬됨)
        """
        questions = []
        with open(self.questions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("survey_id"):
                    continue
                try:
                    if row["survey_id"] == survey_id:
                        questions.append(Question.from_dict(row))
                except (KeyError, ValueError) as e:
                    logger.warning(f"손상된 질문 데이터를 건너뜁니다", extra={"error": str(e), "row": row})
                    continue

        # order 필드로 정렬 (기본값 0을 가진 기존 데이터도 처리)
        questions.sort(key=lambda q: q.order)
        return questions

    def find_by_owner_id(self, owner_id: str) -> list[Survey]:
        """소유자 ID로 설문 목록을 조회합니다.

        Args:
            owner_id: 소유자 식별자

        Returns:
            설문 엔티티 목록
        """
        owner_id = owner_id.strip()
        surveys = []

        with open(self.surveys_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["owner_id"].strip() == owner_id:
                    questions = self.find_questions_by_survey_id(row["id"])
                    surveys.append(Survey.from_dict(row, tuple(questions)))

        return surveys

    def find_by_tenant_id(self, tenant_id: str) -> list[Survey]:
        """테넌트 ID로 설문 목록을 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            설문 엔티티 목록
        """
        tenant_id = tenant_id.strip()
        surveys = []

        with open(self.surveys_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["tenant_id"].strip() == tenant_id:
                    questions = self.find_questions_by_survey_id(row["id"])
                    surveys.append(Survey.from_dict(row, tuple(questions)))

        return surveys

    def update_survey(self, survey_id: str, **updates) -> None:
        """설문 정보를 수정합니다.

        Args:
            survey_id: 설문 식별자
            **updates: 수정할 필드

        Raises:
            ValueError: 설문을 찾을 수 없는 경우
        """
        survey_id = survey_id.strip()
        rows = []
        found = False

        with open(self.surveys_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == survey_id:
                    found = True
                    for key, value in updates.items():
                        if key in row:
                            row[key] = str(value)
                rows.append(row)

        if not found:
            raise ValueError(f"설문을 찾을 수 없습니다: {survey_id}")

        with open(self.surveys_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "tenant_id", "owner_id", "title", "description", "created_at"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

        logger.info("설문 정보를 수정했습니다", extra={"survey_id": survey_id, "updates": updates})

    def update_question(self, question_id: str, **updates) -> None:
        """질문 정보를 수정합니다.

        Args:
            question_id: 질문 식별자
            **updates: 수정할 필드

        Raises:
            ValueError: 질문을 찾을 수 없는 경우
        """
        OPTIONS_DELIMITER = "\x1f"
        question_id = question_id.strip()
        rows = []
        found = False

        with open(self.questions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == question_id:
                    found = True
                    for key, value in updates.items():
                        if key in row:
                            if key == "options" and isinstance(value, (list, tuple)):
                                row[key] = OPTIONS_DELIMITER.join(value)
                            else:
                                row[key] = str(value)
                rows.append(row)

        if not found:
            raise ValueError(f"질문을 찾을 수 없습니다: {question_id}")

        with open(self.questions_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "survey_id", "text", "question_type", "options", "category_id"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

        logger.info("질문 정보를 수정했습니다", extra={"question_id": question_id, "updates": updates})

    def delete_survey(self, survey_id: str) -> None:
        """설문을 삭제합니다.

        Args:
            survey_id: 설문 식별자

        Raises:
            ValueError: 설문을 찾을 수 없는 경우
        """
        survey_id = survey_id.strip()
        rows = []
        found = False

        with open(self.surveys_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == survey_id:
                    found = True
                    continue
                rows.append(row)

        if not found:
            raise ValueError(f"설문을 찾을 수 없습니다: {survey_id}")

        with open(self.surveys_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "tenant_id", "owner_id", "title", "description", "created_at"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

        question_rows = []
        with open(self.questions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue
                if row["survey_id"].strip() != survey_id:
                    question_rows.append(row)

        with open(self.questions_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "survey_id", "text", "question_type", "options", "category_id"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(question_rows)
            f.flush()

        logger.info("설문 및 관련 질문을 삭제했습니다", extra={"survey_id": survey_id})

    def delete_question(self, question_id: str) -> None:
        """질문을 삭제합니다.

        Args:
            question_id: 질문 식별자

        Raises:
            ValueError: 질문을 찾을 수 없는 경우
        """
        question_id = question_id.strip()
        rows = []
        found = False

        with open(self.questions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == question_id:
                    found = True
                    continue
                rows.append(row)

        if not found:
            raise ValueError(f"질문을 찾을 수 없습니다: {question_id}")

        with open(self.questions_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "survey_id", "text", "question_type", "options", "category_id"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

        logger.info("질문을 삭제했습니다", extra={"question_id": question_id})
