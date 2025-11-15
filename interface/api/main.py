from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import settings
from interface.api.exceptions import global_exception_handler
from interface.api.routers import (
    auth,
    surveys,
    questions,
    categories,
    responses,
    results,
    sessions
)


app = FastAPI(
    title="SaaS 설문조사 플랫폼 API",
    description="""
## SaaS 멀티테넌트 설문조사 플랫폼 RESTful API

DDD 4계층 구조로 설계된 설문조사 플랫폼입니다.

### 주요 기능
- 멀티테넌트 지원 (테넌트 격리)
- 역할 기반 권한 관리 (RBAC)
- 세션 기반 인증 (X-API-Key 헤더)
- 설문 생성 및 관리
- 다양한 질문 유형 지원 (TEXT, RATING, MULTIPLE_CHOICE, 등)
- 응답 수집 및 통계 분석
- CSV 내보내기

### 인증
모든 API (로그인, 테넌트 등록, 사용자 등록 제외)는 인증이 필요합니다.
로그인 후 발급받은 API 키를 요청 헤더에 포함하세요:
```
X-API-Key: your-api-key-here
```

### 역할
- **TENANT_ADMIN**: 모든 권한 (테넌트 관리, 사용자 관리, 설문 관리, 결과 조회)
- **SURVEY_MANAGER**: 설문 생성 및 관리, 결과 조회
- **RESPONDENT**: 설문 응답만 가능

### 데이터베이스
- 개발: SQLite (data/saas_survey.db)
- 프로덕션: PostgreSQL (DI로 쉽게 전환 가능)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(Exception, global_exception_handler)


app.include_router(auth.router, prefix="/api/v1")
app.include_router(surveys.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(responses.router, prefix="/api/v1")
app.include_router(results.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")


@app.get("/", tags=["헬스체크"])
def root() -> dict[str, str]:
    """루트 엔드포인트입니다.

    Returns:
        상태 정보
    """
    return {
        "status": "healthy",
        "message": "SaaS 설문조사 플랫폼 API가 정상 작동 중입니다",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["헬스체크"])
def health_check() -> dict[str, str]:
    """헬스 체크 엔드포인트입니다.

    Returns:
        상태 정보
    """
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행됩니다."""
    logger.info("SaaS 설문조사 플랫폼 API 서버 시작")
    logger.info(f"스토리지 타입: {settings.storage_type}")
    logger.info(f"데이터베이스 URL: {settings.database_url}")
    logger.info(f"CORS Origins: {settings.cors_origins}")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행됩니다."""
    logger.info("SaaS 설문조사 플랫폼 API 서버 종료")
