# 배포 가이드

## PostgreSQL 설정

### 1. PostgreSQL 서버 시작

```bash
cd deployment/postgresql

# .env 파일 생성
cat > .env << EOF
POSTGRES_DB=saas_survey
POSTGRES_USER=survey_admin
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=5432
EOF

# Docker Compose로 PostgreSQL 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 2. 데이터베이스 연결 확인

```bash
# PostgreSQL 컨테이너 접속
docker exec -it saas_survey_db psql -U survey_admin -d saas_survey

# 테이블 목록 확인
\dt

# 종료
\q
```

## 테스트 계정 생성

### 1. 의존성 설치

```bash
# psycopg2-binary 설치 (PostgreSQL 드라이버)
pip install psycopg2-binary
```

### 2. 테스트 계정 생성 스크립트 실행

```bash
# 환경변수 설정 후 실행
POSTGRES_PASSWORD=your_secure_password_here python scripts/add_test_account.py
```

**생성되는 계정:**
- 테넌트: Hospital
- 이메일: admin@hospital.com
- 비밀번호: password123
- 역할: TENANT_ADMIN (전체 권한)

### 3. 로그인 테스트

스크립트 실행 시 출력되는 API 키를 복사하여 사용합니다.

```bash
# 출력 예시:
# ==================================================
# 테스트 계정 정보
# ==================================================
# 테넌트: Hospital
# 테넌트 ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# 사용자명: admin
# 이메일: admin@hospital.com
# 비밀번호: password123
# 역할: TENANT_ADMIN
# API 키: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ==================================================
```

## 환경변수 설정

스크립트는 다음 환경변수를 사용합니다:

| 환경변수 | 기본값 | 설명 |
|---------|--------|------|
| POSTGRES_HOST | 10.10.20.21 | PostgreSQL 호스트 |
| POSTGRES_PORT | 5432 | PostgreSQL 포트 |
| POSTGRES_DB | saas_survey | 데이터베이스 이름 |
| POSTGRES_USER | survey_admin | 사용자 이름 |
| POSTGRES_PASSWORD | (필수) | 비밀번호 |

## 문제 해결

### 연결 실패 시

1. PostgreSQL 서버가 실행 중인지 확인
   ```bash
   docker ps | grep saas_survey_db
   ```

2. 방화벽 확인
   ```bash
   # 포트 5432가 열려있는지 확인
   telnet 10.10.20.21 5432
   ```

3. PostgreSQL 로그 확인
   ```bash
   docker-compose logs postgres
   ```

### 계정 생성 실패 시

1. 이미 동일한 이름의 테넌트/사용자가 있는지 확인
2. 데이터베이스 테이블이 올바르게 생성되었는지 확인
3. 스크립트 로그에서 에러 메시지 확인
