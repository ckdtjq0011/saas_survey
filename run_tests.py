import sys
import subprocess
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_tests() -> int:
    """시나리오 테스트를 실행합니다.

    Returns:
        테스트 실행 결과 코드 (0: 성공, 1: 실패)

    Raises:
        Exception: 테스트 실행 중 오류 발생 시
    """
    try:
        logger.info("시나리오 테스트를 시작합니다")

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_scenarios.py", "-v", "--tb=short"],
            check=False
        )

        if result.returncode == 0:
            logger.info("모든 테스트가 통과했습니다")
        else:
            logger.error("일부 테스트가 실패했습니다")

        return result.returncode

    except Exception:
        logger.exception("테스트 실행 중 오류가 발생했습니다")
        raise


if __name__ == "__main__":
    sys.exit(run_tests())
