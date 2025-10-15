from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from interface.api.routers import surveys, responses


app = FastAPI(
    title="병원 만족도 설문조사 API",
    description="DDD 기반 병원 만족도 설문조사 플랫폼 RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(surveys.router, prefix="/api/v1")
app.include_router(responses.router, prefix="/api/v1")


@app.get("/", tags=["health"])
def health_check() -> dict[str, str]:
    """헬스 체크 엔드포인트입니다.

    Returns:
        상태 정보
    """
    return {"status": "healthy", "message": "병원 만족도 설문조사 API가 정상 작동 중입니다"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """헬스 체크 엔드포인트입니다.

    Returns:
        상태 정보
    """
    return {"status": "healthy"}
