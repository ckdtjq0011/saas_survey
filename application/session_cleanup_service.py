"""세션 정리 서비스"""

import time
import uuid
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from domain.repositories.session_repository import SessionRepository
from domain.value_objects.result import Success, Failure, Result


@dataclass(frozen=True, slots=True)
class CleanupStats:
    """세션 정리 통계입니다.

    Attributes:
        deleted_count: 삭제된 세션 개수
        total_before: 정리 전 전체 세션 개수
        total_after: 정리 후 전체 세션 개수
        duration_seconds: 정리 소요 시간 (초)
        cleaned_at: 정리 실행 시각
    """

    deleted_count: int
    total_before: int
    total_after: int
    duration_seconds: float
    cleaned_at: datetime


class SessionCleanupService:
    """세션 정리 서비스입니다.

    만료된 세션을 정리하고 통계를 제공합니다.
    """

    def __init__(self, session_repository: SessionRepository):
        """세션 정리 서비스를 초기화합니다.

        Args:
            session_repository: 세션 저장소
        """
        self.session_repository = session_repository

    def cleanup_expired_sessions(self) -> Result[CleanupStats, str]:
        """만료된 세션들을 정리합니다.

        Returns:
            성공 시 CleanupStats, 실패 시 에러 메시지
        """
        try:
            start_time = time.time()
            current_time = datetime.now()

            total_before = self.session_repository.count_sessions()
            expired_sessions = self.session_repository.find_expired_sessions(current_time)

            if not expired_sessions:
                duration = time.time() - start_time
                logger.info("정리할 만료 세션이 없습니다")
                return Success(CleanupStats(
                    deleted_count=0,
                    total_before=total_before,
                    total_after=total_before,
                    duration_seconds=duration,
                    cleaned_at=current_time
                ))

            session_ids = [session.id for session in expired_sessions]
            deleted_count = self.session_repository.delete_sessions_bulk(session_ids)
            total_after = self.session_repository.count_sessions()

            duration = time.time() - start_time

            logger.info(
                f"세션 정리 완료: 삭제={deleted_count}개, "
                f"전={total_before}개, 후={total_after}개, 소요={duration:.2f}초"
            )

            return Success(CleanupStats(
                deleted_count=deleted_count,
                total_before=total_before,
                total_after=total_after,
                duration_seconds=duration,
                cleaned_at=current_time
            ))

        except Exception as e:
            logger.exception(f"세션 정리 중 오류 발생: {str(e)}")
            return Failure(f"세션 정리 실패: {str(e)}")

    def get_cleanup_stats(self) -> dict[str, int]:
        """현재 세션 통계를 조회합니다.

        Returns:
            세션 통계 딕셔너리
        """
        try:
            current_time = datetime.now()
            total_sessions = self.session_repository.count_sessions()
            expired_sessions = self.session_repository.count_expired_sessions(current_time)

            return {
                "total_sessions": total_sessions,
                "expired_sessions": expired_sessions,
                "active_sessions": total_sessions - expired_sessions
            }

        except Exception as e:
            logger.exception(f"세션 통계 조회 중 오류 발생: {str(e)}")
            return {
                "total_sessions": 0,
                "expired_sessions": 0,
                "active_sessions": 0
            }
