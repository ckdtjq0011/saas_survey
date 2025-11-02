import csv
from pathlib import Path
from domain.entities.response import Response
from domain.repositories.response_repository import ResponseRepository


class CsvResponseRepository(ResponseRepository):
    """CSV 파일 기반 응답 저장소 구현입니다.

    Attributes:
        data_dir: CSV 파일이 저장될 디렉토리 경로
        responses_file: responses.csv 파일 경로
    """

    def __init__(self, data_dir: Path):
        """CSV 저장소를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = data_dir
        self.responses_file = data_dir / "responses.csv"
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """CSV 파일이 없으면 생성합니다."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.responses_file.exists():
            with open(self.responses_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["id", "survey_id", "question_id", "answer", "respondent_id", "created_at"]
                )
                writer.writeheader()

    def save(self, response: Response) -> None:
        """응답을 CSV에 저장합니다.

        Args:
            response: 저장할 응답 엔티티
        """
        with open(self.responses_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f, fieldnames=["id", "survey_id", "question_id", "answer", "respondent_id", "created_at"]
            )
            writer.writerow(response.to_dict())
            f.flush()

    def find_by_survey_id(self, survey_id: str) -> list[Response]:
        """설문 ID로 응답 목록을 조회합니다.

        Args:
            survey_id: 설문 식별자

        Returns:
            응답 엔티티 목록
        """
        responses = []
        with open(self.responses_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["survey_id"] == survey_id:
                    responses.append(Response.from_dict(row))
        return responses

    def find_by_question_id(self, question_id: str) -> list[Response]:
        """질문 ID로 응답 목록을 조회합니다.

        Args:
            question_id: 질문 식별자

        Returns:
            응답 엔티티 목록
        """
        responses = []
        with open(self.responses_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["question_id"] == question_id:
                    responses.append(Response.from_dict(row))
        return responses

    def find_by_respondent_id(self, respondent_id: str) -> list[Response]:
        """응답자 ID로 응답 목록을 조회합니다.

        Args:
            respondent_id: 응답자 식별자

        Returns:
            응답 엔티티 목록
        """
        respondent_id = respondent_id.strip()
        responses = []

        with open(self.responses_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["respondent_id"].strip() == respondent_id:
                    responses.append(Response.from_dict(row))

        return responses

    def update_response(self, response_id: str, answer: str) -> None:
        """응답을 수정합니다.

        Args:
            response_id: 응답 식별자
            answer: 새로운 답변

        Raises:
            ValueError: 응답을 찾을 수 없는 경우
        """
        response_id = response_id.strip()
        rows = []
        found = False

        with open(self.responses_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == response_id:
                    found = True
                    row["answer"] = answer
                rows.append(row)

        if not found:
            raise ValueError(f"응답을 찾을 수 없습니다: {response_id}")

        with open(self.responses_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "survey_id", "question_id", "answer", "respondent_id", "created_at"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

    def delete_response(self, response_id: str) -> None:
        """응답을 삭제합니다.

        Args:
            response_id: 응답 식별자

        Raises:
            ValueError: 응답을 찾을 수 없는 경우
        """
        response_id = response_id.strip()
        rows = []
        found = False

        with open(self.responses_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == response_id:
                    found = True
                    continue
                rows.append(row)

        if not found:
            raise ValueError(f"응답을 찾을 수 없습니다: {response_id}")

        with open(self.responses_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "survey_id", "question_id", "answer", "respondent_id", "created_at"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

    def delete_by_survey_id(self, survey_id: str) -> None:
        """설문의 모든 응답을 삭제합니다.

        Args:
            survey_id: 설문 식별자
        """
        survey_id = survey_id.strip()
        rows = []

        with open(self.responses_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["survey_id"].strip() != survey_id:
                    rows.append(row)

        with open(self.responses_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "survey_id", "question_id", "answer", "respondent_id", "created_at"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()
