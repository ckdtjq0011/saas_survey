import logging
from pathlib import Path
from interface.cli.interactive_cli import InteractiveCLI


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """병원 만족도 설문조사 플랫폼 CLI를 실행합니다."""
    try:
        data_dir = Path("data")
        cli = InteractiveCLI(data_dir)
        cli.run()

    except Exception:
        logger.exception("프로그램 실행 중 오류가 발생했습니다")
        raise


if __name__ == "__main__":
    main()
