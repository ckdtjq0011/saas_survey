import uvicorn
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """FastAPI 애플리케이션을 실행합니다."""
    logger.info("FastAPI 서버를 시작합니다")
    logger.info("Swagger UI: http://localhost:8000/docs")
    logger.info("ReDoc: http://localhost:8000/redoc")

    uvicorn.run(
        "interface.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
