# PostgreSQL 18 Setup Guide for SaaS Survey Platform

이 가이드는 우분투 서버에 Docker Compose를 사용하여 PostgreSQL 18을 설정하는 방법을 설명합니다.

## 사전 요구사항

- Ubuntu 20.04 LTS 이상
- Root 또는 sudo 권한
- 최소 2GB RAM
- 최소 10GB 여유 디스크 공간

## 설치 단계

### 1. 파일 업로드

이 폴더의 모든 파일을 우분투 서버에 업로드합니다:

```bash
# 로컬에서 서버로 복사 (예시)
scp -r deployment/postgresql user@your-server:/home/user/postgresql-setup
```

### 2. 서버 접속 및 권한 설정

```bash
ssh user@your-server
cd /home/user/postgresql-setup

# 스크립트에 실행 권한 부여
chmod +x setup-postgresql.sh backup.sh
```

### 3. PostgreSQL 설치 실행

```bash
sudo ./setup-postgresql.sh
```

이 스크립트는 다음을 자동으로 수행합니다:
- 시스템 패키지 업데이트
- Docker 및 Docker Compose 설치
- SSL 인증서 생성
- 환경 변수 파일 생성 (랜덤 비밀번호 포함)
- PostgreSQL 컨테이너 시작

**중요**: 스크립트 실행 후 출력된 비밀번호를 안전하게 저장하세요!

### 4. 연결 테스트

```bash
# 컨테이너 상태 확인
docker compose ps

# PostgreSQL 연결 테스트
docker exec -it saas_survey_db psql -U survey_admin -d saas_survey

# SQL 쿼리 실행 테스트
\l  # 데이터베이스 목록
\q  # 종료
```

## FastAPI 프로젝트 연동

### 1. 프로젝트 루트에 .env 파일 업데이트

`C:\Dev\Python\saas_survey\.env` 파일에 다음 내용 추가:

```env
# PostgreSQL Configuration
DATABASE_URL=postgresql://survey_admin:YOUR_PASSWORD@YOUR_SERVER_IP:5432/saas_survey
storage_type=sqlite  # 처음에는 sqlite로 유지
```

### 2. config.py 확인

`config.py`에서 환경 변수를 올바르게 읽는지 확인:

```python
class Settings(BaseSettings):
    storage_type: str = "sqlite"  # 또는 "postgresql"
    database_url: str = "sqlite:///./data/saas_survey.db"
    # ...
```

### 3. SQLite에서 PostgreSQL로 마이그레이션

#### 옵션 A: 새로운 데이터베이스로 시작

`.env` 파일 수정:
```env
storage_type=postgresql
DATABASE_URL=postgresql://survey_admin:YOUR_PASSWORD@YOUR_SERVER_IP:5432/saas_survey
```

Alembic 마이그레이션 실행:
```bash
cd C:\Dev\Python\saas_survey
alembic upgrade head
```

#### 옵션 B: 기존 데이터 마이그레이션 (선택)

SQLite 데이터를 PostgreSQL로 이동하려면 별도 스크립트가 필요합니다.

### 4. 애플리케이션 재시작

```bash
# 로컬에서 API 서버 재시작
python app.py
```

브라우저에서 http://localhost:8000/docs 접속하여 API가 정상 작동하는지 확인

## 관리 명령어

### 컨테이너 관리

```bash
# 로그 확인
docker compose logs -f

# 컨테이너 재시작
docker compose restart

# 컨테이너 중지
docker compose down

# 컨테이너 시작
docker compose up -d

# 컨테이너 상태 확인
docker compose ps
```

### 데이터베이스 관리

```bash
# PostgreSQL 콘솔 접속
docker exec -it saas_survey_db psql -U survey_admin -d saas_survey

# 백업 생성
./backup.sh

# 백업 복원
gunzip -c backups/saas_survey_backup_TIMESTAMP.sql.gz | \
  docker exec -i saas_survey_db psql -U survey_admin -d saas_survey
```

### 모니터링

```bash
# 리소스 사용량 확인
docker stats saas_survey_db

# 연결 수 확인
docker exec saas_survey_db psql -U survey_admin -d saas_survey -c \
  "SELECT count(*) FROM pg_stat_activity;"

# 데이터베이스 크기 확인
docker exec saas_survey_db psql -U survey_admin -d saas_survey -c \
  "SELECT pg_size_pretty(pg_database_size('saas_survey'));"
```

## 보안 설정

### 방화벽 설정 (선택)

```bash
# UFW 설치 및 활성화
sudo apt-get install -y ufw

# SSH 허용 (먼저!)
sudo ufw allow ssh

# PostgreSQL 포트 허용 (특정 IP만)
sudo ufw allow from YOUR_CLIENT_IP to any port 5432

# 방화벽 활성화
sudo ufw enable

# 상태 확인
sudo ufw status
```

### SSL 인증서 업그레이드 (프로덕션)

Self-signed 인증서 대신 Let's Encrypt 사용:

```bash
# Certbot 설치
sudo apt-get install -y certbot

# 인증서 발급 (도메인 필요)
sudo certbot certonly --standalone -d your-domain.com

# 인증서 복사
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/server.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/server.key
sudo chmod 600 ssl/server.key

# 컨테이너 재시작
docker compose restart
```

### 비밀번호 변경

```bash
# PostgreSQL 콘솔 접속
docker exec -it saas_survey_db psql -U survey_admin -d saas_survey

# 비밀번호 변경
ALTER USER survey_admin WITH PASSWORD 'new_strong_password';
\q

# .env 파일도 업데이트
nano .env
```

## 문제 해결

### 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker compose logs

# 포트 충돌 확인
sudo netstat -tulpn | grep 5432

# 권한 확인
ls -la ssl/
ls -la postgres-data/
```

### 연결 거부 오류

1. 방화벽 확인
2. `pg_hba.conf`에서 IP 대역 확인
3. 네트워크 설정 확인

```bash
# PostgreSQL이 실제로 수신 대기 중인지 확인
docker exec saas_survey_db netstat -tulpn | grep 5432
```

### 성능 최적화

`postgresql.conf`에서 메모리 설정 조정:

```conf
# 서버 RAM의 25%
shared_buffers = 1GB

# 서버 RAM의 50-75%
effective_cache_size = 4GB
```

컨테이너 재시작:
```bash
docker compose restart
```

## 백업 및 복구

### 자동 백업 설정 (Cron)

```bash
# Cron 편집
crontab -e

# 매일 새벽 2시 백업 추가
0 2 * * * cd /home/user/postgresql-setup && ./backup.sh >> ./backup.log 2>&1
```

### 수동 백업

```bash
./backup.sh
```

### 복구

```bash
# 백업 파일 압축 해제 및 복원
gunzip -c backups/saas_survey_backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i saas_survey_db psql -U survey_admin -d saas_survey
```

## 참고 자료

- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)

## 지원

문제가 발생하면 다음을 확인하세요:
1. Docker 로그: `docker compose logs -f`
2. PostgreSQL 로그: `docker exec saas_survey_db cat /var/lib/postgresql/data/log/postgresql-*.log`
3. 연결 테스트: `telnet YOUR_SERVER_IP 5432`
