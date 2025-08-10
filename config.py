# API 서버 설정
# 외부 접속용 (production)
# API_HOST = "10.10.10.26"

# 로컬 테스트용
API_HOST = "localhost"
API_PORT = 8000
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# 데이터베이스 설정
DATABASE_URL = "sqlite:///./survey.db"

# 기타 설정
DEBUG = True
MAX_QUESTIONS_PER_SURVEY = 50
MAX_RESPONSES_PER_USER = 10