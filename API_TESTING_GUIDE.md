# SaaS Survey API 테스트 가이드

## 서버 실행 방법

```bash
# 서버 시작
uv run python run.py

# 또는 uvicorn으로 직접 실행
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## API 테스트 방법

### 1. 자동 테스트 스크립트 사용

```bash
# 전체 API 테스트 실행
uv run python test_api.py
```

### 2. FastAPI 자동 문서 사용

서버 실행 후 브라우저에서 접속:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 수동 테스트 (curl 또는 Postman)

#### 루트 엔드포인트 확인
```bash
curl http://localhost:8000/
```

#### 설문 생성
```bash
curl -X POST http://localhost:8000/surveys \
  -H "Content-Type: application/json" \
  -d '{
    "title": "고객 만족도 조사",
    "description": "서비스 만족도 조사",
    "questions": [
      {
        "question": "만족도는?",
        "type": "rating",
        "options": ["1", "2", "3", "4", "5"]
      }
    ]
  }'
```

#### 모든 설문 조회
```bash
curl http://localhost:8000/surveys
```

#### 특정 설문 조회
```bash
curl http://localhost:8000/surveys/1
```

#### 설문 응답 제출
```bash
curl -X POST http://localhost:8000/responses \
  -H "Content-Type: application/json" \
  -d '{
    "survey_id": 1,
    "respondent": "user@example.com",
    "answers": [
      {
        "question_index": 0,
        "answer": "5"
      }
    ]
  }'
```

#### 설문 응답 조회
```bash
curl http://localhost:8000/surveys/1/responses
```

## 환경 설정

### IP 설정 변경

#### run.py에서 host 설정
```python
# 로컬 테스트 (localhost만 접속 가능)
host="127.0.0.1"  # 기본값

# 네트워크 접속 (다른 기기에서 접속 가능)
host="0.0.0.0"  # 모든 네트워크 인터페이스에서 접속 허용
```

#### config.py에서 API 호출 설정
```python
# 로컬 테스트
API_HOST = "localhost"

# 네트워크 접속 (다른 기기에서 접속 가능)
API_HOST = "10.10.10.26"  # 실제 IP 주소로 변경
```

### 방화벽 설정 (Windows)

포트 8000을 열어야 외부에서 접속 가능:

```powershell
# Windows PowerShell (관리자 권한)
New-NetFirewallRule -DisplayName "FastAPI Port 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

## 문제 해결

### 서버가 시작되지 않을 때
1. 포트 8000이 사용 중인지 확인: `netstat -an | findstr 8000`
2. Python 환경 확인: `uv run python --version`
3. 의존성 재설치: `uv pip install -r requirements.txt`

### API 호출이 실패할 때
1. 서버 로그 확인
2. 네트워크 연결 확인: `ping localhost`
3. 방화벽 설정 확인
4. CORS 설정 확인 (main.py)

### 데이터베이스 오류
1. survey.db 파일 권한 확인
2. 데이터베이스 초기화: 
   ```python
   from app.db.base import engine, Base
   Base.metadata.drop_all(bind=engine)
   Base.metadata.create_all(bind=engine)
   ```

## API 엔드포인트 요약

### Public Endpoints (인증 불필요)
- `GET /` - API 정보
- `GET /health` - 헬스 체크
- `GET /surveys` - 모든 설문 조회
- `POST /surveys` - 새 설문 생성
- `GET /surveys/{id}` - 특정 설문 조회
- `GET /surveys/{id}/responses` - 설문 응답 조회
- `POST /responses` - 설문 응답 제출

### Protected Endpoints (인증 필요)
- `/api/v1/users/*` - 사용자 관리
- `/api/v1/forms/*` - 설문 관리 (고급)
- `/api/v1/responses/*` - 응답 관리 (고급)