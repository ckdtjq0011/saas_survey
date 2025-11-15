"""세션 정리 스케줄러"""

from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class SessionCleanupScheduler:
    """세션 정리 스케줄러입니다.

    만료된 세션을 주기적으로 자동 정리합니다.

    Attributes:
        cleanup_service: SessionCleanupService 인스턴스
        scheduler: APScheduler 백그라운드 스케줄러
        schedule: Cron 표현식
    """

    def __init__(self, cleanup_service, schedule: str = "0 0 * * *"):
        """스케줄러를 초기화합니다.

        Args:
            cleanup_service: SessionCleanupService 인스턴스
            schedule: Cron 표현식 (기본: 매일 자정)
                     분 시 일 월 요일
                     예: "0 0 * * *" - 매일 자정
                         "0 */6 * * *" - 6시간마다
                         "0 2 * * 0" - 매주 일요일 새벽 2시
        """
        self.cleanup_service = cleanup_service
        self.scheduler = BackgroundScheduler()
        self.schedule = schedule
        self._is_running = False

    def start(self) -> None:
        """스케줄러를 시작합니다."""
        if self._is_running:
            logger.warning("스케줄러가 이미 실행 중입니다")
            return

        try:
            self.scheduler.add_job(
                self._cleanup_job,
                trigger=CronTrigger.from_crontab(self.schedule),
                id="session_cleanup",
                name="세션 정리",
                replace_existing=True
            )

            self.scheduler.start()
            self._is_running = True
            logger.info(f"세션 정리 스케줄러 시작 (스케줄: {self.schedule})")
        except Exception as e:
            logger.exception(f"스케줄러 시작 실패: {str(e)}")
            raise

    def stop(self) -> None:
        """스케줄러를 중지합니다."""
        if not self._is_running:
            logger.warning("스케줄러가 실행 중이 아닙니다")
            return

        try:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("세션 정리 스케줄러 중지")
        except Exception as e:
            logger.exception(f"스케줄러 중지 실패: {str(e)}")
            raise

    def run_now(self) -> None:
        """즉시 정리를 실행합니다."""
        logger.info("수동으로 세션 정리 실행")
        self._cleanup_job()

    def _cleanup_job(self) -> None:
        """스케줄러에서 호출되는 정리 작업입니다."""
        try:
            result = self.cleanup_service.cleanup_expired_sessions()

            if result.is_success():
                stats = result.value
                logger.info(
                    f"세션 정리 완료: "
                    f"삭제={stats.deleted_count}개, "
                    f"전={stats.total_before}개, "
                    f"후={stats.total_after}개, "
                    f"소요={stats.duration_seconds:.2f}초"
                )
            else:
                logger.error(f"세션 정리 실패: {result.error}")
        except Exception as e:
            logger.exception(f"세션 정리 작업 중 예외 발생: {str(e)}")

    @property
    def is_running(self) -> bool:
        """스케줄러 실행 상태를 반환합니다.

        Returns:
            실행 중이면 True
        """
        return self._is_running
