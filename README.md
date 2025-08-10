# SaaS Survey Platform

[![CI](https://github.com/ckdtjq0011/saas_survey/actions/workflows/ci.yml/badge.svg)](https://github.com/ckdtjq0011/saas_survey/actions/workflows/ci.yml)
[![CD - Deploy](https://github.com/ckdtjq0011/saas_survey/actions/workflows/cd.yml/badge.svg)](https://github.com/ckdtjq0011/saas_survey/actions/workflows/cd.yml)

구글폼과 유사한 설문조사 플랫폼 백엔드 API - FastAPI와 현대적인 Python 도구로 구축

## 🚀 주요 기능

### 인증 시스템
- 🔐 회원가입/로그인 (JWT 토큰)
- 👤 사용자 인증 및 권한 관리

### 설문 관리 
- 📝 CRUD (생성/조회/수정/삭제)
- 🔗 공유 링크 생성
- 📋 설문 복사
- ⏰ 응답 기한 설정
- 🔢 응답 수 제한
- 🔒 로그인 필수 옵션

### 응답 시스템
- ✅ 응답 제출/조회/수정/삭제
- 🛡️ 답변 유효성 검증
- 🚫 중복 응답 방지
- ⭐ 필수 답변 확인

### 통계 및 내보내기
- 📊 응답 통계 조회
- 📁 CSV 내보내기
- 📄 JSON 내보내기

## 🛠️ 기술 스택

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: SQLite (개발), PostgreSQL (운영)
- **Authentication**: JWT with python-jose
- **Package Management**: uv (초고속 Python 패키지 관리자)
- **Testing**: pytest, pytest-cov
- **CI/CD**: GitHub Actions
- **Containerization**: Docker, Docker Compose

## 📋 사전 요구사항

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (권장) 또는 pip

## 🔧 설치 방법

### uv 사용 (권장)

```bash
# 저장소 클론
git clone https://github.com/ckdtjq0011/saas_survey.git
cd saas_survey

# uv 설치 (아직 설치하지 않은 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync

# 환경변수 설정
cp .env.example .env

# 안전한 SECRET_KEY 생성
python -c "import secrets; print(secrets.token_hex(32))"
# 생성된 키를 .env 파일에 추가

# 애플리케이션 실행
uv run uvicorn app.main:app --reload
```

### Docker 사용

```bash
# 저장소 클론
git clone https://github.com/ckdtjq0011/saas_survey.git
cd saas_survey

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 설정

# Docker Compose로 빌드 및 실행
docker-compose up -d
```

## 🧪 개발

### 테스트 실행

```bash
# 모든 테스트 실행
uv run pytest

# 커버리지 포함 실행
uv run pytest --cov=app --cov-report=html

# 특정 테스트 파일 실행
uv run pytest tests/test_config.py -v
```

### 코드 품질

```bash
# 코드 포맷팅
uv run ruff format .

# 린트 검사
uv run ruff check .

# 타입 체킹
uv run mypy app
```

## 📚 API 문서

애플리케이션 실행 후 접속 가능:

- **대화형 API 문서**: http://localhost:8000/docs
- **대체 API 문서**: http://localhost:8000/redoc
- **OpenAPI 스키마**: http://localhost:8000/api/v1/openapi.json

## 🌐 주요 API 엔드포인트

### 인증
- `POST /auth/register` - 회원가입
- `POST /auth/login` - 로그인  
- `GET /auth/me` - 내 정보

### 설문
- `POST /surveys/` - 설문 생성
- `GET /surveys/` - 설문 목록
- `GET /surveys/{id}` - 설문 조회
- `PUT /surveys/{id}` - 설문 수정
- `DELETE /surveys/{id}` - 설문 삭제
- `GET /surveys/s/{token}` - 공유 링크로 조회
- `POST /surveys/{id}/duplicate` - 설문 복사
- `GET /surveys/{id}/stats` - 통계

### 응답
- `POST /responses/` - 응답 제출
- `GET /responses/{id}` - 응답 조회
- `PUT /responses/{id}` - 응답 수정
- `DELETE /responses/{id}` - 응답 삭제

### 내보내기
- `GET /export/{id}/csv` - CSV 다운로드
- `GET /export/{id}/json` - JSON 다운로드

## 📁 프로젝트 구조

```
saas_survey/
├── app/
│   ├── api/           # API 엔드포인트
│   ├── core/          # 핵심 설정
│   ├── db/            # 데이터베이스 설정
│   ├── models/        # SQLAlchemy 모델
│   └── main.py        # 애플리케이션 진입점
├── tests/             # 테스트 파일
├── .github/
│   └── workflows/     # CI/CD 워크플로우
├── docker-compose.yml # Docker Compose 설정
├── Dockerfile         # Docker 설정
├── pyproject.toml     # 프로젝트 의존성
├── uv.lock           # 고정된 의존성
└── README.md         # 이 파일
```

## 🔑 환경 변수

주요 환경 변수 (전체 목록은 `.env.example` 참조):

- `SECRET_KEY`: JWT용 비밀 키 (필수, 최소 32자)
- `DATABASE_URL`: 데이터베이스 연결 문자열
- `DEBUG`: 디버그 모드 (True/False)
- `BACKEND_CORS_ORIGINS`: 허용된 CORS 출처

## 🚀 CI/CD 파이프라인

### Continuous Integration (CI)

모든 push와 pull request에서 실행:

1. **테스팅**: Python 3.10, 3.11, 3.12에서 실행
2. **린팅**: ruff로 코드 품질 검사
3. **타입 체킹**: mypy로 정적 타입 분석
4. **보안**: pip-audit과 bandit으로 취약점 스캔
5. **커버리지**: codecov로 테스트 커버리지 보고

### Continuous Deployment (CD)

배포 파이프라인:

1. **빌드**: Docker 이미지 생성 및 GitHub Container Registry에 푸시
2. **배포**: 스테이징/프로덕션 환경에 자동 배포
   - 스테이징: `dev` 브랜치에서 배포
   - 프로덕션: `main` 브랜치에서 배포 (수동 승인 필요)

## 🤝 기여하기

1. 저장소 포크
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 열기

## 🔒 보안

- 모든 민감한 설정은 환경 변수로 관리
- 인증을 위한 JWT 토큰
- bcrypt로 비밀번호 해싱
- SQLAlchemy ORM으로 SQL 인젝션 방지
- Dependabot으로 정기적인 의존성 업데이트

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 있습니다 - 자세한 내용은 LICENSE 파일을 참조하세요.

## 📞 연락처

- GitHub: [@ckdtjq0011](https://github.com/ckdtjq0011)
- 프로젝트 링크: [https://github.com/ckdtjq0011/saas_survey](https://github.com/ckdtjq0011/saas_survey)