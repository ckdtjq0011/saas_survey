import csv
import logging
from datetime import datetime
from pathlib import Path

from domain.entities.session import Session
from domain.repositories.session_repository import SessionRepository


logger = logging.getLogger(__name__)


class CsvSessionRepository(SessionRepository):
    """CSV 파일 기반 세션 저장소 구현입니다.

    Attributes:
        data_dir: CSV 파일이 저장될 디렉토리 경로
        sessions_file: sessions.csv 파일 경로
    """

    def __init__(self, data_dir: Path):
        """CSV 저장소를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = data_dir
        self.sessions_file = data_dir / "sessions.csv"
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        """CSV 파일이 없으면 생성합니다."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.sessions_file.exists():
            with open(self.sessions_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["id", "user_id", "tenant_id", "api_key", "expires_at", "created_at"]
                )
                writer.writeheader()

    def save_session(self, session: Session) -> None:
        """세션을 CSV에 저장합니다.

        Args:
            session: 저장할 세션 엔티티
        """
        with open(self.sessions_file, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "user_id", "tenant_id", "api_key", "expires_at", "created_at"]
            )
            writer.writerow(session.to_dict())
            f.flush()

    def find_session_by_api_key(self, api_key: str) -> Session | None:
        """API 키로 세션을 조회합니다.

        Args:
            api_key: API 키

        Returns:
            세션 엔티티 또는 None
        """
        api_key = api_key.strip()

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_api_key = row["api_key"].strip()
                if row_api_key == api_key:
                    return Session.from_dict(row)

        return None

    def find_session_by_user_id(self, user_id: str) -> Session | None:
        """사용자 ID로 세션을 조회합니다.

        Args:
            user_id: 사용자 식별자

        Returns:
            세션 엔티티 또는 None
        """
        user_id = user_id.strip()

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_user_id = row["user_id"].strip()
                if row_user_id == user_id:
                    return Session.from_dict(row)

        return None

    def delete_session(self, session_id: str) -> None:
        """세션을 삭제합니다.

        Args:
            session_id: 세션 식별자
        """
        session_id = session_id.strip()
        sessions = []

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_id = row["id"].strip()
                if row_id != session_id:
                    sessions.append(row)

        with open(self.sessions_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "user_id", "tenant_id", "api_key", "expires_at", "created_at"]
            )
            writer.writeheader()
            writer.writerows(sessions)
            f.flush()

    def find_expired_sessions(self, current_time: datetime) -> list[Session]:
        """만료된 세션들을 조회합니다.

        Args:
            current_time: 현재 시각

        Returns:
            만료된 세션 목록
        """
        expired_sessions = []

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                session = Session.from_dict(row)
                if session.is_expired(current_time):
                    expired_sessions.append(session)

        return expired_sessions

    def delete_sessions_bulk(self, session_ids: list[str]) -> int:
        """세션들을 일괄 삭제하고 삭제된 개수를 반환합니다.

        Args:
            session_ids: 삭제할 세션 식별자 목록

        Returns:
            삭제된 세션 개수
        """
        session_ids_set = {sid.strip() for sid in session_ids}
        sessions = []
        deleted_count = 0

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                row_id = row["id"].strip()
                if row_id in session_ids_set:
                    deleted_count += 1
                else:
                    sessions.append(row)

        with open(self.sessions_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "user_id", "tenant_id", "api_key", "expires_at", "created_at"]
            )
            writer.writeheader()
            writer.writerows(sessions)
            f.flush()

        return deleted_count

    def count_sessions(self) -> int:
        """전체 세션 개수를 반환합니다.

        Returns:
            세션 개수
        """
        count = 0

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and row.get("id"):
                    count += 1

        return count

    def count_expired_sessions(self, current_time: datetime) -> int:
        """만료된 세션 개수를 반환합니다.

        Args:
            current_time: 현재 시각

        Returns:
            만료된 세션 개수
        """
        count = 0

        with open(self.sessions_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue

                session = Session.from_dict(row)
                if session.is_expired(current_time):
                    count += 1

        return count
