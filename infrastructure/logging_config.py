from loguru import logger
import sys
from pathlib import Path


def setup_logging(
    debug: bool = False,
    log_dir: Path = Path("logs")
) -> None:
    """로깅 설정을 초기화합니다.

    Args:
        debug: 디버그 모드 활성화 여부
        log_dir: 로그 파일 저장 디렉토리
    """
    logger.remove()

    log_dir.mkdir(exist_ok=True, parents=True)

    logger.add(
        log_dir / "app.log",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    )

    if debug:
        logger.add(
            log_dir / "debug.log",
            level="DEBUG",
            rotation="10 MB",
            retention="3 days",
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            backtrace=True,
            diagnose=True
        )

    logger.add(
        sys.stderr,
        level="ERROR",
        format="<red>{level}</red>: {message}",
        colorize=True
    )

    if debug:
        logger.add(
            sys.stdout,
            level="DEBUG",
            format="<cyan>[DEBUG]</cyan> {message}",
            colorize=True
        )

    logger.info(f"로깅 시스템 초기화 완료 (debug={debug})")
