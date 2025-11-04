import csv
from pathlib import Path
from domain.entities.survey_session import SurveySession
from domain.repositories.survey_session_repository import SurveySessionRepository


class CsvSurveySessionRepository(SurveySessionRepository):
    """CSV 파일 기반 설문 세션 저장소 구현입니다.

    Attributes:
        data_dir: CSV 파일이 저장될 디렉토리 경로
        sessions_file: survey_sessions.csv 파일 경로
    """

    def __init__(self, data_dir: Path):
        """CSV 저장소를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = data_dir
        self.sessions_file = data_dir / "survey_sessions.csv"
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """CSV 파일이 없으면 생성합니다."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.sessions_file.exists():
            with open(self.sessions_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "id",
                        "survey_id",
                        "respondent_id",
                        "started_at",
                        "submitted_at",
                        "completed",
                        "completion_percentage",
                        "user_agent",
                        "total_time_spent_seconds",
                    ],
                )
                writer.writeheader()

    def save(self, session: SurveySession) -> None:
        """세션을 CSV에 저장합니다.

        Args:
            session: 저장할 세션 엔티티
        """
        with open(self.sessions_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "survey_id",
                    "respondent_id",
                    "started_at",
                    "submitted_at",
                    "completed",
                    "completion_percentage",
                    "user_agent",
                    "total_time_spent_seconds",
                ],
            )
            writer.writerow(session.to_dict())
            f.flush()

    def find_by_id(self, session_id: str) -> SurveySession | None:
        """세션 ID로 세션을 조회합니다.

        Args:
            session_id: 세션 식별자

        Returns:
            세션 엔티티 또는 None
        """
        session_id = session_id.strip()

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == session_id:
                    return SurveySession.from_dict(row)

        return None

    def find_by_respondent_and_survey(self, respondent_id: str, survey_id: str) -> list[SurveySession]:
        """응답자 ID와 설문 ID로 세션 목록을 조회합니다.

        Args:
            respondent_id: 응답자 식별자
            survey_id: 설문 식별자

        Returns:
            세션 엔티티 목록
        """
        respondent_id = respondent_id.strip()
        survey_id = survey_id.strip()
        sessions = []

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["respondent_id"].strip() == respondent_id and row["survey_id"].strip() == survey_id:
                    sessions.append(SurveySession.from_dict(row))

        return sessions

    def update_session(self, session: SurveySession) -> None:
        """세션을 수정합니다.

        Args:
            session: 수정할 세션 엔티티

        Raises:
            ValueError: 세션을 찾을 수 없는 경우
        """
        session_id = session.id.strip()
        rows = []
        found = False

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == session_id:
                    found = True
                    row = session.to_dict()
                rows.append(row)

        if not found:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        with open(self.sessions_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = [
                "id",
                "survey_id",
                "respondent_id",
                "started_at",
                "submitted_at",
                "completed",
                "completion_percentage",
                "user_agent",
                "total_time_spent_seconds",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()

    def delete_session(self, session_id: str) -> None:
        """세션을 삭제합니다.

        Args:
            session_id: 세션 식별자

        Raises:
            ValueError: 세션을 찾을 수 없는 경우
        """
        session_id = session_id.strip()
        rows = []
        found = False

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                if row["id"].strip() == session_id:
                    found = True
                    continue
                rows.append(row)

        if not found:
            raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")

        with open(self.sessions_file, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = [
                "id",
                "survey_id",
                "respondent_id",
                "started_at",
                "submitted_at",
                "completed",
                "completion_percentage",
                "user_agent",
                "total_time_spent_seconds",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()
