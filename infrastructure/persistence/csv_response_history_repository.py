import csv
from pathlib import Path
from domain.entities.response_history import ResponseHistory
from domain.repositories.response_history_repository import ResponseHistoryRepository


class CsvResponseHistoryRepository(ResponseHistoryRepository):
    """CSV 파일 기반 응답 수정 이력 저장소 구현입니다.

    Attributes:
        data_dir: CSV 파일이 저장될 디렉토리 경로
        histories_file: response_histories.csv 파일 경로
    """

    def __init__(self, data_dir: Path):
        """CSV 저장소를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = data_dir
        self.histories_file = data_dir / "response_histories.csv"
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """CSV 파일이 없으면 생성합니다."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.histories_file.exists():
            with open(self.histories_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "id",
                        "response_id",
                        "old_answer",
                        "new_answer",
                        "updated_at",
                        "updated_by",
                    ],
                )
                writer.writeheader()

    def save(self, history: ResponseHistory) -> None:
        """수정 이력을 CSV에 저장합니다.

        Args:
            history: 저장할 이력 엔티티
        """
        with open(self.histories_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "response_id",
                    "old_answer",
                    "new_answer",
                    "updated_at",
                    "updated_by",
                ],
            )
            writer.writerow(history.to_dict())
            f.flush()

    def find_by_response_id(self, response_id: str) -> list[ResponseHistory]:
        """응답 ID로 수정 이력 목록을 조회합니다.

        Args:
            response_id: 응답 식별자

        Returns:
            이력 엔티티 목록 (시간순 정렬)
        """
        response_id = response_id.strip()
        histories = []

        with open(self.histories_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["response_id"].strip() == response_id:
                    histories.append(ResponseHistory.from_dict(row))

        histories.sort(key=lambda h: h.updated_at)
        return histories
