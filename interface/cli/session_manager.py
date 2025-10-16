"""CLI 세션 관리자입니다."""

import json
import logging
from pathlib import Path
from datetime import datetime
from domain.entities.user import User
from domain.entities.session import Session


logger = logging.getLogger(__name__)


class SessionManager:
    """CLI 세션을 파일로 관리하는 클래스입니다.

    Attributes:
        session_file: 세션 파일 경로
    """

    def __init__(self, session_file: Path = Path.home() / ".saas_survey_session"):
        """세션 관리자를 초기화합니다.

        Args:
            session_file: 세션 파일 경로
        """
        self.session_file = session_file

    def save_session(self, api_key: str, user: User, session: Session) -> None:
        """세션 정보를 파일에 저장합니다.

        Args:
            api_key: API 키
            user: 사용자 엔티티
            session: 세션 엔티티
        """
        data = {
            "api_key": api_key,
            "user_id": user.id,
            "tenant_id": user.tenant_id,
            "username": user.username,
            "role": user.role.value,
            "expires_at": session.expires_at.isoformat(),
        }

        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info("세션 정보 저장 완료", extra={"username": user.username})

    def load_session(self) -> dict[str, str] | None:
        """파일에서 세션 정보를 로드합니다.

        Returns:
            세션 정보 딕셔너리 또는 None
        """
        if not self.session_file.exists():
            return None

        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            expires_at = datetime.fromisoformat(data["expires_at"])
            if expires_at <= datetime.now():
                logger.warning("세션 만료됨")
                self.clear_session()
                return None

            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.exception("세션 파일 읽기 실패", extra={"error": str(e)})
            self.clear_session()
            return None

    def clear_session(self) -> None:
        """세션 파일을 삭제합니다."""
        if self.session_file.exists():
            self.session_file.unlink()
            logger.info("세션 정보 삭제 완료")

    def is_logged_in(self) -> bool:
        """로그인 상태를 확인합니다.

        Returns:
            로그인 여부
        """
        return self.load_session() is not None
