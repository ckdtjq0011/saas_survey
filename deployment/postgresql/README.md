# PostgreSQL 설정 - 빠른 시작 가이드

## 🚀 빠른 설치 (3단계)

### 1️⃣ 우분투 서버에 파일 업로드

```bash
# 로컬 PC에서 실행
scp -r deployment/postgresql user@your-server-ip:/home/user/postgresql-setup
```

### 2️⃣ 서버에서 설치 스크립트 실행

```bash
# 서버에 SSH 접속
ssh user@your-server-ip

# 설치 디렉토리로 이동
cd /home/user/postgresql-setup

# 실행 권한 부여
chmod +x setup-postgresql.sh backup.sh

# PostgreSQL 설치 및 설정 (자동)
sudo ./setup-postgresql.sh
```

**중요**: 스크립트가 출력하는 비밀번호를 꼭 저장하세요!

### 3️⃣ FastAPI 프로젝트 연동

프로젝트 루트의 `.env` 파일 수정:

```env
# PostgreSQL 설정
storage_type=postgresql
DATABASE_URL=postgresql://survey_admin:비밀번호@서버IP:5432/saas_survey
```

마이그레이션 실행:
```bash
cd C:\Dev\Python\saas_survey
alembic upgrade head
```

## 📋 설치되는 항목

- ✅ Docker & Docker Compose
- ✅ PostgreSQL 18 (Alpine 기반)
- ✅ SSL 인증서 (자동 생성)
- ✅ 보안 설정 (암호화 연결)
- ✅ 자동 백업 스크립트

## 🔧 자주 사용하는 명령어

```bash
# 컨테이너 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f

# PostgreSQL 콘솔 접속
docker exec -it saas_survey_db psql -U survey_admin -d saas_survey

# 백업 생성
./backup.sh

# 재시작
docker compose restart

# 중지
docker compose down

# 시작
docker compose up -d
```

## 🔍 연결 정보

설치 후 다음 정보로 접속:

- **Host**: `서버 IP 주소`
- **Port**: `5432`
- **Database**: `saas_survey`
- **User**: `survey_admin`
- **Password**: `스크립트 실행 시 출력된 비밀번호` (또는 `.env` 파일 확인)

## 🛠 문제 해결

### 컨테이너가 시작 안 됨
```bash
docker compose logs
```

### 연결이 안 됨
```bash
# 포트 확인
sudo netstat -tulpn | grep 5432

# 방화벽 확인
sudo ufw status
```

### 비밀번호 분실
```bash
# .env 파일 확인
cat .env
```

## 🔒 보안 설정 (선택)

### 방화벽 설정
```bash
# SSH 먼저 허용 (중요!)
sudo ufw allow ssh

# PostgreSQL 특정 IP만 허용
sudo ufw allow from YOUR_CLIENT_IP to any port 5432

# 활성화
sudo ufw enable
```

### 비밀번호 변경
```bash
# PostgreSQL 콘솔 접속
docker exec -it saas_survey_db psql -U survey_admin -d saas_survey

# 비밀번호 변경
ALTER USER survey_admin WITH PASSWORD 'new_password';
\q

# .env 파일도 업데이트
nano .env
```

## 📚 상세 문서

더 자세한 내용은 `README-POSTGRESQL.md` 파일을 참고하세요:
- 상세 설치 가이드
- 성능 최적화
- 백업 및 복구
- SSL 인증서 업그레이드
- 모니터링 방법

## 🆘 긴급 백업

```bash
# 즉시 백업
./backup.sh

# 백업 파일 위치
ls -lh backups/
```

## 📞 지원

문제 발생 시:
1. `docker compose logs -f` 로그 확인
2. `README-POSTGRESQL.md` 상세 가이드 확인
3. PostgreSQL 로그: `docker exec saas_survey_db cat /var/lib/postgresql/data/log/postgresql-*.log`

---

## ⚡ 한 줄 요약

```bash
# 1. 파일 업로드 → 2. sudo ./setup-postgresql.sh → 3. 비밀번호 저장 → 완료!
```

**이게 전부입니다!** 🎉
